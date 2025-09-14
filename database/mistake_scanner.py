#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版错误翻译扫描器 - 不依赖pandas
扫描所有子文件夹中的JSON文件，提取flag为false的翻译错误数据
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
    
    def process_json_file(self, json_file_path):
        """处理单个JSON文件"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            folder_name = data.get('folder_name', '')
            timestamp = data.get('timestamp', '')
            
            file_errors = []
            
            for message in data.get('raw_messages', []):
                raw_content = message.get('raw_content', '')
                content_data = self.extract_content_from_raw(raw_content)
                
                if not content_data:
                    continue
                
                usage_output = content_data.get('usage_output', [])
                
                for idx, item in enumerate(usage_output, 1):
                    flag = item.get('flag', '')
                    if flag == 'false':
                        chinese_txt = item.get('chinese_txt', '')
                        bracket_en_mistake = item.get('bracket_en_mistake', '')
                        
                        error_record = {
                            'folder_name': folder_name,
                            'timestamp': timestamp,
                            'json_file': json_file_path.name,
                            'sentence_index': idx,
                            'chinese_txt': chinese_txt,
                            'bracket_en_mistake': bracket_en_mistake,
                            'flag': flag
                        }
                        
                        file_errors.append(error_record)
                        print(f"找到错误: {folder_name} - 句子{idx}: {chinese_txt[:30]}...")
            
            return file_errors
            
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
                errors = self.process_json_file(json_file)
                self.error_data.extend(errors)
        
        self.total_false_count = len(self.error_data)
        print(f"扫描完成，共找到 {self.total_false_count} 个错误翻译")
    
    def save_results(self):
        """保存结果"""
        if not self.error_data:
            print("没有找到错误数据，跳过保存")
            return
        
        timestamp = datetime.now().strftime(self.config["global_config"]["timestamp_format"])
        
        # 使用配置的字段映射保存CSV
        csv_file = self.base_dir / f"translation_errors_{timestamp}.csv"
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
            for error in self.error_data:
                row = {
                    'folder_name': error['folder_name'],
                    'timestamp': error['timestamp'],
                    'json_file': error['json_file'],
                    'sentence_index': error['sentence_index'],
                    self.field_mappings['chinese_txt']: error['chinese_txt'],
                    self.field_mappings['bracket_en_mistake']: error['bracket_en_mistake'],
                    self.field_mappings['flag']: error['flag']
                }
                writer.writerow(row)
        
        print(f"CSV文件已保存: {csv_file}")
        
        # 保存为文本格式，使用配置的字段映射
        txt_file = self.base_dir / f"translation_errors_{timestamp}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("翻译错误分析报告\n")
            f.write("=" * 60 + "\n")
            f.write(f"扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"总错误数量: {self.total_false_count}\n")
            
            # 统计涉及的文件夹
            folders = set(error['folder_name'] for error in self.error_data)
            f.write(f"涉及文件夹数: {len(folders)}\n")
            f.write("\n" + "=" * 60 + "\n")
            f.write("错误详情:\n")
            f.write("=" * 60 + "\n\n")
            
            for idx, error in enumerate(self.error_data, 1):
                f.write(f"【错误 {idx}】\n")
                f.write(f"文件夹: {error['folder_name']}\n")
                f.write(f"时间戳: {error['timestamp']}\n")
                f.write(f"句子序号: {error['sentence_index']}\n")
                f.write(f"{self.field_mappings['chinese_txt']}: {error['chinese_txt']}\n")
                f.write(f"{self.field_mappings['bracket_en_mistake']}: {error['bracket_en_mistake']}\n")
                f.write(f"{self.field_mappings['flag']}: {error['flag']}\n")
                f.write("-" * 40 + "\n\n")
        
        print(f"文本文件已保存: {txt_file}")
        
        # 保存为JSON
        json_file = self.base_dir / f"translation_errors_{timestamp}.json"
        result_data = {
            'scan_time': datetime.now().isoformat(),
            'total_false_count': self.total_false_count,
            'total_folders': len(folders),
            'field_mappings': self.field_mappings,  # 添加字段映射信息
            'error_details': self.error_data
        }
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        
        print(f"JSON文件已保存: {json_file}")
    
    def print_report(self):
        """打印分析报告"""
        if not self.error_data:
            print("没有找到错误数据")
            return
        
        print("\n" + "=" * 60)
        print("翻译错误分析报告")
        print("=" * 60)
        print(f"扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"总错误数量: {self.total_false_count}")
        
        # 统计涉及的文件夹
        folders = {}
        for error in self.error_data:
            folder = error['folder_name']
            folders[folder] = folders.get(folder, 0) + 1
        
        print(f"涉及文件夹数: {len(folders)}")
        
        # 按文件夹统计
        print(f"\n按文件夹错误统计:")
        for folder, count in sorted(folders.items()):
            print(f"  {folder}: {count} 个错误")
        
        # 错误表达统计，使用配置的字段名
        mistakes = {}
        for error in self.error_data:
            mistake = error['bracket_en_mistake']
            if mistake:  # 只统计非空的错误表达
                mistakes[mistake] = mistakes.get(mistake, 0) + 1
        
        if mistakes:
            print(f"\n常见{self.field_mappings['bracket_en_mistake']}统计:")
            sorted_mistakes = sorted(mistakes.items(), key=lambda x: x[1], reverse=True)
            for mistake, count in sorted_mistakes[:10]:  # 显示前10个
                print(f"  '{mistake}': {count} 次")


def main():
    """主函数"""
    base_dir = r"E:\真真英语\作文\test\Translation_Test"
    
    scanner = SimpleErrorScanner(base_dir)
    scanner.scan_all_folders()
    scanner.print_report()
    scanner.save_results()
    
    print(f"\n所有结果文件已保存到: {base_dir}")


if __name__ == "__main__":
    main()