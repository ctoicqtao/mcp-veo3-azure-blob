# 日志查看指南

## 日志文件位置
- 主日志文件: `mcp_server.log`
- 控制台输出: 实时显示在终端

## 日志格式说明

### 请求ID格式
- 视频生成请求: `[veo3_1234567890]`
- Azure上传请求: `[azure_1234567890]`
- MCP工具调用: `[generate_video_1234567890]`

### 日志级别
- `INFO`: 正常操作信息
- `ERROR`: 错误信息
- `WARNING`: 警告信息

## 查看日志的方法

### 1. 查看最新日志
```bash
# 查看最新50行日志
python view_logs.py

# 查看最新100行日志
python view_logs.py --lines 100
```

### 2. 实时跟踪日志
```bash
# 实时跟踪日志文件
python view_logs.py --follow
```

### 3. 过滤特定内容
```bash
# 只查看Azure相关日志
python view_logs.py --azure

# 只查看错误日志
python view_logs.py --errors

# 只查看请求日志
python view_logs.py --requests

# 自定义过滤
python view_logs.py --filter "blob.core.windows.net"
```

### 4. 直接使用系统命令
```bash
# 查看最新日志
tail -f mcp_server.log

# 搜索特定内容
grep "Azure Blob URL" mcp_server.log

# 搜索错误
grep "ERROR" mcp_server.log
```

## 典型日志示例

### 成功的视频生成日志
```
2024-12-19 12:30:00 - mcp-veo3-azure-blob - INFO - [veo3_1703001000] Starting video generation request
2024-12-19 12:30:00 - mcp-veo3-azure-blob - INFO - [veo3_1703001000] Model: veo-3.0-generate-preview
2024-12-19 12:30:00 - mcp-veo3-azure-blob - INFO - [veo3_1703001000] Prompt: A beautiful sunset over the ocean
2024-12-19 12:30:01 - mcp-veo3-azure-blob - INFO - [veo3_1703001000] Calling Gemini API for text-to-video generation
2024-12-19 12:30:01 - mcp-veo3-azure-blob - INFO - [veo3_1703001000] API call initiated, operation name: operations/12345
2024-12-19 12:32:30 - mcp-veo3-azure-blob - INFO - [veo3_1703001000] Video generation completed successfully
2024-12-19 12:32:30 - mcp-veo3-azure-blob - INFO - [veo3_1703001000] Generated video URI: gs://gemini-generated-videos/video123.mp4
2024-12-19 12:32:31 - mcp-veo3-azure-blob - INFO - [veo3_1703001000] Video downloaded successfully, size: 5242880 bytes
2024-12-19 12:32:31 - mcp-veo3-azure-blob - INFO - [veo3_1703001000] Starting Azure Blob Storage upload
2024-12-19 12:32:33 - mcp-veo3-azure-blob - INFO - [azure_1703001151] ✅ Azure upload completed successfully!
2024-12-19 12:32:33 - mcp-veo3-azure-blob - INFO - [azure_1703001151] 🔗 Blob URL: https://mystorageaccount.blob.core.windows.net/generated-videos/veo3_video_20241219_123233.mp4
2024-12-19 12:32:33 - mcp-veo3-azure-blob - INFO - [veo3_1703001000] 🎉 Video generation process completed!
```

### Azure上传成功日志
```
2024-12-19 12:32:31 - mcp-veo3-azure-blob - INFO - [azure_1703001151] Starting Azure Blob upload
2024-12-19 12:32:31 - mcp-veo3-azure-blob - INFO - [azure_1703001151] File: /path/to/veo3_video_20241219_123233.mp4
2024-12-19 12:32:31 - mcp-veo3-azure-blob - INFO - [azure_1703001151] Blob name: veo3_video_20241219_123233.mp4
2024-12-19 12:32:31 - mcp-veo3-azure-blob - INFO - [azure_1703001151] Container: generated-videos
2024-12-19 12:32:33 - mcp-veo3-azure-blob - INFO - [azure_1703001151] ✅ Azure upload completed successfully!
2024-12-19 12:32:33 - mcp-veo3-azure-blob - INFO - [azure_1703001151] 🔗 Blob URL: https://mystorageaccount.blob.core.windows.net/generated-videos/veo3_video_20241219_123233.mp4
2024-12-19 12:32:33 - mcp-veo3-azure-blob - INFO - [azure_1703001151] Upload time: 2.15s
2024-12-19 12:32:33 - mcp-veo3-azure-blob - INFO - [azure_1703001151] File size: 5242880 bytes (5.0 MB)
2024-12-19 12:32:33 - mcp-veo3-azure-blob - INFO - [azure_1703001151] Upload speed: 2.3 MB/s
```

### MCP工具调用日志
```
2024-12-19 12:30:00 - mcp-veo3-azure-blob - INFO - [generate_video_1703001000] 🎬 MCP Tool Called: generate_video
2024-12-19 12:30:00 - mcp-veo3-azure-blob - INFO - [generate_video_1703001000] Parameters: prompt='A beautiful sunset over the ocean', model='veo-3.0-generate-preview'
2024-12-19 12:32:33 - mcp-veo3-azure-blob - INFO - [generate_video_1703001000] ✅ MCP Tool Response: {"azure_video_url": "https://mystorageaccount.blob.core.windows.net/generated-videos/veo3_video_20241219_123233.mp4"}
2024-12-19 12:32:33 - mcp-veo3-azure-blob - INFO - [generate_video_1703001000] 🎬 generate_video completed successfully
```

### 错误日志示例
```
2024-12-19 12:30:05 - mcp-veo3-azure-blob - ERROR - [veo3_1703001005] ❌ Video generation failed with exception: 400 FAILED_PRECONDITION
2024-12-19 12:30:05 - mcp-veo3-azure-blob - ERROR - [veo3_1703001005] Exception type: GoogleAPIError
2024-12-19 12:30:05 - mcp-veo3-azure-blob - ERROR - [veo3_1703001005] Total elapsed time: 5.2s
```

## 重要的日志信息

### 查找Azure Blob URL
```bash
grep "🔗 Blob URL" mcp_server.log
```

### 查找生成时间
```bash
grep "generation time" mcp_server.log
```

### 查找上传速度
```bash
grep "Upload speed" mcp_server.log
```

### 查找错误
```bash
grep "❌" mcp_server.log
```

## 日志轮转

如果日志文件变得太大，可以手动轮转：
```bash
# 备份当前日志
mv mcp_server.log mcp_server.log.backup

# 重启服务器将创建新的日志文件
```

## 调试技巧

1. **跟踪特定请求**: 使用请求ID（如`veo3_1703001000`）跟踪整个请求流程
2. **监控Azure上传**: 查找包含"Azure"的日志行
3. **性能分析**: 查找"generation time"和"Upload speed"
4. **错误排查**: 查找"ERROR"和"❌"标记的日志
