"""
API响应格式化配置文件
"""

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

def get_format_config():
    """获取格式化配置"""
    return DEFAULT_FORMAT_CONFIG.copy()