"""
后处理缓存文件 - 解析原始API响应生成的json
根据键值对的关系生成对应txt内容（markdown格式）
难度：解决层层嵌套的markdown
参考test里的文件如何解套多层嵌套json
"""
import json
import os
import re
from typing import Any, Dict, List

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
                    result.append(f"\n消息 {i+1}:")
                    
                    if isinstance(message, dict):
                        for msg_key, msg_value in message.items():
                            
                            if msg_key == "raw_content":
                                # 特殊处理 raw_content - 解套JSON
                                embedded_json = extract_json_from_raw_content(msg_value)
                                
                                if embedded_json:
                                    # 找到所有叶子节点并输出
                                    leaf_pairs = find_all_leaf_key_values(embedded_json)
                                    
                                    for leaf_key, leaf_value in leaf_pairs:
                                        result.append(f"**{leaf_key}**")
                                        result.append(f"*{str(leaf_value)}*")
                                        result.append("")  # 空行
                                        result.append("")  # 第二个空行
                                else:
                                    # JSON解析失败，作为普通字符串处理
                                    result.append(f"**{msg_key}**")
                                    result.append(f"*{str(msg_value)}*")
                                    result.append("")
                                    result.append("")
                            
                            else:
                                # 其他字段直接输出
                                result.append(f"**{msg_key}**")
                                result.append(f"*{str(msg_value)}*")
                                result.append("")
                                result.append("")
                    
                    result.append("")  # 消息间分隔
        else:
            # 其他顶级字段直接输出
            result.append(f"**{key}**")
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
    directory = r"E:\zhenzhen_eng_coze\example\高三第二周作文_reduced_example"
    
    if os.path.exists(directory):
        print(f"\n批量处理目录: {directory}")
        processed = parse_and_save_json_files(directory)
        print(f"处理完成！共处理了 {processed} 个JSON文件")
