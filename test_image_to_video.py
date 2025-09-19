#!/usr/bin/env python3
"""
本地测试脚本：测试图片生成视频功能
"""

import asyncio
import sys
import os
from pathlib import Path

# 直接导入已安装的包
import mcp_veo3_azure_blob
from fastmcp import Context

class MockContext:
    """模拟MCP Context用于测试"""
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

async def test_image_to_video():
    """测试图片生成视频功能"""
    print("开始测试图片生成视频功能...")
    print("=" * 60)
    
    # 测试参数
    test_params = {
        "prompt": "生成一段这个运动员运动的视频，在跑步吧。",
        "image_path": "https://jinderublobpublic.blob.core.windows.net/nano-banana-images/edited-2025-09-19T06-19-01-290Z-bc78cm.png"
    }
    
    print(f"测试参数:")
    print(f"  提示词: {test_params['prompt']}")
    print(f"  图片URL: {test_params['image_path']}")
    print("=" * 60)
    
    # 创建模拟上下文
    ctx = MockContext()
    
    try:
        # 调用图片生成视频方法
        print("正在调用 generate_video_from_image 方法...")
        
        # 检查 FunctionTool 对象的属性
        tool = mcp_veo3_azure_blob.generate_video_from_image
        print(f"Tool attributes: {dir(tool)}")
        
        # 尝试使用不同的方法调用
        if hasattr(tool, 'fn') and tool.fn:
            print("使用 tool.fn 调用...")
            result = await tool.fn(
                prompt=test_params["prompt"],
                image_path=test_params["image_path"],
                ctx=ctx,
                model="veo-3.0-generate-preview"
            )
        elif hasattr(tool, 'run'):
            print("使用 tool.run 调用...")
            # 准备参数字典
            params = {
                "prompt": test_params["prompt"],
                "image_path": test_params["image_path"],
                "model": "veo-3.0-generate-preview"
            }
            result = await tool.run(ctx, **params)
        else:
            raise Exception("无法找到合适的调用方法")
        
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
        
        # 打印详细的错误堆栈
        import traceback
        print("\n详细错误堆栈:")
        traceback.print_exc()
        
        return False

async def check_environment():
    """检查环境配置"""
    print("检查环境配置...")
    print("-" * 40)
    
    # 检查必要的环境变量
    required_vars = [
        "GEMINI_API_KEY",
        "AZURE_STORAGE_CONNECTION_STRING",
        "AZURE_BLOB_CONTAINER_NAME"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # 只显示前几个字符，保护敏感信息
            masked_value = value[:8] + "..." if len(value) > 8 else value
            print(f"✅ {var}: {masked_value}")
        else:
            print(f"❌ {var}: 未设置")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️  缺少环境变量: {', '.join(missing_vars)}")
        print("请检查 .env 文件配置")
        return False
    
    print("✅ 环境配置检查通过")
    return True

async def main():
    """主函数"""
    print("🎬 MCP Veo3 Azure Blob - 图片生成视频测试")
    print("=" * 60)
    
    # 检查环境配置
    if not await check_environment():
        print("\n❌ 环境配置检查失败，请先配置环境变量")
        return 1
    
    print("\n" + "=" * 60)
    
    # 运行测试
    success = await test_image_to_video()
    
    if success:
        print("\n🎉 所有测试通过!")
        return 0
    else:
        print("\n💥 测试失败!")
        return 1

if __name__ == "__main__":
    # 运行测试
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
