"""
测试Markdown转图片功能（Playwright版本）
"""
import os
import sys
import traceback

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import markdown
from playwright.sync_api import sync_playwright


def validate_png_file(path: str) -> tuple[bool, str]:
    if not os.path.exists(path):
        return False, "文件不存在"
    try:
        file_size = os.path.getsize(path)
        if file_size <= 100:
            return False, f"文件太小({file_size} bytes)"
        with open(path, "rb") as f:
            signature = f.read(8)
        if signature != b"\x89PNG\r\n\x1a\n":
            return False, f"PNG签名错误: {signature!r}"
        return True, f"有效PNG({file_size} bytes)"
    except Exception as e:
        return False, f"校验失败: {e}"


def test_playwright(markdown_content: str):
    print("\n--- 测试 Playwright 方案 ---")
    html = markdown.markdown(markdown_content, extensions=["extra", "codehilite", "nl2br"])

    css = """
    body {
        font-family: 'Microsoft YaHei', 'SimHei', Arial, sans-serif;
        margin: 30px;
        line-height: 1.8;
        background-color: white;
        max-width: 820px;
        font-size: 16px;
    }
    h1 {
        color: #2c3e50;
        border-bottom: 2px solid #3498db;
        padding-bottom: 10px;
    }
    code {
        background-color: #f8f8f8;
        padding: 3px 6px;
        border-radius: 4px;
        font-family: 'Consolas', monospace;
    }
    """

    full_html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>{css}</style>
    </head>
    <body>{html}</body>
    </html>
    """

    output_path = os.path.join(os.path.dirname(__file__), "test_playwright.png")

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 900, "height": 900}, device_scale_factor=2)
            page.set_content(full_html, wait_until="networkidle")
            page.screenshot(path=output_path, full_page=True, type="png")
            browser.close()

        is_valid, detail = validate_png_file(output_path)
        if is_valid:
            print(f"[OK] Playwright 转换成功: {output_path} ({detail})")
        else:
            print(f"[ERROR] Playwright 转换失败: {detail}")
    except Exception as e:
        print(f"[ERROR] Playwright 方案失败: {e}")
        print(traceback.format_exc())


def test_markdown_libraries():
    markdown_content = """# 批改结果

## rewrite_output

**Hello, everyone.** I'm Li Ming.

This sentence means that everything in the world is not perfect.

---

### 语法特点:
- **粗体文字**
- *斜体文字*
- `代码文字`

> 这是一个引用块
> 可以包含多行内容
"""

    print("=== 测试Markdown转图片功能（Playwright） ===")
    test_playwright(markdown_content)


if __name__ == "__main__":
    test_markdown_libraries()
