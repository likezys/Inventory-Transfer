import datetime
import random
import time
import os
import re
from urllib.parse import quote
import requests
import json
from login import login

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# 用于API请求的额外Headers
API_HEADERS = {
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "zh-CN,zh;q=0.9",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "priority": "u=1, i",
    "sec-ch-ua": '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "x-requested-with": "XMLHttpRequest",
}


def get_attach_uuid(session, base_url, id_value):
    """
    获取附件管理的UUID
    :param session: 登录后的session
    :param base_url: 基础URL
    :param id_value: id参数值，如211547
    :return: uuid字符串，如果获取失败返回None
    """
    try:
        print(f"\n[5] 访问附件管理页面，id={id_value}...")
        url = f"{base_url}/attachment/dialog"
        params = {
            "entityName": "E_Y29tLmluY2Euc2Fhcy5pYnMuZW50aXR5LnN5cy5FeHBvcnRSZXN1bHQ=",
            "id": id_value
        }
        
        response = session.get(url, params=params, headers=HEADERS, timeout=100)
        
        # 等待2秒后开始检查UUID
        print("[6] 等待2秒后开始检查UUID...")
        time.sleep(2)
        
        # 循环检查直到获取到UUID
        max_retries = 100  # 最多重试3600次，共约3小时
        for i in range(max_retries):
            print(f"  检查UUID (第{i+1}次)...")
            
            # 重新请求页面
            response = session.get(url, params=params, headers=HEADERS, timeout=100)
            
            # 查找隐藏的attachuuid字段
            if 'id="attachuuid"' in response.text:
                # 使用简单的方法提取value
                pattern = r'id="attachuuid"[^>]*value="([^"]*)"'
                match = re.search(pattern, response.text)
                if match:
                    uuid_value = match.group(1)
                    if uuid_value and uuid_value.startswith(base_url.replace("https://", "")):
                        print(f"  成功获取UUID: {uuid_value}")
                        return uuid_value
            
            # 如果没找到，等待3秒后重试
            if i < max_retries - 1:
                time.sleep(10)
        
        print("  获取UUID超时")
        return None
        
    except Exception as e:
        print(f"获取UUID异常: {e}")
        return None


def get_attachment_list(session, base_url, uuid_value, id_value):
    """
    获取附件列表
    :param session: 登录后的session
    :param base_url: 基础URL
    :param uuid_value: UUID值
    :param id_value: ID值，用于构造Referer
    :return: 附件列表，失败返回None
    """
    try:
        print(f"\n[7] 获取附件列表...")
        url = f"{base_url}/attachment/list"
        
        # 更新headers，添加cookie等信息
        headers = API_HEADERS.copy()
        headers["Referer"] = f"{base_url}/IBSSYS101/?id={id_value}"
        
        data = {"uuid": uuid_value}
        
        response = session.post(url, data=data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            attachments = response.json()
            print(f"  成功获取附件列表，共{len(attachments)}个文件")
            for att in attachments:
                print(f"    - {att['name']} ({att['length']} bytes)")
            return attachments
        else:
            print(f"  获取附件列表失败，状态码: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"获取附件列表异常: {e}")
        return None


def download_file(session, base_url, uuid_value, filename, download_path, id_value, max_retries=5):
    """
    下载文件（带重试和断点续传）
    :param session: 登录后的session
    :param base_url: 基础URL
    :param uuid_value: UUID值
    :param filename: 文件名
    :param download_path: 下载路径
    :param id_value: ID值，用于构造Referer
    :param max_retries: 最大重试次数
    :return: (success, file_path)
    """
    # 确保下载路径存在
    os.makedirs(download_path, exist_ok=True)
    file_path = os.path.join(download_path, filename)
    temp_file_path = file_path + ".tmp"  # 临时文件
    
    # 构建下载URL
    encoded_uuid = quote(uuid_value, safe='')
    encoded_filename = quote(filename, safe='')
    url = f"{base_url}/attachment/download?uuid={encoded_uuid}&fileName={encoded_filename}"
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"  尝试下载 {filename} (第{attempt}/{max_retries}次)")
            
            # 检查是否有未完成的临时文件（断点续传）
            headers = API_HEADERS.copy()
            headers["Referer"] = f"{base_url}/IBSSYS101/?id={id_value}"
            
            downloaded_size = 0
            if os.path.exists(temp_file_path):
                downloaded_size = os.path.getsize(temp_file_path)
                if downloaded_size > 0:
                    # 添加 Range 头实现断点续传
                    headers["Range"] = f"bytes={downloaded_size}-"
                    print(f"  断点续传，已下载 {downloaded_size} bytes，继续下载...")
            
            # 流式下载，增加超时时间
            response = session.get(
                url, 
                headers=headers, 
                stream=True, 
                timeout=120,  # 连接超时120秒
                verify=False  # 如果SSL有问题可以加上，生产环境建议True
            )
            
            if response.status_code in [200, 206]:  # 200: 全新下载, 206: 断点续传
                # 打开文件（追加模式）
                mode = 'ab' if response.status_code == 206 else 'wb'
                
                with open(temp_file_path, mode) as f:
                    # 使用更小的chunk_size，避免一次性传输太多
                    chunk_count = 0
                    for chunk in response.iter_content(chunk_size=4096):
                        if chunk:
                            f.write(chunk)
                            chunk_count += 1
                            # 每100个chunk打印一次进度
                            if chunk_count % 100 == 0:
                                current_size = os.path.getsize(temp_file_path)
                                print(f"    已下载: {current_size / 1024 / 1024:.2f} MB", end='\r')
                
                # 验证文件完整性（可选：对比Content-Length）
                final_size = os.path.getsize(temp_file_path)
                content_length = response.headers.get('content-length')
                
                if content_length:
                    expected_size = int(content_length)
                    if downloaded_size > 0:
                        expected_size += downloaded_size
                    
                    if final_size == expected_size:
                        # 下载完成，重命名临时文件
                        os.rename(temp_file_path, file_path)
                        print(f"\n  ✅ 下载成功: {filename} ({final_size / 1024 / 1024:.2f} MB)")
                        return True, file_path
                    else:
                        print(f"\n  ⚠️ 文件不完整: {final_size}/{expected_size} bytes，继续重试...")
                        # 保留临时文件，下次继续
                        continue
                else:
                    # 没有Content-Length，假设下载完成
                    os.rename(temp_file_path, file_path)
                    print(f"\n  ✅ 下载成功（未知大小）: {filename}")
                    return True, file_path
                    
            elif response.status_code == 416:  # Range请求超出范围，文件已完整
                if os.path.exists(temp_file_path):
                    os.rename(temp_file_path, file_path)
                    print(f"  ✅ 文件已完整: {filename}")
                    return True, file_path
                    
            else:
                print(f"  下载失败，状态码: {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"  ⚠️ 下载超时（第{attempt}次），准备重试...")
            
        except requests.exceptions.ConnectionError as e:
            print(f"  ⚠️ 连接错误: {e}（第{attempt}次），准备重试...")
            
        except Exception as e:
            print(f"  ⚠️ 下载异常: {e}（第{attempt}次），准备重试...")
        
        # 重试前等待（递增等待时间）
        if attempt < max_retries:
            wait_time = min(attempt * 3, 30)  # 3, 6, 9, 12, 15...最大30秒
            print(f"  等待 {wait_time} 秒后重试...")
            time.sleep(wait_time)
    
    # 所有重试都失败
    print(f"  ❌ 下载失败: {filename}，已重试{max_retries}次")
    
    # 清理临时文件
    if os.path.exists(temp_file_path):
        try:
            os.remove(temp_file_path)
            print(f"  清理临时文件: {temp_file_path}")
        except:
            pass
    
    return False, None

def remove_fileid(session, base_url, id_value):
    """
    从ID列表中移除文件ID
    """
    url = f"{base_url}/IBSSYS101/remove"
    
    headers = API_HEADERS.copy()
    headers["Referer"] = f"{base_url}/IBSSYS101/?id={id_value}"
    headers["X-Requested-With"]= "XMLHttpRequest"
    
    data = {f"ids": f'[{id_value}]'}
    
    
    response = session.post(url, data=data, headers=headers, timeout=30)
    print(f"发送数据: {data}, 响应状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        if result.get('error') is None:
            print(f"✅ 成功移除文件ID: {id_value}")
            return []
    
    return target_ids




def process_id(session, base_url, target_id, download_path):
    """
    处理单个ID的下载任务
    :param session: 登录后的session
    :param base_url: 基础URL
    :param target_id: 目标ID
    :param download_path: 下载路径
    :return: (success, file_path)
    """
    print(f"\n{'='*60}")
    print(f"开始处理ID: {target_id}")
    print(f"{'='*60}")
    
    # 1. 获取UUID
    uuid_value = get_attach_uuid(session, base_url, target_id)
    if not uuid_value:
        print(f"ID {target_id} 获取UUID失败")
        return False, None
    
    # 2. 获取附件列表
    time.sleep(2)  # 等待2秒后获取附件列表
    attachments = get_attachment_list(session, base_url, uuid_value, target_id)
    if not attachments:
        print(f"ID {target_id} 获取附件列表失败")
        return False, None
    
    # 3. 下载所有文件
    print(f"\n开始下载文件到: {download_path}")
    time.sleep(2)  # 等待2秒后开始下载
    
    success_count = 0
    downloaded_file = None
    
    for attachment in attachments:
        filename = attachment['name']
        # 只下载Excel文件，跳过zip文件
        if filename.endswith('.xlsx') or filename.endswith('.xls') or filename.endswith('.csv'):
            print(f"\n[8] 下载文件: {filename}")
            success, file_path = download_file(
                session, base_url, uuid_value, filename, 
                download_path, target_id, max_retries=5
            )
            if success:
                success_count += 1
                downloaded_file = file_path
                print(f"  ✅ 文件 {filename} 下载完成")
            else:
                print(f"  ❌ 文件 {filename} 下载失败")
        else:
            print(f"  ⏭️ 跳过非Excel文件: {filename}")
        
        # 文件间延迟，避免请求过快
        time.sleep(1)
    
    print(f"\nID {target_id} 处理完成: 成功下载 {success_count} 个文件")



    return success_count > 0, downloaded_file


def export_file(session, base_url, target_ids, download_path):
    """
    文件导出主函数
    :param session: 登录后的session
    :param base_url: 基础URL
    :param target_ids: 目标ID列表
    :param download_path: 下载路径
    :return: 文件名映射字典 {target_id: file_path}
    """
    print(f"准备处理 {len(target_ids)} 个ID: {target_ids}")
    
    # 处理每个ID
    total_success = 0
    file_name_mapping = {}
    
    for idx, target_id in enumerate(target_ids, 1):
        print(f"\n进度: {idx}/{len(target_ids)}")
        
        success, file_path = process_id(session, base_url, target_id, download_path)
        
        if success and file_path:
            total_success += 1
            file_name_mapping[target_id] = file_path
            print(f"✅ ID {target_id} 处理成功，文件: {os.path.basename(file_path)}")
        else:
            print(f"❌ ID {target_id} 处理失败")
            return None  # 如果任何一个ID处理失败，返回None
        
        # 如果还有下一个ID，等待一下
        if idx < len(target_ids):
            print("\n等待3秒后处理下一个ID...")
            time.sleep(3)
    
    print(f"\n{'='*60}")
    print(f"全部处理完成: 成功 {total_success}/{len(target_ids)} 个ID")
    remove_fileid(session, base_url, target_ids[0])  # 移除文件ID
    print(f"{'='*60}")
    
    return file_name_mapping
