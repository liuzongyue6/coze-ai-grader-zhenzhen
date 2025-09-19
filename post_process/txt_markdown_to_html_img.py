"""
使用html2image方案将markdown格式的txt文件转换为图片
支持完整的markdown语法渲染
"""
import os
import markdown
from html2image import Html2Image
from typing import Optional

def convert_markdown_to_image(markdown_content: str, output_path: str, width: int = 900, height: int = None) -> bool:
    """
    将markdown内容转换为图片
    
    Args:
        markdown_content: markdown格式的文本内容
        output_path: 输出图片路径
        width: 图片宽度，默认900px
        height: 图片高度，如果为None则根据内容自动计算
        
    Returns:
        bool: 转换是否成功
    """
    try:
        print(f"开始转换markdown到图片: {output_path}")
        
        # 1. Markdown转HTML
        html = markdown.markdown(
            markdown_content, 
            extensions=[
                'extra',           # 支持表格、脚注等扩展语法
                'codehilite',      # 代码高亮
                'toc',             # 目录
                'nl2br'            # 换行转换
            ]
        )
        
        # 2. 添加完整的CSS样式
        css = """
        body { 
            font-family: 'Microsoft YaHei', 'SimHei', 'PingFang SC', Arial, sans-serif; 
            margin: 30px; 
            line-height: 1.8;
            background-color: white;
            max-width: 820px;
            font-size: 16px;
            color: #333;
        }
        
        /* 标题样式 */
        h1 { 
            color: #2c3e50; 
            border-bottom: 3px solid #3498db;
            padding-bottom: 12px;
            margin-top: 0;
            margin-bottom: 25px;
            font-size: 28px;
            font-weight: bold;
        }
        h2 { 
            color: #34495e; 
            margin-top: 35px;
            margin-bottom: 20px;
            font-size: 22px;
            border-bottom: 1px solid #ecf0f1;
            padding-bottom: 8px;
        }
        h3 { 
            color: #7f8c8d; 
            margin-top: 25px;
            margin-bottom: 15px;
            font-size: 18px;
        }
        h4, h5, h6 {
            color: #95a5a6;
            margin-top: 20px;
            margin-bottom: 10px;
        }
        
        /* 文本格式 */
        p {
            margin: 12px 0;
            text-align: justify;
        }
        
        strong { 
            color: #e74c3c; 
            font-weight: bold;
        }
        
        em { 
            color: #3498db; 
            font-style: italic;
        }
        
        /* 代码样式 */
        code { 
            background-color: #f8f8f8; 
            padding: 3px 6px; 
            border-radius: 4px; 
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            color: #e74c3c;
            font-size: 14px;
        }
        
        pre {
            background-color: #f8f8f8;
            border: 1px solid #e1e8ed;
            border-radius: 6px;
            padding: 15px;
            overflow-x: auto;
            margin: 15px 0;
        }
        
        pre code {
            background-color: transparent;
            padding: 0;
            color: #333;
        }
        
        /* 引用块 */
        blockquote {
            border-left: 4px solid #3498db;
            padding-left: 20px;
            margin: 20px 0;
            color: #7f8c8d;
            background-color: #f8f9fa;
            padding: 15px 20px;
            border-radius: 4px;
            font-style: italic;
        }
        
        /* 分割线 */
        hr {
            border: none;
            height: 2px;
            background-color: #ecf0f1;
            margin: 30px 0;
        }
        
        /* 列表样式 */
        ul, ol {
            padding-left: 25px;
            margin: 15px 0;
        }
        
        li {
            margin: 8px 0;
            line-height: 1.6;
        }
        
        /* 表格样式 */
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }
        
        th, td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        
        th {
            background-color: #f8f9fa;
            font-weight: bold;
            color: #2c3e50;
        }
        
        /* 链接样式 */
        a {
            color: #3498db;
            text-decoration: none;
        }
        
        a:hover {
            text-decoration: underline;
        }
        
        /* 键值对样式 (特殊处理原有格式) */
        .key-value {
            margin: 15px 0;
        }
        
        .key {
            color: #2980b9;
            font-weight: bold;
            font-size: 16px;
        }
        
        .value {
            margin-left: 20px;
            margin-top: 8px;
            color: #2c3e50;
        }
        """
        
        # 3. 创建完整的HTML文档
        full_html = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>{css}</style>
        </head>
        <body>
        {html}
        </body>
        </html>
        """
        
        # 4. 动态计算高度
        if height is None:
            # 根据内容长度估算高度
            line_count = markdown_content.count('\n') + 1
            char_count = len(markdown_content)
            
            # 基础估算：每行约25px，每个字符约0.8px额外高度
            estimated_height = max(
                line_count * 25 + char_count * 0.8 + 200,  # 基于行数和字符数
                1500,  # 最小高度
                min(char_count * 2, 4000)  # 根据字符数，但不超过4000px
            )
            
            height = int(estimated_height)
            print(f"根据内容估算图片高度: {height}px (行数: {line_count}, 字符数: {char_count})")
        
        # 5. 转换为图片
        output_dir = os.path.dirname(output_path)
        output_filename = os.path.basename(output_path)
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 使用html2image转换，尝试多种方法
        try:
            # 方法1: 指定尺寸
            hti = Html2Image(size=(width, height), output_path=output_dir)
            hti.screenshot(html_str=full_html, save_as=output_filename)
        except Exception as e:
            print(f"方法1失败，尝试方法2: {e}")
            # 方法2: 不指定高度，让其自动调整
            try:
                hti = Html2Image(size=(width, 0), output_path=output_dir)
                hti.screenshot(html_str=full_html, save_as=output_filename)
            except Exception as e2:
                print(f"方法2失败，尝试方法3: {e2}")
                # 方法3: 完全不指定尺寸
                hti = Html2Image(output_path=output_dir)
                hti.screenshot(html_str=full_html, save_as=output_filename)
        
        # 检查文件是否生成成功
        if os.path.exists(output_path):
            # 检查文件大小，确保不是空文件
            file_size = os.path.getsize(output_path)
            if file_size > 1000:  # 大于1KB
                print(f"✓ 图片转换成功: {output_path} (大小: {file_size} bytes)")
                return True
            else:
                print(f"✗ 图片文件太小，可能转换失败: {file_size} bytes")
                return False
        else:
            print(f"✗ 图片转换失败: 文件未生成")
            return False
            
    except Exception as e:
        print(f"✗ 转换过程中出错: {e}")
        return False

def preprocess_special_format(content: str) -> str:
    """
    预处理特殊格式，将键值对格式转换为更好的markdown格式
    
    Args:
        content: 原始文本内容
        
    Returns:
        str: 处理后的markdown内容
    """
    lines = content.strip().split('\n')
    processed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # 处理 === 标题 ===
        if line.startswith('===') and line.endswith('==='):
            title = line.replace('===', '').strip()
            processed_lines.append(f"# {title}")
            processed_lines.append("")
            
        # 处理消息标题
        elif line.startswith('消息') and line.endswith(':'):
            processed_lines.append(f"## {line}")
            processed_lines.append("")
            
        # 处理 **键名**
        elif line.startswith('**') and line.endswith('**'):
            key = line[2:-2]
            processed_lines.append(f"### {key}")
            
            # 收集值内容
            i += 1
            value_lines = []
            
            while i < len(lines):
                current_line = lines[i]
                stripped = current_line.strip()
                
                # 如果是空行，保留
                if not stripped:
                    value_lines.append("")
                    i += 1
                    continue
                
                # 如果遇到新的键或标题，停止
                if (stripped.startswith('**') and stripped.endswith('**')) or \
                   (stripped.startswith('===') and stripped.endswith('===')) or \
                   (stripped.startswith('消息') and stripped.endswith(':')):
                    break
                
                # 添加当前行
                value_lines.append(current_line)
                i += 1
            
            # 处理值内容
            if value_lines:
                full_value = '\n'.join(value_lines).strip()
                
                # 去掉开头和结尾的*号
                if full_value.startswith('*'):
                    full_value = full_value[1:]
                if full_value.endswith('*'):
                    full_value = full_value[:-1]
                
                # 添加值内容
                processed_lines.append("")
                processed_lines.append(full_value)
                processed_lines.append("")
            
            i -= 1  # 因为外层循环会+1
            
        else:
            # 普通行直接添加
            if line:
                processed_lines.append(line)
            else:
                processed_lines.append("")
        
        i += 1
    
    return '\n'.join(processed_lines)

def convert_file_to_image(input_path: str, output_path: Optional[str] = None, 
                         width: int = 900, height: int = None) -> bool:
    """
    将单个txt文件转换为图片
    
    Args:
        input_path: 输入txt文件路径
        output_path: 输出图片路径，如果为None则自动生成
        width: 图片宽度
        height: 图片高度，如果为None则自动计算
        
    Returns:
        bool: 转换是否成功
    """
    if not os.path.exists(input_path):
        print(f"✗ 输入文件不存在: {input_path}")
        return False
    
    if output_path is None:
        output_path = input_path.replace('.txt', '_markdown图片.png')
    
    try:
        # 读取文件内容
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 预处理特殊格式
        markdown_content = preprocess_special_format(content)
        
        # 转换为图片
        return convert_markdown_to_image(markdown_content, output_path, width, height)
        
    except Exception as e:
        print(f"✗ 处理文件失败: {e}")
        return False

def batch_convert_directory(directory_path: str, width: int = 900, height: int = None) -> int:
    """
    批量转换目录下的所有txt文件
    
    Args:
        directory_path: 目录路径
        width: 图片宽度
        height: 图片高度，如果为None则自动计算
        
    Returns:
        int: 成功转换的文件数量
    """
    if not os.path.exists(directory_path):
        print(f"✗ 目录不存在: {directory_path}")
        return 0
    
    converted_count = 0
    total_files = 0
    
    print(f"开始批量转换目录: {directory_path}")
    
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.endswith('.txt'):
                total_files += 1
                input_path = os.path.join(root, file)
                output_path = input_path.replace('.txt', '_markdown图片.png')
                
                print(f"\n正在处理 ({converted_count + 1}/{total_files}): {file}")
                
                if convert_file_to_image(input_path, output_path, width, height):
                    converted_count += 1
    
    print(f"\n批量转换完成: 成功 {converted_count}/{total_files} 个文件")
    return converted_count

# 主程序
if __name__ == "__main__":
    import sys
    
    print("=== Markdown转图片工具 (基于html2image) ===")
    
    if len(sys.argv) > 1:
        # 命令行模式
        target_path = sys.argv[1]
        
        if os.path.isfile(target_path):
            # 单文件转换
            print(f"转换单个文件: {target_path}")
            convert_file_to_image(target_path)
        elif os.path.isdir(target_path):
            # 批量转换
            print(f"批量转换目录: {target_path}")
            batch_convert_directory(target_path)
        else:
            print(f"✗ 路径不存在: {target_path}")
    else:
        # 默认批量处理
        default_directory = r"E:\zhenzhen_eng_coze\example\高三第二周作文_reduced"
        if os.path.exists(default_directory):
            batch_convert_directory(default_directory)
        else:
            print("请提供要转换的文件或目录路径作为参数")
            print("用法: python markdown_html_converter.py <文件或目录路径>")
