"""
这个文件专门用来批改翻译

翻译批改API响应JSON解析器 - api_response_json_to_txt_markdown_translation.py

功能说明：
- 解析Coze API返回的翻译批改JSON响应文件
- 提取嵌套的翻译评价内容（处理转义字符和多层JSON结构）
- 将每个翻译评价对象作为一组进行拆分
- 生成便于阅读的markdown格式txt文件
- 支持批量处理目录下的所有JSON文件

主要用途：
- 专门处理翻译批改的API响应
- 按翻译评价对象分组展示结果
- 生成结构化的markdown格式批改结果

输入：原始API响应JSON文件
输出：按评价对象分组的markdown格式txt文件
"""
import json
import os
import re
from typing import Any, Dict, List

def extract_json_from_raw_content(raw_content: str):
    """
    从raw_content字符串中提取JSON内容
    """
    # 查找 content=' 开始位置
    start_marker = "content='"
    start_pos = raw_content.find(start_marker)
    
    if start_pos == -1:
        return None
    
    # JSON开始位置
    json_start = start_pos + len(start_marker)
    
    # 查找结束位置 - 寻找 ' node_title
    end_marker = "' node_title"
    json_end = raw_content.find(end_marker, json_start)
    
    if json_end == -1:
        return None
    
    # 提取JSON字符串
    json_str = raw_content[json_start:json_end]
    
    # 全面修复转义问题
    fixed_json_str = json_str
    
    # 1. 修复 \' -> '
    fixed_json_str = fixed_json_str.replace("\\'", "'")
    
    # 2. 修复 \" -> "  
    fixed_json_str = fixed_json_str.replace('\\"', '"')
    
    # 3. 修复 \\n -> \n
    fixed_json_str = fixed_json_str.replace('\\\\n', '\\n')
    
    try:
        parsed = json.loads(fixed_json_str)
        return parsed
    except json.JSONDecodeError:
        return None

def extract_translation_evaluations(embedded_json: dict) -> List[Dict]:
    """
    从嵌套JSON中提取翻译评价对象列表
    """
    evaluations = []
    
    # 查找output_arr_obj数组
    if 'output_arr_obj' in embedded_json:
        output_arr = embedded_json['output_arr_obj']
        
        if isinstance(output_arr, list):
            for i, item in enumerate(output_arr, 1):
                if isinstance(item, dict):
                    evaluation = {
                        'index': i,
                        'comment': item.get('comment', ''),
                        'student_translation': item.get('std_input', ''),
                        'grammar_explanation': item.get('thought', '')
                    }
                    evaluations.append(evaluation)
    
    return evaluations

def format_translation_evaluation(evaluation: Dict, index: int) -> str:
    """
    格式化单个翻译评价对象为markdown
    """
    result = []
    
    # 分组标题
    result.append(f"## 翻译评价 {index}")
    result.append("")
    
    # 学生翻译
    result.append("### 📝 学生翻译")
    result.append(f"```")
    result.append(evaluation.get('student_translation', ''))
    result.append(f"```")
    result.append("")
    
    # 批改评价
    result.append("### 💬 批改评价")
    result.append(evaluation.get('comment', ''))
    result.append("")
    
    # 语法解释
    result.append("### 📚 语法解释")
    result.append(evaluation.get('grammar_explanation', ''))
    result.append("")
    
    # 分隔线
    result.append("---")
    result.append("")
    
    return "\n".join(result)

def parse_translation_json(json_file_path: str) -> str:
    """
    解析翻译批改JSON文件，按评价对象分组
    """
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    result = []
    result.append("# 翻译批改结果")
    result.append("")
    
    # 添加基本信息
    result.append("## 📋 基本信息")
    result.append(f"**学生**: {data.get('folder_name', 'N/A')}")
    result.append(f"**批改时间**: {data.get('timestamp', 'N/A')}")
    result.append(f"**作业总数**: {data.get('total_messages', 'N/A')}")
    result.append("")
    result.append("---")
    result.append("")
    
    # 处理raw_messages
    raw_messages = data.get('raw_messages', [])
    
    for message_idx, message in enumerate(raw_messages, 1):
        if isinstance(message, dict) and 'raw_content' in message:
            raw_content = message['raw_content']
            
            # 提取嵌套的JSON
            embedded_json = extract_json_from_raw_content(raw_content)
            
            if embedded_json:
                # 提取翻译评价对象
                evaluations = extract_translation_evaluations(embedded_json)
                
                if evaluations:
                    result.append(f"# 消息 {message_idx} - 翻译评价详情")
                    result.append("")
                    
                    # 为每个评价对象创建一个分组
                    for eval_obj in evaluations:
                        formatted_eval = format_translation_evaluation(eval_obj, eval_obj['index'])
                        result.append(formatted_eval)
                else:
                    result.append(f"# 消息 {message_idx} - 无翻译评价内容")
                    result.append("")
            else:
                result.append(f"# 消息 {message_idx} - JSON解析失败")
                result.append("")
                result.append("```")
                result.append(raw_content)
                result.append("```")
                result.append("")
    
    return "\n".join(result)

def parse_and_save_translation_json_files(directory_path: str):
    """
    批量解析翻译批改JSON文件
    """
    processed_count = 0
    
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.endswith('.json'):
                json_file_path = os.path.join(root, file)
                
                # 生成TXT文件名
                base_name = os.path.splitext(file)[0]
                txt_file_name = f"{base_name}_翻译批改解析.txt"
                txt_file_path = os.path.join(root, txt_file_name)
                
                print(f"正在处理: {json_file_path}")
                
                try:
                    # 解析JSON
                    parsed_content = parse_translation_json(json_file_path)
                    
                    # 保存结果
                    with open(txt_file_path, 'w', encoding='utf-8') as txt_file:
                        txt_file.write(parsed_content)
                    
                    print(f"  ✓ 已生成: {txt_file_path}")
                    processed_count += 1
                    
                except Exception as e:
                    print(f"  ✗ 处理失败: {e}")
    
    return processed_count

# 主程序
if __name__ == "__main__":
    
    # 批量处理
    directory = r"E:\zhenzhen_eng_coze\example\高一_10_reduced"
    
    if os.path.exists(directory):
        print(f"\n批量处理目录: {directory}")
        processed = parse_and_save_translation_json_files(directory)
        print(f"处理完成！共处理了 {processed} 个JSON文件")
    else:
        print(f"目录不存在: {directory}")
