# 测试不同的markdown转图片方案
import os
import sys
# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_html2image(markdown_content):
    """测试html2image方案"""
    try:
        import markdown
        from html2image import Html2Image
        
        print("\n--- 测试 html2image 方案 ---")
        
        # 1. Markdown转HTML
        html = markdown.markdown(markdown_content, extensions=['extra', 'codehilite'])
        
        # 2. 添加CSS样式
        css = """
        body { 
            font-family: 'Microsoft YaHei', 'SimHei', Arial, sans-serif; 
            margin: 30px; 
            line-height: 1.8;
            background-color: white;
            max-width: 800px;
            font-size: 16px;
        }
        h1 { 
            color: #2c3e50; 
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        h2 { 
            color: #34495e; 
            margin-top: 30px;
        }
        h3 { 
            color: #7f8c8d; 
        }
        strong { 
            color: #e74c3c; 
            font-weight: bold;
        }
        em { 
            color: #3498db; 
            font-style: italic;
        }
        code { 
            background-color: #f8f8f8; 
            padding: 3px 6px; 
            border-radius: 4px; 
            font-family: 'Consolas', monospace;
            color: #e74c3c;
        }
        blockquote {
            border-left: 4px solid #3498db;
            padding-left: 20px;
            margin-left: 0;
            color: #7f8c8d;
            background-color: #f8f9fa;
            padding: 15px 20px;
            border-radius: 4px;
        }
        hr {
            border: none;
            height: 2px;
            background-color: #ecf0f1;
            margin: 30px 0;
        }
        ul {
            padding-left: 20px;
        }
        li {
            margin: 8px 0;
        }
        """
        
        # 3. 转换为图片 - 修复尺寸问题
        output_path = os.path.join(os.path.dirname(__file__), "test_html2image.png")
        
        # 方法1: 使用固定高度
        hti = Html2Image(size=(900, 1200))  # 设置具体的高度
        hti.screenshot(html_str=html, css_str=css, save_as="test_html2image.png")
        
        # 移动文件到正确位置
        if os.path.exists("test_html2image.png"):
            if os.path.exists(output_path):
                os.remove(output_path)
            os.rename("test_html2image.png", output_path)
            print(f"✓ html2image 转换成功: {output_path}")
        else:
            # 方法2: 如果方法1失败，尝试不指定尺寸
            print("尝试方法2: 不指定尺寸")
            hti = Html2Image()
            hti.screenshot(html_str=html, css_str=css, save_as=output_path)
            print(f"✓ html2image 转换成功: {output_path}")
        
    except ImportError as e:
        print(f"✗ html2image 方案失败: 缺少依赖 {e}")
        print("  请安装: pip install markdown html2image")
    except Exception as e:
        print(f"✗ html2image 方案失败: {e}")
        print("  尝试替代方案...")
        
        # 替代方案: 使用selenium后端
        try_selenium_backend(markdown_content)

def try_selenium_backend(markdown_content):
    """尝试使用selenium后端"""
    try:
        import markdown
        from html2image import Html2Image
        
        print("--- 尝试selenium后端 ---")
        
        html = markdown.markdown(markdown_content, extensions=['extra', 'codehilite'])
        
        css = """
        body { 
            font-family: 'Microsoft YaHei', Arial, sans-serif; 
            margin: 30px; 
            line-height: 1.8;
            background-color: white;
            width: 800px;
        }
        h1 { color: #2c3e50; }
        strong { color: #e74c3c; }
        em { color: #3498db; }
        """
        
        output_path = os.path.join(os.path.dirname(__file__), "test_html2image_selenium.png")
        
        # 使用selenium后端，更稳定
        hti = Html2Image(browser='chrome', output_path=os.path.dirname(__file__))
        hti.screenshot(
            html_str=html, 
            css_str=css, 
            save_as="test_html2image_selenium.png",
            size=(900, 1200)
        )
        
        print(f"✓ selenium后端转换成功: {output_path}")
        
    except Exception as e:
        print(f"✗ selenium后端也失败: {e}")

def test_markdown_libraries():
    """测试各种markdown转图片的库"""
    
    # 测试内容
    markdown_content = """# 批改结果

## rewrite_output

**Hello, everyone.** I'm Li Ming. Our class is going to hold a class meeting with the theme of *'A sentence I like'*. I've chosen the sentence **There is a crack in everything. That's how the light gets in.**

This sentence means that everything in the world is not perfect. It always has some flaws. But we shouldn't just focus on the imperfections negatively because there might be light shining through the cracks. The light is like hope, bringing a glimmer of brightness to life.

*I realized that failure is the 'crack' that allowed me to see what I needed to improve.* **Last semester, unfortunately, I failed in a significant Math exam.** It was really a tough time for me. However, this quote gave me the strength to face it. **I love this quote because it has helped me remain optimistic during difficult times.** I **began to study in a more effective and systematic way.** Eventually, I made great progress.

Thank you, dear classmates and teachers, for listening.

---

### 语法特点:
- **粗体文字**
- *斜体文字*  
- `代码文字`
- 普通文字

> 这是一个引用块
> 可以包含多行内容
"""
    
    print("=== 测试Markdown转图片功能 ===")
    
    # 只测试html2image方案
    test_html2image(markdown_content)

if __name__ == "__main__":
    test_markdown_libraries()