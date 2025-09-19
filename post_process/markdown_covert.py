"""
对txt内容（markdown格式）通过html2image的方案转换成图片
直接使用txt对应的键值对
"""
from PIL import Image, ImageDraw, ImageFont
import os
import textwrap
from typing import List, Tuple

def get_chinese_fonts():
    """
    获取中文字体，按优先级尝试
    """
    font_paths = [
        # Windows 字体路径
        "C:/Windows/Fonts/msyh.ttc",      # 微软雅黑
        "C:/Windows/Fonts/simhei.ttf",    # 黑体
        "C:/Windows/Fonts/simsun.ttc",    # 宋体
        "C:/Windows/Fonts/simkai.ttf",    # 楷体
        # 相对路径
        "msyh.ttc",
        "simhei.ttf", 
        "simsun.ttc",
        # macOS 字体路径
        "/System/Library/Fonts/PingFang.ttc",
        "/Library/Fonts/Arial Unicode MS.ttf",
        # Linux 字体路径
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            return font_path
    
    return None

def wrap_text_by_width(text, font, max_width, draw):
    """
    根据像素宽度智能换行
    """
    if not text:
        return []
    
    lines = []
    current_line = ""
    
    for char in text:
        test_line = current_line + char
        try:
            # 尝试使用textbbox测量宽度
            bbox = draw.textbbox((0, 0), test_line, font=font)
            text_width = bbox[2] - bbox[0]
        except:
            # 如果textbbox不可用，使用估算
            text_width = len(test_line) * 14  # 估算每个字符14像素
        
        if text_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
                current_line = char
            else:
                # 单个字符就超宽的情况
                lines.append(char)
                current_line = ""
    
    if current_line:
        lines.append(current_line)
    
    return lines

def create_image_from_text(text_content: str, output_path: str, width: int = 900):
    """
    直接从文本创建图片，不经过HTML转换 - 使用简化的解析逻辑
    """
    # 字体设置
    chinese_font_path = get_chinese_fonts()
    
    if chinese_font_path:
        try:
            title_font = ImageFont.truetype(chinese_font_path, 24)
            key_font = ImageFont.truetype(chinese_font_path, 18)
            value_font = ImageFont.truetype(chinese_font_path, 16)
            print(f"使用字体: {chinese_font_path}")
        except Exception as e:
            print(f"加载字体失败: {e}")
            title_font = ImageFont.load_default()
            key_font = ImageFont.load_default()
            value_font = ImageFont.load_default()
    else:
        print("未找到中文字体，使用默认字体")
        title_font = ImageFont.load_default()
        key_font = ImageFont.load_default()
        value_font = ImageFont.load_default()
    
    # 颜色定义
    bg_color = (255, 255, 255)    # 白色背景
    text_color = (51, 51, 51)     # 深灰文字
    key_color = (41, 128, 185)    # 蓝色键名
    title_color = (44, 62, 80)    # 深蓝标题
    
    # 创建临时draw对象用于测量文本
    temp_image = Image.new('RGB', (width, 100), bg_color)
    temp_draw = ImageDraw.Draw(temp_image)
    
    # 布局参数
    left_margin = 30
    right_margin = 30
    max_text_width = width - left_margin - right_margin - 40
    
    # 解析内容
    lines = text_content.strip().split('\n')
    elements = []
    current_y = 40
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if line.startswith('===') and line.endswith('==='):
            # 标题
            title = line.replace('===', '').strip()
            elements.append({
                'type': 'title',
                'text': title,
                'y': current_y,
                'font': title_font,
                'color': title_color
            })
            current_y += 60
            
        elif line.startswith('消息') and line.endswith(':'):
            # 消息标题
            elements.append({
                'type': 'subtitle',
                'text': line,
                'y': current_y,
                'font': key_font,
                'color': key_color
            })
            current_y += 40
            
        elif line.startswith('**') and line.endswith('**'):
            # 键名
            key = line[2:-2]
            elements.append({
                'type': 'key',
                'text': f"{key}:",
                'y': current_y,
                'font': key_font,
                'color': key_color
            })
            current_y += 35
            
            # 寻找值内容
            i += 1
            value_lines = []
            
            # 收集所有值行
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
                # 将所有值行合并
                full_value = '\n'.join(value_lines).strip()
                
                # 去掉开头和结尾的*号
                if full_value.startswith('*'):
                    full_value = full_value[1:]
                if full_value.endswith('*'):
                    full_value = full_value[:-1]
                
                # 按段落分割
                paragraphs = full_value.split('\n\n')
                
                for paragraph in paragraphs:
                    if paragraph.strip():
                        # 智能换行
                        wrapped_lines = wrap_text_by_width(paragraph.strip(), value_font, max_text_width, temp_draw)
                        
                        for wrapped_line in wrapped_lines:
                            elements.append({
                                'type': 'value',
                                'text': wrapped_line,
                                'y': current_y,
                                'font': value_font,
                                'color': text_color
                            })
                            current_y += 26
                        
                        current_y += 15  # 段落间距
            
            current_y += 20  # 键值对间距
            i -= 1  # 因为外层循环会+1
        
        else:
            # 普通文本行
            if line:
                wrapped_lines = wrap_text_by_width(line, value_font, max_text_width, temp_draw)
                
                for wrapped_line in wrapped_lines:
                    elements.append({
                        'type': 'text',
                        'text': wrapped_line,
                        'y': current_y,
                        'font': value_font,
                        'color': text_color
                    })
                    current_y += 26
                
                current_y += 10
        
        i += 1
    
    # 创建图片
    total_height = current_y + 100
    print(f"图片总高度: {total_height}px, 元素数量: {len(elements)}")
    
    image = Image.new('RGB', (width, total_height), bg_color)
    draw = ImageDraw.Draw(image)
    
    # 绘制边框
    border_color = (200, 200, 200)
    draw.rectangle([10, 10, width-10, total_height-10], outline=border_color, width=2)
    
    # 绘制所有元素
    for element in elements:
        x_pos = left_margin
        
        if element['type'] == 'title':
            # 标题居中
            try:
                bbox = draw.textbbox((0, 0), element['text'], font=element['font'])
                text_width = bbox[2] - bbox[0]
                x_pos = (width - text_width) // 2
            except:
                # 如果textbbox不可用，使用估算
                x_pos = (width - len(element['text']) * 12) // 2
        elif element['type'] in ['value', 'text']:
            x_pos = left_margin + 20  # 值内容缩进
        
        draw.text(
            (x_pos, element['y']),
            element['text'],
            font=element['font'],
            fill=element['color']
        )
    
    # 保存图片
    image.save(output_path, 'PNG', quality=95)
    print(f"图片已保存: {output_path}")
    return output_path

def batch_convert_direct(directory_path: str):
    """
    批量直接转换
    """
    converted_count = 0
    
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.endswith('.txt'):
                input_path = os.path.join(root, file)
                output_path = input_path.replace('.txt', '_图片.png')
                
                print(f"正在处理: {input_path}")
                
                try:
                    with open(input_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    create_image_from_text(content, output_path)
                    print(f"✓ 已生成: {output_path}")
                    converted_count += 1
                    
                except Exception as e:
                    print(f"✗ 处理失败: {e}")
    
    return converted_count

# 主程序
if __name__ == "__main__":
    # 测试字体
    font_path = get_chinese_fonts()
    if font_path:
        print(f"找到中文字体: {font_path}")
    else:
        print("警告: 未找到中文字体，可能出现乱码")
    
    
    # 批量处理
    directory = r"E:\zhenzhen_eng_coze\example\高三第二周作文_reduced_example"
    if os.path.exists(directory):
        converted = batch_convert_direct(directory)
        print(f"批量转换完成，共处理 {converted} 个文件")