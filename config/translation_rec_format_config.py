"""
多输出格式化配置文件 - 支持处理多种数据类型
"""

# 多输出格式化配置
MULTI_OUTPUT_FORMAT_CONFIG = {
    # 数据提取配置
    "content_pattern": r"content='(.+?)'(?:\s+node_title=|$)",  # content提取正则
    
    # 输出类型配置
    "output_types": {
        "output_arr_obj": {
            "enabled": True,
            "title": "=== 批改 ===",
            "summary_template": "一共 {count} 题",
            "item_title_template": "【题 {index}】",
            "separator": "=" * 50,
            "field_mappings": {
                "std_input": "学生翻译",
                "thought": "思路", 
                "comment": "批改",
                "std_mistake": "错误分析"
            },
            "field_order": ["std_input", "std_mistake", "thought", "comment"],
            "output_suffix": "批改结果",
            "file_header_template": """=== 批改结果 ===

处理时间: {process_time}
学生姓名: {folder_name}
原始缓存: {cache_file}
消息数量: {message_count}

"""
        },
        
        "usage_output": {
            "enabled": True,
            "title": "=== 快速总结 ===",
            "summary_template": "一共 {count} 个句子",
            "item_title_template": "【句子 {index}】",
            "separator": "-" * 40,
            "field_mappings": {
                "chinese_txt": "中文原句",
                "bracket_en_mistake": "错误表达",
                "flag": "判断结果"
            },
            "field_order": ["chinese_txt", "bracket_en_mistake", "flag"],
            "output_suffix": "quick_summary",
            "file_header_template": """=== 快速总结 ===

处理时间: {process_time}
学生姓名: {folder_name}
原始缓存: {cache_file}
消息数量: {message_count}

"""
        }
    },
    
    # 全局配置
    "global_config": {
        "output_prefix": "评论",
        "timestamp_format": "%Y%m%d_%H%M%S"
    }
}

def get_multi_output_config():
    """获取多输出格式化配置"""
    return MULTI_OUTPUT_FORMAT_CONFIG.copy()

