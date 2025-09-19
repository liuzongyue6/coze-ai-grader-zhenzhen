"""
JSON提取和解析测试工具 - test_json_extraction.py

功能说明：
- 测试从API原始响应中提取JSON内容的算法
- 处理复杂的转义字符和嵌套结构
- 验证JSON解析的正确性和叶子节点提取
- 模拟实际API响应的解套过程

测试内容：
- 转义字符修复 (\' → ', \" → ", \\n → \n)
- JSON边界识别 (content=' ... ' node_title)
- 递归叶子节点查找和键值对提取
- Markdown格式输出模拟

适用场景：
- 验证API响应解析逻辑
- 调试JSON提取问题
- 测试新的解析算法
"""
# -*- coding: utf-8 -*-
import json

# 测试数据
test_raw_content = """content='{"comment_output":[{"grammer_comment":"有一处错误，\\'failed in a Math exam\\'表述有误，\\'fail\\'是及物动词，应去掉\\'in\\'，改为\\'failed a Math exam\\'。","sentence_comment":"亮点句1：\\'There is a crack in everything. That\\'s how the light gets in.\\'，用词精准，\\'crack\\'和\\'light\\'形象表达观点；句式简单有力；高度贴合主题。"}],"hand_writing":"书写较为工整，字迹清晰，整体卷面整洁，无明显多处修改和字迹凌乱情况。"}' node_title='End' node_seq_id='0' node_is_finish=True ext=None"""

def extract_json_from_raw_content(raw_content: str):
    """从raw_content字符串中提取JSON内容 - 最终修复版"""
    print(f"输入长度: {len(raw_content)}")
    print(f"前100字符: {raw_content[:100]}")
    
    # 查找 content=' 开始位置
    start_marker = "content='"
    start_pos = raw_content.find(start_marker)
    
    if start_pos == -1:
        print("未找到 content=' 标记")
        return None
    
    print(f"找到start_marker在位置: {start_pos}")
    
    # JSON开始位置
    json_start = start_pos + len(start_marker)
    
    # 查找结束位置 - 寻找 ' node_title
    end_marker = "' node_title"
    json_end = raw_content.find(end_marker, json_start)
    
    if json_end == -1:
        print("未找到 ' node_title 标记")
        return None
    
    print(f"找到end_marker在位置: {json_end}")
    
    # 提取JSON字符串
    json_str = raw_content[json_start:json_end]
    print(f"提取的JSON长度: {len(json_str)}")
    print(f"JSON前100字符: {json_str[:100]}")
    
    # 全面修复转义问题
    fixed_json_str = json_str
    
    # 1. 修复 \' -> '
    fixed_json_str = fixed_json_str.replace("\\'", "'")
    
    # 2. 修复 \\" -> "  
    fixed_json_str = fixed_json_str.replace('\\"', '"')
    
    # 3. 修复 \\n -> \n
    fixed_json_str = fixed_json_str.replace('\\\\n', '\\n')
    
    print(f"修复后JSON前100字符: {fixed_json_str[:100]}")
    
    try:
        parsed = json.loads(fixed_json_str)
        print(f"JSON解析成功！顶级键: {list(parsed.keys())}")
        return parsed
    except json.JSONDecodeError as e:
        print(f"JSON解析失败: {e}")
        print(f"错误位置: {e.pos}")
        if e.pos < len(fixed_json_str):
            error_context = fixed_json_str[max(0, e.pos-50):e.pos+50]
            print(f"错误周围文本: ...{error_context}...")
        return None

def find_all_leaf_key_values(obj):
    """递归查找所有叶子节点的键值对"""
    leaf_pairs = []
    
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, (dict, list)):
                # 继续递归
                leaf_pairs.extend(find_all_leaf_key_values(value))
            else:
                # 找到叶子节点
                leaf_pairs.append((key, value))
                print(f"找到叶子节点: {key}")
    
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, (dict, list)):
                # 递归处理数组元素
                leaf_pairs.extend(find_all_leaf_key_values(item))
    
    return leaf_pairs

# 测试
if __name__ == "__main__":
    print("=" * 60)
    print("测试JSON提取")
    print("=" * 60)
    
    result = extract_json_from_raw_content(test_raw_content)
    if result:
        print("\n成功解析的JSON:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        print("\n=" * 60)
        print("测试叶子节点查找")
        print("=" * 60)
        
        leaf_pairs = find_all_leaf_key_values(result)
        print(f"\n找到 {len(leaf_pairs)} 个叶子节点:")
        for key, value in leaf_pairs:
            print(f"  {key}: {str(value)[:50]}...")
            
        print("\n=" * 60)
        print("模拟最终输出格式")
        print("=" * 60)
        for key, value in leaf_pairs:
            print(f"**{key}**")
            print(f"*{str(value)}*")
            print()
            print()
    else:
        print("JSON提取失败!")