"""
TXT文件转精美图片生成器
自动将作文批改报告转换成制作精美的图片
"""

import os
import re
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import textwrap
from typing import List, Tuple, Optional

class TextToImageConverter:
    def __init__(self, 
                 image_width: int = 1200, 
                 image_height: int = 1600,
                 margin: int = 80,
                 line_spacing: int = 8):
        """
        初始化图片转换器
        
        Args:
            image_width: 图片宽度
            image_height: 图片高度  
            margin: 边距
            line_spacing: 行间距
        """
        self.image_width = image_width
        self.image_height = image_height
        self.margin = margin
        self.line_spacing = line_spacing
        self.content_width = image_width - 2 * margin
        
        # 颜色配置
        self.colors = {
            'background': '#FFFFFF',
            'title': '#2C3E50',
            'subtitle': '#34495E', 
            'section_header': '#E74C3C',
            'content': '#2C3E50',
            'highlight': '#3498DB',
            'separator': '#BDC3C7',
            'accent': '#F39C12'
        }
        
        # 字体配置 - 需要根据系统调整
        self.fonts = self._load_fonts()
    
    def _load_fonts(self) -> dict:
        """加载字体"""
        fonts = {}
        try:
            # Windows系统字体路径
            font_paths = {
                'title': 'C:/Windows/Fonts/simhei.ttf',      # 黑体
                'header': 'C:/Windows/Fonts/simhei.ttf',     # 黑体  
                'content': 'C:/Windows/Fonts/simsun.ttc',    # 宋体
                'bold': 'C:/Windows/Fonts/simhei.ttf'        # 黑体粗体
            }
            
            fonts = {
                'title': ImageFont.truetype(font_paths['title'], 32),
                'header': ImageFont.truetype(font_paths['header'], 24),
                'subheader': ImageFont.truetype(font_paths['header'], 20),
                'content': ImageFont.truetype(font_paths['content'], 16),
                'small': ImageFont.truetype(font_paths['content'], 14),
                'bold': ImageFont.truetype(font_paths['bold'], 18)
            }
        except:
            print("警告: 无法加载系统字体，使用默认字体")
            fonts = {
                'title': ImageFont.load_default(),
                'header': ImageFont.load_default(), 
                'subheader': ImageFont.load_default(),
                'content': ImageFont.load_default(),
                'small': ImageFont.load_default(),
                'bold': ImageFont.load_default()
            }
        
        return fonts
    
    def _wrap_text(self, text: str, font: ImageFont, max_width: int) -> List[str]:
        """文本自动换行"""
        if not text:
            return []
            
        lines = []
        for paragraph in text.split('\n'):
            if not paragraph.strip():
                lines.append('')
                continue
                
            # 计算每行能容纳的字符数
            avg_char_width = font.getbbox('测')[2]  # 使用中文字符测量
            chars_per_line = max_width // avg_char_width
            
            # 使用textwrap进行智能换行
            wrapped = textwrap.fill(paragraph, width=chars_per_line)
            lines.extend(wrapped.split('\n'))
        
        return lines
    
    def _draw_separator_line(self, draw: ImageDraw, y: int, width: Optional[int] = None) -> int:
        """绘制分隔线"""
        if width is None:
            width = self.content_width
        
        x1 = self.margin
        x2 = self.margin + width
        
        draw.line([(x1, y), (x2, y)], fill=self.colors['separator'], width=2)
        return y + 20
    
    def _draw_decorative_border(self, draw: ImageDraw):
        """绘制装饰性边框"""
        # 外边框
        draw.rectangle([10, 10, self.image_width-10, self.image_height-10], 
                      outline=self.colors['accent'], width=3)
        
        # 内边框
        draw.rectangle([25, 25, self.image_width-25, self.image_height-25], 
                      outline=self.colors['highlight'], width=1)
    
    def _parse_formatted_report(self, content: str) -> dict:
        """解析格式化的作文批改报告"""
        report_data = {
            'title': '英语作文批改报告',
            'student_name': '',
            'date': '',
            'sections': []
        }
        
        lines = content.split('\n')
        current_section = None
        section_content = []
        
        for line in lines:
            line = line.strip()
            
            # 提取学生姓名
            if line.startswith('学生姓名：'):
                report_data['student_name'] = line.replace('学生姓名：', '').strip()
            
            # 提取批改时间
            elif line.startswith('批改时间：'):
                report_data['date'] = line.replace('批改时间：', '').strip()
            
            # 检查是否是新的章节
            elif line.startswith('【') and line.endswith('】'):
                # 保存之前的章节
                if current_section and section_content:
                    report_data['sections'].append({
                        'title': current_section,
                        'content': '\n'.join(section_content)
                    })
                
                # 开始新章节
                current_section = line[1:-1]  # 去掉【】
                section_content = []
            
            # 跳过分隔线
            elif '=' in line and len(set(line)) <= 2:
                continue
                
            # 添加内容到当前章节
            elif line and current_section:
                section_content.append(line)
        
        # 添加最后一个章节
        if current_section and section_content:
            report_data['sections'].append({
                'title': current_section,
                'content': '\n'.join(section_content)
            })
        
        return report_data
    
    def _parse_raw_result(self, content: str) -> dict:
        """解析原始批改结果"""
        report_data = {
            'title': '作文批改结果',
            'student_name': '',
            'date': '',
            'sections': []
        }
        
        # 提取文件夹名称作为学生姓名
        folder_match = re.search(r'文件夹名称:\s*(.+)', content)
        if folder_match:
            report_data['student_name'] = folder_match.group(1).strip()
        
        # 提取处理时间
        time_match = re.search(r'处理时间:\s*(.+)', content)
        if time_match:
            report_data['date'] = time_match.group(1).strip()
        
        # 提取评论内容
        sections = []
        
        # 处理过程部分
        if '=== 处理过程 ===' in content:
            sections.append({
                'title': '处理信息',
                'content': '批改已完成，详细结果请参考具体评价内容。'
            })
        
        # 提取详细评价 (如果有)
        eng_match = re.search(r'"eng_comment":"([^"]*(?:\\.[^"]*)*)"', content)
        if eng_match:
            eng_comment = eng_match.group(1)
            eng_comment = eng_comment.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
            sections.append({
                'title': '详细评价',
                'content': eng_comment
            })
        
        # 提取书写评价
        hand_match = re.search(r'"hand_writing_final":"([^"]*(?:\\.[^"]*)*)"', content)
        if hand_match:
            hand_comment = hand_match.group(1)
            hand_comment = hand_comment.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
            sections.append({
                'title': '书写评价',
                'content': hand_comment
            })
        
        report_data['sections'] = sections
        return report_data
    
    def convert_txt_to_image(self, txt_file_path: str, output_path: str) -> bool:
        """将txt文件转换为图片"""
        try:
            # 读取文件内容
            with open(txt_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 判断文件类型并解析
            if '英语作文批改报告' in content and '详细评价' in content:
                report_data = self._parse_formatted_report(content)
            else:
                report_data = self._parse_raw_result(content)
            
            # 创建图片
            image = Image.new('RGB', (self.image_width, self.image_height), self.colors['background'])
            draw = ImageDraw.Draw(image)
            
            # 绘制装饰边框
            self._draw_decorative_border(draw)
            
            current_y = self.margin + 20
            
            # 绘制标题
            title_text = report_data['title']
            title_bbox = draw.textbbox((0, 0), title_text, font=self.fonts['title'])
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (self.image_width - title_width) // 2
            
            draw.text((title_x, current_y), title_text, 
                     fill=self.colors['title'], font=self.fonts['title'])
            current_y += title_bbox[3] - title_bbox[1] + 30
            
            # 绘制学生信息
            if report_data['student_name']:
                info_text = f"学生：{report_data['student_name']}"
                if report_data['date']:
                    info_text += f"    时间：{report_data['date']}"
                
                draw.text((self.margin, current_y), info_text, 
                         fill=self.colors['subtitle'], font=self.fonts['header'])
                current_y += 40
            
            # 绘制分隔线
            current_y = self._draw_separator_line(draw, current_y)
            
            # 绘制各个章节
            for section in report_data['sections']:
                # 检查是否需要分页（简单检查）
                if current_y > self.image_height - 200:
                    break
                
                # 章节标题
                section_title = f"【{section['title']}】"
                draw.text((self.margin, current_y), section_title, 
                         fill=self.colors['section_header'], font=self.fonts['header'])
                current_y += 35
                
                # 章节内容
                content_lines = self._wrap_text(section['content'], 
                                               self.fonts['content'], 
                                               self.content_width)
                
                for line in content_lines:
                    if current_y > self.image_height - 100:
                        break
                    
                    # 处理特殊格式
                    if line.startswith('•') or line.startswith('○'):
                        draw.text((self.margin + 20, current_y), line, 
                                 fill=self.colors['content'], font=self.fonts['content'])
                    elif line.startswith('###') or line.startswith('**'):
                        # 子标题
                        clean_line = re.sub(r'[#*]', '', line).strip()
                        draw.text((self.margin + 10, current_y), clean_line, 
                                 fill=self.colors['highlight'], font=self.fonts['bold'])
                    else:
                        draw.text((self.margin, current_y), line, 
                                 fill=self.colors['content'], font=self.fonts['content'])
                    
                    current_y += 25
                
                # 章节间距
                current_y += 20
            
            # 保存图片
            image.save(output_path, quality=95)
            return True
            
        except Exception as e:
            print(f"转换失败 {txt_file_path}: {e}")
            return False

def process_folder(folder_path: str):
    """处理文件夹中的所有txt文件，图片保存在对应的原始文件夹"""
    if not os.path.exists(folder_path):
        print(f"文件夹不存在: {folder_path}")
        return
    
    converter = TextToImageConverter()
    success_count = 0
    total_count = 0
    
    print(f"开始处理文件夹: {folder_path}")
    print("-" * 60)
    
    # 递归处理所有txt文件
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.txt'):
                txt_path = os.path.join(root, file)
                
                # 在同一文件夹生成图片文件
                img_name = file.replace('.txt', '.png')
                img_path = os.path.join(root, img_name)
                
                # 显示相对路径
                rel_path = os.path.relpath(txt_path, folder_path)
                print(f"处理: {rel_path}")
                
                total_count += 1
                if converter.convert_txt_to_image(txt_path, img_path):
                    print(f"  ✅ 成功生成: {img_name}")
                    success_count += 1
                else:
                    print(f"  ❌ 转换失败")
    
    print("-" * 60)
    print(f"处理完成！成功: {success_count}/{total_count}")

def main():
    """主函数"""
    print("=== TXT文件转精美图片生成器 ===")
    
    # 获取用户输入的源文件夹路径
    source_folder = input("请输入要处理的文件夹路径 (或直接回车使用默认): ").strip()
    if not source_folder:
        source_folder = r"test"
    
    print(f"\n配置信息:")
    print(f"处理文件夹: {source_folder}")
    print("-" * 50)
    
    # 检查源文件夹是否存在
    if not os.path.exists(source_folder):
        print(f"错误: 文件夹不存在 - {source_folder}")
        return
    
    # 统计txt文件数量
    txt_count = 0
    for root, dirs, files in os.walk(source_folder):
        for file in files:
            if file.endswith('.txt'):
                txt_count += 1
    
    if txt_count == 0:
        print("未找到TXT文件")
        return
    
    print(f"找到 {txt_count} 个TXT文件")
    
    # 询问用户确认
    confirm = input("\n确认开始转换吗？(输入 'y' 或 'yes' 继续): ")
    if confirm.lower() not in ['y', 'yes']:
        print("操作已取消")
        return
    
    # 开始处理
    process_folder(source_folder)

if __name__ == "__main__":
    main()
