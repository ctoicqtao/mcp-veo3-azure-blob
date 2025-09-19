#!/usr/bin/env python3
"""
测试已安装包中的修复是否生效
"""

import sys
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置必要的命令行参数
sys.argv = [sys.argv[0], '--output-dir', './test_videos']

# 导入已安装的包
import mcp_veo3_azure_blob
import asyncio

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

async def test_package_fix():
    """测试包中的修复"""
    print("🔍 测试已安装包中的修复...")
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
    
    try:
        # 获取工具函数
        tool = mcp_veo3_azure_blob.generate_video_from_image
        print(f"✅ 成功导入工具: {tool}")
        
        # 尝试调用函数
        print("正在调用 generate_video_from_image 方法...")
        result = await tool.fn(
            prompt=test_params["prompt"],
            image_path=test_params["image_path"],
            ctx=ctx,
            model="veo-3.0-generate-preview"
        )
        
        print("=" * 60)
        print("✅ 测试成功!")
        print(f"结果: {result}")
        
        if result.get('azure_video_url'):
            print(f"🔗 Azure视频URL: {result['azure_video_url']}")
        
        return True
        
    except Exception as e:
        print("=" * 60)
        print(f"❌ 测试失败!")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        
        # 检查是否还是同样的API错误
        if "bytesBase64Encoded" in str(e) and "mimeType" in str(e):
            print("\n🚨 这是同样的API格式错误！说明修复没有生效。")
            print("可能的原因:")
            print("1. 包发布可能有延迟")
            print("2. 缓存问题")
            print("3. 修复没有正确应用")
        
        return False

async def main():
    """主函数"""
    success = await test_package_fix()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
