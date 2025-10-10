import os
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Set, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

# ==========================================
# DATA MODELS (For Better Type Safety)
# ==========================================

@dataclass
class MistakeEntry:
    """Data model for a single mistake entry."""
    chinese_txt: str
    mistake: str
    mistake_flag: str
    comment: str
    std_input: str
    thought: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MistakeEntry':
        """Create MistakeEntry from dictionary."""
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
    """Data model for student-specific mistake."""
    student_name: str
    mistake: str
    comment: str
    std_input: str
    file_path: str

# ==========================================
# LAYER 1: File I/O & Parsing (Low-Level)
# ==========================================

def parse_log_content(file_path: Path) -> Optional[List[Dict[str, Any]]]:
    """
    Parses a log file to extract and load the inner JSON data.
    Handles escaped quotes and apostrophes properly.
    
    Args:
        file_path: Path to the JSON log file
        
    Returns:
        List of dictionaries containing output_arr_obj data, or None if parsing fails
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()
        
        # First, load the outer JSON structure
        outer_data = json.loads(raw_content)
        
        # Navigate to the raw_content field
        if 'raw_messages' not in outer_data or len(outer_data['raw_messages']) == 0:
            print(f"Warning: No raw_messages found in {file_path}")
            return None
        
        raw_message = outer_data['raw_messages'][0]['raw_content']
        
        # Extract the content='...' part using regex
        match = re.search(r"content='(\{.*\})'", raw_message, re.DOTALL)
        if not match:
            print(f"Warning: No valid 'content={{...}}' format found in {file_path}")
            return None
        
        json_string = match.group(1)
        
        # The key fix: use decode with 'unicode_escape' for the escape sequences
        # But we need to be careful with Chinese characters
        # Instead, let's use a different approach: replace the escape sequences correctly
        
        # Replace the problematic escape sequences
        # The string has \' which is not valid in JSON (JSON only recognizes \")
        cleaned_string = json_string.replace("\\'", "'")
        
        # Parse the cleaned JSON
        data = json.loads(cleaned_string)
        
        return data.get("output_arr_obj")

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file: {file_path}")
        print(f"       Parser failed with message: {e}")
        # Debug: show the problematic part
        try:
            if 'json_string' in locals():
                error_pos = e.pos if hasattr(e, 'pos') else 0
                snippet_start = max(0, error_pos - 50)
                snippet_end = min(len(json_string), error_pos + 50)
                print(f"       Near position {error_pos}:")
                print(f"       ...{json_string[snippet_start:snippet_end]}...")
        except:
            pass
        return None
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while processing {file_path}: {e}")
        import traceback
        traceback.print_exc()
    
    return None

def find_json_files(root_folder: Path) -> List[Path]:
    """
    Recursively finds all .json files in the given folder.
    
    Args:
        root_folder: Root directory to search
        
    Returns:
        List of Path objects pointing to JSON files
    """
    return list(root_folder.rglob("*.json"))

# ==========================================
# LAYER 2: Data Extraction (Business Logic)
# ==========================================

def extract_mistakes_from_data(
    parsed_data: List[Dict[str, Any]], 
    target_flag: str = "翻得不好"
) -> List[MistakeEntry]:
    """
    Extracts mistakes where the flag matches the target.
    
    Args:
        parsed_data: Parsed JSON data from log file
        target_flag: Mistake flag to filter (default: "翻得不好")
        
    Returns:
        List of MistakeEntry objects matching the target flag
    """
    mistakes = []
    if not parsed_data:
        return mistakes
        
    for item in parsed_data:
        if item.get("mistake_flag") == target_flag:
            try:
                mistakes.append(MistakeEntry.from_dict(item))
            except Exception as e:
                print(f"Warning: Failed to parse mistake entry: {e}")
    
    return mistakes

def extract_all_chinese_sentences(parsed_data: List[Dict[str, Any]]) -> Set[str]:
    """
    Extracts all unique Chinese sentences from parsed data.
    
    Args:
        parsed_data: Parsed JSON data from log file
        
    Returns:
        Set of unique Chinese sentences
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
# LAYER 3: Baseline Management
# ==========================================

def establish_baseline_sentences(baseline_folder_path: Path) -> Set[str]:
    """
    Extracts unique Chinese sentences from the baseline folder.
    This creates a reference set for matching other students' work.
    
    Args:
        baseline_folder_path: Path to the baseline folder (1st student folder)
        
    Returns:
        Set of unique Chinese sentences that serve as the baseline
    """
    baseline_sentences = set()
    json_files = find_json_files(baseline_folder_path)
    
    print(f"Processing baseline folder: {baseline_folder_path.name}")
    print(f"Found {len(json_files)} JSON file(s)")
    
    for file_path in json_files:
        parsed_data = parse_log_content(file_path)
        if parsed_data:
            sentences = extract_all_chinese_sentences(parsed_data)
            baseline_sentences.update(sentences)
            print(f"  - Extracted {len(sentences)} sentences from {file_path.name}")
    
    print(f"✓ Established baseline with {len(baseline_sentences)} unique sentences.\n")
    return baseline_sentences

# ==========================================
# LAYER 4: Mistake Summary & Statistics
# ==========================================

def summarize_student_mistakes(
    root_directory: str, 
    baseline_folder_name: str
) -> Tuple[Dict[str, List[StudentMistake]], Set[str]]:
    """
    Orchestrates the process of finding, matching, and summarizing mistakes.
    
    Args:
        root_directory: Root path containing all student folders
        baseline_folder_name: Name of the folder to use as baseline
        
    Returns:
        Tuple of (mistake_summary, baseline_sentences)
        - mistake_summary: Dict mapping chinese_txt to list of StudentMistake objects
        - baseline_sentences: Set of baseline Chinese sentences
    """
    root_path = Path(root_directory)
    baseline_path = root_path / baseline_folder_name
    
    # Validate baseline folder exists
    if not baseline_path.is_dir():
        raise FileNotFoundError(
            f"Baseline folder '{baseline_folder_name}' not found in '{root_directory}'"
        )

    # Step 1: Establish baseline from 1st folder
    baseline_sentences = establish_baseline_sentences(baseline_path)
    
    # Step 2: Process all student folders
    mistake_summary = defaultdict(list)
    
    for student_folder_path in sorted(root_path.iterdir()):
        # Skip non-directories and baseline folder
        if not student_folder_path.is_dir():
            continue
            
        student_name = student_folder_path.name
        print(f"Processing student: {student_name}...")
        
        # Find and process all JSON files for this student
        student_json_files = find_json_files(student_folder_path)
        print(f"  - Found {len(student_json_files)} JSON file(s)")
        
        mistakes_count = 0
        for file_path in student_json_files:
            parsed_data = parse_log_content(file_path)
            mistakes_found = extract_mistakes_from_data(parsed_data)
            
            for mistake_entry in mistakes_found:
                sentence = mistake_entry.chinese_txt.strip()
                
                # Only record if sentence is in baseline
                if sentence in baseline_sentences:
                    mistake_summary[sentence].append(StudentMistake(
                        student_name=student_name,
                        mistake=mistake_entry.mistake,
                        comment=mistake_entry.comment,
                        std_input=mistake_entry.std_input,
                        file_path=str(file_path.name)
                    ))
                    mistakes_count += 1
                else:
                    print(f"  ⚠ Warning: Sentence not in baseline: '{sentence[:40]}...'")
        
        print(f"  ✓ Recorded {mistakes_count} mistake(s)\n")

    return dict(mistake_summary), baseline_sentences

# ==========================================
# LAYER 5: Statistics & Reporting
# ==========================================

def generate_statistics_report(
    mistake_summary: Dict[str, List[StudentMistake]]
) -> Dict[str, Any]:
    """
    Generates comprehensive statistics from the mistake summary.
    
    Args:
        mistake_summary: Dictionary mapping chinese_txt to student mistakes
        
    Returns:
        Dictionary containing various statistics:
        - total_unique_sentences: Number of unique sentences with mistakes
        - total_mistake_instances: Total count of all mistake occurrences
        - mistakes_per_student: Count of mistakes for each student
        - sentences_with_most_mistakes: Sentences sorted by frequency
        - mistake_rate: Percentage of sentences with mistakes
    """
    stats = {
        "total_unique_sentences": len(mistake_summary),
        "total_mistake_instances": sum(len(students) for students in mistake_summary.values()),
        "mistakes_per_student": defaultdict(int),
        "sentences_with_most_mistakes": [],
        "students_processed": set()
    }
    
    # Count mistakes per student
    for sentence, student_mistakes in mistake_summary.items():
        for student_mistake in student_mistakes:
            stats["mistakes_per_student"][student_mistake.student_name] += 1
            stats["students_processed"].add(student_mistake.student_name)
    
    # Sort sentences by mistake frequency
    sentence_freq = [
        (sentence, len(students)) 
        for sentence, students in mistake_summary.items()
    ]
    stats["sentences_with_most_mistakes"] = sorted(
        sentence_freq, 
        key=lambda x: x[1], 
        reverse=True
    )
    
    # Convert set to count
    stats["total_students"] = len(stats["students_processed"])
    del stats["students_processed"]
    
    return dict(stats)

def export_summary_to_json(
    mistake_summary: Dict[str, List[StudentMistake]], 
    output_path: str,
    include_metadata: bool = True
) -> None:
    """
    Exports mistake summary to a JSON file.
    
    Args:
        mistake_summary: Dictionary of mistakes to export
        output_path: Path to save the JSON file
        include_metadata: Whether to include metadata like timestamp
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
    
    print(f"✓ Exported summary to: {output_path}")

def export_student_mistakes_json(
    mistake_summary: Dict[str, List[StudentMistake]], 
    baseline_sentences: Set[str],
    output_path: str
) -> None:
    """
    Exports mistake summary organized by student for each Chinese sentence.
    
    Format:
    {
      "chinese_sentence": {
        "student_name": "mistake_text",
        ...
      },
      ...
    }
    
    Args:
        mistake_summary: Dictionary mapping chinese_txt to student mistakes
        baseline_sentences: Set of all baseline sentences
        output_path: Path to save the JSON file
    """
    export_data = {}
    
    # Process each sentence in the baseline
    for sentence in sorted(baseline_sentences):
        student_mistakes_dict = {}
        
        # Get all mistakes for this sentence
        if sentence in mistake_summary:
            for student_mistake in mistake_summary[sentence]:
                student_mistakes_dict[student_mistake.student_name] = student_mistake.mistake
        
        # Only include sentences that have mistakes
        if student_mistakes_dict:
            export_data[sentence] = student_mistakes_dict
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Exported student mistakes to: {output_path}")


def export_statistics_json(
    mistake_summary: Dict[str, List[StudentMistake]], 
    baseline_sentences: Set[str],
    total_students: int,
    output_path: str
) -> None:
    """
    Exports statistical summary for each Chinese sentence without student names.
    
    Format:
    {
      "chinese_sentence": {
        "total_submissions": 10,
        "mistake_count": 3,
        "mistake_rate": "30.00%",
        "unique_mistakes": ["mistake1", "mistake2", ...]
      },
      ...
    }
    
    Args:
        mistake_summary: Dictionary mapping chinese_txt to student mistakes
        baseline_sentences: Set of all baseline sentences
        total_students: Total number of students processed
        output_path: Path to save the JSON file
    """
    export_data = {}
    
    # Process each sentence in the baseline
    for sentence in sorted(baseline_sentences):
        # Collect all unique mistakes for this sentence (no student names)
        unique_mistakes = set()
        mistake_count = 0
        
        if sentence in mistake_summary:
            mistake_count = len(mistake_summary[sentence])
            for student_mistake in mistake_summary[sentence]:
                if student_mistake.mistake:  # Only add non-empty mistakes
                    unique_mistakes.add(student_mistake.mistake)
        
        # Calculate mistake rate
        mistake_rate = (mistake_count / total_students * 100) if total_students > 0 else 0
        
        export_data[sentence] = {
            "total_submissions": total_students,
            "mistake_count": mistake_count,
            "mistake_rate": f"{mistake_rate:.2f}%",
            "unique_mistakes": sorted(list(unique_mistakes))  # Sort for consistency
        }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Exported statistics to: {output_path}")


# ==========================================
# MAIN EXECUTION
# ==========================================

if __name__ == '__main__':
    # Configuration
    ROOT_DIRECTORY = r"E:\zhenzhen_eng_coze\example\高一_翻译_10_4_reduced_example"
    BASELINE_FOLDER = "于子航"
    OUTPUT_JSON_STUDENTS = os.path.join(ROOT_DIRECTORY, "1_student_mistakes.json")
    OUTPUT_JSON_STATISTICS = os.path.join(ROOT_DIRECTORY, "2_statistics_summary.json")

    try:
        print("=" * 60)
        print("STUDENT MISTAKE SUMMARY SYSTEM")
        print("=" * 60)
        print()
        
        # Run the summarization process
        final_summary, baseline_sentences = summarize_student_mistakes(
            ROOT_DIRECTORY, 
            BASELINE_FOLDER
        )
        
        # Display results
        print("=" * 60)
        print("FINAL MISTAKE SUMMARY")
        print("=" * 60)
        
        if final_summary:
            for sentence, student_mistakes in final_summary.items():
                print(f"\n📝 Chinese Text: {sentence}")
                for sm in student_mistakes:
                    print(f"   └─ Student: {sm.student_name}")
                    print(f"      Mistake: {sm.mistake}")
                    print(f"      Comment: {sm.comment[:60]}...")
            
            # Generate and display statistics
            stats = generate_statistics_report(final_summary)
            print("\n" + "=" * 60)
            print("STATISTICS REPORT")
            print("=" * 60)
            print(f"Total unique sentences with mistakes: {stats['total_unique_sentences']}")
            print(f"Total mistake instances: {stats['total_mistake_instances']}")
            print(f"Total students processed: {stats['total_students']}")
            print(f"\n📊 Mistakes per student:")
            for student, count in sorted(stats['mistakes_per_student'].items()):
                print(f"   • {student}: {count}")
            print(f"\n🔥 Top 5 sentences with most mistakes:")
            for sentence, count in stats['sentences_with_most_mistakes'][:5]:
                print(f"   • ({count}x) {sentence[:50]}...")
            
            # Export to JSON files
            print("\n" + "=" * 60)
            print("EXPORTING JSON FILES")
            print("=" * 60)
            
            # Export 1st JSON: Student-focused
            export_student_mistakes_json(
                final_summary, 
                baseline_sentences,
                OUTPUT_JSON_STUDENTS
            )
            
            # Export 2nd JSON: Statistics-focused
            export_statistics_json(
                final_summary, 
                baseline_sentences,
                stats['total_students'],
                OUTPUT_JSON_STATISTICS
            )
            
        else:
            print("No mistakes found matching the baseline.")
            
    except FileNotFoundError as e:
        print(f"\n❌ FATAL ERROR: {e}")
        print("Please ensure the ROOT_DIRECTORY and BASELINE_FOLDER are correct.")
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()