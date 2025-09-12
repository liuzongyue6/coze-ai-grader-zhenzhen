# AI Essay Grader

🤖 基于 Coze Workflow 的英语作文自动批改系统

## 功能特点

- 📸 **批量图片处理**: 自动处理文件夹中的作文图片
- 🎯 **AI智能批改**: 使用 Coze 工作流进行作文评价
- 📊 **详细反馈**: 提供英语评价和书写评价
- 🔄 **后处理工具**: 格式化结果，压缩图片
- 📁 **批量操作**: 支持微信文件夹批量处理

## 项目结构
```
├── essay_processor.py          # 主处理器 - 调用Coze批改作文
├── config/
│   └── config.example.json          # 配置文件 (需要设置API密钥)
├── post_process/              # 后处理工具
│   ├── txt_result_orgnize.py  # 结果格式化
│   └── txt_to_image_converter.py
├── utils/
│   └── compress_file.py       # 图片压缩工具
└── test/                      # 测试文件夹
```

## 快速开始

### 1. 安装依赖

```bash
pip install cozepy pillow
```

### 2. 配置设置

复制 `config/config.example.json` 到 `config/config.json` 并填入你的配置：

```json
{
    "workflow_id": "你的工作流ID",
    "api_token": "你的API令牌"
}
```

### 3. 运行程序

```bash
python essay_processor.py
```

## 使用说明

1. 将作文图片按学生姓名分文件夹存放
2. 运行主程序，系统会自动：
   - 上传图片到 Coze
   - 调用工作流进行批改
   - 生成批改结果文件
3. 使用后处理工具格式化结果

## 工具说明

- **essay_processor.py**: 主要的批改处理器
- **post_process/txt_result_orgnize.py**: 将批改结果格式化为易读的报告
- **utils/compress_file.py**: 压缩图片以减少上传时间

## 注意事项

- 请确保 Coze API 配置正确
- 支持的图片格式：PNG, JPG, JPEG, BMP, GIF
- 建议图片大小不超过 5MB

## 许可证

MIT License
```
