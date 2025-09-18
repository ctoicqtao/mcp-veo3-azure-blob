#!/usr/bin/env python3
"""
Test script for Azure Blob Storage functionality
Usage: python test_azure_blob.py
"""

import os
import asyncio
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our Azure functions
try:
    from mcp_veo3_azure_blob import (
        get_azure_blob_client,
        upload_to_azure_blob,
        AZURE_CONNECTION_STRING,
        AZURE_CONTAINER_NAME,
        AZURE_UPLOAD_ENABLED
    )
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure to install dependencies: pip install -r requirements.txt")
    exit(1)

class MockContext:
    """Mock context for testing"""
    async def info(self, message: str):
        print(f"INFO: {message}")
    
    async def error(self, message: str):
        print(f"ERROR: {message}")
    
    async def report_progress(self, progress: int, total: int):
        print(f"PROGRESS: {progress}/{total}")

async def test_azure_configuration():
    """Test Azure configuration"""
    print("=== Testing Azure Configuration ===")
    
    print(f"Azure Upload Enabled: {AZURE_UPLOAD_ENABLED}")
    print(f"Azure Container Name: {AZURE_CONTAINER_NAME}")
    print(f"Azure Connection String: {'✓ Set' if AZURE_CONNECTION_STRING else '✗ Not Set'}")
    
    if not AZURE_CONNECTION_STRING:
        print("\n❌ Azure connection string not configured!")
        print("Please set AZURE_STORAGE_CONNECTION_STRING in your .env file")
        return False
    
    # Test blob client initialization
    client = get_azure_blob_client()
    if client:
        print("✅ Azure Blob client initialized successfully")
        return True
    else:
        print("❌ Failed to initialize Azure Blob client")
        return False

async def test_azure_upload():
    """Test Azure Blob upload with a dummy file"""
    print("\n=== Testing Azure Blob Upload ===")
    
    if not AZURE_CONNECTION_STRING:
        print("❌ Skipping upload test - Azure not configured")
        return False
    
    # Create a temporary test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.mp4', delete=False) as temp_file:
        temp_file.write("This is a test video file content")
        temp_file_path = temp_file.name
    
    try:
        # Test upload
        ctx = MockContext()
        blob_name = f"test_video_{int(asyncio.get_event_loop().time())}.mp4"
        
        print(f"Uploading test file: {temp_file_path}")
        print(f"Blob name: {blob_name}")
        
        result = await upload_to_azure_blob(
            file_path=temp_file_path,
            blob_name=blob_name,
            ctx=ctx
        )
        
        if result.success:
            print(f"✅ Upload successful!")
            print(f"   Blob URL: {result.blob_url}")
            print(f"   Upload time: {result.upload_time:.2f}s")
            print(f"   File size: {result.file_size} bytes")
            return True
        else:
            print(f"❌ Upload failed: {result.error_message}")
            return False
            
    except Exception as e:
        print(f"❌ Upload test failed with exception: {str(e)}")
        return False
    finally:
        # Clean up temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

async def test_azure_list():
    """Test listing Azure Blob videos"""
    print("\n=== Testing Azure Blob List ===")
    
    if not AZURE_CONNECTION_STRING:
        print("❌ Skipping list test - Azure not configured")
        return False
    
    try:
        from mcp_veo3_azure_blob import list_azure_blob_videos
        
        ctx = MockContext()
        result = await list_azure_blob_videos(ctx)
        
        print(f"✅ List successful!")
        print(f"   Container: {result.container_name}")
        print(f"   Total videos: {result.total_count}")
        
        if result.blobs:
            print("   Recent videos:")
            for blob in result.blobs[:3]:  # Show first 3
                print(f"     - {blob['name']} ({blob['size_mb']} MB)")
        
        return True
        
    except Exception as e:
        print(f"❌ List test failed: {str(e)}")
        return False

async def main():
    """Run all tests"""
    print("🧪 Azure Blob Storage Test Suite")
    print("=" * 50)
    
    tests = [
        ("Configuration", test_azure_configuration),
        ("Upload", test_azure_upload),
        ("List", test_azure_list),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:15} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Azure Blob Storage is ready to use.")
    else:
        print("⚠️  Some tests failed. Please check your Azure configuration.")
        print("\nTroubleshooting:")
        print("1. Make sure you have set AZURE_STORAGE_CONNECTION_STRING in .env")
        print("2. Verify your Azure Storage account is accessible")
        print("3. Check that azure-storage-blob package is installed")

if __name__ == "__main__":
    asyncio.run(main())
