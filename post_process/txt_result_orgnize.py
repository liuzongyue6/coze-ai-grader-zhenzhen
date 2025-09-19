"""
批改结果格式化
"""

import os
import json
import re
from datetime import datetime

def parse_txt_file_simple(file_path: str):
    """简化版解析函数"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取学生姓名
        student_name = ""
        if "文件夹名称:" in content:
            match = re.search(r"文件夹名称:\s*(.+)", content)
            if match:
                student_name = match.group(1).strip()
        
        # 查找包含评论的行
        eng_comment = None
        hand_writing_comment = None
        
        # 查找包含"eng_comment"的行
        eng_match = re.search(r'"eng_comment":"([^"]*(?:\\.[^"]*)*)"', content)
        if eng_match:
            eng_comment = eng_match.group(1)
            # 处理转义字符
            eng_comment = eng_comment.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
        
        # 查找包含"hand_writing_final"的行
        hand_match = re.search(r'"hand_writing_final":"([^"]*(?:\\.[^"]*)*)"', content)
        if hand_match:
            hand_writing_comment = hand_match.group(1)
            # 处理转义字符
            hand_writing_comment = hand_writing_comment.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
        
        return student_name, eng_comment, hand_writing_comment
        
    except Exception as e:
        print(f"解析文件失败 {file_path}: {e}")
        return "", None, None

def format_comment_for_word(comment: str) -> str:
    """格式化评论内容"""
    if not comment:
        return ""
    
    formatted = comment
    
    # 处理Markdown标题
    formatted = re.sub(r'### (.+)', r'\n【\1】\n', formatted)
    formatted = re.sub(r'## (.+)', r'\n【\1】\n', formatted)
    formatted = re.sub(r'# (.+)', r'\n【\1】\n', formatted)
    
    # 处理粗体
    formatted = re.sub(r'\*\*(.+?)\*\*', r'【\1】', formatted)
    
    # 处理列表
    formatted = re.sub(r'- ', '• ', formatted)
    formatted = re.sub(r'    - ', '  ○ ', formatted)
    
    # 清理多余空行
    formatted = re.sub(r'\n\s*\n\s*\n+', '\n\n', formatted)
    
    return formatted.strip()

def create_formatted_report(student_name: str, eng_comment: str, hand_writing: str) -> str:
    """创建格式化报告"""
    
    report = f"""英语作文批改报告
{'='*60}

学生姓名：{student_name}
批改时间：{datetime.now().strftime('%Y年%m月%d日')}

{'='*60}
详细评价
{'='*60}

{format_comment_for_word(eng_comment) if eng_comment else '无详细评价'}

{'='*60}
书写评价  
{'='*60}

{hand_writing if hand_writing else '无书写评价'}

{'='*60}
批改完成
{'='*60}"""
    
    return report

def main():
    """主函数"""
    print("=== 微信作文批改结果格式化器（修复版）===")
    
    # 配置参数 - 用户可以在这里修改
    wechat_folder = input("请输入微信文件夹路径 (或直接回车使用默认): ").strip()
    if not wechat_folder:
        wechat_folder = r"test"
    
    print(f"\n处理文件夹: {wechat_folder}")
    print("-" * 50)
    
    if not os.path.exists(wechat_folder):
        print(f"错误: 文件夹不存在 - {wechat_folder}")
        return
    
    # 询问用户确认
    confirm = input("\n确认开始处理吗？(输入 'y' 或 'yes' 继续): ")
    if confirm.lower() not in ['y', 'yes']:
        print("操作已取消")
        return
    
    print("-" * 50)
    
    success_count = 0
    
    # 遍历子文件夹
    for item in os.listdir(wechat_folder):
        item_path = os.path.join(wechat_folder, item)
        if os.path.isdir(item_path):
            # 查找txt文件
            for file in os.listdir(item_path):
                if file.endswith('.txt') and file.startswith('批改结果_'):
                    txt_path = os.path.join(item_path, file)
                    print(f"\n处理文件: {item}/{file}")
                    
                    # 解析文件
                    student_name, eng_comment, hand_writing = parse_txt_file_simple(txt_path)
                    
                    if not student_name:
                        student_name = item
                    
                    print(f"学生姓名: {student_name}")
                    print(f"英语评论: {'有' if eng_comment else '无'}")
                    print(f"书写评价: {'有' if hand_writing else '无'}")
                    
                    if eng_comment or hand_writing:
                        # 生成报告
                        report = create_formatted_report(student_name, eng_comment, hand_writing)
                        
                        # 保存文件到对应的输入文件夹里，文件名添加 _整理
                        output_file = f"{student_name}_作文批改报告_{datetime.now().strftime('%Y%m%d')}_整理.txt"
                        output_path = os.path.join(item_path, output_file)  # 保存到当前学生文件夹
                        
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(report)
                        
                        print(f"✅ 保存成功: {output_file}")
                        print(f"   保存路径: {output_path}")
                        success_count += 1
                    else:
                        print("⚠️ 未找到有效内容")
    
    print(f"\n=== 处理完成 ===")
    print(f"成功处理: {success_count} 个文件")

if __name__ == "__main__":
    main()