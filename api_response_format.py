"""
后处理缓存文件 - 解析原始API响应并生成格式化的批改结果
"""

import os
import json
import glob
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# 默认格式化配置
DEFAULT_FORMAT_CONFIG = {
    # 数据提取配置
    "data_field": "output_arr_obj",  # 主要数据字段名
    "content_pattern": r"content='(.+?)'(?:\s+node_title=|$)",  # content提取正则
    
    # 格式化文本配置
    "title": "=== 批改结果 ===",
    "summary_template": "一共读到 {count} 题",
    "item_title_template": "【题 {index}】",
    "separator": "=" * 50,
    
    # 字段显示配置
    "field_mappings": {
        "std_input": "学生翻译",
        "thought": "思路", 
        "comment": "批改"
    },
    "field_order": ["std_input", "thought", "comment"],  # 字段显示顺序
    
    # 输出文件配置
    "output_prefix": "格式化批改结果",
    "file_header_template": """=== 批改结果 ===

处理时间: {process_time}
学生姓名: {folder_name}
原始缓存: {cache_file}
消息数量: {message_count}

"""
}

def load_format_config(config_file: Optional[str] = None) -> Dict[str, Any]:
    """加载格式化配置"""
    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
            # 合并用户配置和默认配置
            config = DEFAULT_FORMAT_CONFIG.copy()
            config.update(user_config)
            return config
        except Exception as e:
            print(f"⚠️ 配置文件加载失败，使用默认配置: {str(e)}")
    
    return DEFAULT_FORMAT_CONFIG.copy()

def extract_json_from_content(content_str: str, config: Dict[str, Any]) -> Optional[Dict]:
    """从content字符串中提取JSON数据"""
    try:
        # 使用配置中的正则模式
        pattern = config.get("content_pattern", DEFAULT_FORMAT_CONFIG["content_pattern"])
        content_match = re.search(pattern, content_str, re.DOTALL)
        
        if content_match:
            json_str = content_match.group(1)
            # 处理转义字符
            json_str = json_str.replace("\\'", "'")
            return json.loads(json_str)
        else:
            # 如果没有找到content=格式，尝试直接解析
            return json.loads(content_str)
    except (json.JSONDecodeError, AttributeError) as e:
        print(f"JSON解析失败: {str(e)}")
        print(f"原始内容: {content_str[:200]}...")
        return None

def format_results(parsed_data: Dict, config: Dict[str, Any]) -> str:
    """格式化批改结果"""
    data_field = config.get("data_field", "output_arr_obj")
    
    if data_field not in parsed_data:
        return f"未识别的数据格式，找不到字段 '{data_field}': {json.dumps(parsed_data, ensure_ascii=False, indent=2)}"
    
    output_array = parsed_data[data_field]
    formatted_text = ""
    
    # 标题和摘要
    title = config.get("title", "=== 批改结果 ===")
    summary_template = config.get("summary_template", "一共读到 {count} 题")
    formatted_text += f"{title}\n\n"
    formatted_text += f"{summary_template.format(count=len(output_array))}\n\n"
    
    # 处理每个项目
    item_title_template = config.get("item_title_template", "【题 {index}】")
    separator = config.get("separator", "=" * 50)
    field_mappings = config.get("field_mappings", {})
    field_order = config.get("field_order", list(field_mappings.keys()))
    
    for idx, item in enumerate(output_array, 1):
        formatted_text += f"{item_title_template.format(index=idx)}\n"
        formatted_text += f"{separator}\n"
        
        # 按配置的顺序显示字段
        for field_name in field_order:
            if field_name in item and field_name in field_mappings:
                display_name = field_mappings[field_name]
                formatted_text += f"{display_name}:\n{item[field_name]}\n\n"
        
        formatted_text += f"{separator}\n\n"
    
    return formatted_text

def process_cache_file(cache_file_path: str, config: Dict[str, Any]) -> bool:
    """处理单个缓存文件"""
    try:
        print(f"📁 处理缓存文件: {os.path.basename(cache_file_path)}")
        
        # 读取缓存文件
        with open(cache_file_path, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        folder_name = cache_data.get("folder_name", "Unknown")
        timestamp = cache_data.get("timestamp", datetime.now().strftime('%Y%m%d_%H%M%S'))
        messages = cache_data.get("raw_messages", [])
        
        if not messages:
            print(f"   ❌ 缓存文件中没有消息数据")
            return False
        
        # 生成输出文件路径
        cache_dir = os.path.dirname(cache_file_path)
        output_prefix = config.get("output_prefix", "格式化批改结果")
        output_file = os.path.join(cache_dir, f"{output_prefix}_{folder_name}_{timestamp}.txt")
        
        all_formatted_results = []
        
        # 处理每个消息
        for msg_data in messages:
            raw_content = msg_data.get("raw_content", "")
            
            # 提取并解析JSON
            parsed_data = extract_json_from_content(raw_content, config)
            if parsed_data:
                formatted_result = format_results(parsed_data, config)
                all_formatted_results.append(formatted_result)
        
        # 写入格式化结果
        with open(output_file, 'w', encoding='utf-8') as f:
            # 使用配置的文件头模板
            header_template = config.get("file_header_template", DEFAULT_FORMAT_CONFIG["file_header_template"])
            header = header_template.format(
                process_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                folder_name=folder_name,
                cache_file=os.path.basename(cache_file_path),
                message_count=len(messages)
            )
            f.write(header)
            
            for i, formatted_result in enumerate(all_formatted_results, 1):
                if len(all_formatted_results) > 1:
                    f.write(f"=== 消息 {i} 处理结果 ===\n\n")
                f.write(formatted_result)
                f.write("\n")
        
        print(f"   ✅ 处理完成! 输出文件: {os.path.basename(output_file)}")
        return True
        
    except Exception as e:
        print(f"   ❌ 处理失败: {str(e)}")
        return False

def scan_and_process_cache_files(directory: str, config: Dict[str, Any]):
    """扫描目录中的所有缓存文件并处理"""
    print(f"🔍 扫描目录: {directory}")
    
    # 查找所有缓存文件
    cache_pattern = os.path.join(directory, "**/raw_response_cache_*.json")
    cache_files = glob.glob(cache_pattern, recursive=True)
    
    if not cache_files:
        print("❌ 没有找到缓存文件")
        return
    
    print(f"📋 找到 {len(cache_files)} 个缓存文件")
    
    success_count = 0
    for cache_file in cache_files:
        if process_cache_file(cache_file, config):
            success_count += 1
    
    print(f"\n🎉 处理完成! 成功: {success_count}/{len(cache_files)}")

def create_example_config(config_path: str):
    """创建示例配置文件"""
    example_config = {
        "data_field": "output_arr_obj",
        "content_pattern": r"content='(.+?)'(?:\s+node_title=|$)",
        "title": "=== 批改结果 ===",
        "summary_template": "一共读到 {count} 题",
        "item_title_template": "【题 {index}】",
        "separator": "=" * 50,
        "field_mappings": {
            "std_input": "学生翻译",
            "thought": "思路",
            "comment": "批改"
        },
        "field_order": ["std_input", "thought", "comment"],
        "output_prefix": "格式化批改结果"
    }
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(example_config, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已创建示例配置文件: {config_path}")

def main():
    """主函数"""
    print("=== 缓存文件后处理器 ===\n")
    
    # 配置文件路径
    config_file = "post_process_config.json"
    
    # 如果配置文件不存在，创建示例配置
    if not os.path.exists(config_file):
        print(f"🔧 配置文件不存在，创建示例配置: {config_file}")
        create_example_config(config_file)
        print("📝 请根据需要修改配置文件，然后重新运行程序\n")
    
    # 加载配置
    config = load_format_config(config_file)
    print(f"📋 已加载配置，数据字段: {config['data_field']}")
    print(f"📋 字段映射: {config['field_mappings']}")
    print(f"📋 字段顺序: {config['field_order']}\n")
    
    # 配置目录
    test_directory = r"E:\真真英语\作文\test"
    
    print(f"📂 测试目录: {test_directory}")
    
    if not os.path.exists(test_directory):
        print(f"❌ 目录不存在: {test_directory}")
        return
    
    # 处理所有缓存文件
    scan_and_process_cache_files(test_directory, config)

if __name__ == "__main__":
    main()
