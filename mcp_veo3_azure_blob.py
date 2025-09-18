#!/usr/bin/env python3
"""
MCP Veo 3 Video Generator - A Model Context Protocol server for Veo 3 video generation and Azure Blob Upload
Usage:
  python mcp_veo3_azure_blob.py --output-dir ~/Videos/Generated
"""

import argparse
import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastmcp import FastMCP, Context
from pydantic import BaseModel
from dotenv import load_dotenv

try:
    from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
except ImportError:
    BlobServiceClient = None
    BlobClient = None
    ContainerClient = None

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:
    genai = None
    genai_types = None

# Load environment variables from .env file
load_dotenv()

# Parse CLI arguments
parser = argparse.ArgumentParser()
parser.add_argument("--output-dir", required=True, help="Directory to save generated videos")
parser.add_argument("--api-key", help="Gemini API key (overrides .env)")
args = parser.parse_args()

OUTPUT_DIR = os.path.abspath(os.path.expanduser(args.output_dir))

# Get API key from CLI args or environment
API_KEY = args.api_key or os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("Gemini API key must be provided via --api-key argument or GEMINI_API_KEY in .env file")

# Azure Blob Storage configuration
AZURE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_CONTAINER_NAME = os.getenv("AZURE_BLOB_CONTAINER_NAME", "generated-videos")
AZURE_UPLOAD_ENABLED = os.getenv("AZURE_UPLOAD_ENABLED", "true").lower() == "true"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-veo3-azure-blob")

# Initialize FastMCP
mcp = FastMCP("MCP Veo 3 Video Generator with Azure Blob Upload")

# Initialize Gemini client
if not genai:
    raise ImportError("google-genai package not installed. Run: pip install google-genai")

gemini_client = genai.Client(api_key=API_KEY)


class VideoGenerationResponse(BaseModel):
    video_path: str
    filename: str
    model: str
    prompt: str
    negative_prompt: Optional[str] = None
    generation_time: float
    file_size: int
    aspect_ratio: str
    azure_blob_url: Optional[str] = None
    azure_upload_success: bool = False


class VideoListResponse(BaseModel):
    videos: list[dict]
    total_count: int
    output_dir: str


class VideoInfoResponse(BaseModel):
    filename: str
    path: str
    size: int
    created: str
    modified: str
    azure_blob_url: Optional[str] = None


class AzureBlobUploadResponse(BaseModel):
    success: bool
    blob_url: Optional[str] = None
    error_message: Optional[str] = None
    upload_time: float
    file_size: int


class AzureBlobListResponse(BaseModel):
    blobs: list[dict]
    total_count: int
    container_name: str
def safe_join(root: str, user_path: str) -> str:
    """Safely join paths and prevent directory traversal"""
    abs_path = os.path.abspath(os.path.join(root, user_path))
    if not abs_path.startswith(root):
        raise ValueError("Path escapes allowed root")
    return abs_path


def get_azure_blob_client() -> Optional[BlobServiceClient]:
    """Initialize Azure Blob Service Client"""
    if not BlobServiceClient or not AZURE_CONNECTION_STRING:
        return None
    
    try:
        return BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
    except Exception as e:
        logger.error(f"Failed to initialize Azure Blob client: {str(e)}")
        return None


async def upload_to_azure_blob(
    file_path: str, 
    blob_name: str, 
    ctx: Context
) -> AzureBlobUploadResponse:
    """Upload a file to Azure Blob Storage"""
    start_time = time.time()
    
    if not AZURE_UPLOAD_ENABLED:
        await ctx.info("Azure upload is disabled")
        return AzureBlobUploadResponse(
            success=False,
            error_message="Azure upload is disabled",
            upload_time=0,
            file_size=0
        )
    
    if not BlobServiceClient:
        await ctx.error("Azure Storage SDK not available. Install: pip install azure-storage-blob")
        return AzureBlobUploadResponse(
            success=False,
            error_message="Azure Storage SDK not available",
            upload_time=0,
            file_size=0
        )
    
    if not AZURE_CONNECTION_STRING:
        await ctx.error("Azure connection string not configured")
        return AzureBlobUploadResponse(
            success=False,
            error_message="Azure connection string not configured",
            upload_time=0,
            file_size=0
        )
    
    try:
        blob_service_client = get_azure_blob_client()
        if not blob_service_client:
            raise Exception("Failed to initialize Azure Blob client")
        
        # Create container if it doesn't exist
        container_client = blob_service_client.get_container_client(AZURE_CONTAINER_NAME)
        try:
            container_client.create_container()
            await ctx.info(f"Created Azure container: {AZURE_CONTAINER_NAME}")
        except Exception:
            # Container already exists, which is fine
            pass
        
        # Upload the file
        await ctx.info(f"Uploading {blob_name} to Azure Blob Storage...")
        
        with open(file_path, "rb") as data:
            blob_client = blob_service_client.get_blob_client(
                container=AZURE_CONTAINER_NAME, 
                blob=blob_name
            )
            blob_client.upload_blob(data, overwrite=True)
        
        # Get the blob URL
        blob_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{AZURE_CONTAINER_NAME}/{blob_name}"
        
        file_size = os.path.getsize(file_path)
        upload_time = time.time() - start_time
        
        await ctx.info(f"Successfully uploaded to Azure Blob: {blob_url}")
        
        return AzureBlobUploadResponse(
            success=True,
            blob_url=blob_url,
            upload_time=upload_time,
            file_size=file_size
        )
        
    except Exception as e:
        upload_time = time.time() - start_time
        error_msg = f"Azure upload failed: {str(e)}"
        await ctx.error(error_msg)
        
        return AzureBlobUploadResponse(
            success=False,
            error_message=error_msg,
            upload_time=upload_time,
            file_size=os.path.getsize(file_path) if os.path.exists(file_path) else 0
        )


async def generate_video_with_progress(
    prompt: str,
    model: str,
    ctx: Context,
    image_path: Optional[str] = None,
    poll_interval: int = 10,
    max_poll_time: int = 600
) -> dict:
    """Generate a video using Veo 3 with progress tracking"""
    
    start_time = time.time()
    
    try:
        await ctx.info(f"Starting video generation with model: {model}")
        await ctx.info(f"Prompt: {prompt[:100]}...")
        
        # Start video generation - using official API format
        await ctx.report_progress(progress=5, total=100)
        
        if image_path and os.path.exists(image_path):
            await ctx.info(f"Uploading image: {image_path}")
            image_file = gemini_client.files.upload(path=image_path)
            # For image-to-video, we need to pass the image
            operation = gemini_client.models.generate_videos(
                model=model,
                prompt=prompt,
                image=image_file
            )
        else:
            # For text-to-video, only model and prompt are needed
            operation = gemini_client.models.generate_videos(
                model=model,
                prompt=prompt
            )
        
        await ctx.report_progress(progress=10, total=100)
        
        # Poll for completion with progress updates
        while not operation.done:
            elapsed = time.time() - start_time
            if elapsed > max_poll_time:
                await ctx.report_progress(progress=0, total=100)  # Reset on timeout
                raise TimeoutError(f"Video generation timed out after {max_poll_time} seconds")
            
            # Calculate progress based on elapsed time (rough estimate)
            # Most generations take 30-300 seconds, so we'll estimate progress
            estimated_progress = min(10 + (elapsed / 300) * 80, 85)  # Cap at 85% until done
            await ctx.report_progress(progress=int(estimated_progress), total=100)
            
            await ctx.info(f"Generating video... ({elapsed:.1f}s elapsed)")
            await asyncio.sleep(poll_interval)
            operation = gemini_client.operations.get(operation)
        
        # Check if generation was successful
        if not hasattr(operation.response, 'generated_videos') or not operation.response.generated_videos:
            await ctx.report_progress(progress=0, total=100)  # Reset on error
            raise RuntimeError("Video generation failed - no videos in response")
        
        generated_video = operation.response.generated_videos[0]
        
        await ctx.report_progress(progress=90, total=100)
        
        # Ensure output directory exists
        output_dir = Path(OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"veo3_video_{timestamp}.mp4"
        output_path = output_dir / filename
        
        # Download the video
        await ctx.info(f"Downloading video to: {output_path}")
        gemini_client.files.download(file=generated_video.video)
        generated_video.video.save(str(output_path))
        
        await ctx.report_progress(progress=95, total=100)
        
        file_size = output_path.stat().st_size if output_path.exists() else 0
        generation_time = time.time() - start_time
        
        await ctx.info(f"Video generation completed in {generation_time:.1f} seconds")
        
        # Upload to Azure Blob Storage if enabled
        azure_blob_url = None
        azure_upload_success = False
        
        if AZURE_UPLOAD_ENABLED and output_path.exists():
            await ctx.info("Uploading video to Azure Blob Storage...")
            upload_result = await upload_to_azure_blob(
                file_path=str(output_path),
                blob_name=filename,
                ctx=ctx
            )
            azure_upload_success = upload_result.success
            azure_blob_url = upload_result.blob_url
        
        await ctx.report_progress(progress=100, total=100)
        
        return {
            "video_path": str(output_path),
            "filename": filename,
            "model": model,
            "prompt": prompt,
            "negative_prompt": None,  # Not supported in current API
            "generation_time": generation_time,
            "file_size": file_size,
            "aspect_ratio": "16:9",  # Default for Veo 3
            "azure_blob_url": azure_blob_url,
            "azure_upload_success": azure_upload_success
        }
        
    except Exception as e:
        await ctx.report_progress(progress=0, total=100)  # Reset on error
        await ctx.error(f"Video generation failed: {str(e)}")
        raise ValueError(f"Video generation failed: {str(e)}")

@mcp.tool()
async def generate_video(
    prompt: str,
    ctx: Context,
    model: str = "veo-3.0-generate-preview"
) -> VideoGenerationResponse:
    """Generate a video using Google Veo 3 from a text prompt
    
    Args:
        prompt: Text prompt describing the video to generate
        model: Veo model to use (veo-3.0-generate-preview, veo-3.0-fast-generate-preview, veo-2.0-generate-001)
    
    Returns:
        VideoGenerationResponse with video path, metadata, and generation info
    
    Note: Veo 3 generates 8-second 720p videos with audio. Aspect ratio and other advanced 
    parameters are not currently supported in the public API.
    """
    
    await ctx.info(f"Starting video generation with prompt: {prompt[:100]}...")
    
    if not prompt.strip():
        await ctx.error("Prompt cannot be empty")
        raise ValueError("Prompt cannot be empty")
    
    # Validate model
    valid_models = ["veo-3.0-generate-preview", "veo-3.0-fast-generate-preview", "veo-2.0-generate-001"]
    if model not in valid_models:
        await ctx.error(f"Invalid model: {model}. Must be one of: {valid_models}")
        raise ValueError(f"Invalid model: {model}")
    
    try:
        result = await generate_video_with_progress(
            prompt=prompt,
            model=model,
            ctx=ctx
        )
        
        await ctx.info(f"Video generated successfully: {result['filename']}")
        
        return VideoGenerationResponse(**result)
        
    except Exception as e:
        await ctx.error(f"Video generation failed: {str(e)}")
        raise ValueError(f"Video generation failed: {str(e)}")

@mcp.tool()
async def generate_video_from_image(
    prompt: str,
    image_path: str,
    ctx: Context,
    model: str = "veo-3.0-generate-preview"
) -> VideoGenerationResponse:
    """Generate a video using Google Veo 3 from an image and text prompt
    
    Args:
        prompt: Text prompt describing the video motion/action
        image_path: Path to the starting image file
        model: Veo model to use (veo-3.0-generate-preview, veo-3.0-fast-generate-preview, veo-2.0-generate-001)
    
    Returns:
        VideoGenerationResponse with video path, metadata, and generation info
        
    Note: Veo 3 generates 8-second 720p videos with audio. Advanced parameters like 
    negative prompts and aspect ratios are not currently supported in the public API.
    """
    
    await ctx.info(f"Starting image-to-video generation: {image_path}")
    
    if not prompt.strip():
        await ctx.error("Prompt cannot be empty")
        raise ValueError("Prompt cannot be empty")
    
    if not image_path.strip():
        await ctx.error("Image path cannot be empty")
        raise ValueError("Image path cannot be empty")
    
    # Resolve image path (allow relative paths within output directory for security)
    if not os.path.isabs(image_path):
        full_image_path = safe_join(OUTPUT_DIR, image_path)
    else:
        full_image_path = image_path
    
    if not os.path.exists(full_image_path):
        await ctx.error(f"Image file not found: {full_image_path}")
        raise ValueError(f"Image file not found: {full_image_path}")
    
    # Validate model
    valid_models = ["veo-3.0-generate-preview", "veo-3.0-fast-generate-preview", "veo-2.0-generate-001"]
    if model not in valid_models:
        await ctx.error(f"Invalid model: {model}. Must be one of: {valid_models}")
        raise ValueError(f"Invalid model: {model}")
    
    try:
        result = await generate_video_with_progress(
            prompt=prompt,
            model=model,
            ctx=ctx,
            image_path=full_image_path
        )
        
        await ctx.info(f"Image-to-video generation successful: {result['filename']}")
        
        return VideoGenerationResponse(**result)
        
    except Exception as e:
        await ctx.error(f"Image-to-video generation failed: {str(e)}")
        raise ValueError(f"Image-to-video generation failed: {str(e)}")


@mcp.tool()
async def list_generated_videos(ctx: Context) -> VideoListResponse:
    """List all generated videos in the output directory
    
    Returns:
        VideoListResponse with list of videos, count, and directory info
    """
    
    await ctx.info(f"Listing videos in: {OUTPUT_DIR}")
    
    output_dir = Path(OUTPUT_DIR)
    
    if not output_dir.exists():
        await ctx.info(f"Output directory {OUTPUT_DIR} does not exist yet")
        return VideoListResponse(
            videos=[],
            total_count=0,
            output_dir=str(output_dir)
        )
    
    # Find all video files
    video_extensions = ["*.mp4", "*.mov", "*.avi", "*.mkv"]
    video_files = []
    for ext in video_extensions:
        video_files.extend(output_dir.glob(ext))
    
    if not video_files:
        await ctx.info("No video files found")
        return VideoListResponse(
            videos=[],
            total_count=0,
            output_dir=str(output_dir)
        )
    
    # Sort by modification time (newest first)
    video_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    videos = []
    for video_file in video_files:
        stat = video_file.stat()
        videos.append({
            "filename": video_file.name,
            "path": str(video_file.absolute()),
            "size": stat.st_size,
            "size_mb": round(stat.st_size / 1024 / 1024, 1),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
        })
    
    await ctx.info(f"Found {len(videos)} video files")
    
    return VideoListResponse(
        videos=videos,
        total_count=len(videos),
        output_dir=str(output_dir)
    )


@mcp.tool()
async def get_video_info(video_path: str, ctx: Context) -> VideoInfoResponse:
    """Get detailed information about a video file
    
    Args:
        video_path: Path to the video file (can be relative to output directory)
    
    Returns:
        VideoInfoResponse with file metadata
    """
    
    await ctx.info(f"Getting info for video: {video_path}")
    
    if not video_path.strip():
        await ctx.error("Video path cannot be empty")
        raise ValueError("Video path cannot be empty")
    
    # Resolve video path (allow relative paths within output directory for security)
    if not os.path.isabs(video_path):
        full_video_path = safe_join(OUTPUT_DIR, video_path)
    else:
        full_video_path = video_path
    
    video_file = Path(full_video_path)
    
    if not video_file.exists():
        await ctx.error(f"Video file not found: {full_video_path}")
        raise ValueError(f"Video file not found: {full_video_path}")
    
    stat = video_file.stat()
    created_time = datetime.fromtimestamp(stat.st_ctime).isoformat()
    modified_time = datetime.fromtimestamp(stat.st_mtime).isoformat()
    
    await ctx.info(f"Video info retrieved: {video_file.name} ({stat.st_size:,} bytes)")
    
    return VideoInfoResponse(
        filename=video_file.name,
        path=str(video_file.absolute()),
        size=stat.st_size,
        created=created_time,
        modified=modified_time
    )


@mcp.tool()
async def upload_video_to_azure(
    video_path: str,
    ctx: Context,
    blob_name: Optional[str] = None
) -> AzureBlobUploadResponse:
    """Upload a video file to Azure Blob Storage
    
    Args:
        video_path: Path to the video file (can be relative to output directory)
        blob_name: Optional custom blob name (defaults to filename)
    
    Returns:
        AzureBlobUploadResponse with upload status and blob URL
    """
    
    await ctx.info(f"Uploading video to Azure Blob: {video_path}")
    
    if not video_path.strip():
        await ctx.error("Video path cannot be empty")
        raise ValueError("Video path cannot be empty")
    
    # Resolve video path (allow relative paths within output directory for security)
    if not os.path.isabs(video_path):
        full_video_path = safe_join(OUTPUT_DIR, video_path)
    else:
        full_video_path = video_path
    
    video_file = Path(full_video_path)
    
    if not video_file.exists():
        await ctx.error(f"Video file not found: {full_video_path}")
        raise ValueError(f"Video file not found: {full_video_path}")
    
    # Use custom blob name or default to filename
    if not blob_name:
        blob_name = video_file.name
    
    return await upload_to_azure_blob(
        file_path=str(video_file),
        blob_name=blob_name,
        ctx=ctx
    )


@mcp.tool()
async def list_azure_blob_videos(ctx: Context) -> AzureBlobListResponse:
    """List all videos in Azure Blob Storage container
    
    Returns:
        AzureBlobListResponse with list of blob videos and metadata
    """
    
    await ctx.info(f"Listing videos in Azure Blob container: {AZURE_CONTAINER_NAME}")
    
    if not BlobServiceClient:
        await ctx.error("Azure Storage SDK not available. Install: pip install azure-storage-blob")
        raise ValueError("Azure Storage SDK not available")
    
    if not AZURE_CONNECTION_STRING:
        await ctx.error("Azure connection string not configured")
        raise ValueError("Azure connection string not configured")
    
    try:
        blob_service_client = get_azure_blob_client()
        if not blob_service_client:
            raise Exception("Failed to initialize Azure Blob client")
        
        container_client = blob_service_client.get_container_client(AZURE_CONTAINER_NAME)
        
        # List all blobs in the container
        blobs = []
        try:
            blob_list = container_client.list_blobs()
            for blob in blob_list:
                # Filter for video files
                if blob.name.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                    blob_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{AZURE_CONTAINER_NAME}/{blob.name}"
                    blobs.append({
                        "name": blob.name,
                        "url": blob_url,
                        "size": blob.size,
                        "size_mb": round(blob.size / 1024 / 1024, 1) if blob.size else 0,
                        "created": blob.creation_time.isoformat() if blob.creation_time else None,
                        "modified": blob.last_modified.isoformat() if blob.last_modified else None,
                        "content_type": blob.content_settings.content_type if blob.content_settings else None
                    })
        except Exception as e:
            if "ContainerNotFound" in str(e):
                await ctx.info(f"Container {AZURE_CONTAINER_NAME} does not exist yet")
                return AzureBlobListResponse(
                    blobs=[],
                    total_count=0,
                    container_name=AZURE_CONTAINER_NAME
                )
            else:
                raise e
        
        # Sort by modification time (newest first)
        blobs.sort(key=lambda x: x.get('modified', ''), reverse=True)
        
        await ctx.info(f"Found {len(blobs)} video files in Azure Blob Storage")
        
        return AzureBlobListResponse(
            blobs=blobs,
            total_count=len(blobs),
            container_name=AZURE_CONTAINER_NAME
        )
        
    except Exception as e:
        await ctx.error(f"Failed to list Azure Blob videos: {str(e)}")
        raise ValueError(f"Failed to list Azure Blob videos: {str(e)}")


@mcp.tool()
async def delete_azure_blob_video(
    blob_name: str,
    ctx: Context
) -> dict:
    """Delete a video from Azure Blob Storage
    
    Args:
        blob_name: Name of the blob to delete
    
    Returns:
        Dictionary with deletion status
    """
    
    await ctx.info(f"Deleting video from Azure Blob: {blob_name}")
    
    if not blob_name.strip():
        await ctx.error("Blob name cannot be empty")
        raise ValueError("Blob name cannot be empty")
    
    if not BlobServiceClient:
        await ctx.error("Azure Storage SDK not available. Install: pip install azure-storage-blob")
        raise ValueError("Azure Storage SDK not available")
    
    if not AZURE_CONNECTION_STRING:
        await ctx.error("Azure connection string not configured")
        raise ValueError("Azure connection string not configured")
    
    try:
        blob_service_client = get_azure_blob_client()
        if not blob_service_client:
            raise Exception("Failed to initialize Azure Blob client")
        
        blob_client = blob_service_client.get_blob_client(
            container=AZURE_CONTAINER_NAME,
            blob=blob_name
        )
        
        # Check if blob exists
        if not blob_client.exists():
            await ctx.error(f"Blob not found: {blob_name}")
            raise ValueError(f"Blob not found: {blob_name}")
        
        # Delete the blob
        blob_client.delete_blob()
        
        await ctx.info(f"Successfully deleted blob: {blob_name}")
        
        return {
            "success": True,
            "blob_name": blob_name,
            "message": f"Successfully deleted {blob_name}"
        }
        
    except Exception as e:
        await ctx.error(f"Failed to delete Azure Blob video: {str(e)}")
        raise ValueError(f"Failed to delete Azure Blob video: {str(e)}")


def main():
    """Main entry point for the MCP Veo 3 server"""
    mcp.run()


if __name__ == "__main__":
    main()
