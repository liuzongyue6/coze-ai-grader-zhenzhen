"""
多输入输出处理器 - 使用指定的file_id数组调用Coze Workflow流式接口并将结果保存到json文档
后续的json处理交给下游格式
"""
import re
import os
import json
import glob
import logging
from typing import Optional, List
from datetime import datetime
from pathlib import Path
import time  

from cozepy import (
    COZE_CN_BASE_URL,
    Coze,
    TokenAuth,
    Stream,
    WorkflowEvent,
    WorkflowEventType
)

def setup_logger(log_dir="logs"):
    """设置日志记录器"""
    # 创建日志目录
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 创建日志文件名（包含时间戳）
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(log_dir, f"coze_workflow_{timestamp}.log")
    
    # 配置日志格式
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()  # 同时输出到控制台
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"日志系统初始化完成，日志文件: {log_file}")
    return logger

def load_config(config_file_path="config/config.json", logger=None):
    """从配置文件加载workflow ID和API token"""
    try:
        with open(config_file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        if logger:
            logger.info(f"配置文件加载成功: {config_file_path}")
        return config.get("workflow_id"), config.get("api_token")
    except FileNotFoundError:
        error_msg = f"配置文件 {config_file_path} 不存在"
        if logger:
            logger.error(error_msg)
        print(error_msg)
        return None, None
    except json.JSONDecodeError:
        error_msg = f"配置文件 {config_file_path} 格式错误"
        if logger:
            logger.error(error_msg)
        print(error_msg)
        return None, None
    except Exception as e:
        error_msg = f"读取配置文件失败: {str(e)}"
        if logger:
            logger.error(error_msg)
        print(error_msg)
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

def upload_images_and_get_file_ids(coze, image_paths, logger=None):
    """上传图片文件并返回file_ids列表"""
    file_ids = []
    failed_files = []
    try:
        for image_path in image_paths:
            try:
                file = coze.files.upload(file=Path(image_path))
                file_ids.append(file.id)
                print(f"上传成功: {os.path.basename(image_path)} -> file_id: {file.id}")
                if logger:
                    logger.info(f"上传成功: {os.path.basename(image_path)} -> file_id: {file.id}")
            except Exception as e:
                error_msg = f"上传单个文件失败: {os.path.basename(image_path)}, 错误: {str(e)}"
                failed_files.append(os.path.basename(image_path))
                if logger:
                    logger.error(error_msg)
                print(error_msg)
        
        if failed_files and logger:
            logger.warning(f"部分文件上传失败，失败文件列表: {failed_files}")
        
        return file_ids
    except Exception as e:
        error_msg = f"上传图片失败: {str(e)}"
        if logger:
            logger.error(error_msg)
        print(error_msg)
        return []

def scan_wechat_folders(wechat_folder, supported_formats, logger=None):
    """扫描微信作文文件夹，返回{文件夹名: [图片路径列表]}的字典"""
    folders_data = {}
    
    if not os.path.exists(wechat_folder):
        error_msg = f"微信作文文件夹不存在: {wechat_folder}"
        if logger:
            logger.error(error_msg)
        print(error_msg)
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
                if logger:
                    logger.info(f"发现文件夹 '{item}': {len(image_paths)} 张图片")
            else:
                warning_msg = f"文件夹 '{item}' 中没有图片文件"
                print(warning_msg)
                if logger:
                    logger.warning(warning_msg)
    
    return folders_data

def save_raw_response_cache(folder_path: str, folder_name: str, messages: List, timestamp: str, logger=None):
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
    
    cache_file = os.path.join(folder_path, f"{folder_name}_response_cache_{timestamp}.json")
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        print(f"   💾 原始响应已缓存到: {cache_file}")
        if logger:
            logger.info(f"原始响应已缓存到: {cache_file}")
        return cache_file
    except Exception as e:
        error_msg = f"保存缓存失败: {str(e)}, 文件夹: {folder_name}"
        print(f"   ❌ {error_msg}")
        if logger:
            logger.error(error_msg)
        return None

def handle_workflow_iterator(stream: Stream[WorkflowEvent], file_ids: List[str], folder_name: str = None, workflow_id: str = None, logger=None):
    """处理工作流流式事件，只收集数据不保存txt文件"""
    messages = []
    errors = []
    
    for event in stream:
        if event.event == WorkflowEventType.MESSAGE:
            print("got message", event.message)
            messages.append(event.message)
            
        elif event.event == WorkflowEventType.ERROR:
            error_msg = f"工作流错误: {event.error}, 文件夹: {folder_name}"
            print("got error", event.error)
            if logger:
                logger.error(error_msg)
            errors.append(event.error)
            
        elif event.event == WorkflowEventType.INTERRUPT:
            print("got interrupt, resuming...")
            if logger:
                logger.info(f"工作流中断，正在恢复... 文件夹: {folder_name}")
            # 递归处理中断恢复
            sub_messages, sub_errors = handle_workflow_iterator(
                coze.workflows.runs.resume(
                    workflow_id=workflow_id,
                    event_id=event.interrupt.interrupt_data.event_id,
                    resume_data="hey",
                    interrupt_type=event.interrupt.interrupt_data.type,
                ),
                file_ids,
                folder_name,
                workflow_id,
                logger
            )
            messages.extend(sub_messages)
            errors.extend(sub_errors)
    
    return messages, errors

def check_empty_result(messages: List) -> bool:
    """检查工作流返回的结果是否为空"""
    if not messages:
        return True
    
    
    for msg in messages:
        msg_str = str(msg)
        if re.search(r'output_arr_obj.*?:\s*\[\s*\]', msg_str):
            return True
    
    return False  

def process_files_with_workflow_stream(coze, workflow_id, file_ids: List[str], output_folder: str, folder_name: str = None, logger=None, max_retries: int = 3, retry_delay: int = 5):
    """使用工作流流式接口处理指定的文件ID数组，只保存JSON缓存，支持重试机制（包括空结果重试）"""
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                print(f"   🔄 第 {attempt + 1}/{max_retries} 次重试...")
                if logger:
                    logger.info(f"文件夹 {folder_name} 第 {attempt + 1} 次重试")
                time.sleep(retry_delay)  # 重试前等待
            
            print(f"开始流式处理文件数组: {file_ids}")
            print(f"文件数量: {len(file_ids)}")
            if logger:
                logger.info(f"开始处理文件夹: {folder_name}, 文件数量: {len(file_ids)}, file_ids: {file_ids}")
            
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
            messages, errors = handle_workflow_iterator(stream, file_ids, folder_name, workflow_id, logger)
            
            # 检查是否有超时错误
            has_timeout_error = False
            if errors:
                for error in errors:
                    error_str = str(error)
                    if 'timeout' in error_str.lower() or 'error_code=5000' in error_str:
                        has_timeout_error = True
                        break
            
            # 检查是否返回了空结果
            has_empty_result = check_empty_result(messages)
            
            if has_empty_result:
                warning_msg = f"检测到空结果 (output_arr_obj为空)"
                print(f"   ⚠️  {warning_msg}")
                if logger:
                    logger.warning(f"{warning_msg}, 文件夹: {folder_name}, 尝试: {attempt + 1}/{max_retries}")
                
                # 如果还有重试机会，继续重试
                if attempt < max_retries - 1:
                    print(f"   🔄 将在 {retry_delay} 秒后重试...")
                    continue
            
            # 如果有超时错误且还有重试机会，继续重试
            if has_timeout_error and attempt < max_retries - 1:
                warning_msg = f"检测到超时错误，将进行重试 (尝试 {attempt + 1}/{max_retries})"
                print(f"   ⚠️  {warning_msg}")
                if logger:
                    logger.warning(f"{warning_msg}, 文件夹: {folder_name}")
                continue
            
            # 如果有消息返回或者已经是最后一次重试，保存结果
            if messages or attempt == max_retries - 1:
                # 只保存JSON缓存
                if messages and folder_name:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    save_raw_response_cache(output_folder, folder_name, messages, timestamp, logger)
                
                # 如果是空结果且已达到最大重试次数
                if has_empty_result and attempt == max_retries - 1:
                    error_msg = f"达到最大重试次数 ({max_retries})，返回结果仍然为空"
                    print(f"   ❌ {error_msg}")
                    if logger:
                        logger.error(f"{error_msg}, 文件夹: {folder_name}")
                    return False, messages
                
                # 如果是超时错误且已达到最大重试次数
                if has_timeout_error and attempt == max_retries - 1:
                    error_msg = f"达到最大重试次数 ({max_retries})，仍然失败"
                    print(f"   ❌ {error_msg}")
                    if logger:
                        logger.error(f"{error_msg}, 文件夹: {folder_name}")
                    return False, messages
                
                # 成功完成
                if not has_empty_result and not has_timeout_error:
                    print("流式处理完成!")
                    if logger:
                        logger.info(f"文件夹 {folder_name} 流式处理完成，消息数量: {len(messages)}")
                    return True, messages
            
        except Exception as e:
            error_msg = f"流式处理文件数组失败: {str(e)}, 文件夹: {folder_name}"
            
            # 检查是否是超时相关的异常
            is_timeout = 'timeout' in str(e).lower()
            
            if is_timeout and attempt < max_retries - 1:
                print(f"   ⚠️  {error_msg}")
                print(f"   🔄 将在 {retry_delay} 秒后重试 ({attempt + 1}/{max_retries})...")
                if logger:
                    logger.warning(f"{error_msg}, 将进行第 {attempt + 1} 次重试")
                time.sleep(retry_delay)
                continue
            else:
                print(error_msg)
                if logger:
                    logger.error(error_msg)
                return False, []
    
        # 如果所有重试都失败
        error_msg = f"所有重试均失败"
        print(f"   ❌ {error_msg}")
        if logger:
            logger.error(f"{error_msg}, 文件夹: {folder_name}")
        return False, []
        

def process_folders(coze, workflow_id, wechat_folder, supported_formats, logger=None, max_retries: int = 3, retry_delay: int = 5, folder_interval: int = 2):
    """处理微信作文文件夹中的所有子文件夹"""
    print("=== 第一步：扫描文件夹结构 ===")
    if logger:
        logger.info("开始扫描文件夹结构")
    
    folders_data = scan_wechat_folders(wechat_folder, supported_formats, logger)
    
    if not folders_data:
        error_msg = "没有找到包含图片的文件夹"
        print(error_msg)
        if logger:
            logger.error(error_msg)
        return
    
    print(f"\n=== 第二步：逐个处理 {len(folders_data)} 个文件夹 ===")
    if logger:
        logger.info(f"开始处理 {len(folders_data)} 个文件夹")
    
    successful_folders = []
    failed_folders = []
    
    for idx, (folder_name, image_paths) in enumerate(folders_data.items(), 1):
        print(f"\n📁 [{idx}/{len(folders_data)}] 正在处理文件夹: {folder_name}")
        print(f"   图片文件: {[os.path.basename(p) for p in image_paths]}")
        if logger:
            logger.info(f"[{idx}/{len(folders_data)}] 开始处理文件夹: {folder_name}, 图片数量: {len(image_paths)}")
        
        # 上传图片获取file_ids
        print(f"   ⬆️  正在上传 {len(image_paths)} 张图片...")
        file_ids = upload_images_and_get_file_ids(coze, image_paths, logger)
        
        if not file_ids:
            error_msg = f"文件夹 '{folder_name}' 图片上传失败，跳过处理"
            print(f"   ❌ {error_msg}")
            if logger:
                logger.error(error_msg)
            failed_folders.append(folder_name)
            continue
        
        folder_path = os.path.join(wechat_folder, folder_name)
        
        print(f"   🔄 开始流式处理...")
        print(f"   📄 只保存JSON缓存文件")
        
        # 处理这个文件夹的文件，只保存JSON，传递重试参数
        success, messages = process_files_with_workflow_stream(
            coze, 
            workflow_id, 
            file_ids, 
            folder_path, 
            folder_name, 
            logger,
            max_retries=max_retries,
            retry_delay=retry_delay
        )
        
        if success:
            print(f"   ✅ 文件夹 '{folder_name}' 处理完成!")
            if messages:
                print(f"   💾 JSON缓存已保存")
            successful_folders.append(folder_name)
        else:
            error_msg = f"文件夹 '{folder_name}' 处理失败"
            print(f"   ❌ {error_msg}")
            if logger:
                logger.error(error_msg)
            failed_folders.append(folder_name)
        
        print(f"   📋 进度: {idx}/{len(folders_data)} 个文件夹已处理")
        
        # 在处理下一个文件夹前添加延迟（最后一个文件夹不需要延迟）
        if idx < len(folders_data) and folder_interval > 0:
            print(f"   ⏱️  等待 {folder_interval} 秒后处理下一个文件夹...")
            if logger:
                logger.info(f"文件夹间隔延迟 {folder_interval} 秒")
            time.sleep(folder_interval)
    
    # 输出最终统计
    if logger:
        logger.info(f"处理完成! 成功: {len(successful_folders)}, 失败: {len(failed_folders)}")
        if successful_folders:
            logger.info(f"成功处理的文件夹: {successful_folders}")
        if failed_folders:
            logger.error(f"失败的文件夹: {failed_folders}")

def main():
    """主函数"""
    print("=== 多文件流式处理器启动 ===")
    
    # 初始化日志系统
    logger = setup_logger()
    logger.info("=== 多文件流式处理器启动 ===")
    
    # ======= 配置设置区域 =======
    config_file = "config/config.translation.json"
    
    folder_tobe_process = r"E:\zhenzhen_eng_coze\example\高一_11_reduced_debug"
    
    # 支持的图片格式 - 可以根据需要添加或删除格式
    supported_formats = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
    
    # 重试配置
    max_retries = 3  # 最大重试次数
    retry_delay = 3  # 重试延迟（秒）
    
    # 文件夹处理间隔配置
    folder_interval = 1  # 每个文件夹处理完成后的等待时间（秒），设为0则不等待
    
    print(f"配置文件路径: {config_file}")
    print(f"微信作文文件夹: {folder_tobe_process}")
    print(f"支持的图片格式: {supported_formats}")
    print(f"最大重试次数: {max_retries}")
    print(f"重试延迟: {retry_delay}秒")
    print(f"文件夹处理间隔: {folder_interval}秒")
    logger.info(f"配置文件路径: {config_file}")
    logger.info(f"微信作文文件夹: {folder_tobe_process}")
    logger.info(f"支持的图片格式: {supported_formats}")
    logger.info(f"最大重试次数: {max_retries}, 重试延迟: {retry_delay}秒, 文件夹间隔: {folder_interval}秒")
    # ======= 配置设置区域结束 =======
    
    # 检查配置文件
    workflow_id, api_token = load_config(config_file, logger)
    
    if not workflow_id or not api_token:
        error_msg = f"错误: 请检查配置文件 {config_file} 是否正确设置了 workflow_id 和 api_token"
        print(error_msg)
        logger.error(error_msg)
        print("配置文件格式示例:")
        print("""{
    "workflow_id": "your_workflow_id_here",
    "api_token": "your_api_token_here"
}""")
        return
    
    print(f"工作流ID: {workflow_id}")
    print(f"API Token: {api_token[:10]}***{api_token[-10:] if len(api_token) > 20 else '***'}")
    logger.info(f"工作流ID: {workflow_id}")
    logger.info("API Token已加载")
    
    # 初始化Coze客户端
    try:
        coze = Coze(
            auth=TokenAuth(token=api_token), 
            base_url=get_coze_api_base()
        )
        print("Coze客户端初始化成功")
        logger.info("Coze客户端初始化成功")
    except Exception as e:
        error_msg = f"Coze客户端初始化失败: {str(e)}"
        print(error_msg)
        logger.error(error_msg)
        return
    
    # 开始处理
    process_folders(
        coze, 
        workflow_id, 
        folder_tobe_process, 
        supported_formats, 
        logger,
        max_retries=max_retries,
        retry_delay=retry_delay,
        folder_interval=folder_interval
    )
    logger.info("=== 所有处理完成 ===")

if __name__ == "__main__":
    main()
