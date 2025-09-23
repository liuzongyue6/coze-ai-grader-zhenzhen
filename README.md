# AI Essay Grader

🤖 Automated English Essay Grading System Based on Coze Workflow

## Features

- 📸 **Batch Image Processing**: Automatically process essay images in folders
- 🎯 **AI-Powered Grading**: Use Coze workflow for essay evaluation
- 📊 **Detailed Feedback**: Provide English evaluation and writing assessment
- 🔄 **Post-processing Tools**: Format results and compress images
- 📁 **Batch Operations**: Support batch processing of WeChat folders

## Project Structure
```
├── coze_workflow_client.py          # Main processor - calls Coze API
├── config/
│   └── config.example.json         # Configuration file (API keys required)
├── post_process/                   # Post-processing tools
│   ├── json_to_markdown.py         # general paser, from json to makrdown, for single instance
│   ├── json_to_markdown_trans.py   # specific paser, for translation
│   └── txt_markdown_to_html_img.py # transfer txt markdown to image
├── utils/
│   └── compress_file.py            # Image compression tool
└── test/                           # Test folder
```

## Quick Start

### 1. Install Dependencies

```bash
pip install cozepy pillow
```

### 2. Configuration Setup

Copy `config/config.example.json` to `config/config.json` and fill in your configuration:

```json
{
    "workflow_id": "your_workflow_id",
    "api_token": "your_api_token"
}
```

### 3. Run the Program

```bash
python essay_processor.py
```

## Usage Instructions

1. Organize essay images in folders by student names
2. Run the main program, the system will automatically:
   - Upload images to Coze
   - Call workflow for grading
   - Generate grading result files
3. Use post-processing tools to format results

## Tool Descriptions

- **coze_workflow_client.py**: Main processor
- **api_response_format.py**: Format API results into readable txt
- **post_process/txt_to_image_converter.py**: post_process the txt file to images
- **utils/compress_file.py**: Compress images to reduce upload time
- **database/mistake_scanner.py**: count and summarize the mistakes
## Notes

- Ensure Coze API is configured correctly
- Supported image formats: PNG, JPG, JPEG, BMP, GIF
- Recommended image size: under 2MB

## License

MIT License
