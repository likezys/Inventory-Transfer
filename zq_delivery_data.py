import json
import time
import requests
from login import login
from datetime import datetime,timedelta
from export_file import export_file
from dotenv import load_dotenv
import os
# 配置参数
# 加载 .env 文件
load_dotenv()

BASE_URL = os.getenv("ZQ_BASE_URL")

# API请求头
API_HEADERS = {
    "accept": "text/plain, */*; q=0.01",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "zh-CN,zh;q=0.9",
    "content-type": "application/x-www-form-urlencoded",
    "origin": BASE_URL,
    "priority": "u=1, i",
    "sec-ch-ua": '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest",
}


def visit_search_page(session):
    """先访问搜索页面，获取必要的cookie或token"""
    try:
        print("[准备] 访问搜索页面...")
        url = f"{BASE_URL}/IBSAST003/"
        headers = API_HEADERS.copy()
        headers["Referer"] = BASE_URL
        
        response = session.get(url, headers=headers, timeout=10)
        print(f"[准备] 访问搜索页面响应状态: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"[准备] 访问搜索页面异常: {e}")
        return False
    


def search_data(session, start_date, end_date):
    """
    搜索数据，获取查询结果
    :param session: 登录后的session
    :param start_date: 开始日期
    :param end_date: 结束日期
    :return: 搜索结果字典，包含columns, data, sql, total等字段
    """
    try:
        print(f"\n[搜索] 开始搜索数据...")
        url = f"{BASE_URL}/IBSAST003/search"
        
        # 构建查询条件
        query_keys = {"busiDateFrom": f"{start_date}T00:00:00", "busiDateTo": end_date, "disTypeView": "", "qdocumentCode": "", "goodsId": "", "delivaryCompanyName": "", "receiveCompanyName": "", "retailType": "", "transfer": "", "zdyaClass": "", "zdybClass": "", "zdycClass": "", "centerName": ""}
        
        # 构建显示选项
        display_options = {"documentFlag": "true", "recCompanyFlag": "true", "goodsFlag": "true"}
        
        # 合并query_keys和display_options
        query_data = f"{json.dumps(query_keys, ensure_ascii=False)};{json.dumps(display_options, ensure_ascii=False)}"
        
        # 组合表单数据
        form_data = {
            "queryKeys": query_data,
            "pageIndex": "0",
            "pageSize": "100",
            "sortField": "",
            "sortOrder": ""
        }
        
        # 设置Referer
        headers = API_HEADERS.copy()
        headers["Referer"] = f"{BASE_URL}/IBSAST003/"
        
        print("[搜索] 发送搜索请求...")
        
        response = session.post(url, data=form_data, headers=headers, timeout=3600)
        
        print(f"[搜索] 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            # 检查响应内容是否为空
            if not response.text:
                print("[搜索] 响应内容为空")
                return None
            
            # 尝试解析JSON
            try:
                result = response.json()
                print(f"[搜索] 搜索成功，共找到 {result.get('total', 0)} 条记录")
                return result
            except json.JSONDecodeError as e:
                print(f"[搜索] JSON解析失败: {e}")
                print(f"[搜索] 原始响应: {response.text[:500]}")
                return None
        else:
            print(f"[搜索] 搜索失败，状态码: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"[搜索] 搜索异常: {e}")
        import traceback
        traceback.print_exc()
        return None

# columns处理函数
def get_simple_columns(full_json_str: str) -> list:
    """
    传入完整版columns JSON字符串，仅保留 visible=true 的列，输出精简版数组
    :param full_json_str: 完整版columns JSON字符串
    :return: 仅保留 header/field/type 的精简列列表
    """
    # 兼容 JS 原生 true/false
    json_str = full_json_str.replace("true", "true").replace("false", "false")
    full_cols = json.loads(json_str)

    result = []
    for col in full_cols:
        # 只保留 visible 为 true 的列；visible 为 null/False 全部过滤
        visible = col.get("visible")
        if visible is False or col.get("field") is None:
            continue
        
        result.append({
            "header": col.get("header"),
            "field": col.get("field"),
            "type": col.get("type")
        })
    return result

def export_excel(session, search_result):
    """
    导出Excel文件，获取export_id
    :param session: 登录后的session
    :param search_result: 搜索结果
    :return: export_id (target_id)，失败返回None
    """
    try:
        print(f"\n[导出] 开始导出Excel...")
        url = f"{BASE_URL}/IBSRPTEXP/expByAsyn/IBSAST003"
        
        # 构建导出选项
        option = {"zdyb_class":"PUB_GOODS_DEF_CLASS_ZDY2_TYPE","retail_type":"PUB_RETAIL_TYPE","zdyc_class":"PUB_GOODS_DEF_CLASS_ZDY3_TYPE","zdya_class":"PUB_GOODS_DEF_CLASS_ZDY1_TYPE"}
        sumcolumns = "zt_qty,zt_money,gpcs_qty,gpcs_money,rec_qty,rec_money,check_qty,check_money,in_qty,in_money,offset_qty,back_qty,zt_qty,zt_money,gpcs_qty,gpcs_money,rec_qty,rec_money,check_qty,check_money,in_qty,in_money,offset_qty,back_qty,zt_qty,zt_money,gpcs_qty,gpcs_money,rec_qty,rec_money,check_qty,check_money,in_qty,in_money,offset_qty,back_qty,zt_qty,zt_money,gpcs_qty,gpcs_money,rec_qty,rec_money,check_qty,check_money,in_qty,in_money,offset_qty,back_qty"
        # 获取columns列表
        columns_start = search_result.get("columns", [])
        # 过滤columns
        columns = get_simple_columns(json.dumps(columns_start, ensure_ascii=False))
        # 构建表单数据
        form_data = {
            "type": "excel",
            "columns": json.dumps(columns, ensure_ascii=False),
            "notNullColumns": "",
            "maskColumns": "",
            "comment": "",
            "option": json.dumps(option, ensure_ascii=False),
            "renderField": "",
            "sumSql":search_result.get("sumSql", ""),
            "sumColumns": sumcolumns,
            "implService": "rptDisInTransitMiniService",
            "sql": search_result.get("sql", ""),
            "thirdSql": "",
            "filename": "配送在途商品查询",
            "indexColumn": "",
            "functionCode": "IBSAST003",
            "_fc": "IBSAST003",
            "exportCount": str(search_result.get("total", 0)),
            "sumData": ""
        }
        
        # 设置Referer
        headers = API_HEADERS.copy()
        headers["Referer"] = f"{BASE_URL}/IBSAST003/"
        print("[导出] 发送导出请求...")
        response = session.post(url, data=form_data, headers=headers, timeout=3600)
        
        if response.status_code == 200:
            # 响应应该是export_id
            export_id = response.text.strip()
            print(f"[导出] 导出请求成功，获得export_id: {export_id}")
            return export_id
        else:
            print(f"[导出] 导出失败，状态码: {response.status_code}")
            print(f"[导出] 响应内容: {response.text}")
            return None
            
    except Exception as e:
        print(f"[导出] 导出异常: {e}")
        return None


def zq_delivery_data_export(session, base_url, download_path=None):
    """
    搜索数据并导出Excel的完整流程
    :param session: 登录后的session对象
    :param base_url: 基础URL
    :param start_date: 搜索开始日期
    :param download_path: 下载路径
    :return: 导出的文件路径，失败返回None
    """
    end_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    if not visit_search_page(session):
        print("访问搜索页面失败")
        exit(1)

    # 1. 搜索数据
    print(f"  [步骤1/3] 搜索数据...")
    print(f"    开始日期: {start_date}")
    print(f"    结束日期: {end_date}")
    search_result = search_data(session, start_date, end_date)
    if not search_result:
        print("搜索数据失败，无法继续导出")
        return None

    # 2. 导出Excel，获取export_id
    print(f"  [步骤2/3] 导出Excel，获取export_id...")
    export_id = export_excel(session, search_result)
    if not export_id:
        print("导出Excel失败，无法继续下载")
        return None
    
    # 3. 使用获取到的export_id下载文件
    print(f"  [步骤3/3] 使用export_id下载文件...")
    target_ids = [export_id]
    
    # 调用export_file函数下载文件
    file = export_file(session, base_url, target_ids, download_path)
    if not file:
        print("下载文件失败,重来")
        file = zq_delivery_data_export(session, base_url, start_date, download_path)
        return file

    return file[export_id]

