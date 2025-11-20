import os
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Set, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.patches import Rectangle

# Configure matplotlib for Chinese characters
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False

"""
==========================================
学生翻译错误分析工具
==========================================

功能说明：
1. 解析学生翻译作业的JSON日志文件
2. 提取标记为"翻得不好"的错误
3. 生成错误统计报告
4. 导出两个JSON文件：
   - 1_student_mistakes.json: 按中文句子分组的学生错误
   - 2_statistics_summary.json: 每个句子的统计摘要
5. 生成可视化图表：
   - mistake_rate_pie_charts.png: 每句话的错误率饼图
   - student_mistakes_visual.png: 学生错误详细列表图

使用方法：
1. 设置 ROOT_DIRECTORY 为包含所有学生文件夹的根目录
2. 设置 BASELINE_FOLDER 为基准学生的文件夹名称（用于提取题目）
3. 运行脚本，自动生成所有报告和图表

输出文件：
- 1_student_mistakes.json: 学生错误详情
- 2_statistics_summary.json: 统计摘要
- mistake_rate_pie_charts.png: 错误率饼图
- student_mistakes_visual.png: 错误详情可视化图
"""

# ==========================================
# 数据模型 (用于类型安全)
# ==========================================

@dataclass
class MistakeEntry:
    """单个错误条目的数据模型"""
    chinese_txt: str
    mistake: str
    mistake_flag: str
    comment: str
    std_input: str
    thought: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MistakeEntry':
        """从字典创建 MistakeEntry 对象"""
        return cls(
            chinese_txt=data.get('chinese_txt', ''),
            mistake=data.get('mistake', ''),
            mistake_flag=data.get('mistake_flag', ''),
            comment=data.get('comment', ''),
            std_input=data.get('std_input', ''),
            thought=data.get('thought', '')
        )

@dataclass
class StudentMistake:
    """学生特定错误的数据模型"""
    student_name: str
    mistake: str
    comment: str
    std_input: str
    file_path: str

# ==========================================
# 第一层: 文件读写与解析 (底层)
# ==========================================

def parse_log_content(file_path: Path) -> Optional[List[Dict[str, Any]]]:
    """
    解析日志文件，提取并加载内部JSON数据
    正确处理转义的引号和撇号
    
    参数：
        file_path: 日志文件路径
        
    返回：
        解析后的JSON数据列表，失败则返回None
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()
        
        # 首先加载外层JSON结构
        outer_data = json.loads(raw_content)
        
        # 导航到 raw_content 字段
        if 'raw_messages' not in outer_data or len(outer_data['raw_messages']) == 0:
            return None
        
        raw_message = outer_data['raw_messages'][0]['raw_content']
        
        # 使用正则表达式提取 content='...' 部分
        match = re.search(r"content='(\{.*\})'", raw_message, re.DOTALL)
        if not match:
            return None
        
        json_string = match.group(1)
        
        # 替换有问题的转义序列
        cleaned_string = json_string.replace("\\'", "'")
        
        # 解析清理后的JSON
        data = json.loads(cleaned_string)
        
        return data.get("output_arr_obj")

    except json.JSONDecodeError as e:
        print(f"⚠ JSON解析错误: {file_path.name}")
        return None
    except FileNotFoundError:
        print(f"⚠ 文件未找到: {file_path}")
        return None
    except Exception as e:
        print(f"⚠ 处理文件时出错 {file_path.name}: {e}")
        return None

def find_json_files(root_folder: Path) -> List[Path]:
    """
    递归查找给定文件夹中的所有.json文件
    
    参数：
        root_folder: 要搜索的根目录
        
    返回：
        指向JSON文件的Path对象列表
    """
    return list(root_folder.rglob("*.json"))

# ==========================================
# 第二层: 数据提取 (业务逻辑)
# ==========================================

def extract_mistakes_from_data(
    parsed_data: List[Dict[str, Any]], 
    target_flag: str = "翻得不好"
) -> List[MistakeEntry]:
    """
    提取标志匹配目标的错误
    
    参数：
        parsed_data: 从日志文件解析的JSON数据
        target_flag: 要过滤的错误标志（默认："翻得不好"）
        
    返回：
        匹配目标标志的 MistakeEntry 对象列表
    """
    mistakes = []
    if not parsed_data:
        return mistakes
        
    for item in parsed_data:
        if item.get("mistake_flag") == target_flag:
            try:
                mistakes.append(MistakeEntry.from_dict(item))
            except Exception as e:
                print(f"警告: 解析错误条目失败: {e}")
    
    return mistakes

def extract_all_chinese_sentences(parsed_data: List[Dict[str, Any]]) -> Set[str]:
    """
    从解析的数据中提取所有唯一的中文句子
    
    参数：
        parsed_data: 从日志文件解析的JSON数据
        
    返回：
        唯一中文句子的集合
    """
    sentences = set()
    if not parsed_data:
        return sentences
    
    for item in parsed_data:
        chinese_txt = item.get('chinese_txt')
        if chinese_txt:
            sentences.add(chinese_txt.strip())
    
    return sentences

# ==========================================
# 第三层: 基准管理
# ==========================================

def establish_baseline_sentences(baseline_folder_path: Path) -> Set[str]:
    """
    从基准文件夹中提取唯一的中文句子
    这将创建一个参考集，用于匹配其他学生的作业
    
    参数：
        baseline_folder_path: 基准文件夹的路径（第一个学生文件夹）
        
    返回：
        作为基准的唯一中文句子集合
    """
    baseline_sentences = set()
    json_files = find_json_files(baseline_folder_path)
    
    for file_path in json_files:
        parsed_data = parse_log_content(file_path)
        if parsed_data:
            sentences = extract_all_chinese_sentences(parsed_data)
            baseline_sentences.update(sentences)
    
    print(f"✓ 基准已建立: 从 {baseline_folder_path.name} 提取了 {len(baseline_sentences)} 个句子")
    return baseline_sentences

# ==========================================
# 第四层: 错误汇总与统计
# ==========================================

def summarize_student_mistakes(
    root_directory: str, 
    baseline_folder_name: str
) -> Tuple[Dict[str, List[StudentMistake]], Set[str]]:
    """
    协调查找、匹配和汇总错误的过程
    
    参数：
        root_directory: 包含所有学生文件夹的根路径
        baseline_folder_name: 用作基准的文件夹名称
        
    返回：
        元组 (mistake_summary, baseline_sentences)
        - mistake_summary: 将 chinese_txt 映射到 StudentMistake 对象列表的字典
        - baseline_sentences: 基准中文句子集合
    """
    root_path = Path(root_directory)
    baseline_path = root_path / baseline_folder_name
    
    # 验证基准文件夹是否存在
    if not baseline_path.is_dir():
        raise FileNotFoundError(
            f"基准文件夹 '{baseline_folder_name}' 未在 '{root_directory}' 中找到"
        )

    # 步骤1: 从第一个文件夹建立基准
    baseline_sentences = establish_baseline_sentences(baseline_path)
    
    # 步骤2: 处理所有学生文件夹
    mistake_summary = defaultdict(list)
    student_count = 0
    
    for student_folder_path in sorted(root_path.iterdir()):
        # 跳过非目录和基准文件夹
        if not student_folder_path.is_dir():
            continue
            
        student_name = student_folder_path.name
        student_count += 1
        
        # 查找并处理该学生的所有JSON文件
        student_json_files = find_json_files(student_folder_path)
        
        mistakes_count = 0
        for file_path in student_json_files:
            parsed_data = parse_log_content(file_path)
            mistakes_found = extract_mistakes_from_data(parsed_data)
            
            for mistake_entry in mistakes_found:
                sentence = mistake_entry.chinese_txt.strip()
                
                # 只记录在基准中的句子
                if sentence in baseline_sentences:
                    mistake_summary[sentence].append(StudentMistake(
                        student_name=student_name,
                        mistake=mistake_entry.mistake,
                        comment=mistake_entry.comment,
                        std_input=mistake_entry.std_input,
                        file_path=str(file_path.name)
                    ))
                    mistakes_count += 1
    
    print(f"✓ 已处理 {student_count} 名学生")
    return dict(mistake_summary), baseline_sentences

# ==========================================
# 第五层: 统计与报告
# ==========================================

def generate_statistics_report(
    mistake_summary: Dict[str, List[StudentMistake]]
) -> Dict[str, Any]:
    """
    从错误汇总中生成综合统计信息
    
    参数：
        mistake_summary: 将 chinese_txt 映射到学生错误的字典
        
    返回：
        包含各种统计信息的字典
    """
    stats = {
        "total_unique_sentences": len(mistake_summary),
        "total_mistake_instances": sum(len(students) for students in mistake_summary.values()),
        "mistakes_per_student": defaultdict(int),
        "sentences_with_most_mistakes": [],
        "students_processed": set()
    }
    
    # 统计每个学生的错误数量
    for sentence, student_mistakes in mistake_summary.items():
        for student_mistake in student_mistakes:
            stats["mistakes_per_student"][student_mistake.student_name] += 1
            stats["students_processed"].add(student_mistake.student_name)
    
    # 按错误频率排序句子
    sentence_freq = [
        (sentence, len(students)) 
        for sentence, students in mistake_summary.items()
    ]
    stats["sentences_with_most_mistakes"] = sorted(
        sentence_freq, 
        key=lambda x: x[1], 
        reverse=True
    )
    
    # 将集合转换为计数
    stats["total_students"] = len(stats["students_processed"])
    del stats["students_processed"]
    
    return dict(stats)

def export_summary_to_json(
    mistake_summary: Dict[str, List[StudentMistake]], 
    output_path: str,
    include_metadata: bool = True
) -> None:
    """
    将错误汇总导出到JSON文件
    
    参数：
        mistake_summary: 要导出的错误字典
        output_path: 保存JSON文件的路径
        include_metadata: 是否包含时间戳等元数据
    """
    export_data = {}
    
    if include_metadata:
        export_data["metadata"] = {
            "export_timestamp": datetime.now().isoformat(),
            "total_sentences": len(mistake_summary),
            "total_instances": sum(len(v) for v in mistake_summary.values())
        }
    
    export_data["mistakes"] = {
        sentence: [
            {
                "student": sm.student_name,
                "mistake": sm.mistake,
                "comment": sm.comment,
                "std_input": sm.std_input,
                "file": sm.file_path
            }
            for sm in students
        ]
        for sentence, students in mistake_summary.items()
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 已导出汇总到: {output_path}")

def export_student_mistakes_json(
    mistake_summary: Dict[str, List[StudentMistake]], 
    baseline_sentences: Set[str],
    output_path: str
) -> None:
    """
    导出按学生组织的每个中文句子的错误汇总
    
    格式:
    {
      "chinese_sentence": {
        "student_name": "mistake_text",
        ...
      },
      ...
    }
    
    参数：
        mistake_summary: 将 chinese_txt 映射到学生错误的字典
        baseline_sentences: 所有基准句子的集合
        output_path: 保存JSON文件的路径
    """
    export_data = {}
    
    # 处理基准中的每个句子
    for sentence in sorted(baseline_sentences):
        student_mistakes_dict = {}
        
        # 获取该句子的所有错误
        if sentence in mistake_summary:
            for student_mistake in mistake_summary[sentence]:
                student_mistakes_dict[student_mistake.student_name] = student_mistake.mistake
        
        # 只包含有错误的句子
        if student_mistakes_dict:
            export_data[sentence] = student_mistakes_dict
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 已导出学生错误到: {output_path}")


def export_statistics_json(
    mistake_summary: Dict[str, List[StudentMistake]], 
    baseline_sentences: Set[str],
    total_students: int,
    output_path: str
) -> None:
    """
    导出每个中文句子的统计摘要（不包含学生姓名）
    
    格式:
    {
      "chinese_sentence": {
        "total_submissions": 10,
        "mistake_count": 3,
        "mistake_rate": "30.00%",
        "unique_mistakes": ["mistake1", "mistake2", ...]
      },
      ...
    }
    
    参数：
        mistake_summary: 将 chinese_txt 映射到学生错误的字典
        baseline_sentences: 所有基准句子的集合
        total_students: 处理的学生总数
        output_path: 保存JSON文件的路径
    """
    export_data = {}
    
    # 处理基准中的每个句子
    for sentence in sorted(baseline_sentences):
        # 收集该句子的所有唯一错误（不包含学生姓名）
        unique_mistakes = set()
        mistake_count = 0
        
        if sentence in mistake_summary:
            mistake_count = len(mistake_summary[sentence])
            for student_mistake in mistake_summary[sentence]:
                if student_mistake.mistake:  # 只添加非空错误
                    unique_mistakes.add(student_mistake.mistake)
        
        # 计算错误率
        mistake_rate = (mistake_count / total_students * 100) if total_students > 0 else 0
        
        export_data[sentence] = {
            "total_submissions": total_students,
            "mistake_count": mistake_count,
            "mistake_rate": f"{mistake_rate:.2f}%",
            "unique_mistakes": sorted(list(unique_mistakes))  # 排序以保持一致性
        }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 已导出统计信息到: {output_path}")


def create_pie_charts_from_json(json_path: str, output_folder: str) -> None:
    """
    从统计摘要JSON文件创建饼图
    
    参数：
        json_path: 2_statistics_summary.json 文件的路径
        output_folder: 保存输出图表的文件夹
    """
    # 加载JSON数据
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not data:
        print("没有数据可绘制!")
        return
    
    num_sentences = len(data)
    
    # 计算网格大小
    cols = 3
    rows = (num_sentences + cols - 1) // cols  # 向上取整
    
    # 增加每行的高度，从 5 改为 6
    fig, axes = plt.subplots(rows, cols, figsize=(15, 6 * rows))
    fig.suptitle('各句翻译错误率', fontsize=16, fontweight='bold', y=0.995)
    
    # 展平axes以便于迭代（处理单行情况）
    if num_sentences == 1:
        axes_flat = [axes]
    elif rows == 1:
        axes_flat = axes
    else:
        axes_flat = axes.flatten()
    
    # 配色方案
    colors = ['#66c2a5', '#fc8d62']  # 绿色表示正确，橙色表示错误
    explode = (0.05, 0)  # 稍微分离错误切片
    
    for idx, (sentence, stats) in enumerate(data.items()):
        ax = axes_flat[idx]
        
        # 计算正确和错误的数量
        total = stats['total_submissions']
        incorrect = stats['mistake_count']
        correct = total - incorrect
        
        # 饼图数据
        sizes = [correct, incorrect]
        labels = [f'正确\n({correct}/{total})', f'错误\n({incorrect}/{total})']
        
        # 创建饼图
        wedges, texts, autotexts = ax.pie(
            sizes, 
            labels=labels, 
            colors=colors,
            autopct='%1.0f%%',
            startangle=90,
            explode=explode if incorrect > 0 else (0, 0),
            textprops={'fontsize': 10}
        )
        
        # 加粗百分比文本
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(11)
        
        # 添加带句子的标题（手动分成两行以避免拥挤）
        # 如果句子太长，在合适的位置分成两行
        max_line_length = 25  # 每行最多25个字符
        
        if len(sentence) > max_line_length:
            # 尝试在逗号、句号等标点处分割
            split_point = max_line_length
            for punctuation in ['，', '。', '、', '；', ' ']:
                pos = sentence[:max_line_length + 10].rfind(punctuation)
                if pos > 15:  # 确保第一行至少有15个字符
                    split_point = pos + 1
                    break
            
            line1 = sentence[:split_point].strip()
            line2 = sentence[split_point:].strip()
            
            # 如果第二行还是太长，截断并添加省略号
            if len(line2) > max_line_length:
                line2 = line2[:max_line_length] + '...'
            
            sentence_display = f"{idx+1}. {line1}\n{line2}"
        else:
            sentence_display = f"{idx+1}. {sentence}"
        
        ax.set_title(sentence_display, fontsize=10, pad=20)
    
    # 隐藏未使用的子图
    for idx in range(num_sentences, len(axes_flat)):
        axes_flat[idx].axis('off')
    
    # 增加子图之间的间距，使用 h_pad 和 w_pad 参数
    plt.tight_layout(rect=[0, 0, 1, 0.985], h_pad=3.0, w_pad=2.0)
    
    # 保存在同一文件夹中
    output_path = os.path.join(output_folder, 'mistake_rate_pie_charts.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ 饼图已保存到: {output_path}")
    
    # 不自动显示图表以避免阻塞
    # plt.show()


def create_student_mistakes_visual(json_path: str, output_folder: str) -> None:
    """
    从 1_student_mistakes.json 创建可视化图片
    显示中文句子及其对应的学生错误
    
    参数：
        json_path: 1_student_mistakes.json 文件的路径
        output_folder: 保存输出图片的文件夹
    """
    # 加载JSON数据
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not data:
        print("没有数据可显示!")
        return
    
    # 计算需要的图片高度
    num_sentences = len(data)
    
    # 动态计算高度：每个句子区块约占 1.5 英寸
    fig_height = max(8, num_sentences * 1.5)
    
    fig, ax = plt.subplots(figsize=(14, fig_height))
    ax.axis('off')
    
    # 设置标题
    title_text = '学生翻译错误详情'
    fig.suptitle(title_text, fontsize=18, fontweight='bold', y=0.98)
    
    # 起始y坐标
    y_position = 0.95
    x_left = 0.05
    line_height = 0.85 / num_sentences  # 根据句子数量动态调整行高
    
    # 颜色配置
    sentence_color = '#2c3e50'  # 深灰蓝色 - 中文句子
    student_color = '#e74c3c'   # 红色 - 学生名字
    mistake_color = '#34495e'   # 深灰色 - 错误内容
    box_color = '#ecf0f1'       # 浅灰色 - 背景框
    
    for idx, (sentence, student_mistakes) in enumerate(data.items()):
        # 1. 显示中文句子（加粗）
        sentence_display = f"{idx + 1}. {sentence}"
        fig.text(x_left, y_position, sentence_display, 
                fontsize=11, fontweight='bold', color=sentence_color,
                va='top', ha='left', wrap=True, transform=fig.transFigure, zorder=2)
        
        y_position -= line_height * 0.35
        
        # 2. 显示学生错误
        for student_name, mistake_text in student_mistakes.items():
            mistake_line = f"   • {student_name}: {mistake_text}"
            fig.text(x_left + 0.02, y_position, mistake_line,
                    fontsize=9, color=mistake_color,
                    va='top', ha='left', wrap=True, transform=fig.transFigure, zorder=2)
            y_position -= line_height * 0.25
        
        # 句子之间的间距
        y_position -= line_height * 0.15
    
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    
    # 保存图片
    output_path = os.path.join(output_folder, 'student_mistakes_visual.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✓ 学生错误可视化图已保存到: {output_path}")
    
    plt.close()


# ==========================================
# 主程序执行
# ==========================================

if __name__ == '__main__':
    # 配置
    ROOT_DIRECTORY = r"E:\zhenzhen_eng_coze\example\高二_8_reduced"
    BASELINE_FOLDER = "czc"
    OUTPUT_JSON_STUDENTS = os.path.join(ROOT_DIRECTORY, "1_student_mistakes.json")
    OUTPUT_JSON_STATISTICS = os.path.join(ROOT_DIRECTORY, "2_statistics_summary.json")

    try:
        print("=" * 60)
        print("学生翻译错误分析")
        print("=" * 60)
        
        # 运行汇总过程
        final_summary, baseline_sentences = summarize_student_mistakes(
            ROOT_DIRECTORY, 
            BASELINE_FOLDER
        )
        
        # 生成统计信息
        stats = generate_statistics_report(final_summary)
        
        # 简单汇总输出
        print(f"\n📊 汇总:")
        print(f"   • 有错误的句子数: {stats['total_unique_sentences']}")
        print(f"   • 错误实例总数: {stats['total_mistake_instances']}")
        print(f"   • 已处理学生数: {stats['total_students']}")
        
        # 导出JSON文件
        print(f"\n📁 导出文件...")
        export_student_mistakes_json(
            final_summary, 
            baseline_sentences,
            OUTPUT_JSON_STUDENTS
        )
        
        export_statistics_json(
            final_summary, 
            baseline_sentences,
            stats['total_students'],
            OUTPUT_JSON_STATISTICS
        )
        
        # 创建饼图
        print(f"\n📈 生成饼图...")
        create_pie_charts_from_json(OUTPUT_JSON_STATISTICS, ROOT_DIRECTORY)
        
        # 创建学生错误可视化图
        print(f"\n📈 生成学生错误详情图...")
        create_student_mistakes_visual(OUTPUT_JSON_STUDENTS, ROOT_DIRECTORY)
        
        print(f"\n✅ 所有任务已成功完成!")
            
    except FileNotFoundError as e:
        print(f"\n❌ 错误: {e}")
    except Exception as e:
        print(f"\n❌ 意外错误: {e}")
        import traceback
        traceback.print_exc()