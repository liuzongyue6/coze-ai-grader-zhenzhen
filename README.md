# AI Essay Grader

🤖 基于Coze Workflow的自动化英语翻译批改系统

## 功能特性

- 📸 **批量图片处理**: 自动处理文件夹中的图片
- 🎯 **AI智能批改**: 使用Coze workflow进行作文/翻译评估
- 🔄 **后处理工具**: 格式化结果并生成图片报告
- 📁 **批量操作**: 支持批量处理文件夹结构
- 📈 **错误分析**: 统计和可视化翻译错误

## 项目结构
```
├── coze_workflow_client.py          # 主处理器 - 调用Coze API进行批改
├── config/
│   ├── config.example.json         # 配置文件示例 (需要API密钥)
│   ├── translation_format_config.py      # 翻译格式配置
│   └── translation_rec_format_config.py  # 翻译推荐格式配置
├── post_process/                   # 后处理工具集
│   ├── api_response_format.py      # 通用API响应格式化器
│   ├── json_to_markdown.py         # JSON转Markdown转换器
│   ├── text_to_image_simple.py     # 简单文本转图片工具(PIL)
│   └── txt_markdown_to_html_img.py # Markdown转HTML图片工具(chromium内核)
│   └── txt_markdown_to_html_img_Playwright.py # Markdown转HTML图片工具(Playwright)
├── database/
│   └── translation_mistake_scanner_report.py  # 翻译错误统计分析工具
├── utils/
│   └── compress_file.py            # 图片压缩工具
└── test/                           # 测试文件夹
    ├── test_json_decouple_extraction.py  # JSON解析测试
    └── test_playwright_converter.py      # 图片转换测试
```

## 快速开始

### 1. 安装依赖

```bash
pip install cozepy pillow markdown playwright matplotlib
python -m playwright install chromium
```

### 2. 配置设置

复制 `config/config.example.json` 为 `config/config.json` 并填入您的配置：

```json
{
    "workflow_id": "your_workflow_id",
    "api_token": "your_api_token"
}
```

可以从Coze工作流页面获取这些信息：
- workflow_id: 工作流ID
- api_token: 您的API访问令牌

### 3. 运行程序

#### 主流程：批改作文/翻译

编辑 `coze_workflow_client.py` 中的配置区域：

```python
# 配置设置
config_file = "config/config.json"
folder_tobe_process = r"your_folder_path"  # 包含作业的根文件夹
supported_formats = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
```

然后运行：
```bash
python coze_workflow_client.py
```

程序会自动：
1. 扫描指定文件夹下的所有子文件夹
2. 上传每个文件夹中的图片到Coze
3. 调用workflow进行AI批改
4. 保存原始JSON响应到各文件夹

## 使用说明

### 工作流程

1. **组织文件结构**
   ```
   根文件夹/
   ├── 学生1/
   │   ├── 图片1.jpg
   │   └── 图片2.jpg
   ├── 学生2/
   │   └── 图片1.jpg
   └── ...
   ```

2. **批改处理** - 运行 `coze_workflow_client.py`
   - 自动上传图片
   - 调用Coze workflow批改
   - 生成JSON缓存文件 (格式: `学生名_response_cache_时间戳.json`)

3. **格式化结果** - 使用 `post_process/api_response_format.py`
   - 解析JSON响应
   - 提取批改内容
   - 生成Markdown格式文本
   - 支持单输出和多输出配置

4. **生成图片报告** - 选择转换工具
   - `text_to_image_simple.py`: 使用PIL库，适合简单格式
   - `txt_markdown_to_html_img.py`: 基于 html2image，将Markdown转换为图片
   - `txt_markdown_to_html_img_playwright.py`: 使用Playwright，支持完整Markdown语法
   


5. **错误分析** (翻译专用) - 运行 `translation_mistake_scanner_report.py`
   - 提取标记为"翻得不好"的错误
   - 生成统计报告JSON
   - 生成可视化图表

## 工具详细说明

### 核心处理器

- **coze_workflow_client.py**: 主处理程序
  - 批量上传图片到Coze
  - 流式调用workflow API
  - 处理中断恢复
  - 保存原始JSON响应

### 后处理工具

- **api_response_format.py**: 通用API响应格式化器
  - 支持单输出和多输出配置
  - 从JSON提取嵌套内容
  - 处理转义字符
  - 生成格式化Markdown文本

- **json_to_markdown.py**: JSON到Markdown转换器
  - 字段映射和排序
  - 自定义输出格式
  - 适配批改报告

- **text_to_image_simple.py**: 简单文本转图片
  - 使用PIL库直接渲染
  - 支持中文字体
  - 智能文本换行
  - 轻量快速

- **txt_markdown_to_html_img_playwright.py**: Markdown转HTML图片
  - 完整Markdown语法支持
  - 使用Playwright渲染，额外安装渲染为图片，使用内置Chromium
  - CSS样式， 适合复杂格式

- **txt_markdown_to_html_img.py**: Markdown转HTML图片
  - 完整Markdown语法支持
  - 使用 html2image 渲染为图片，使用内置Chromium
  - CSS样式， 适合复杂格式

### 数据分析工具

- **translation_mistake_scanner_report.py**: 翻译错误分析
  - 解析学生翻译JSON日志
  - 提取"翻得不好"的错误
  - 生成错误统计报告
  - 创建可视化图表
  - 输出文件：
    - `1_student_mistakes.json`: 学生错误详情
    - `2_statistics_summary.json`: 统计摘要
    - `mistake_rate_pie_charts.png`: 错误率饼图
    - `student_mistakes_visual.png`: 错误详情可视化

### 实用工具

- **compress_file.py**: 图片压缩工具
  - 批量压缩图片到指定大小
  - 减少上传时间
  - 保持图片质量
  - 支持多种格式

## 配置说明

### 主配置文件 (config.json)

```json
{
    "workflow_id": "your_workflow_id",
    "api_token": "your_api_token"
}
```

### 格式配置文件

- `translation_format_config.py`: 翻译输出格式配置
- `translation_rec_format_config.py`: 翻译推荐格式配置

这些配置文件定义了：
- 输出字段映射
- 字段显示顺序
- Markdown格式模板
- 多输出类型配置

## 注意事项

- 确保正确配置Coze API密钥
- 支持的图片格式: PNG, JPG, JPEG, BMP, GIF
- 建议图片大小: 2MB以下
- 中文字体路径可能需要根据系统调整
- API调用需要稳定的网络连接
- 流式处理支持中断恢复
- Playwright首次安装后需执行 `python -m playwright install chromium`
- 如图片文件存在但打不开，请检查脚本日志中的PNG校验与异常堆栈

## 许可证

MIT License
