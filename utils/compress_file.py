"""
图片压缩工具 - 将指定文件夹中的图片压缩到指定大小，保存到新文件夹
"""

import os
import glob
from PIL import Image
import tempfile
import shutil
from pathlib import Path

def get_file_size_mb(file_path):
    """获取文件大小（MB）"""
    return os.path.getsize(file_path) / (1024 * 1024)

def compress_image(image_path, output_path, target_size_bytes, quality_start=95):
    """
    压缩单张图片到目标大小，保存到指定路径
    """
    print(f"正在压缩: {os.path.basename(image_path)}")
    
    # 获取原始文件大小
    original_size = os.path.getsize(image_path)
    original_size_mb = original_size / (1024 * 1024)
    
    print(f"  原始大小: {original_size_mb:.2f} MB")
    
    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)
    
    # 如果文件已经小于目标大小，直接复制
    if original_size <= target_size_bytes:
        print(f"  文件已经小于目标大小，直接复制")
        shutil.copy2(image_path, output_path)
        return True, original_size
    
    try:
        # 打开图片
        with Image.open(image_path) as img:
            # 转换为RGB（如果是RGBA）
            if img.mode in ('RGBA', 'LA'):
                img = img.convert('RGB')
            
            # 计算初始压缩参数
            quality = quality_start
            width, height = img.size
            
            # 如果图片很大，先缩小尺寸
            max_dimension = 2048  # 最大尺寸
            if max(width, height) > max_dimension:
                ratio = max_dimension / max(width, height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                print(f"  调整尺寸: {width}x{height} -> {new_width}x{new_height}")
            
            # 创建临时文件
            temp_fd, temp_path = tempfile.mkstemp(suffix='.jpg', dir=output_dir)
            os.close(temp_fd)  # 关闭文件描述符
            
            # 逐步降低质量直到达到目标大小
            while quality > 10:
                img.save(temp_path, 'JPEG', quality=quality, optimize=True)
                current_size = os.path.getsize(temp_path)
                
                if current_size <= target_size_bytes:
                    # 达到目标大小，移动到最终位置
                    if os.path.exists(output_path):
                        os.remove(output_path)
                    shutil.move(temp_path, output_path)
                    
                    final_size_mb = current_size / (1024 * 1024)
                    print(f"  压缩完成: {final_size_mb:.2f} MB (质量: {quality})")
                    return True, current_size
                
                quality -= 5
            
            # 如果质量降到很低仍然太大，进一步缩小尺寸
            current_width, current_height = img.size
            while quality <= 10 and current_width > 600:
                ratio = 0.85
                new_width = int(current_width * ratio)
                new_height = int(current_height * ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                current_width, current_height = new_width, new_height
                
                img.save(temp_path, 'JPEG', quality=25, optimize=True)
                current_size = os.path.getsize(temp_path)
                
                if current_size <= target_size_bytes:
                    # 移动到最终位置
                    if os.path.exists(output_path):
                        os.remove(output_path)
                    shutil.move(temp_path, output_path)
                    
                    final_size_mb = current_size / (1024 * 1024)
                    print(f"  压缩完成: {final_size_mb:.2f} MB (尺寸: {new_width}x{new_height})")
                    return True, current_size
            
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            print(f"  警告: 无法将图片压缩到目标大小")
            return False, original_size
            
    except Exception as e:
        print(f"  错误: 压缩失败 - {str(e)}")
        return False, original_size

def get_all_image_files(root_folder, supported_formats):
    """获取所有子文件夹中的图片文件"""
    image_files = []
    
    for root, dirs, files in os.walk(root_folder):
        for file in files:
            if file.lower().endswith(supported_formats):
                file_path = os.path.join(root, file)
                image_files.append(file_path)
    
    return image_files

def main():
    """主函数"""
    # 配置参数 - 用户可以在这里修改
    source_folder = input("请输入源文件夹路径 (或直接回车使用默认): ").strip()
    if not source_folder:
        source_folder = r"test"
    
    # 创建目标文件夹名称（原文件夹_reduced）
    source_folder_name = os.path.basename(source_folder.rstrip(os.sep))
    parent_dir = os.path.dirname(source_folder)
    target_folder = os.path.join(parent_dir, f"{source_folder_name}_reduced")
    
    # 获取目标大小
    target_size_input = input("请输入目标大小(MB) (或直接回车使用默认0.5MB): ").strip()
    if target_size_input:
        try:
            target_size_mb = float(target_size_input)
        except ValueError:
            print("无效的数字，使用默认值0.5MB")
            target_size_mb = 0.5
    else:
        target_size_mb = 0.5
    
    target_size_bytes = int(target_size_mb * 1024 * 1024)
    supported_formats = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
    
    print(f"\n图片压缩工具")
    print(f"源文件夹: {source_folder}")
    print(f"目标文件夹: {target_folder}")
    print(f"目标大小: {target_size_mb} MB")
    print("-" * 50)
    
    # 检查源文件夹是否存在
    if not os.path.exists(source_folder):
        print(f"错误: 源文件夹不存在 - {source_folder}")
        return
    
    # 创建目标文件夹
    os.makedirs(target_folder, exist_ok=True)
    print(f"已创建目标文件夹: {target_folder}")
    
    # 获取所有图片文件
    image_files = get_all_image_files(source_folder, supported_formats)
    
    if not image_files:
        print("未找到图片文件")
        return
    
    print(f"找到 {len(image_files)} 个图片文件")
    
    # 询问用户确认
    confirm = input("\n确认开始压缩吗？(输入 'y' 或 'yes' 继续): ")
    if confirm.lower() not in ['y', 'yes']:
        print("操作已取消")
        return
    
    print("-" * 50)
    
    # 统计信息
    total_original_size = 0
    total_compressed_size = 0
    success_count = 0
    
    # 逐个压缩图片
    for i, image_path in enumerate(image_files, 1):
        # 计算相对路径
        rel_path = os.path.relpath(image_path, source_folder)
        output_path = os.path.join(target_folder, rel_path)
        
        # 确保输出文件是jpg格式
        output_path = os.path.splitext(output_path)[0] + '.jpg'
        
        folder_name = os.path.dirname(image_path).split(os.sep)[-1]
        print(f"\n[{i}/{len(image_files)}] 处理文件夹: {folder_name}")
        
        original_size = os.path.getsize(image_path)
        total_original_size += original_size
        
        success, final_size = compress_image(image_path, output_path, target_size_bytes)
        
        if success:
            success_count += 1
        
        total_compressed_size += final_size
    
    # 输出统计信息
    print("\n" + "=" * 50)
    print("压缩完成统计:")
    print(f"处理文件数: {len(image_files)}")
    print(f"成功压缩: {success_count}")
    print(f"原始总大小: {total_original_size / (1024 * 1024):.2f} MB")
    print(f"压缩后总大小: {total_compressed_size / (1024 * 1024):.2f} MB")
    if total_original_size > 0:
        reduction_percent = (1 - total_compressed_size / total_original_size) * 100
        print(f"节省空间: {(total_original_size - total_compressed_size) / (1024 * 1024):.2f} MB")
        print(f"压缩率: {reduction_percent:.1f}%")
    print(f"压缩文件保存在: {target_folder}")
    print("=" * 50)

if __name__ == "__main__":
    main()