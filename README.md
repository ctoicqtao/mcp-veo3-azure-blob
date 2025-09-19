# MCP Veo 3 Azure Blob Video Generator

A powerful Model Context Protocol (MCP) server that provides professional video generation capabilities using Google's state-of-the-art Veo 3 API through the Gemini API, with seamless Azure Blob Storage integration. Generate high-quality 8-second videos with native audio from text prompts or images, and automatically store them in the cloud.

## ✨ Key Features

- 🎬 **Text-to-Video Generation**: Create videos from descriptive text prompts
- 🖼️ **Image-to-Video Animation**: Animate static images with motion prompts
  - 📁 **Local Files**: Support for local image files (JPG, PNG, GIF, WebP, BMP)
  - 🌐 **Online URLs**: Direct support for online image URLs
- 🎵 **Native Audio**: Automatic audio generation with Veo 3 models
- 🎨 **Multiple Models**: Veo 3, Veo 3 Fast, and Veo 2 support
- ⚡ **Real-time Progress**: Live progress tracking with detailed status updates
- ☁️ **Azure Integration**: Automatic upload to Azure Blob Storage
- 🔗 **Cloud URLs**: Instant access to cloud-hosted videos
- 🗂️ **Cloud Management**: Complete Azure Blob Storage management tools
- 🛡️ **Robust Error Handling**: Comprehensive error handling and recovery
- ⏱️ **Extended Timeout**: 45-minute timeout for complex video generation

## Supported Models

| Model | Description | Speed | Quality | Audio |
|-------|-------------|-------|---------|-------|
| `veo-3.0-generate-preview` | Latest Veo 3 with highest quality | Slower | Highest | ✅ |
| `veo-3.0-fast-generate-preview` | Optimized for speed and business use | Faster | High | ✅ |
| `veo-2.0-generate-001` | Previous generation model | Medium | Good | ❌ |

## 🚀 Quick Start

### Option 1: Install from PyPI (Recommended)
```bash
# Install the package
pip install mcp-veo3-azure-blob

# Set up environment variables
export GEMINI_API_KEY='your_gemini_api_key_here'
export AZURE_STORAGE_CONNECTION_STRING='your_azure_connection_string_here'
```

### Option 2: Development Setup
```bash
# Clone the repository
git clone https://github.com/ctoicqtao/mcp-veo3-azure-blob
cd mcp-veo3-azure-blob

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp env_example.txt .env
# Edit .env file with your API keys
```

## 🔑 API Keys Setup

### 1. Get Gemini API Key
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key for configuration

### 2. Set up Azure Blob Storage
1. Go to [Azure Portal](https://portal.azure.com)
2. Create a Storage Account
3. Get the connection string from "Access keys"
4. Create a container for videos (optional - will be auto-created)

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Azure Blob Storage (Required for cloud upload)
AZURE_STORAGE_CONNECTION_STRING=your_azure_storage_connection_string_here
AZURE_BLOB_CONTAINER_NAME=generated-videos
AZURE_UPLOAD_ENABLED=true

# Optional
DEFAULT_OUTPUT_DIR=generated_videos
DEFAULT_MODEL=veo-3.0-generate-preview
DEFAULT_ASPECT_RATIO=16:9
PERSON_GENERATION=dont_allow
POLL_INTERVAL=10
MAX_POLL_TIME=600
```

### MCP Client Configuration

Add this to your MCP client configuration file:

```json
{
  "mcpServers": {
    "veo3-azure-blob": {
      "command": "python",
      "args": ["mcp_veo3_azure_blob.py", "--output-dir", "~/Videos/Generated"],
      "env": {
        "GEMINI_API_KEY": "${GEMINI_API_KEY}",
        "AZURE_STORAGE_CONNECTION_STRING": "${AZURE_STORAGE_CONNECTION_STRING}",
        "AZURE_BLOB_CONTAINER_NAME": "${AZURE_BLOB_CONTAINER_NAME:-generated-videos}",
        "AZURE_UPLOAD_ENABLED": "${AZURE_UPLOAD_ENABLED:-true}"
      }
    }
  }
}
```

**CLI Arguments:**
- `--output-dir` (required): Directory to save generated videos locally
- `--api-key` (optional): Gemini API key (overrides environment variable)

## 🛠️ Available MCP Tools

### 1. `generate_video`
Generate a video from a text prompt with automatic Azure upload.

**Parameters:**
- `prompt` (required): Detailed text description of the video
- `model` (optional): Model to use (default: `veo-3.0-generate-preview`)

**Example:**
```json
{
  "prompt": "A cinematic drone shot of a red sports car driving through winding mountain roads at golden hour, with dramatic shadows and warm sunlight filtering through pine trees",
  "model": "veo-3.0-generate-preview"
}
```

**Returns:**
```json
{
  "video_path": "/path/to/veo3_video_20250919_151806.mp4",
  "filename": "veo3_video_20250919_151806.mp4",
  "azure_video_url": "https://yourstorageaccount.blob.core.windows.net/generated-videos/veo3_video_20250919_151806.mp4",
  "file_size": 15728640,
  "generation_time": 127.5,
  "azure_upload_success": true
}
```

### 2. `generate_video_from_image`
Animate a static image with motion prompts. Supports both local files and online URLs.

**Parameters:**
- `prompt` (required): Description of the desired motion/animation
- `image_path` (required): Local file path OR online image URL
- `model` (optional): Model to use (default: `veo-3.0-generate-preview`)

**Supported Image Formats:**
- **Local files**: JPG, PNG, GIF, WebP, BMP, TIFF
- **Online URLs**: Direct image URLs from any accessible server

**Example with local file:**
```json
{
  "prompt": "生成一段这个运动员运动的视频，在跑步吧。",
  "image_path": "./images/athlete.jpg",
  "model": "veo-3.0-generate-preview"
}
```

**Example with online URL:**
```json
{
  "prompt": "The flowers in the garden gently sway in a warm breeze",
  "image_path": "https://example.com/images/garden.jpg",
  "model": "veo-3.0-fast-generate-preview"
}
```

### 3. `list_generated_videos`
List all locally generated videos.

**Parameters:**
- `output_dir` (optional): Directory to scan (default: configured output directory)

**Returns:** Array of video files with metadata

### 4. `get_video_info`
Get detailed information about a specific video file.

**Parameters:**
- `video_path` (required): Path to the video file

**Returns:** Video metadata including size, duration, and creation time

### 5. `upload_video_to_azure`
Manually upload a video to Azure Blob Storage.

**Parameters:**
- `video_path` (required): Path to video file (relative to output directory)
- `blob_name` (optional): Custom blob name (defaults to filename)

**Example:**
```json
{
  "video_path": "veo3_video_20250919_151806.mp4",
  "blob_name": "my_awesome_video.mp4"
}
```

### 6. `list_azure_blob_videos`
List all videos stored in Azure Blob Storage.

**Parameters:** None

**Returns:**
```json
{
  "videos": [
    {
      "name": "veo3_video_20250919_151806.mp4",
      "url": "https://storage.blob.core.windows.net/container/video.mp4",
      "size": 15728640,
      "last_modified": "2025-09-19T15:18:06Z"
    }
  ],
  "total_count": 1,
  "total_size": 15728640
}
```

### 7. `delete_azure_blob_video`
Delete a video from Azure Blob Storage.

**Parameters:**
- `blob_name` (required): Name of the blob to delete

**Example:**
```json
{
  "blob_name": "old_video.mp4"
}
```

## 💡 Usage Examples

### Text-to-Video Generation
```python
# Generate a cinematic video
result = await mcp_client.call_tool("generate_video", {
    "prompt": "A majestic eagle soaring over snow-capped mountains at sunrise, cinematic wide shot with golden lighting",
    "model": "veo-3.0-generate-preview"
})

# Result includes local path and Azure URL
print(f"Video saved locally: {result['video_path']}")
print(f"Azure URL: {result['azure_video_url']}")
```

### Image-to-Video Animation
```python
# Animate a local image
result = await mcp_client.call_tool("generate_video_from_image", {
    "prompt": "The person starts walking forward with confident steps",
    "image_path": "./portrait.jpg",
    "model": "veo-3.0-generate-preview"
})

# Animate from online URL
result = await mcp_client.call_tool("generate_video_from_image", {
    "prompt": "生成一段这个运动员运动的视频，在跑步吧。",
    "image_path": "https://example.com/athlete.jpg",
    "model": "veo-3.0-fast-generate-preview"
})
```

### Azure Blob Management
```python
# List all cloud videos
videos = await mcp_client.call_tool("list_azure_blob_videos", {})
print(f"Found {videos['total_count']} videos in cloud storage")

# Upload a specific video
upload_result = await mcp_client.call_tool("upload_video_to_azure", {
    "video_path": "special_video.mp4",
    "blob_name": "presentation_video.mp4"
})

# Clean up old videos
await mcp_client.call_tool("delete_azure_blob_video", {
    "blob_name": "old_video.mp4"
})
```

## 🎨 Prompt Writing Guide

### Best Practices
- **Be descriptive**: Include lighting, mood, camera angles, and atmosphere
- **Specify motion**: Describe the exact type of movement or action
- **Set the scene**: Include environmental details and context
- **Choose style**: Mention cinematic, realistic, animated, artistic styles
- **Use active language**: Focus on what IS happening, not what isn't

### Effective Prompt Examples

**Cinematic Shots:**
```
A sweeping drone shot of a lone figure walking across a vast desert at sunset, dramatic golden lighting casting long shadows, cinematic wide-angle perspective
```

**Nature Scenes:**
```
A gentle waterfall cascading over moss-covered rocks in a serene forest, with dappled sunlight filtering through green leaves and creating dancing light patterns
```

**Urban Environments:**
```
A bustling city street at night with neon lights reflecting on wet pavement, people walking with umbrellas, rain creating atmospheric mood lighting
```

**Character Animation:**
```
A person in a cozy café slowly turning pages of a book while steam rises from their coffee cup, warm ambient lighting creating a peaceful atmosphere
```

## ⚡ Technical Specifications

### Video Output
- **Duration**: 8 seconds per video
- **Resolution**: 720p (1280x720) or 1080p (1920x1080)
- **Audio**: Native audio generation with Veo 3 models
- **Format**: MP4 with H.264 encoding
- **Watermark**: SynthID digital watermark included

### Performance
- **Generation Time**: 30 seconds to 10 minutes (depending on complexity)
- **Timeout**: 45 minutes maximum (3x extended from default)
- **Concurrent Requests**: Handled asynchronously
- **Progress Tracking**: Real-time status updates

### Storage
- **Local**: Videos saved to specified output directory
- **Cloud**: Automatic upload to Azure Blob Storage
- **Retention**: Google servers store videos for 2 days
- **Azure**: Permanent storage with configurable retention policies

## 🚨 Troubleshooting

### Common Issues

**API Key Problems**
```bash
# Set environment variable
export GEMINI_API_KEY='your_api_key_here'

# Or add to .env file
echo "GEMINI_API_KEY=your_api_key_here" >> .env

# Verify key is set
echo $GEMINI_API_KEY
```

**Azure Connection Issues**
```bash
# Check connection string format
echo $AZURE_STORAGE_CONNECTION_STRING

# Test Azure connectivity
python -c "from azure.storage.blob import BlobServiceClient; print('Azure SDK working')"

# Verify container exists in Azure Portal
```

**Video Generation Timeouts**
- Use `veo-3.0-fast-generate-preview` for faster generation
- Current timeout is 45 minutes (3x extended)
- Check network connectivity
- Monitor progress logs for status updates

**Image Format Issues**
- Supported formats: JPG, PNG, GIF, WebP, BMP, TIFF
- Online URLs must be directly accessible
- Check image file size (recommended < 10MB)
- Verify MIME type detection in logs

**Permission Errors**
```bash
# Ensure output directory is writable
mkdir -p ~/Videos/Generated
chmod 755 ~/Videos/Generated

# Check file permissions
ls -la ~/Videos/Generated
```

### Error Recovery

The server includes comprehensive error handling:

- **Auto-retry**: Network failures are automatically retried
- **Graceful fallback**: Azure upload failures don't stop video generation
- **Detailed logging**: All operations are logged with request IDs
- **Progress tracking**: Real-time status updates during generation
- **Cleanup**: Temporary files are automatically cleaned up
- **Validation**: Input validation prevents common errors

## 🔧 Development

### Testing
```bash
# Test basic functionality
python test_direct_call.py

# Test Azure Blob Storage
python test_azure_blob.py

# Test image URL functionality
python test_url_image.py
```

### Building and Publishing
```bash
# Build the package
uv build

# Publish to PyPI
uv publish
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📚 Resources

- **PyPI Package**: https://pypi.org/project/mcp-veo3-azure-blob/
- **GitHub Repository**: https://github.com/ctoicqtao/mcp-veo3-azure-blob
- **MCP Documentation**: https://modelcontextprotocol.io/
- **Google Veo 3 API**: https://ai.google.dev/gemini-api/docs/video
- **Azure Blob Storage**: https://docs.microsoft.com/en-us/azure/storage/blobs/

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **API Key Setup**: [Get your Gemini API key](https://makersuite.google.com/app/apikey)
- **Azure Setup**: [Azure Blob Storage Documentation](https://docs.microsoft.com/en-us/azure/storage/blobs/)
- **Issues**: Report bugs and feature requests in [GitHub Issues](https://github.com/ctoicqtao/mcp-veo3-azure-blob/issues)
- **Discussions**: Join the conversation in [GitHub Discussions](https://github.com/ctoicqtao/mcp-veo3-azure-blob/discussions)

## 📋 Changelog

### v1.0.18 (Current)
- **⏱️ Extended Timeout**: Increased default timeout to 45 minutes (3x original) for complex video generation
- **🛡️ Enhanced Error Handling**: Improved error recovery and retry mechanisms
- **📊 Better Progress Tracking**: More detailed progress updates during generation

### v1.0.17
- **🔧 API Format Fix**: Fixed Google Gemini API image format issues
- **📥 Download Fix**: Corrected video download method for proper file saving
- **🎯 Image Processing**: Enhanced image handling with proper MIME type detection

### v1.0.16
- **🖼️ Image Format Support**: Fixed image-to-video generation with correct API format
- **🌐 URL Image Support**: Enhanced support for online image URLs
- **🔄 Improved Retry Logic**: Better handling of network failures

### v1.0.15
- **☁️ Azure Blob Storage Integration**: Complete Azure cloud storage integration
- **🔗 Cloud URLs**: Direct access to cloud-hosted videos
- **🗂️ Cloud Management Tools**: Full suite of Azure Blob Storage management tools
- **📱 Progress Tracking**: Real-time progress updates with detailed status
- **🛡️ Error Recovery**: Comprehensive error handling and graceful fallbacks

### v1.0.0 - v1.0.14
- Initial releases with core video generation functionality
- Text-to-video and image-to-video generation
- FastMCP framework integration
- Basic file management utilities

---

**🚀 Built with FastMCP** | **🐍 Python 3.10+** | **📄 MIT License** | **☁️ Azure Powered**
