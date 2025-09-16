#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扫描所有子文件夹中的JSON文件，提取翻译数据
"""

import os
import json
import re
import csv
from datetime import datetime
from pathlib import Path
import sys

# 添加config目录到Python路径
current_dir = Path(__file__).parent
config_dir = current_dir.parent / "config"
sys.path.append(str(config_dir))

from translation_rec_format_config import get_multi_output_config

class SimpleErrorScanner:
    def __init__(self, base_dir):
        """
        初始化扫描器
        
        Args:
            base_dir (str): 基础目录路径
        """
        self.base_dir = Path(base_dir)
        self.config = get_multi_output_config()
        self.content_pattern = self.config["content_pattern"]
        self.error_data = []
        self.total_false_count = 0
        
        # 获取usage_output的字段映射
        self.usage_output_config = self.config["output_types"]["usage_output"]
        self.field_mappings = self.usage_output_config["field_mappings"]
        
    def extract_content_from_raw(self, raw_content):
        """从raw_content中提取JSON内容"""
        try:
            match = re.search(self.content_pattern, raw_content)
            if not match:
                return None
                
            content_str = match.group(1)
            
            # 关键修复：处理转义字符
            # 将 \' 替换为 '，这是JSON字符串中转义的单引号
            content_str = content_str.replace("\\'", "'")
            
            print(f"调试：提取的content前100字符: {content_str[:100]}")
            
            content_data = json.loads(content_str)
            return content_data
            
        except (json.JSONDecodeError, Exception) as e:
            print(f"内容提取错误: {e}")
            print(f"尝试解析的内容片段: {content_str[:200]}...")
            return None
    
    def clean_chinese_text(self, text):
        """
        清理中文原句，去掉开头的数字标号
        例如: "73. 值得一提的是..." -> "值得一提的是..."
        """
        if not text:
            return text
        
        # 匹配开头的数字标号模式，如 "73.", "1.", "123." 等
        pattern = r'^\d+\.\s*'
        cleaned_text = re.sub(pattern, '', text)
        return cleaned_text.strip()
    
    def process_json_file(self, json_file_path):
        """处理单个JSON文件"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            folder_name = data.get('folder_name', '')
            timestamp = data.get('timestamp', '')
            
            file_records = []
            
            for message in data.get('raw_messages', []):
                raw_content = message.get('raw_content', '')
                content_data = self.extract_content_from_raw(raw_content)
                
                if not content_data:
                    continue
                
                usage_output = content_data.get('usage_output', [])
                
                for idx, item in enumerate(usage_output, 1):
                    flag = item.get('flag', '')
                    chinese_txt = item.get('chinese_txt', '')
                    bracket_en_mistake = item.get('bracket_en_mistake', '')
                    
                    # 清理中文原句，去掉开头的数字标号
                    cleaned_chinese_txt = self.clean_chinese_text(chinese_txt)
                    
                    record = {
                        'folder_name': folder_name,
                        'timestamp': timestamp,
                        'json_file': json_file_path.name,
                        'sentence_index': idx,
                        'chinese_txt': cleaned_chinese_txt,
                        'original_chinese_txt': chinese_txt,  # 保留原始文本用于调试
                        'bracket_en_mistake': bracket_en_mistake,
                        'flag': flag
                    }
                    
                    file_records.append(record)
                    status = "正确" if flag == 'true' else "错误"
                    print(f"找到{status}: {folder_name} - 句子{idx}: {cleaned_chinese_txt[:30]}...")
            
            return file_records
            
        except Exception as e:
            print(f"处理文件 {json_file_path} 时出错: {e}")
            return []
    
    def scan_all_folders(self):
        """扫描所有子文件夹"""
        print(f"开始扫描目录: {self.base_dir}")
        
        if not self.base_dir.exists():
            print(f"错误：目录不存在: {self.base_dir}")
            return
        
        for folder_path in self.base_dir.iterdir():
            if not folder_path.is_dir():
                continue
            
            print(f"扫描文件夹: {folder_path.name}")
            
            json_files = list(folder_path.glob("*_response_cache_*.json"))
            
            if not json_files:
                print(f"警告：文件夹 {folder_path.name} 中未找到JSON文件")
                continue
            
            for json_file in json_files:
                print(f"处理文件: {json_file.name}")
                records = self.process_json_file(json_file)
                self.error_data.extend(records)
        
        self.total_false_count = len([r for r in self.error_data if r['flag'] == 'false'])
        total_records = len(self.error_data)
        print(f"扫描完成，共找到 {total_records} 个句子记录，其中 {self.total_false_count} 个错误翻译")
    
    def save_results(self):
        """保存结果"""
        if not self.error_data:
            print("没有找到数据，跳过保存")
            return
        
        timestamp = datetime.now().strftime(self.config["global_config"]["timestamp_format"])
        
        # 使用配置的字段映射保存CSV
        csv_file = self.base_dir / f"translation_records_{timestamp}.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
            # 使用配置中的中文字段名作为CSV头部
            fieldnames = [
                'folder_name', 'timestamp', 'json_file', 'sentence_index', 
                self.field_mappings['chinese_txt'],  # "中文原句"
                self.field_mappings['bracket_en_mistake'],  # "错误表达"
                self.field_mappings['flag']  # "判断结果"
            ]
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            # 转换数据行，使用中文字段名
            for record in self.error_data:
                row = {
                    'folder_name': record['folder_name'],
                    'timestamp': record['timestamp'],
                    'json_file': record['json_file'],
                    'sentence_index': record['sentence_index'],
                    self.field_mappings['chinese_txt']: record['chinese_txt'],
                    self.field_mappings['bracket_en_mistake']: record['bracket_en_mistake'],
                    self.field_mappings['flag']: record['flag']
                }
                writer.writerow(row)
        
        print(f"CSV文件已保存: {csv_file}")
        
        # 保存为文本格式，使用配置的字段映射
        txt_file = self.base_dir / f"translation_records_{timestamp}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("翻译记录分析报告\n")
            f.write("=" * 60 + "\n")
            f.write(f"扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            total_records = len(self.error_data)
            f.write(f"总记录数量: {total_records}\n")
            f.write(f"错误数量: {self.total_false_count}\n")
            f.write(f"正确数量: {total_records - self.total_false_count}\n")
            
            # 统计涉及的文件夹
            folders = set(record['folder_name'] for record in self.error_data)
            f.write(f"涉及文件夹数: {len(folders)}\n")
            f.write("\n" + "=" * 60 + "\n")
            f.write("记录详情:\n")
            f.write("=" * 60 + "\n\n")
            
            for idx, record in enumerate(self.error_data, 1):
                f.write(f"【记录 {idx}】\n")
                f.write(f"文件夹: {record['folder_name']}\n")
                f.write(f"时间戳: {record['timestamp']}\n")
                f.write(f"句子序号: {record['sentence_index']}\n")
                f.write(f"{self.field_mappings['chinese_txt']}: {record['chinese_txt']}\n")
                f.write(f"{self.field_mappings['bracket_en_mistake']}: {record['bracket_en_mistake']}\n")
                f.write(f"{self.field_mappings['flag']}: {record['flag']}\n")
                f.write("-" * 40 + "\n\n")
        
        print(f"文本文件已保存: {txt_file}")
        
        # 保存为JSON
        json_file = self.base_dir / f"translation_records_{timestamp}.json"
        result_data = {
            'scan_time': datetime.now().isoformat(),
            'total_records': len(self.error_data),
            'total_false_count': self.total_false_count,
            'total_true_count': len(self.error_data) - self.total_false_count,
            'total_folders': len(folders),
            'field_mappings': self.field_mappings,  # 添加字段映射信息
            'record_details': self.error_data
        }
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        
        print(f"JSON文件已保存: {json_file}")
    
    def print_report(self):
        """打印分析报告"""
        if not self.error_data:
            print("没有找到数据")
            return
        
        total_records = len(self.error_data)
        total_true_count = total_records - self.total_false_count
        
        print("\n" + "=" * 60)
        print("翻译记录分析报告")
        print("=" * 60)
        print(f"扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"总记录数量: {total_records}")
        print(f"正确数量: {total_true_count}")
        print(f"错误数量: {self.total_false_count}")
        if total_records > 0:
            print(f"正确率: {total_true_count/total_records*100:.1f}%")
        
        # 统计涉及的文件夹
        folders = {}
        folder_stats = {}
        for record in self.error_data:
            folder = record['folder_name']
            folders[folder] = folders.get(folder, 0) + 1
            
            if folder not in folder_stats:
                folder_stats[folder] = {'total': 0, 'correct': 0, 'error': 0}
            folder_stats[folder]['total'] += 1
            if record['flag'] == 'true':
                folder_stats[folder]['correct'] += 1
            else:
                folder_stats[folder]['error'] += 1
        
        print(f"涉及文件夹数: {len(folders)}")
        
        # 按文件夹统计
        print(f"\n按文件夹统计:")
        for folder in sorted(folder_stats.keys()):
            stats = folder_stats[folder]
            accuracy = stats['correct'] / stats['total'] * 100 if stats['total'] > 0 else 0
            print(f"  {folder}: 总计{stats['total']}句, 正确{stats['correct']}句, 错误{stats['error']}句 (正确率: {accuracy:.1f}%)")
        
        # 错误表达统计，使用配置的字段名
        mistakes = {}
        for record in self.error_data:
            if record['flag'] == 'false':  # 只统计错误的
                mistake = record['bracket_en_mistake']
                if mistake:  # 只统计非空的错误表达
                    mistakes[mistake] = mistakes.get(mistake, 0) + 1
        
        if mistakes:
            print(f"\n常见{self.field_mappings['bracket_en_mistake']}统计:")
            sorted_mistakes = sorted(mistakes.items(), key=lambda x: x[1], reverse=True)
            for mistake, count in sorted_mistakes[:10]:  # 显示前10个
                print(f"  '{mistake}': {count} 次")


def main():
    """主函数"""
    base_dir = r"E:\zhenzhen_eng_coze\example\翻译\作业内容_翻译_Download_1_50"
    
    scanner = SimpleErrorScanner(base_dir)
    scanner.scan_all_folders()
    scanner.print_report()
    scanner.save_results()
    
    print(f"\n所有结果文件已保存到: {base_dir}")


if __name__ == "__main__":
    main()