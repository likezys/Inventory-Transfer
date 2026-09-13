import json
import time
import requests
from login import login
from export_file import export_file
import pandas as pd
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
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
        url = f"{BASE_URL}/IBSWAR419/"
        headers = API_HEADERS.copy()
        headers["Referer"] = BASE_URL
        
        response = session.get(url, headers=headers, timeout=10)
        print(f"[准备] 访问搜索页面响应状态: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"[准备] 访问搜索页面异常: {e}")
        return False
    
def search_liangxxx(session,keyword):
    """先访问搜索页面，获取所有item_id拼接成逗号分隔字符串返回，失败返回None"""
    try:
        print(f"[搜索] 自定义3 {keyword} 的id...")
        url = f"{BASE_URL}/common/getOption"
        headers = API_HEADERS.copy()
        headers["Referer"] = BASE_URL
        form_data = {
            'keyword': keyword,
            'option': 'PUB_GOODS_DEF_CLASS_ZDY3_TYPE',
            'pageIndex': '0',
            'pageSize': '100',
            'sortField': '',
            'sortOrder': ''
        }

        response = session.post(url, data=form_data, headers=headers, timeout=30)
        if response.status_code == 200:
            try:
                data_list = response.json()
                print(f"[搜索] 响应内容: {data_list}")
                # 提取所有item_id
                id_list = [item["item_id"] for item in data_list if "item_id" in item]
                if id_list:
                    id_str = ",".join(id_list)
                    print(f"[搜索] 成功获取所有id: {id_str}")
                    return id_str
                else:
                    print("[搜索] 未匹配到任何item_id")
                    return ""
            except json.JSONDecodeError as e:
                print(f"[搜索] JSON解析失败: {e}")
                print(f"[搜索] 原始响应: {response.text[:500]}")
                return ""
        print(f"[搜索] 接口响应状态码异常: {response.status_code}")
        return ""
    except Exception as e:
        print(f"[搜索] 请求异常: {e}")
        return ""


def save_table_setup(session):
    """
    保存表格列配置
    设置哪些列可见、列宽、列标题等
    :param session: 登录后的session对象
    :return: 是否成功
    """
    try:
        print("[表格配置] 正在保存表格列配置...")
        
        url = f"{BASE_URL}/IBSWAR419/saveTableSetup"
        headers = API_HEADERS.copy()
        headers["Referer"] = BASE_URL
        
        # 构建表单数据
        form_data = {}
        
        # 定义所有列的配置
        columns_config = [
            # (索引, data, title, visible, width)
            (0, "retail_code", "门店编号", False, "100px"),
            (1, "retail_name", "门店名称", True, "200px"),
            (2, "short_name", "门店简称", False, "120px"),
            (3, "area_name", "运营区域", False, "120px"),
            (4, "goods_code", "商品编码", True, "100px"),
            (5, "commodity_name", "商品名", True, "200px"),          # 新配置中索引5变为 commodity_name
            (6, "goods_name", "通用名", True, "200px"),             # 新配置中索引6为 goods_name，且可见
            (7, "goods_opcode", "助记码", False, "100px"),
            (8, "goods_spec", "规格", True, "100px"),
            (9, "medicine_type", "剂型", False, "100px"),
            (10, "factory_name", "生产厂商", True, "200px"),
            (11, "prod_area", "产地", False, "100px"),
            (12, "barcode", "条形码", False, "150px"),
            (13, "goods_unit", "基本单位", True, "100px"),
            (14, "sal_goods_qty", "基本单位数量", True, "100px"),
            (15, "packing", "包装规格", True, "100px"),
            (16, "packing_qty", "商品包装数量", False, "100px"),
            (17, "carton_qty", "装箱数量", False, "100px"),
            (18, "piece_count", "件数", False, "100px"),
            (19, "batch_no", "批次", False, "150px"),
            (20, "lot_no", "批号", False, "100px"),                 # 新配置中索引20改为 lot_no
            (21, "ori_batch_no", "上游批次号", False, "150px"),
            (22, "prod_date", "生产日期", True, "100px"),           # 新配置中索引22新增 prod_date
            (23, "supply_name", "供应商", False, "100px"),
            (24, "invalid_date", "有效期至", True, "100px"),        # 新配置中索引24新增 invalid_date
            (25, "deputy_name", "联络人", False, "100px"),
            (26, "jxq_days", "减近效期天数", True, "100px"),        # 新配置中索引26新增 jxq_days
            (27, "last_stio_time", "最近入库时间", False, "100px"),
            (28, "account_date", "入库日期", True, "100px"),
            (29, "st_days", "在库天数", True, "100px"),
            (30, "su_memo", "采购备注", False, "200px"),
            (31, "udi_main_code", "UDI主码", False, "200px"),
            (32, "udi_slave_code", "UDI从码", False, "200px"),
            (33, "def_resa_price", "缺省零售价", False, "100px"),
            (34, "resa_price", "零售价", False, "100px"),
            (35, "resa_money", "零售金额", False, "100px"),
            (36, "vip_price", "会员价", False, "100px"),
            (37, "vip_money", "会员价金额", False, "100px"),
            (38, "goods_incode", "内部编码", False, "100px"),
            (39, "alias_name", "别名", False, "200px"),
            (40, "trade_mark", "商标", False, "100px"),
            (41, "approval_no", "批准文号", False, "200px"),
            (42, "goods_class_name", "商品分类", False, "200px"),
            (43, "abc_class", "商品ABC", False, "100px"),
            (44, "goods_level", "商品级别", True, "100px"),
            (45, "drug_type", "药物类型", False, "100px"),
            (46, "yb_goods_code", "国家药品代码", False, "100px"),
            (47, "yb_fee_level", "医保收费等级", False, "200px"),
            (48, "yb_standard_code", "贯标码", False, "200px"),
            (49, "standard_code", "本位码", False, "200px"),
            (50, "scope_category_name", "经营类别", False, "100px"),
            (51, "rx_flag", "处方药", False, "100px"),
            (52, "ephedrine_flag", "含麻黄碱", False, "100px"),
            (53, "epidemic_flag", "疫情用药", False, "100px"),
            (54, "compound_flag", "含特殊药品复方制剂", False, "100px"),
            (55, "shot_flag", "兴奋剂药品", False, "100px"),
            (56, "imported_flag", "进口药品", False, "100px"),
            (57, "unit_price", "成本单价", True, "100px"),
            (58, "amount_money", "成本金额", False, "100px"),
            (59, "goods_models", "器械型号", False, "100px"),
            (60, "goods_memo", "商品备注", False, "100px"),
            (61, "spmll_class", "商品毛利率分类", False, "100px"),
            (62, "jysx_class", "经营属性分类", False, "100px"),
            (63, "jgglsx_class", "价格管理属性分类", False, "100px"),
            (64, "spxsfe_class", "商品销售份额分类", False, "100px"),
            (65, "mlgx_class", "毛利贡献分类", False, "100px"),
            (66, "psxs_class", "配送属性分类", False, "100px"),
            (67, "cpsmzqsx_class", "产品生命周期属性分类", False, "100px"),
            (68, "jyfs_class", "经营方式", False, "100px"),
            (69, "zdya_class", "自定义分类1", False, "100px"),
            (70, "zdyb_class", "自定义分类2", False, "100px"),
            (71, "zdyc_class", "自定义分类3", False, "100px"),
            (72, "zdyd_class", "自定义分类4", False, "100px"),
            (73, "zdye_class", "自定义分类5", False, "100px"),
            (74, "zdyf_class", "自定义分类6", False, "100px"),
            (75, "approval_file_no", "首营审批档案号", False, "200px"),
            (76, "goods_status", "商品状态", False, "100px"),
            (77, "stop_pur", "停采", False, "100px"),
            (78, "stop_sal", "停销", False, "100px"),
            (79, "gift_flag", "赠品", False, "100px"),
            (80, "pur_power", "采购权", False, "100px"),
            (81, "storage_condition", "存储条件", False, "100px"),
            (82, "goods_class_full_name", "分类全名", False, "200px"),
            (83, "permit_holder", "上市许可持有人", False, "200px"),
            (84, "social_flag", "医保药品", False, "100px"),
            (85, "zhb", "医保转换比", False, "80px"),
            (86, "alicode_start", "追溯码前七位", False, "200px"),
            (87, "wms_code", "物流对码", False, "200px"),
        ]
        
        # 构建表单数据
        for idx, (col_idx, data, title, visible, width) in enumerate(columns_config):
            form_data[f"columns[{col_idx}].data"] = data
            form_data[f"columns[{col_idx}].title"] = title
            form_data[f"columns[{col_idx}].visible"] = str(visible).lower()
            form_data[f"columns[{col_idx}].width"] = width
        
        # 添加额外参数
        form_data["tableId"] = "datagrid1"
        form_data["isApp"] = "0"
        form_data["uriStr"] = "/IBSWAR419"
        
        # 发送POST请求
        response = session.post(url, data=form_data, headers=headers, timeout=30)
        
        print(f"[表格配置] 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("[表格配置] ✅ 表格列配置保存成功")
            return True
        else:
            print(f"[表格配置] ❌ 保存表格配置失败: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[表格配置] ❌ 保存表格配置异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def search_data(session, retailAreaId, zdycClass):
    """
    搜索数据，获取查询结果
    :param session: 登录后的session
    :param retailAreaId: 门店区域ID
    :return: 搜索结果字典，包含columns, data, sql, total等字段
    """
    try:
        print(f"\n[搜索] 开始搜索数据...")
        url = f"{BASE_URL}/IBSWAR419/search"
        # 构建查询条件
        query_keys = {
            "keyword": "",
            "goodsId": "",
            "goodsCode": "",
            "abcClass": "",
            "factoryId": "",
            "scopeCategoryId": "",
            "qretailType": "",
            "retailId": "",
            "retailClassId": "1,2,20006",
            "posId": "",
            "medicineType": "",
            "supplyId": "",
            "deputyId": "",
            "rxflag": "",
            "giftType": "",
            "goodsLevel": "",
            "retailAreaId": retailAreaId,
            "goodsClassId": "",
            "stopPur": "",
            "stopSal": "",
            "zdyaClass": "",
            "zdybClass": "",
            "zdycClass": zdycClass,  # 获取的item_id
            "zdydClass": "",
            "zdyeClass": "",
            "zdyfClass": "",
            "packType": "",
            "social": "",
            "storageCondition": "",
            "epidemicFlag": "",
            "goodsType": "",
            "compoundFlag": "",
            "shotFlag": "",
            "importedFlag": "",
            "goodsIncode": "",
            "startAccountDate": "",
            "endAccountDate": "",
            "startInvalidDate": "",
            "endInvalidDate": "",
            "brand": "",
            "coldFlag": "",
            "purPower": "",
            "qretailStatus": "",
            "jyfsClass": "",
            "wmsCode": "",
            "drugType": "",
            "tradeMark": ""
        }

        # 构建筛选条件
        display_options = {
            "isRetailMsg": "true",
            "retail": "true",
            "retailType": "false",
            "retailClass": "false",
            "retailAbcClass": "false",
            "goods": "true",
            "pack": "false",
            "pos": "false",
            "lot": "true",
            "goodsStatus": "false",
            "batch": "true",
            "isGoodsClass": "false",
            "goodsClass1": "false",
            "goodsClass2": "false",
            "goodsClass3": "false",
            "goodsClass4": "false",
            "goodsClass5": "false",
            "goodsClass6": "false"
        }
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
        headers["Referer"] = f"{BASE_URL}/IBSWAR419/"
        
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
    
def reset_set_table(session):
    '''
    重置表格设置
    '''
    try:
        print("[表格配置] 正在重置表格设置...")
        url = f"{BASE_URL}/IBSWAR419/resetSetTable"
        headers = API_HEADERS.copy()
        headers["Referer"] = BASE_URL
        headers["Content-Type"] = "application/x-www-form-urlencoded"  # 表单提交
        
        # 表单数据
        data = {
            "tableId": "datagrid1",
            "isApp": "0",
            "uriStr": "/IBSWAR419"
        }
        
        response = session.post(url, headers=headers, data=data, timeout=10)
        
        print(f"[表格配置] 响应状态码: {response.status_code}")
        print(f"[表格配置] 响应内容: {response.text[:200] if response.text else '空'}")
        
        if response.status_code == 200:
            # 检查响应内容是否表示成功
            try:
                result = response.json()
                if result.get('code') == 200 or result.get('success') == True:
                    print("[表格配置] ✅ 表格设置重置成功")
                    return True
                else:
                    print(f"[表格配置] ⚠️ 表格设置重置响应异常: {result}")
                    return False
            except:
                # 如果响应不是JSON格式，但状态码是200，视为成功
                print("[表格配置] ✅ 表格设置重置成功（状态码200）")
                return True
        else:
            print(f"[表格配置] ❌ 重置表格设置失败: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[表格配置] ❌ 重置表格设置异常: {e}")
        import traceback
        traceback.print_exc()
        return False

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
        url = f"{BASE_URL}/IBSRPTEXP/expByAsyn/IBSWAR419"
        
        # 构建导出选项
        option = {
            "spxsfe_class":"PUB_GOODS_DEF_CLASS_SPXSFE_TYPE",
            "storage_condition":"PUB_GOODS_STORAGE_CONDITION",
            "pur_power":"PUB_GOODS_PUR_POWER",
            "spmll_class":"PUB_GOODS_DEF_CLASS_SPMLL_TYPE",
            "zdya_class":"PUB_GOODS_DEF_CLASS_ZDY1_TYPE",
            "jgglsx_class":"PUB_GOODS_DEF_CLASS_JGGL_TYPE",
            "cpsmzqsx_class":"PUB_GOODS_DEF_CLASS_CPSMZQSX_TYPE",
            "zdyf_class":"PUB_GOODS_DEF_CLASS_ZDY6_TYPE",
            "zdyc_class":"PUB_GOODS_DEF_CLASS_ZDY3_TYPE",
            "stop_sal":"PUB_GOODS_STOP_SAL_TYPE",
            "goods_status_id":"PUB_GOODS_STATUS",
            "zdyb_class":"PUB_GOODS_DEF_CLASS_ZDY2_TYPE",
            "mlgx_class":"PUB_GOODS_DEF_CLASS_SPMLGX_TYPE",
            "rsa_abc_class":"PUB_GOODS_ABC",
            "social_flag":"PUB_GOODS_STOP_PUR_TYPE",
            "store_type":"PUB_STORE_TYPE",
            "stop_pur":"PUB_GOODS_STOP_PUR_TYPE",
            "psxs_class":"PUB_GOODS_DEF_CLASS_PSXS_TYPE",
            "zdye_class":"PUB_GOODS_DEF_CLASS_ZDY5_TYPE",
            "jyfs_class":"PUB_GOODS_DEF_CLASS_JYFS_TYPE",
            "rx_flag":"PUB_GOODS_RX",
            "goods_level":"PUB_GOODS_LEVEL",
            "zdyd_class":"PUB_GOODS_DEF_CLASS_ZDY4_TYPE",
            "abc_class":"PUB_GOODS_ABC",
            "jysx_class":"PUB_GOODS_DEF_CLASS_JYSX_TYPE",
            "goods_type":"PUB_GOODS_TYPE",
            "yb_fee_class":"PUB_GOODS_FEE_CLASS"
        }
        sumcolumns = 'sal_goods_qty,sal_pack_qty,sal_goods_qty,sal_goods_qty,sal_goods_qty,sal_goods_qty,sal_goods_qty,sal_goods_qty,sal_goods_qty,sal_goods_qty,sal_goods_qty,resa_money,vip_money,amount_money,sal_goods_qty,resa_money,vip_money,amount_money,sal_goods_qty,resa_money,vip_money,amount_money,sal_goods_qty,resa_money,vip_money,amount_money,sal_goods_qty,sal_goods_qty,sal_goods_qty,sal_goods_qty,sal_goods_qty,sal_goods_qty,sal_goods_qty'
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
            "sumSql": search_result.get("sumSql", ""),
            "sumColumns": sumcolumns,
            "implService":"warStqtySalLstReMiniService",
            "sql": search_result.get("sql", ""),
            "thirdSql": "",
            "filename": "可用库存查询（门店）",
            "indexColumn": "",
            "functionCode": "IBSWAR419",
            "_fc": "IBSWAR419",
            "exportCount": str(search_result.get("total", 0)),
            "sumData": ""
        }
        
        # 设置Referer
        headers = API_HEADERS.copy()
        headers["Referer"] = f"{BASE_URL}/IBSWAR419/"
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
    
def merge_and_sort_excel_files(file_paths, output_dir=None, sort_ascending=False, delete_source=True):
    """
    合并多个Excel表格，去掉合计行，并按在库天数排序
    
    参数:
        file_paths: list, Excel文件的绝对路径列表
        output_dir: str, 输出文件夹路径（可选），默认使用第一个文件所在目录
        sort_ascending: bool, 排序方式，False=降序（天数高到低），True=升序（天数低到高）
        delete_source: bool, 是否在合并成功后删除源文件，默认False
    
    返回:
        str: 合并后的文件路径
    """
    
    # 存储所有数据框和对应的文件路径
    all_dfs = []
    success_files = []  # 记录成功读取的文件
    
    # 遍历每个文件路径
    for file_path in file_paths:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            print(f"警告: 文件不存在，已跳过 - {file_path}")
            continue
        
        # 检查文件格式
        if not file_path.endswith(('.xlsx', '.xls')):
            print(f"警告: 不支持的文件格式，已跳过 - {file_path}")
            continue
        
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path)
            
            # 记录原始行数
            original_rows = len(df)
            
            # 去掉最后一行（合计行）
            last_row = df.iloc[-1].astype(str)
            if '合计' in last_row.values or '合计' in str(last_row.values):
                df = df.iloc[:-1]
                print(f"已移除合计行: {os.path.basename(file_path)} (原始{original_rows}行 -> 现在{len(df)}行)")
            else:
                # 如果没有明确的"合计"行，检查是否最后一行的基本单位数量特别大
                if '基本单位数量' in df.columns:
                    try:
                        last_quantity = df.iloc[-1]['基本单位数量']
                        if isinstance(last_quantity, (int, float)) and last_quantity > 1000000:
                            df = df.iloc[:-1]
                            print(f"已移除疑似合计行: {os.path.basename(file_path)} (原始{original_rows}行 -> 现在{len(df)}行)")
                    except:
                        pass
            
            all_dfs.append(df)
            success_files.append(file_path)  # 记录成功读取的文件
            print(f"成功读取: {os.path.basename(file_path)} (行数: {len(df)})")
            
        except Exception as e:
            print(f"读取失败: {os.path.basename(file_path)}, 错误: {e}")
            continue
    
    # 检查是否有数据
    if not all_dfs:
        raise ValueError("没有成功读取任何文件，请检查文件路径和格式")
    
    # 合并所有数据框
    merged_df = pd.concat(all_dfs, ignore_index=True)
    print(f"\n合并完成，总行数: {len(merged_df)}")
    
    # 检查是否有"在库天数"列
    if '在库天数' not in merged_df.columns:
        print("警告: 未找到'在库天数'列，跳过排序")
    else:
        # 确保在库天数是数值类型
        merged_df['在库天数'] = pd.to_numeric(merged_df['在库天数'], errors='coerce')
        
        # 删除在库天数为空的行（如果有）
        before_drop = len(merged_df)
        merged_df = merged_df.dropna(subset=['在库天数'])
        if len(merged_df) < before_drop:
            print(f"已删除 {before_drop - len(merged_df)} 行在库天数为空的数据")
        
        # 排序
        merged_df = merged_df.sort_values('在库天数', ascending=sort_ascending)
        sort_desc = "降序（高到低）" if not sort_ascending else "升序（低到高）"
        print(f"已按'在库天数'进行{sort_desc}排序")
    
    # 重置索引
    merged_df = merged_df.reset_index(drop=True)
    
    # ============ 生成带日期的输出文件名 ============
    today_date = datetime.now().strftime("%Y-%m-%d")
    output_filename = f"{today_date}库存数据.xlsx"
    
    # 确定输出路径
    if output_dir is None:
        # 默认使用第一个文件所在目录
        output_dir = os.path.dirname(file_paths[0])
    
    # 确保输出目录存在
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    output_path = os.path.join(output_dir, output_filename)
    
    # 保存到Excel
    try:
        merged_df.to_excel(output_path, index=False, engine='openpyxl')
        print(f"\n✅ 结果已保存到: {output_path}")
    except Exception as e:
        print(f"保存失败: {e}")
        # 尝试使用xlsxwriter作为备选
        try:
            merged_df.to_excel(output_path, index=False, engine='xlsxwriter')
            print(f"\n✅ 结果已保存到（使用xlsxwriter）: {output_path}")
        except Exception as e2:
            print(f"保存失败: {e2}")
            raise
    
    # ============ 删除源文件 ============
    if delete_source:
        print("\n开始删除源文件...")
        deleted_count = 0
        failed_files = []
        
        for file_path in success_files:
            try:
                # 确保不删除刚刚生成的合并文件
                if os.path.abspath(file_path) != os.path.abspath(output_path):
                    os.remove(file_path)
                    deleted_count += 1
                    print(f"已删除: {os.path.basename(file_path)}")
                else:
                    print(f"跳过删除（与输出文件相同）: {os.path.basename(file_path)}")
            except Exception as e:
                failed_files.append((file_path, str(e)))
                print(f"删除失败: {os.path.basename(file_path)}, 错误: {e}")
        
        print(f"\n删除完成: 成功删除 {deleted_count} 个文件")
        if failed_files:
            print(f"删除失败 {len(failed_files)} 个文件:")
            for f, err in failed_files:
                print(f"  - {os.path.basename(f)}: {err}")
    
    return output_path

def split_list_half(s):
    """将逗号分隔的字符串从中间分成两半"""
    if not s:
        return [], []
    
    # 按逗号分割
    items = s.split(",")
    total = len(items)
    
    # 计算中间位置（前半段包含前半部分，后半段包含剩余部分）
    mid = total // 2
    
    # 分割成两半
    first_half = items[:mid]
    second_half = items[mid:]
    
    # 重新组合成字符串
    first_str = ",".join(first_half)
    second_str = ",".join(second_half)
    
    return [first_str, second_str]

def for_each_retail_area_id(session,base_url,download_path, retailAreaId, zdycClass):
        # 2. 搜索数据
        print(f"  [a] 搜索数据...")
        retailAreaId_file = []
        search_result = search_data(session, retailAreaId,zdycClass)
        if not search_result:
            print("搜索数据失败，无法继续导出")
            return None
        if search_result.get("total")>200000:
            print(f"搜索结果过大（{search_result.get('total')}条），正在缩小搜索范围")
            retailAreaId_list = split_list_half(retailAreaId)
            for area_id in retailAreaId_list:
                file=for_each_retail_area_id(session, base_url, download_path, area_id, zdycClass)
                if file:
                    retailAreaId_file.extend(file)
            return retailAreaId_file
        # 3. 导出Excel，获取export_id
        print(f"  [b] 导出Excel，获取export_id...")
        export_id = export_excel(session, search_result)
        if not export_id:
            print("导出Excel失败，无法继续下载")
            return None
        
        # 4. 使用获取到的export_id下载文件
        print(f"  [c] 使用export_id下载文件...")
        target_ids = [export_id]  # 这里export_id就是target_id
        # 调用export_file函数下载文件
        file = export_file(session, base_url, target_ids, download_path)
        if not file:
            print('下载文件有点毛病，正在重新搜索下载')
            file_list = for_each_retail_area_id(session, base_url, download_path, retailAreaId, zdycClass)
            if file_list:
                return file_list
        return [file[export_id]]
def inventory_export(session, base_url, download_path):
    """
    搜索数据并导出Excel的完整流程
    :param session: 登录后的session对象
    :param base_url: 基础URL
    :param download_path: 下载路径
    :return: 导出的文件路径，失败返回None
    """
    # 1. 保存表格配置
    print(f"  [步骤1/4] 保存表格配置...")
    if not save_table_setup(session):
        print("保存表格配置失败，无法继续导出")
        return None
    retailAreaId = ['1,3','2,5','4,6']
    # retailAreaId = [1,2,3,4,5,6]
    retailAreaId_file = []
    print(f"  [步骤2/4] 将按运营区域ID分别导出数据: {retailAreaId}")
    liangxxx = search_liangxxx(session,'xxx') or ""
    wangxxx = search_liangxxx(session, "xxx") or ""
    zdycClass = ",".join(filter(None, [liangxxx, wangxxx]))  # 拼接两个结果，过滤空字符串
    for area_id in retailAreaId:
        file_list =  for_each_retail_area_id(session, base_url, download_path, area_id, zdycClass)
        retailAreaId_file.extend(file_list)

    print(f"  [步骤3/4] 合并导出的Excel文件...")
    output_path = merge_and_sort_excel_files(retailAreaId_file, output_dir=download_path, sort_ascending=False, delete_source=True)
    # 5. 重置表格设置
    print(f"  [步骤4/4] 重置表格设置...")
    if not reset_set_table(session):
        print("重置表格设置失败，请手动检查")
    return output_path
