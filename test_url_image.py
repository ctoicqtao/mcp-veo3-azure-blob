#!/usr/bin/env python3
"""
Test script for URL image download functionality in MCP Veo3 Azure Blob server
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_veo3_azure_blob import is_url, download_image_from_url
from fastmcp import Context

class MockContext:
    """Mock context for testing"""
    def __init__(self):
        self.messages = []
    
    async def info(self, message: str):
        print(f"INFO: {message}")
        self.messages.append(("info", message))
    
    async def error(self, message: str):
        print(f"ERROR: {message}")
        self.messages.append(("error", message))

async def test_url_validation():
    """Test URL validation function"""
    print("Testing URL validation...")
    
    # Valid URLs
    valid_urls = [
        "https://example.com/image.jpg",
        "http://test.com/photo.png",
        "https://cdn.example.com/images/test.webp"
    ]
    
    # Invalid URLs
    invalid_urls = [
        "not_a_url",
        "/local/path/image.jpg",
        "ftp://example.com/image.jpg",
        ""
    ]
    
    for url in valid_urls:
        assert is_url(url), f"Should be valid URL: {url}"
        print(f"✓ Valid URL: {url}")
    
    for url in invalid_urls:
        assert not is_url(url), f"Should be invalid URL: {url}"
        print(f"✓ Invalid URL: {url}")
    
    print("URL validation tests passed!\n")

async def test_image_download():
    """Test image download from URL"""
    print("Testing image download...")
    
    # Use a test image URL (this is a small test image)
    test_url = "https://httpbin.org/image/jpeg"
    
    ctx = MockContext()
    
    try:
        # Test downloading image
        temp_path = await download_image_from_url(test_url, ctx)
        
        # Check if file exists and has content
        if os.path.exists(temp_path):
            file_size = os.path.getsize(temp_path)
            print(f"✓ Image downloaded successfully: {temp_path}")
            print(f"✓ File size: {file_size} bytes")
            
            # Clean up
            os.unlink(temp_path)
            print(f"✓ Temporary file cleaned up")
        else:
            print("✗ Downloaded file not found")
            return False
            
    except Exception as e:
        print(f"✗ Image download failed: {str(e)}")
        return False
    
    print("Image download test passed!\n")
    return True

async def main():
    """Run all tests"""
    print("Starting URL image functionality tests...\n")
    
    try:
        # Test URL validation
        await test_url_validation()
        
        # Test image download (requires internet connection)
        print("Note: Image download test requires internet connection")
        success = await test_image_download()
        
        if success:
            print("All tests passed! ✓")
            print("\nThe generate_video_from_image method should now support:")
            print("1. Local file paths (existing functionality)")
            print("2. Image URLs (new functionality)")
            print("\nExample usage:")
            print('generate_video_from_image("A cat walking", "https://example.com/cat.jpg")')
        else:
            print("Some tests failed! ✗")
            
    except Exception as e:
        print(f"Test execution failed: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
