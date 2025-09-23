"""
API响应JSON解析器 - api_response_to_markdown.py

功能说明：
- 解析Coze API返回的原始JSON响应文件
- 提取嵌套的批改内容（处理转义字符和多层JSON结构）
- 将提取的内容转换为markdown格式的txt文件
- 支持批量处理目录下的所有JSON文件

主要用途：
- 处理作文/翻译批改的API响应
- 解套复杂的JSON嵌套结构
- 生成便于阅读的markdown格式批改结果

输入：原始API响应JSON文件
输出：结构化的markdown格式txt文件
"""
import json
import os
import re
from typing import Any, Dict, List, Tuple

# 字段映射字典 - 将英文字段名映射为中文标题
FIELD_NAME_MAPPING = {
    "folder_name": "学生姓名",
    "timestamp": "批改时间", 
    "total_messages": "批改份数",
    "grade": "总分",
    "grade_comment": "点评",
    "message_index": "序号",
    "grammer_comment": "语法",
    "sentence_comment": "句子",
    "sentence_highlight": "亮眼句子",
    "sentence_improve": "词句润色",
    "structure_comment": "语法结构",
    "word_comment": "用词",
    "hand_writing": "手写",
    "pnt_view": "你用到的观点",
    "rewrite_output": "根据你的观点，文章重构"
}

# 字段输出顺序 - 按照这个顺序输出字段
FIELD_OUTPUT_ORDER = [
    "folder_name",       # 学生姓名
    "timestamp",         # 批改时间
    "total_messages",    # 批改份数
    "message_index",     # 序号
    "hand_writing",      # 手写
    "word_comment",      # 用词
    "grammer_comment",   # 语法
    "structure_comment", # 语法结构
    "rewrite_output",    # 根据你的观点，文章重构
    "timestamp"          # 批改时间（最后）
]

def get_display_name(field_name: str) -> str:
    """
    获取字段的显示名称，如果有映射则使用中文，否则使用原字段名
    """
    return FIELD_NAME_MAPPING.get(field_name, field_name)

def extract_json_from_raw_content(raw_content: str):
    """
    从raw_content字符串中提取JSON内容 - 最终修复版
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
    
    # 2. 修复 \\" -> "  
    fixed_json_str = fixed_json_str.replace('\\"', '"')
    
    # 3. 修复 \\n -> \n
    fixed_json_str = fixed_json_str.replace('\\\\n', '\\n')
    
    try:
        parsed = json.loads(fixed_json_str)
        return parsed
    except json.JSONDecodeError:
        return None

def find_all_leaf_key_values(obj):
    """
    递归查找所有叶子节点的键值对
    """
    leaf_pairs = []
    
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, (dict, list)):
                # 继续递归
                leaf_pairs.extend(find_all_leaf_key_values(value))
            else:
                # 找到叶子节点
                leaf_pairs.append((key, value))
    
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, (dict, list)):
                # 递归处理数组元素
                leaf_pairs.extend(find_all_leaf_key_values(item))
    
    return leaf_pairs

def output_fields_in_order(leaf_pairs: List[Tuple[str, Any]], result: List[str]):
    """
    按照指定顺序输出字段
    """
    # 将叶子节点转换为字典，便于查找
    fields_dict = dict(leaf_pairs)
    
    # 按照 FIELD_OUTPUT_ORDER 的顺序输出已定义的字段
    for field_name in FIELD_OUTPUT_ORDER:
        if field_name in fields_dict:
            display_name = get_display_name(field_name)
            result.append(f"**{display_name}**")
            result.append(f"*{str(fields_dict[field_name])}*")
            result.append("")  # 空行
            result.append("")  # 第二个空行
            # 从字典中移除已处理的字段
            del fields_dict[field_name]
    
    # 输出剩余的未在顺序列表中定义的字段
    for field_name, field_value in fields_dict.items():
        display_name = get_display_name(field_name)
        result.append(f"**{display_name}**")
        result.append(f"*{str(field_value)}*")
        result.append("")  # 空行
        result.append("")  # 第二个空行

def parse_json_by_position(json_file_path: str):
    """
    解析JSON文件，提取所有最底层的键值对
    """
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    result = []
    result.append("=== 批改结果 ===")
    
    # 处理顶级字段
    for key, value in data.items():
        if key == "raw_messages":
            # 特殊处理 raw_messages 数组
            if isinstance(value, list):
                for i, message in enumerate(value):
                  
                    
                    if isinstance(message, dict):
                        for msg_key, msg_value in message.items():
                            
                            if msg_key == "raw_content":
                                # 特殊处理 raw_content - 解套JSON
                                embedded_json = extract_json_from_raw_content(msg_value)
                                
                                if embedded_json:
                                    # 找到所有叶子节点并按顺序输出
                                    leaf_pairs = find_all_leaf_key_values(embedded_json)
                                    output_fields_in_order(leaf_pairs, result)
                                else:
                                    # JSON解析失败，作为普通字符串处理
                                    display_name = get_display_name(msg_key)
                                    result.append(f"**{display_name}**")
                                    result.append(f"*{str(msg_value)}*")
                                    result.append("")
                                    result.append("")
                            
                            else:
                                # 其他字段直接输出
                                display_name = get_display_name(msg_key)
                                result.append(f"**{display_name}**")
                                result.append(f"*{str(msg_value)}*")
                                result.append("")
                                result.append("")
                    
                    result.append("")  # 消息间分隔
        else:
            # 其他顶级字段直接输出
            display_name = get_display_name(key)
            result.append(f"**{display_name}**")
            result.append(f"*{str(value)}*")
            result.append("")
            result.append("")
    
    return "\n".join(result)

def parse_and_save_json_files(directory_path: str):
    """
    批量解析JSON文件
    """
    processed_count = 0
    
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.endswith('.json'):
                json_file_path = os.path.join(root, file)
                
                # 生成TXT文件名
                base_name = os.path.splitext(file)[0]
                txt_file_name = f"{base_name}_解析.txt"
                txt_file_path = os.path.join(root, txt_file_name)
                
                print(f"正在处理: {json_file_path}")
                
                try:
                    # 解析JSON
                    parsed_content = parse_json_by_position(json_file_path)
                    
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
    directory = r"E:\zhenzhen_eng_coze\example\高三第三周作文_reduced_example"
    
    if os.path.exists(directory):
        print(f"\n批量处理目录: {directory}")
        processed = parse_and_save_json_files(directory)
        print(f"处理完成！共处理了 {processed} 个JSON文件")
