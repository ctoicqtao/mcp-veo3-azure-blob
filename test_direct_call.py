#!/usr/bin/env python3
"""
直接调用核心函数进行测试
"""

import asyncio
import sys
import os
import tempfile
import aiohttp
import base64
import mimetypes
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入Google GenAI
try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:
    print("❌ 请安装 google-genai: pip install google-genai")
    sys.exit(1)

# 导入Azure相关
try:
    from azure.storage.blob import BlobServiceClient
except ImportError:
    print("❌ 请安装 azure-storage-blob: pip install azure-storage-blob")
    sys.exit(1)

class MockContext:
    """模拟MCP Context"""
    def __init__(self):
        self.messages = []
        self.progress = 0
    
    async def info(self, message: str):
        print(f"INFO: {message}")
        self.messages.append(("info", message))
    
    async def error(self, message: str):
        print(f"ERROR: {message}")
        self.messages.append(("error", message))
    
    async def report_progress(self, progress: int, total: int):
        self.progress = progress
        percentage = (progress / total) * 100
        print(f"PROGRESS: {progress}/{total} ({percentage:.1f}%)")

def is_url(path: str) -> bool:
    """检查路径是否为URL"""
    try:
        result = urlparse(path)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

async def download_image_from_url(url: str, ctx: MockContext) -> str:
    """从URL下载图片到临时文件"""
    if not is_url(url):
        raise ValueError(f"Invalid URL: {url}")
    
    await ctx.info(f"Downloading image from URL: {url}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise ValueError(f"Failed to download image: HTTP {response.status}")
                
                # 获取内容类型
                content_type = response.headers.get('content-type', '').lower()
                if 'image' not in content_type:
                    await ctx.info(f"Warning: Content-Type is '{content_type}', not an image type")
                
                # 确定文件扩展名
                if 'jpeg' in content_type or 'jpg' in content_type:
                    ext = '.jpg'
                elif 'png' in content_type:
                    ext = '.png'
                elif 'gif' in content_type:
                    ext = '.gif'
                elif 'webp' in content_type:
                    ext = '.webp'
                else:
                    # 尝试从URL获取扩展名
                    parsed_url = urlparse(url)
                    path_ext = os.path.splitext(parsed_url.path)[1].lower()
                    if path_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']:
                        ext = path_ext
                    else:
                        ext = '.jpg'  # 默认为jpg
                
                # 创建临时文件
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
                    temp_path = temp_file.name
                    
                    # 下载并写入内容
                    async for chunk in response.content.iter_chunked(8192):
                        temp_file.write(chunk)
                
                await ctx.info(f"Image downloaded successfully to: {temp_path}")
                return temp_path
                
    except aiohttp.ClientError as e:
        raise ValueError(f"Network error downloading image: {str(e)}")
    except Exception as e:
        raise ValueError(f"Failed to download image: {str(e)}")

async def test_image_to_video_direct():
    """直接测试图片生成视频功能"""
    print("🎬 直接测试图片生成视频功能")
    print("=" * 60)
    
    # 检查环境变量
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ 请设置 GEMINI_API_KEY 环境变量")
        return False
    
    print(f"✅ GEMINI_API_KEY: {api_key[:8]}...")
    
    # 测试参数
    test_params = {
        "prompt": "生成一段这个运动员运动的视频，在跑步吧。",
        "image_path": "https://jinderublobpublic.blob.core.windows.net/nano-banana-images/edited-2025-09-19T06-19-01-290Z-bc78cm.png"
    }
    
    print(f"测试参数:")
    print(f"  提示词: {test_params['prompt']}")
    print(f"  图片URL: {test_params['image_path']}")
    print("=" * 60)
    
    ctx = MockContext()
    temp_image_path = None
    
    try:
        # 初始化Gemini客户端
        gemini_client = genai.Client(api_key=api_key)
        
        # 处理图片路径
        image_path = test_params["image_path"]
        
        if is_url(image_path):
            # 从URL下载图片
            temp_image_path = await download_image_from_url(image_path, ctx)
            full_image_path = temp_image_path
        else:
            full_image_path = image_path
        
        # 读取图片文件为字节
        await ctx.info(f"Reading image file: {full_image_path}")
        with open(full_image_path, 'rb') as f:
            image_bytes = f.read()
        
        # 获取MIME类型
        mime_type, _ = mimetypes.guess_type(full_image_path)
        if not mime_type or not mime_type.startswith('image/'):
            mime_type = 'image/jpeg'  # 默认值
        
        await ctx.info(f"Image loaded - Size: {len(image_bytes)} bytes, MIME: {mime_type}")
        
        # 创建图片对象
        image_obj = genai_types.Image(image_bytes=image_bytes, mime_type=mime_type)
        
        # 生成视频
        await ctx.info("Calling Gemini API for image-to-video generation...")
        operation = gemini_client.models.generate_videos(
            model="veo-3.0-generate-preview",
            prompt=test_params["prompt"],
            image=image_obj
        )
        
        await ctx.info(f"API call initiated, operation name: {operation.name}")
        
        # 等待完成
        await ctx.info("Waiting for video generation to complete...")
        while not operation.done:
            await asyncio.sleep(10)
            await ctx.info("Still generating...")
            operation = gemini_client.operations.get(operation)
        
        if not operation.response or not operation.response.generated_videos:
            raise RuntimeError("Video generation failed - no videos in response")
        
        generated_video = operation.response.generated_videos[0]
        await ctx.info(f"Video generation completed! URI: {generated_video.video.uri}")
        
        # 创建输出目录
        output_dir = Path("./test_videos")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"veo3_video_{timestamp}.mp4"
        output_path = output_dir / filename
        
        # 下载视频
        await ctx.info(f"Downloading video to: {output_path}")
        with open(output_path, 'wb') as f:
            for chunk in gemini_client.files.download(generated_video.video):
                f.write(chunk)
        
        file_size = output_path.stat().st_size if output_path.exists() else 0
        await ctx.info(f"Video downloaded successfully, size: {file_size} bytes ({file_size/1024/1024:.1f} MB)")
        
        print("=" * 60)
        print("✅ 测试成功!")
        print(f"视频已保存到: {output_path}")
        print(f"文件大小: {file_size/1024/1024:.1f} MB")
        
        return True
        
    except Exception as e:
        print("=" * 60)
        print(f"❌ 测试失败!")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        
        import traceback
        print("\n详细错误堆栈:")
        traceback.print_exc()
        
        return False
    
    finally:
        # 清理临时文件
        if temp_image_path and os.path.exists(temp_image_path):
            try:
                os.unlink(temp_image_path)
                print(f"✅ 清理临时文件: {temp_image_path}")
            except Exception as e:
                print(f"⚠️  清理临时文件失败: {str(e)}")

async def main():
    """主函数"""
    success = await test_image_to_video_direct()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
