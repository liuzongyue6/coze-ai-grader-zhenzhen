#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分组错误报告生成器 - 按中文原句相似性分组，生成老师友好的报告
"""

import os
import json
import csv
import re
from datetime import datetime
from pathlib import Path
import sys
from collections import defaultdict
from difflib import SequenceMatcher

# 添加config目录到Python路径
current_dir = Path(__file__).parent
config_dir = current_dir.parent / "config"
sys.path.append(str(config_dir))

from translation_rec_format_config import get_multi_output_config

class GroupedMistakeReporter:
    def __init__(self, base_dir):
        """
        初始化分组报告生成器
        
        Args:
            base_dir (str): 基础目录路径
        """
        self.base_dir = Path(base_dir)
        self.config = get_multi_output_config()
        self.content_pattern = self.config["content_pattern"]
        self.error_data = []
        
        # 获取字段映射
        self.usage_output_config = self.config["output_types"]["usage_output"]
        self.field_mappings = self.usage_output_config["field_mappings"]
        
        # 分组数据
        self.grouped_data = defaultdict(list)
        self.similarity_threshold = 0.8  # 相似度阈值
        
    def extract_content_from_raw(self, raw_content):
        """从raw_content中提取JSON内容"""
        try:
            match = re.search(self.content_pattern, raw_content)
            if not match:
                return None
                
            content_str = match.group(1)
            content_str = content_str.replace("\\'", "'")
            content_data = json.loads(content_str)
            return content_data
            
        except (json.JSONDecodeError, Exception) as e:
            print(f"内容提取错误: {e}")
            return None
    
    def clean_chinese_text(self, text):
        """清理中文原句，去掉开头的数字标号"""
        if not text:
            return text
        
        pattern = r'^\d+\.\s*'
        cleaned_text = re.sub(pattern, '', text)
        return cleaned_text.strip()
    
    def text_similarity(self, text1, text2):
        """计算两个文本的相似度"""
        return SequenceMatcher(None, text1, text2).ratio()
    
    def find_similar_group(self, text, existing_groups):
        """查找相似的分组"""
        for group_key in existing_groups:
            if self.text_similarity(text, group_key) >= self.similarity_threshold:
                return group_key
        return None
    
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
                    
                    # 清理中文原句
                    cleaned_chinese_txt = self.clean_chinese_text(chinese_txt)
                    
                    record = {
                        'folder_name': folder_name,
                        'timestamp': timestamp,
                        'json_file': json_file_path.name,
                        'sentence_index': idx,
                        'chinese_txt': cleaned_chinese_txt,
                        'bracket_en_mistake': bracket_en_mistake,
                        'flag': flag
                    }
                    
                    file_records.append(record)
            
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
        
        print(f"扫描完成，共找到 {len(self.error_data)} 个句子记录")
    
    def group_by_similarity(self):
        """按相似度分组数据"""
        print("开始按相似度分组...")
        
        for record in self.error_data:
            chinese_txt = record['chinese_txt']
            if not chinese_txt:
                continue
            
            # 查找相似的分组
            similar_group = self.find_similar_group(chinese_txt, self.grouped_data.keys())
            
            if similar_group:
                # 添加到现有分组
                self.grouped_data[similar_group].append(record)
            else:
                # 创建新分组
                self.grouped_data[chinese_txt].append(record)
        
        print(f"分组完成，共生成 {len(self.grouped_data)} 个分组")
    
    def generate_teacher_report(self):
        """生成适合老师查看的报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. 生成CSV报告
        csv_file = self.base_dir / f"分组错误报告_{timestamp}.csv"
        self.generate_csv_report(csv_file)
        
        # 2. 生成详细文本报告
        txt_file = self.base_dir / f"分组错误详细报告_{timestamp}.txt"
        self.generate_detailed_text_report(txt_file)
        
        # 3. 生成简洁汇总报告
        summary_file = self.base_dir / f"错误汇总报告_{timestamp}.txt"
        self.generate_summary_report(summary_file)
        
        print(f"\n所有报告已生成:")
        print(f"1. CSV报告: {csv_file}")
        print(f"2. 详细报告: {txt_file}")
        print(f"3. 汇总报告: {summary_file}")
    
    def generate_csv_report(self, csv_file):
        """生成CSV格式报告"""
        with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
            fieldnames = [
                '分组序号', '中文原句', '总批改份数', '错误份数', '正确份数', 
                '错误率(%)', '常见错误表达', '涉及学生'
            ]
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for idx, (group_key, records) in enumerate(sorted(self.grouped_data.items()), 1):
                total_count = len(records)
                false_count = len([r for r in records if r['flag'] == 'false'])
                true_count = total_count - false_count
                error_rate = (false_count / total_count * 100) if total_count > 0 else 0
                
                # 收集错误表达
                mistakes = [r['bracket_en_mistake'] for r in records if r['flag'] == 'false' and r['bracket_en_mistake']]
                common_mistakes = ', '.join(list(set(mistakes))[:3])  # 最多显示3个不同的错误
                
                # 涉及学生
                students = list(set([r['folder_name'] for r in records]))
                students_str = ', '.join(students[:5])  # 最多显示5个学生名字
                if len(students) > 5:
                    students_str += f" 等{len(students)}人"
                
                row = {
                    '分组序号': idx,
                    '中文原句': group_key[:50] + "..." if len(group_key) > 50 else group_key,
                    '总批改份数': total_count,
                    '错误份数': false_count,
                    '正确份数': true_count,
                    '错误率(%)': f"{error_rate:.1f}",
                    '常见错误表达': common_mistakes,
                    '涉及学生': students_str
                }
                writer.writerow(row)
    
    def generate_detailed_text_report(self, txt_file):
        """生成详细文本报告"""
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("英语翻译批改分组错误详细报告\n")
            f.write("=" * 80 + "\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"数据来源: {self.base_dir}\n")
            f.write(f"总分组数: {len(self.grouped_data)}\n")
            f.write(f"总句子数: {len(self.error_data)}\n")
            
            # 整体统计
            total_false = len([r for r in self.error_data if r['flag'] == 'false'])
            total_true = len(self.error_data) - total_false
            overall_accuracy = (total_true / len(self.error_data) * 100) if self.error_data else 0
            
            f.write(f"总错误数: {total_false}\n")
            f.write(f"总正确数: {total_true}\n")
            f.write(f"整体正确率: {overall_accuracy:.1f}%\n")
            f.write("\n" + "=" * 80 + "\n\n")
            
            # 按错误率排序分组
            sorted_groups = sorted(
                self.grouped_data.items(), 
                key=lambda x: len([r for r in x[1] if r['flag'] == 'false']) / len(x[1]), 
                reverse=True
            )
            
            for idx, (group_key, records) in enumerate(sorted_groups, 1):
                total_count = len(records)
                false_count = len([r for r in records if r['flag'] == 'false'])
                true_count = total_count - false_count
                error_rate = (false_count / total_count * 100) if total_count > 0 else 0
                
                f.write(f"【分组 {idx}】\n")
                f.write(f"中文原句: {group_key}\n")
                f.write(f"批改统计: 总计 {total_count} 份，错误 {false_count} 份，正确 {true_count} 份\n")
                f.write(f"错误率: {error_rate:.1f}%\n")
                
                # 错误表达统计
                mistakes = {}
                for record in records:
                    if record['flag'] == 'false' and record['bracket_en_mistake']:
                        mistake = record['bracket_en_mistake']
                        mistakes[mistake] = mistakes.get(mistake, 0) + 1
                
                if mistakes:
                    f.write("错误表达统计:\n")
                    for mistake, count in sorted(mistakes.items(), key=lambda x: x[1], reverse=True):
                        f.write(f"  - '{mistake}': {count} 次\n")
                
                
                # 涉及学生 - 只显示翻译错误的学生
                error_students = list(set([r['folder_name'] for r in records if r['flag'] == 'false']))
                f.write(f"涉及学生 ({len(error_students)} 人): {', '.join(error_students)}\n")
                f.write("-" * 60 + "\n\n")
    
    def generate_summary_report(self, summary_file):
        """生成简洁汇总报告"""
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("英语翻译批改错误汇总报告\n")
            f.write("=" * 50 + "\n")
            f.write(f"报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Top 10 错误率最高的分组
            sorted_groups = sorted(
                self.grouped_data.items(), 
                key=lambda x: len([r for r in x[1] if r['flag'] == 'false']) / len(x[1]), 
                reverse=True
            )
            
            f.write("❌ 错误率最高的10个句子类型:\n")
            f.write("-" * 40 + "\n")
            
            for idx, (group_key, records) in enumerate(sorted_groups[:10], 1):
                total_count = len(records)
                false_count = len([r for r in records if r['flag'] == 'false'])
                error_rate = (false_count / total_count * 100) if total_count > 0 else 0
                
                # 最常见的错误
                mistakes = [r['bracket_en_mistake'] for r in records if r['flag'] == 'false' and r['bracket_en_mistake']]
                common_mistake = max(set(mistakes), key=mistakes.count) if mistakes else "无"
                
                f.write(f"{idx}. 错误率: {error_rate:.1f}% ({false_count}/{total_count})\n")
                f.write(f"   句子: {group_key[:60]}{'...' if len(group_key) > 60 else ''}\n")
                f.write(f"   常见错误: {common_mistake}\n\n")
            
            # 整体统计
            f.write("📊 整体统计:\n")
            f.write("-" * 20 + "\n")
            total_students = len(set([r['folder_name'] for r in self.error_data]))
            total_false = len([r for r in self.error_data if r['flag'] == 'false'])
            total_true = len(self.error_data) - total_false
            overall_accuracy = (total_true / len(self.error_data) * 100) if self.error_data else 0
            
            f.write(f"参与学生数: {total_students} 人\n")
            f.write(f"句子分组数: {len(self.grouped_data)} 组\n")
            f.write(f"总句子数: {len(self.error_data)} 句\n")
            f.write(f"正确数: {total_true} 句\n")
            f.write(f"错误数: {total_false} 句\n")
            f.write(f"整体正确率: {overall_accuracy:.1f}%\n")
    
    def print_quick_summary(self):
        """打印快速摘要"""
        print("\n" + "=" * 60)
        print("📋 分组错误报告摘要")
        print("=" * 60)
        
        total_groups = len(self.grouped_data)
        total_sentences = len(self.error_data)
        total_false = len([r for r in self.error_data if r['flag'] == 'false'])
        total_students = len(set([r['folder_name'] for r in self.error_data]))
        
        print(f"📊 基本统计:")
        print(f"   参与学生: {total_students} 人")
        print(f"   句子分组: {total_groups} 组")
        print(f"   总句子数: {total_sentences} 句")
        print(f"   错误句子: {total_false} 句")
        print(f"   整体正确率: {(total_sentences-total_false)/total_sentences*100:.1f}%")
        
        # 显示错误率最高的5个分组
        sorted_groups = sorted(
            self.grouped_data.items(), 
            key=lambda x: len([r for r in x[1] if r['flag'] == 'false']) / len(x[1]), 
            reverse=True
        )
        
        print(f"\n🔴 错误率最高的5个句子类型:")
        for idx, (group_key, records) in enumerate(sorted_groups[:5], 1):
            total_count = len(records)
            false_count = len([r for r in records if r['flag'] == 'false'])
            error_rate = (false_count / total_count * 100) if total_count > 0 else 0
            
            print(f"   {idx}. {error_rate:.1f}% - {group_key[:40]}{'...' if len(group_key) > 40 else ''}")


def main():
    """主函数"""
    base_dir = r"E:\zhenzhen_eng_coze\example\翻译\作业内容_翻译_Download_1_50"
    
    print("🔍 开始生成分组错误报告...")
    
    reporter = GroupedMistakeReporter(base_dir)
    
    # 1. 扫描数据
    reporter.scan_all_folders()
    
    # 2. 按相似度分组
    reporter.group_by_similarity()
    
    # 3. 打印快速摘要
    reporter.print_quick_summary()
    
    # 4. 生成报告文件
    reporter.generate_teacher_report()
    
    print(f"\n✅ 所有报告已生成完成！")
    print(f"📁 文件保存位置: {base_dir}")


if __name__ == "__main__":
    main()
