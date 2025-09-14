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
                 line_spacing: int = 8,
                 supported_fields: list = None):
        """
        初始化图片转换器
        
        Args:
            image_width: 图片宽度
            image_height: 图片高度  
            margin: 边距
            line_spacing: 行间距
            supported_fields: 支持的字段列表
        """
        self.image_width = image_width
        self.image_height = image_height
        self.margin = margin
        self.line_spacing = line_spacing
        self.content_width = image_width - 2 * margin
        
        # 支持的字段配置
        self.supported_fields = supported_fields or ['学生翻译', '思路', '批改']
        
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
    
    def _parse_translation_format(self, content: str) -> dict:
        """解析翻译批改格式的报告"""
        report_data = {
            'title': '英语翻译批改报告',
            'student_name': '',
            'date': '',
            'sections': []
        }
        
        lines = content.split('\n')
        
        # 提取头部信息
        for line in lines:
            line = line.strip()
            if line.startswith('处理时间:'):
                report_data['date'] = line.replace('处理时间:', '').strip()
            elif line.startswith('学生姓名:'):
                report_data['student_name'] = line.replace('学生姓名:', '').strip()
        
        # 提取题目总数
        summary_section = None
        for line in lines:
            if line.strip().startswith('一共读到'):
                summary_section = {
                    'title': '批改概要',
                    'content': line.strip()
                }
                break
        
        if summary_section:
            report_data['sections'].append(summary_section)
        
        # 解析题目部分
        current_question = None
        current_field = None
        field_content = []
        
        for line in lines:
            line = line.strip()
            
            # 检测题目开始
            if line.startswith('【题 ') and line.endswith('】'):
                # 保存之前的字段
                if current_question and current_field and field_content:
                    if current_field not in current_question:
                        current_question[current_field] = []
                    current_question[current_field].extend(field_content)
                
                # 保存之前的题目
                if current_question:
                    question_content = self._format_question_content(current_question)
                    report_data['sections'].append({
                        'title': current_question['title'],
                        'content': question_content
                    })
                
                # 开始新题目
                current_question = {'title': line[1:-1]}  # 去掉【】
                current_field = None
                field_content = []
            
            # 跳过分隔线
            elif '=' in line and len(set(line)) <= 2:
                continue
            
            # 检测字段
            elif line.endswith(':') and line.rstrip(':') in self.supported_fields:
                # 保存之前的字段
                if current_question and current_field and field_content:
                    if current_field not in current_question:
                        current_question[current_field] = []
                    current_question[current_field].extend(field_content)
                
                # 开始新字段
                current_field = line.rstrip(':')
                field_content = []
            
            # 添加内容到当前字段
            elif line and current_question and current_field:
                field_content.append(line)
        
        # 处理最后一个字段和题目
        if current_question and current_field and field_content:
            if current_field not in current_question:
                current_question[current_field] = []
            current_question[current_field].extend(field_content)
        
        if current_question:
            question_content = self._format_question_content(current_question)
            report_data['sections'].append({
                'title': current_question['title'],
                'content': question_content
            })
        
        return report_data
    
    def _format_question_content(self, question: dict) -> str:
        """格式化题目内容"""
        content_parts = []
        
        # 按顺序显示字段
        field_order = self.supported_fields
        
        for field in field_order:
            if field in question and question[field]:
                content_parts.append(f"**{field}:**")
                content_parts.extend(question[field])
                content_parts.append("")  # 空行分隔
        
        return '\n'.join(content_parts).strip()

    def convert_txt_to_image(self, txt_file_path: str, output_path: str) -> bool:
        """将txt文件转换为图片"""
        try:
            print(f"  调试: 开始处理文件 {txt_file_path}")
            print(f"  调试: 支持的字段 {self.supported_fields}")
            
            # 读取文件内容
            with open(txt_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"  调试: 文件内容长度 {len(content)}")
            print(f"  调试: 包含批改结果标记: {'=== 批改结果 ===' in content}")
            print(f"  调试: 包含题目标记: {'【题 ' in content}")
            
            # 判断文件类型并解析
            if '=== 批改结果 ===' in content and '【题 ' in content:
                # 新的翻译批改格式
                print("  调试: 使用翻译批改格式解析")
                report_data = self._parse_translation_format(content)
            elif '英语作文批改报告' in content and '详细评价' in content:
                # 原有的作文批改格式
                print("  调试: 使用作文批改格式解析")
                report_data = self._parse_formatted_report(content)
            else:
                # 原始结果格式
                print("  调试: 使用原始结果格式解析")
                report_data = self._parse_raw_result(content)
            
            print(f"  调试: 解析得到 {len(report_data['sections'])} 个章节")
            for i, section in enumerate(report_data['sections']):
                print(f"    章节 {i+1}: {section['title']}")
            
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
                    if line.startswith('**') and line.endswith(':**'):
                        # 字段标题（如 **学生翻译:** ）
                        clean_line = line[2:-3] + ':'  # 去掉 ** 保留冒号
                        draw.text((self.margin, current_y), clean_line, 
                                 fill=self.colors['highlight'], font=self.fonts['bold'])
                    elif line.startswith('•') or line.startswith('○'):
                        draw.text((self.margin + 20, current_y), line, 
                                 fill=self.colors['content'], font=self.fonts['content'])
                    elif line.startswith('###') or line.startswith('**'):
                        # 其他子标题
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

def process_folder(folder_path: str, supported_fields: list = None):
    """处理文件夹中的所有txt文件，图片保存在对应的原始文件夹"""
    if not os.path.exists(folder_path):
        print(f"文件夹不存在: {folder_path}")
        return
    
    converter = TextToImageConverter(supported_fields=supported_fields)
    success_count = 0
    total_count = 0
    
    print(f"开始处理文件夹: {folder_path}")
    print(f"支持的字段: {converter.supported_fields}")
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
    
    # 字段配置 - 用户可以修改这里
    supported_fields = ['学生翻译', '错误分析', '思路', '批改']  # 可以添加 '错误分析' 等其他字段
    
    # 获取用户输入的源文件夹路径

    source_folder = r"E:\真真英语\作文\test\Translation_Unit"
    
    print(f"\n配置信息:")
    print(f"处理文件夹: {source_folder}")
    print(f"支持字段: {supported_fields}")
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
    
    print(f"找到 {txt_count} 个TXT文件，开始转换...")
    
    # 开始处理
    process_folder(source_folder, supported_fields)

if __name__ == "__main__":
    main()