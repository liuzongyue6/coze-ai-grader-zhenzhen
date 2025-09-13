"""
多文件处理器 - 使用指定的file_id数组调用Coze Workflow流式接口并将结果保存到TXT文档
"""

import os
import json
import glob
from typing import Optional, List
from datetime import datetime
from pathlib import Path

from cozepy import (
    COZE_CN_BASE_URL,
    Coze,
    TokenAuth,
    Stream,
    WorkflowEvent,
    WorkflowEventType
)

def load_config(config_file_path="config/config.json"):
    """从配置文件加载workflow ID和API token"""
    try:
        with open(config_file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config.get("workflow_id"), config.get("api_token")
    except FileNotFoundError:
        print(f"配置文件 {config_file_path} 不存在")
        return None, None
    except json.JSONDecodeError:
        print(f"配置文件 {config_file_path} 格式错误")
        return None, None
    except Exception as e:
        print(f"读取配置文件失败: {str(e)}")
        return None, None

def get_coze_api_base() -> str:
    """获取Coze API基础URL"""
    coze_api_base = os.getenv("COZE_API_BASE")
    if coze_api_base:
        return coze_api_base
    return COZE_CN_BASE_URL

def get_image_files_in_folder(folder_path, supported_formats):
    """获取文件夹中所有图片文件路径"""
    image_paths = []
    for fmt in supported_formats:
        image_paths.extend(glob.glob(os.path.join(folder_path, f'*{fmt}'), recursive=False))
    return sorted(image_paths)

def upload_images_and_get_file_ids(coze, image_paths):
    """上传图片文件并返回file_ids列表"""
    file_ids = []
    try:
        for image_path in image_paths:
            file = coze.files.upload(file=Path(image_path))
            file_ids.append(file.id)
            print(f"上传成功: {os.path.basename(image_path)} -> file_id: {file.id}")
        return file_ids
    except Exception as e:
        print(f"上传图片失败: {str(e)}")
        return []

def scan_wechat_folders(wechat_folder, supported_formats):
    """扫描微信作文文件夹，返回{文件夹名: [图片路径列表]}的字典"""
    folders_data = {}
    
    if not os.path.exists(wechat_folder):
        print(f"微信作文文件夹不存在: {wechat_folder}")
        return folders_data
    
    # 遍历所有子文件夹
    for item in os.listdir(wechat_folder):
        item_path = os.path.join(wechat_folder, item)
        if os.path.isdir(item_path):
            # 获取文件夹中的图片文件
            image_paths = get_image_files_in_folder(item_path, supported_formats)
            if image_paths:
                folders_data[item] = image_paths
                print(f"发现文件夹 '{item}': {len(image_paths)} 张图片")
            else:
                print(f"文件夹 '{item}' 中没有图片文件")
    
    return folders_data

def save_raw_response_cache(folder_path: str, folder_name: str, messages: List, timestamp: str):
    """保存原始API响应到JSON缓存文件"""
    cache_data = {
        "folder_name": folder_name,
        "timestamp": timestamp,
        "total_messages": len(messages),
        "raw_messages": []
    }
    
    for i, msg in enumerate(messages):
        cache_data["raw_messages"].append({
            "message_index": i + 1,
            "raw_content": str(msg),
            "timestamp": datetime.now().isoformat()
        })
    
    # 保存到JSON缓存文件
    cache_file = os.path.join(folder_path, f"raw_response_cache_{folder_name}_{timestamp}.json")
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        print(f"   💾 原始响应已缓存到: {cache_file}")
        return cache_file
    except Exception as e:
        print(f"   ❌ 保存缓存失败: {str(e)}")
        return None

def handle_workflow_iterator(stream: Stream[WorkflowEvent], output_file, file_ids: List[str], folder_name: str = None, workflow_id: str = None):
    """处理工作流流式事件并保存到文件"""
    messages = []
    errors = []
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=== 作文批改结果 (流式处理) ===\n\n")
        f.write(f"处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        if folder_name:
            f.write(f"文件夹名称: {folder_name}\n")
        f.write(f"文件ID数组: {', '.join(file_ids)}\n")
        f.write(f"文件数量: {len(file_ids)}\n")
        f.write(f"工作流ID: {workflow_id}\n\n")
        f.write("=== 处理过程 ===\n")
        
        for event in stream:
            if event.event == WorkflowEventType.MESSAGE:
                print("got message", event.message)
                f.write(f"[MESSAGE] {event.message}\n")
                f.flush()  # 实时写入文件
                messages.append(event.message)
                
            elif event.event == WorkflowEventType.ERROR:
                print("got error", event.error)
                f.write(f"[ERROR] {event.error}\n")
                f.flush()
                errors.append(event.error)
                
            elif event.event == WorkflowEventType.INTERRUPT:
                print("got interrupt, resuming...")
                f.write(f"[INTERRUPT] 工作流被中断，正在恢复...\n")
                f.flush()
                # 递归处理中断恢复
                handle_workflow_iterator(
                    coze.workflows.runs.resume(
                        workflow_id=workflow_id,
                        event_id=event.interrupt.interrupt_data.event_id,
                        resume_data="hey",
                        interrupt_type=event.interrupt.interrupt_data.type,
                    ),
                    output_file,
                    file_ids,
                    folder_name,
                    workflow_id
                )
        
        # 写入最终总结
        f.write(f"\n=== 处理完成总结 ===\n")
        f.write(f"总消息数: {len(messages)}\n")
        f.write(f"总错误数: {len(errors)}\n")
        
        if messages:
            f.write(f"\n=== 所有消息 ===\n")
            for i, msg in enumerate(messages, 1):
                f.write(f"消息 {i}: {msg}\n")
        
        if errors:
            f.write(f"\n=== 所有错误 ===\n")
            for i, err in enumerate(errors, 1):
                f.write(f"错误 {i}: {err}\n")
    
    # 保存原始响应缓存
    if messages and folder_name:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        folder_path = os.path.dirname(output_file)
        save_raw_response_cache(folder_path, folder_name, messages, timestamp)
    
    return messages

def process_files_with_workflow_stream(coze, workflow_id, file_ids: List[str], output_file, folder_name: str = None):
    """使用工作流流式接口处理指定的文件ID数组"""
    try:
        print(f"开始流式处理文件数组: {file_ids}")
        print(f"文件数量: {len(file_ids)}")
        
        # 根据参考文档格式创建文件数组参数
        file_array = []
        for file_id in file_ids:
            file_array.append(json.dumps({"file_id": file_id}))
        
        parameters = {
            "input": file_array
        }
        
        print(f"使用文件数组参数格式: {parameters}")
        
        # 创建流式工作流运行
        stream = coze.workflows.runs.stream(
            workflow_id=workflow_id,
            parameters=parameters
        )
        
        # 处理流式事件
        messages = handle_workflow_iterator(stream, output_file, file_ids, folder_name, workflow_id)
        
        print("流式处理完成!")
        return True, messages
        
    except Exception as e:
        error_msg = f"流式处理文件数组失败: {str(e)}"
        print(error_msg)
        
        # 将错误也写入文件
        try:
            with open(output_file, 'a', encoding='utf-8') as f:
                f.write(f"\n=== 处理错误 ===\n")
                f.write(f"{error_msg}\n")
        except:
            pass
            
        return False, []

def process_wechat_folders(coze, workflow_id, wechat_folder, supported_formats):
    """处理微信作文文件夹中的所有子文件夹"""
    print("=== 第一步：扫描文件夹结构 ===")
    folders_data = scan_wechat_folders(wechat_folder, supported_formats)
    
    if not folders_data:
        print("没有找到包含图片的文件夹")
        return
    
    print(f"\n=== 第二步：逐个处理 {len(folders_data)} 个文件夹 ===")
    
    for idx, (folder_name, image_paths) in enumerate(folders_data.items(), 1):
        print(f"\n📁 [{idx}/{len(folders_data)}] 正在处理文件夹: {folder_name}")
        print(f"   图片文件: {[os.path.basename(p) for p in image_paths]}")
        
        # 上传图片获取file_ids
        print(f"   ⬆️  正在上传 {len(image_paths)} 张图片...")
        file_ids = upload_images_and_get_file_ids(coze, image_paths)
        
        if not file_ids:
            print(f"   ❌ 文件夹 '{folder_name}' 图片上传失败，跳过处理")
            continue
        
        # 生成输出文件名并保存到对应的文件夹中
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"批改结果_{folder_name}_{timestamp}.txt"
        folder_path = os.path.join(wechat_folder, folder_name)
        output_path = os.path.join(folder_path, output_file)
        
        print(f"   🔄 开始流式处理...")
        print(f"   📄 输出文件: {output_file}")
        
        # 处理这个文件夹的文件
        success, messages = process_files_with_workflow_stream(coze, workflow_id, file_ids, output_path, folder_name)
        
        if success:
            print(f"   ✅ 文件夹 '{folder_name}' 处理完成!")
            print(f"   💾 结果已保存到: {output_path}")
            if messages:
                print(f"   🗂️  原始响应已缓存到JSON文件")
        else:
            print(f"   ❌ 文件夹 '{folder_name}' 处理失败")
        
        print(f"   📋 进度: {idx}/{len(folders_data)} 个文件夹已处理")

def main():
    """主函数"""
    print("=== 多文件流式处理器启动 ===")
    
    # ======= 配置设置区域 =======
    config_file = "config/config.translation.json"
    
    wechat_folder = r"E:\真真英语\作文\test\translation"
    
    # 支持的图片格式 - 可以根据需要添加或删除格式
    supported_formats = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
    
    print(f"配置文件路径: {config_file}")
    print(f"微信作文文件夹: {wechat_folder}")
    print(f"支持的图片格式: {supported_formats}")
    # ======= 配置设置区域结束 =======
    
    # 检查配置文件
    workflow_id, api_token = load_config(config_file)
    
    if not workflow_id or not api_token:
        print(f"错误: 请检查配置文件 {config_file} 是否正确设置了 workflow_id 和 api_token")
        print("配置文件格式示例:")
        print("""{
    "workflow_id": "your_workflow_id_here",
    "api_token": "your_api_token_here"
}""")
        return
    
    print(f"工作流ID: {workflow_id}")
    print(f"API Token: {api_token[:10]}***{api_token[-10:] if len(api_token) > 20 else '***'}")
    
    # 初始化Coze客户端
    try:
        coze = Coze(
            auth=TokenAuth(token=api_token), 
            base_url=get_coze_api_base()
        )
        print("Coze客户端初始化成功")
    except Exception as e:
        print(f"Coze客户端初始化失败: {str(e)}")
        return
    
    # 开始处理
    process_wechat_folders(coze, workflow_id, wechat_folder, supported_formats)

if __name__ == "__main__":
    main()
