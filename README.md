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
├── essay_processor.py              # Main processor - calls Coze API
├── post_process_cache.py           # Post-processing - handles Coze API JSON response
├── config/
│   └── config.example.json         # Configuration file (API keys required)
├── post_process/                   # Post-processing tools
│   ├── txt_result_orgnize.py   
│   └── txt_to_image_converter.py
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
