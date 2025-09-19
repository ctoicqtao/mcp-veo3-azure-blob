# MCP Veo3 Azure Blob 部署指南

## 解决504超时问题

### 问题原因
视频生成通常需要1-6分钟，默认的MCP客户端超时设置可能不够长，导致504错误。

### 解决方案

#### 1. 使用正确的配置文件

使用 `mcp_client_config.json` 而不是 `config.json`：

```json
{
  "mcpServers": {
    "veo3-azure": {
      "command": "python",
      "args": ["/absolute/path/to/mcp-veo3-azure-blob/mcp_server.py", "--output-dir", "~/Videos/Generated"],
      "env": {
        "GEMINI_API_KEY": "your_actual_gemini_api_key",
        "AZURE_STORAGE_CONNECTION_STRING": "your_actual_azure_connection_string",
        "AZURE_BLOB_CONTAINER_NAME": "generated-videos",
        "AZURE_UPLOAD_ENABLED": "true"
      },
      "timeout": 600000,
      "requestTimeout": 600000,
      "capabilities": {
        "tools": {
          "timeout": 600000
        }
      }
    }
  }
}
```

#### 2. 环境变量配置

确保你的 `.env` 文件包含：

```bash
# Required
GEMINI_API_KEY=your_actual_gemini_api_key_here

# Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING=your_actual_azure_connection_string_here
AZURE_BLOB_CONTAINER_NAME=generated-videos
AZURE_UPLOAD_ENABLED=true
```

#### 3. 部署步骤

1. **安装依赖**：
   ```bash
   cd /path/to/mcp-veo3-azure-blob
   pip install -r requirements.txt
   ```

2. **测试连接**（快速测试）：
   首先使用 `test_connection` 工具验证MCP服务器配置：
   ```json
   {
     "tool": "test_connection"
   }
   ```

3. **测试视频生成**：
   使用较短的提示词进行测试：
   ```json
   {
     "tool": "generate_video",
     "prompt": "A simple red ball rolling",
     "model": "veo-3.0-fast-generate-preview"
   }
   ```

#### 4. 故障排除

**如果仍然出现504错误**：

1. **检查日志**：
   查看 `mcp_server.log` 文件了解详细错误信息

2. **使用更快的模型**：
   ```json
   {
     "tool": "generate_video",
     "prompt": "your prompt",
     "model": "veo-3.0-fast-generate-preview"
   }
   ```

3. **分步测试**：
   - 先测试 `test_connection`
   - 再测试 `list_generated_videos`
   - 最后测试 `generate_video`

4. **检查地区限制**：
   Veo 3 API在某些地区不可用，会返回 "User location is not supported" 错误

#### 5. 预期响应格式

成功的视频生成会返回：
```json
{
  "azure_video_url": "https://yourstorageaccount.blob.core.windows.net/generated-videos/veo3_video_20241219_123456.mp4"
}
```

如果Azure上传失败：
```json
{
  "azure_video_url": null
}
```

#### 6. 性能优化

- 使用 `veo-3.0-fast-generate-preview` 模型获得更快的生成速度
- 保持提示词简洁明了
- 确保网络连接稳定

#### 7. 监控和日志

服务器会在以下位置记录日志：
- `mcp_server.log` - 服务器启动和错误日志
- 控制台输出 - 实时状态信息

## 常见错误和解决方案

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| 504 Timeout | 请求超时 | 增加客户端超时设置 |
| User location not supported | 地区限制 | 使用VPN或等待API在你的地区可用 |
| Invalid API key | API密钥错误 | 检查GEMINI_API_KEY设置 |
| Azure upload failed | Azure配置错误 | 检查AZURE_STORAGE_CONNECTION_STRING |

## 测试命令

```bash
# 测试Azure配置
python test_azure_blob.py

# 启动MCP服务器
python mcp_server.py --output-dir ~/Videos/Generated
```
