# 日志系统使用指南 (Logging Guide)

## 概述 (Overview)

coze_workflow_client.py 现在包含了一个完整的日志记录系统，用于记录运行过程中的所有错误和重要操作信息，方便后续检查哪些文件没有被正确处理。

## 日志文件位置 (Log File Location)

- 日志文件保存在 `logs/` 目录下
- 文件名格式：`coze_workflow_YYYYMMDD_HHMMSS.log`
- 例如：`coze_workflow_20251119_145758.log`

## 日志内容 (Log Content)

日志记录以下信息：

### 1. 配置加载 (Configuration Loading)
- ✅ 成功加载配置文件
- ❌ 配置文件不存在
- ❌ 配置文件格式错误

### 2. 文件夹扫描 (Folder Scanning)
- ✅ 发现的文件夹及图片数量
- ⚠️ 空文件夹警告
- ❌ 文件夹不存在错误

### 3. 图片上传 (Image Upload)
- ✅ 每个文件上传成功的记录（包含 file_id）
- ❌ 单个文件上传失败的详细信息
- ⚠️ 部分文件上传失败的汇总

### 4. 工作流处理 (Workflow Processing)
- ✅ 开始处理文件夹（包含 file_ids）
- ❌ 工作流错误
- ℹ️ 工作流中断和恢复
- ✅ 处理完成及消息数量

### 5. 缓存保存 (Cache Saving)
- ✅ JSON 缓存文件保存成功
- ❌ 缓存保存失败

### 6. 最终汇总 (Final Summary)
- ✅ 成功处理的文件夹列表
- ❌ 失败的文件夹列表
- 📊 成功/失败统计

## 日志格式 (Log Format)

每条日志包含：
- 时间戳
- 日志级别 (INFO/WARNING/ERROR)
- 详细消息

示例：
```
2025-11-19 14:57:58,662 - INFO - 日志系统初始化完成，日志文件: logs/coze_workflow_20251119_145758.log
2025-11-19 14:57:59,123 - INFO - 配置文件加载成功: config/config.translation.json
2025-11-19 14:58:00,456 - ERROR - 上传单个文件失败: image1.jpg, 错误: Connection timeout
2025-11-19 14:58:05,789 - INFO - 文件夹 student_001 流式处理完成，消息数量: 3
```

## 查看日志 (Viewing Logs)

### 方法 1: 直接查看最新日志
```bash
# Linux/Mac
tail -f logs/coze_workflow_*.log

# Windows
type logs\coze_workflow_*.log
```

### 方法 2: 查看所有错误
```bash
# Linux/Mac
grep "ERROR" logs/coze_workflow_*.log

# Windows
findstr "ERROR" logs\coze_workflow_*.log
```

### 方法 3: 查看失败的文件夹
```bash
# Linux/Mac
grep "失败的文件夹" logs/coze_workflow_*.log

# Windows
findstr "失败的文件夹" logs\coze_workflow_*.log
```

## 故障排查 (Troubleshooting)

1. **找不到日志文件**
   - 检查 `logs/` 目录是否存在
   - 确认程序已经运行过

2. **日志文件为空**
   - 确认程序运行时有适当的写权限
   - 检查是否有异常提前终止了程序

3. **查找特定文件夹的错误**
   ```bash
   grep "folder_name" logs/coze_workflow_*.log
   ```

## 注意事项 (Notes)

1. 日志文件会随着运行次数增加而累积
2. 建议定期清理旧的日志文件
3. 日志目录已添加到 `.gitignore`，不会被提交到 Git
4. 每次运行都会创建新的日志文件，不会覆盖旧文件

## 示例：分析处理失败的原因

假设处理失败，可以按以下步骤查看日志：

1. 打开最新的日志文件
2. 搜索 "ERROR" 关键字
3. 查看具体的错误消息
4. 找到失败的文件夹名称
5. 检查该文件夹相关的所有日志条目
6. 根据错误信息采取相应的修复措施

这样就可以精确定位哪些文件或文件夹没有被正确处理，以及失败的具体原因。
