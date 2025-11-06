"""
通用的api处理器
后处理缓存文件 - 解析原始API响应并生成格式化的批改结果
支持单输出和多输出格式配置
"""

import os
import json
import glob
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

def extract_json_from_content(content_str: str, content_pattern: str) -> Optional[Dict]:
    """从content字符串中提取JSON数据"""
    try:
        content_match = re.search(content_pattern, content_str, re.DOTALL)
        
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

def is_multi_output_config(config: Dict[str, Any]) -> bool:
    """检测是否为多输出配置"""
    return "output_types" in config and "global_config" in config

def format_single_section(data_array: List[Dict], section_config: Dict[str, Any]) -> str:
    """格式化单个数据段"""
    formatted_text = ""
    
    # 标题和摘要
    title = section_config["title"]
    summary_template = section_config["summary_template"]
    formatted_text += f"{title}\n\n"
    formatted_text += f"{summary_template.format(count=len(data_array))}\n\n"
    
    # 处理每个项目
    item_title_template = section_config["item_title_template"]
    separator = section_config["separator"]
    field_mappings = section_config["field_mappings"]
    field_order = section_config["field_order"]
    
    for idx, item in enumerate(data_array, 1):
        formatted_text += f"{item_title_template.format(index=idx)}\n"
        formatted_text += f"{separator}\n"
        
        # 按配置的顺序显示字段
        for field_name in field_order:
            if field_name in item and field_name in field_mappings:
                display_name = field_mappings[field_name]
                formatted_text += f"{display_name}:\n{item[field_name]}\n\n"
        
        formatted_text += f"{separator}\n\n"
    
    return formatted_text

def format_results_unified(parsed_data: Dict, config: Dict[str, Any]) -> str:
    """统一格式化结果 - 支持单输出和多输出配置"""
    all_formatted_text = ""
    
    if is_multi_output_config(config):
        # 多输出配置
        output_types = config["output_types"]
        sections_found = 0
        
        for output_type, output_config in output_types.items():
            if not output_config["enabled"]:
                continue
                
            if output_type not in parsed_data:
                print(f"⚠️ 数据中未找到字段 '{output_type}'，跳过")
                continue
            
            data_array = parsed_data[output_type]
            if not data_array:
                print(f"⚠️ 字段 '{output_type}' 为空，跳过")
                continue
            
            if sections_found > 0:
                all_formatted_text += "\n" + "="*80 + "\n\n"
            
            formatted_section = format_single_section(data_array, output_config)
            all_formatted_text += formatted_section
            sections_found += 1
            
    else:
        # 单输出配置
        data_field = config["data_field"]
        
        if data_field not in parsed_data:
            return f"未识别的数据格式，找不到字段 '{data_field}': {json.dumps(parsed_data, ensure_ascii=False, indent=2)}"
        
        data_array = parsed_data[data_field]
        all_formatted_text = format_single_section(data_array, config)
    
    return all_formatted_text

def get_file_header_template(config: Dict[str, Any]) -> str:
    """获取文件头模板"""
    if is_multi_output_config(config):
        # 多输出配置 - 使用第一个启用的输出类型的模板
        for output_type, output_config in config["output_types"].items():
            if output_config["enabled"]:
                return output_config["file_header_template"]
        return "=== 处理结果 ===\n\n处理时间: {process_time}\n学生姓名: {folder_name}\n原始缓存: {cache_file}\n消息数量: {message_count}\n\n"
    else:
        # 单输出配置
        return config["file_header_template"]

def get_output_prefix(config: Dict[str, Any]) -> str:
    """获取输出文件前缀"""
    if is_multi_output_config(config):
        return config["global_config"]["output_prefix"]
    else:
        return config["output_prefix"]

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
        output_prefix = get_output_prefix(config)
        output_file = os.path.join(cache_dir, f"{folder_name}_{output_prefix}_{timestamp}.txt")
        
        all_formatted_results = []
        
        # 处理每个消息
        for msg_data in messages:
            raw_content = msg_data.get("raw_content", "")
            
            # 提取并解析JSON
            content_pattern = config["content_pattern"]
            parsed_data = extract_json_from_content(raw_content, content_pattern)
            if parsed_data:
                formatted_result = format_results_unified(parsed_data, config)
                all_formatted_results.append(formatted_result)
        
        # 写入格式化结果到单个文件
        with open(output_file, 'w', encoding='utf-8') as f:
            # 使用配置的文件头模板
            header_template = get_file_header_template(config)
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
    cache_pattern = os.path.join(directory, "**/*_response_cache_*.json")
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

def load_config() -> Dict[str, Any]:
    """加载配置文件 - 自动检测配置类型"""
    config_attempts = [
        ("config.translation_rec_format_config", "MULTI_OUTPUT_FORMAT_CONFIG", "多输出格式配置"),
        ("config.translation_format_config", "DEFAULT_FORMAT_CONFIG", "单输出格式配置")
    ]
    
    for module_name, config_name, desc in config_attempts:
        try:
            module = __import__(module_name, fromlist=[config_name])
            config = getattr(module, config_name)
            print(f"✅ 已加载配置文件: {module_name}.py ({desc})")
            return config
        except (ImportError, AttributeError) as e:
            print(f"⚠️ 尝试加载 {module_name} 失败: {str(e)}")
            continue
    
    raise ImportError("无法加载任何配置文件。请确保存在以下配置文件之一：\n"
                     "- config/translation_rec_format_config.py (多输出)\n"
                     "- config/translation_format_config.py (单输出)")

def main():
    """主函数"""
    print("=== 缓存文件后处理器 ===\n")
    
    # 加载格式化配置
    try:
        config = load_config()
    except ImportError as e:
        print(f"❌ 配置文件加载失败: {str(e)}")
        return
    
    # 显示配置信息
    if is_multi_output_config(config):
        enabled_types = [k for k, v in config['output_types'].items() if v['enabled']]
        print(f"📋 配置类型: 多输出格式")
        print(f"📋 启用的输出类型: {enabled_types}")
        print(f"📋 输出前缀: {config['global_config']['output_prefix']}\n")
    else:
        print(f"📋 配置类型: 单输出格式")
        print(f"📋 数据字段: {config['data_field']}")
        print(f"📋 输出前缀: {config['output_prefix']}\n")
    
    # 配置目录
    test_directory = r"E:\zhenzhen_eng_coze\example\高三第3周作文_补_reduced"
    
    print(f"📂 测试目录: {test_directory}")
    
    if not os.path.exists(test_directory):
        print(f"❌ 目录不存在: {test_directory}")
        return
    
    # 处理所有缓存文件
    scan_and_process_cache_files(test_directory, config)

if __name__ == "__main__":
    main()
