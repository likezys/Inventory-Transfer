import json
from datetime import datetime, timedelta
from login import login
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
        url = f"{BASE_URL}/IBSAST101/"
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
        url = f"{BASE_URL}/IBSAST101/search"
        
        # 构建查询条件
        query_keys = {
            "startBusiDate": f"{start_date}T00:00:00",
            "endBusiDate": f"{end_date}T23:59:59",
            "rsaDateType": "1",
            "cardType": "",
            "resaType": "",
            "chanel": "",
            "retailId": "",
            "casherId": "",
            "clerkUserId": "",
            "goodsId": "",
            "goodsCode": "",
            "goodsClassId": "",
            "abcClass": "",
            "abcClassRetail": "",
            "goodsRxFlag": "",
            "prodArea": "",
            "factoryId": "",
            "goodsType": "",
            "goodsLevel": "",
            "newGoods": "",
            "additionCon": "",
            "zdyaClass": "",
            "zdybClass": "",
            "zdycClass": "",
            "zdydClass": "",
            "zdyeClass": "",
            "zdyfClass": "",
            "socialFlag": "",
            "taxRate": "",
            "retailType": "",
            "retailClass": "2,20006",
            "areaId": "",
            "retailAbcClass": "",
            "supplyId": "",
            "consignerId": "",
            "deputyId": "",
            "recommenUserId": "",
            "grossFrom": "",
            "grossTo": "",
            "resaGrossFrom": "",
            "resaGrossTo": "",
            "goodsNature": "",
            "specialGoodsType": "",
            "extInfo1": "",
            "extInfo2": "",
            "shiftId": "",
            "counterId": "",
            "ybPosFlag": "",
            "posId": "",
            "ybPayFlag": "",
            "brand": "",
            "discountRateFrom": "",
            "discountRateTo": "",
            "defBuyerId": "",
            "jyfsClass": "",
            "jgglsxClass": "",
            "engName": "",
            "tradeMark": "",
            "wmsCode": "",
            "drugType": ""
        }
        
        # 构建显示选项
        display_options = {
            "isRetailMsg": "true",
            "resaRetail": "true",
            "retailArea": "false",
            "retailType": "false",
            "retailClass": "false",
            "year": "false",
            "month": "false",
            "week": "false",
            "busiDay": "false",
            "hour": "false",
            "shift": "false",
            "abc": "false",
            "abcRetail": "false",
            "retailAbc": "false",
            "chanel": "false",
            "resaType": "false",
            "resaDoc": "false",
            "cardType": "false",
            "vipCard": "true",
            "casher": "false",
            "clerkUser": "true",
            "counter": "false",
            "posGroup": "false",
            "rxFlagGroup": "false",
            "goodsTypeGroup": "false",
            "supply": "false",
            "goods": "true",
            "factory": "false",
            "prodArea": "false",
            "tradeMark": "false",
            "consigner": "false",
            "deputy": "false",
            "recommenUser": "false",
            "rsaPrice": "false",
            "lotNo": "false",
            "invalidDate": "false",
            "engNameGroup": "false",
            "taxRateGroup": "false",
            "drugTypeGroup": "false",
            "isGoodsClass": "false",
            "goodsClass1": "false",
            "goodsClass2": "false",
            "goodsClass3": "false",
            "goodsClass4": "false",
            "goodsClass5": "false",
            "otherGoodsClass": "false",
            "otherGoodsClassField": "",
            "classDefinition": "false",
            "zdyaClassCheck": "false",
            "zdybClassCheck": "false",
            "zdycClassCheck": "false",
            "zdydClassCheck": "false",
            "zdyeClassCheck": "false",
            "zdyfClassCheck": "false"
        }
        
        # 合并query_keys和display_options
        query_data = f"{json.dumps(query_keys, ensure_ascii=False)};{json.dumps(display_options, ensure_ascii=False)}"
        
        # 组合表单数据
        form_data = {
            "queryKeys": query_data,
            "pageIndex": "0",
            "pageSize": "50",
            "sortField": "",
            "sortOrder": ""
        }
        
        # 设置Referer
        headers = API_HEADERS.copy()
        headers["Referer"] = f"{BASE_URL}/IBSAST101/"
        
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



def save_table_setup(session):
    """
    保存表格列配置
    设置哪些列可见、列宽、列标题等
    :param session: 登录后的session对象
    :return: 是否成功
    """
    try:
        print("[表格配置] 正在保存表格列配置...")
        
        url = f"{BASE_URL}/IBSAST101/saveTableSetup"
        headers = API_HEADERS.copy()
        headers["Referer"] = BASE_URL
        
        # 构建表单数据
        form_data = {}
        
        # 定义所有列的配置
        columns_config = [
            # (索引, data, title, visible, width)
            (0, "retail_code", "门店编号", False, "100px"),
            (1, "retail_name", "门店名称", True, "200px"),
            (2, "short_name", "门店简称", False, "100px"),
            (3, "ext_info_1", "门店自定义1", False, "165px"),
            (4, "ext_info_2", "门店自定义2", False, "165px"),
            (5, "card_no", "会员卡号", True, "100px"),           # 新增会员卡号
            (6, "vip_name", "会员姓名", False, "100px"),        # 新增会员姓名
            (7, "phone_no", "手机号", False, "100px"),          # 新增手机号
            (8, "card_date", "办卡日期", False, "100px"),       # 新增办卡日期
            (9, "goods_code", "商品编码", True, "100px"),
            (10, "goods_name", "通用名", False, "180px"),
            (11, "commodity_name", "商品名", False, "180px"),
            (12, "goods_spec", "规格", False, "100px"),
            (13, "packing", "包装规格", False, "150px"),
            (14, "goods_unit", "基本单位", False, "100px"),
            (15, "approval_no", "批准文号", False, "180px"),
            (16, "factory_code", "厂商编号", False, "200px"),
            (17, "factory_name", "厂商名称", False, "180px"),
            (18, "goods_level", "商品级别", False, "100px"),
            (19, "social_flag", "医保药品", False, "100px"),
            (20, "all_barcode", "条码", False, "180px"),
            (21, "wms_code", "物流对码", False, "180px"),
            (22, "buy_user_name", "专营采购员", False, "100px"),
            (23, "goods_eng_name", "英文名", False, "100px"),
            (24, "trade_mark", "商标", False, "100px"),
            (25, "drug_type", "药物类型", False, "100px"),
            (26, "time_span", "时间跨度", False, "100px"),
            (27, "customer_flow", "客流量", False, "100px"),
            (28, "vip_customer_flow", "会员客流量", False, "100px"),
            (29, "vip_customer_flow_rate", "会员客流量占比", False, "100px"),
            (30, "customer_unit_price", "客单价", False, "100px"),
            (31, "vip_customer_unit_price", "会员客单价", False, "100px"),
            (32, "sal_goods_count", "销售货品次数", False, "100px"),
            (33, "vip_sal_goods_count", "会员销售货品次数", False, "165px"),
            (34, "goods_unit_price", "品单价", False, "100px"),
            (35, "cus_goods_count", "客品次", False, "100px"),
            (36, "vip_cus_goods_count", "会员客品次", False, "165px"),
            (37, "goods_count", "品种数", False, "100px"),
            (38, "sal_goods_qty", "销售数量", True, "100px"),
            (39, "receive_money", "应收金额", False, "100px"),
            (40, "real_money", "实收金额", False, "100px"),
            (41, "cost_money", "实收金额(无税)", False, "165px"),
            (42, "real_money_nogross", "实收金额(不计毛利)", False, "165px"),
            (43, "real_money_gross", "实收金额(计入毛利)", False, "165px"),
            (44, "real_money_gross_taxless", "实收金额(计入毛利/无税)", False, "165px"),
            (45, "ori_batch_price_money", "采购成本", False, "100px"),
            (46, "batch_gross", "总毛利", False, "100px"),
            (47, "resa_sk_amount", "零售成本", False, "100px"),
            (48, "cost_money_taxless", "零售成本(无税)", False, "165px"),
            (49, "resa_gross", "零售毛利", False, "100px"),
            (50, "resa_gross_rate", "零售毛利率", False, "100px"),
            (51, "batch_gross_rate", "总毛利率", False, "100px"),
            (52, "day_sal_qty", "日均销售数量", False, "100px"),
            (53, "day_sal_money", "日均销售额", False, "100px"),
            (54, "day_gross", "日均毛利", False, "100px"),
            (55, "day_gross_rate", "日均毛利率", False, "100px"),
            (56, "vip_sal_qty", "会员销售数量", False, "100px"),
            (57, "vip_receive_money", "会员应收金额", False, "100px"),
            (58, "vip_real_money", "会员实收金额", False, "100px"),
            (59, "vip_real_money_nogross", "会员实收金额(不计毛利)", False, "165px"),
            (60, "vip_real_money_gross", "会员实收金额(计入毛利)", False, "165px"),
            (61, "vip_batch_money", "会员采购成本", False, "100px"),
            (62, "vip_batch_gross", "会员毛利", False, "100px"),
            (63, "vip_batch_gross_rate", "会员毛利率", False, "100px"),
            (64, "vip_day_sal_qty", "会员日均销售数量", False, "100px"),
            (65, "vip_day_receive_money", "会员日均应收", False, "100px"),
            (66, "vip_day_real_money", "会员日均实收", False, "130px"),
            (67, "vip_day_real_money_nogross", "会员日均实收(不计毛利)", False, "165px"),
            (68, "vip_day_real_money_gross", "会员日均实收(计入毛利)", False, "165px"),
            (69, "goods_count_ratio", "品种占比", False, "100px"),
            (70, "vip_sal_qty_ratio_retail", "会员销售数量占比", False, "140px"),
            (71, "vip_sal_qty_ratio", "会员销售数量占比（总）", False, "157px"),
            (72, "vip_receive_money_ratio_retail", "会员应收金额占比", False, "140px"),
            (73, "vip_receive_money_ratio", "会员应收金额占比（总）", False, "157px"),
            (74, "vip_real_money_ratio_retail", "会员实收金额占比", False, "140px"),
            (75, "vip_real_money_ratio", "会员实收金额占比（总）", False, "157px"),
            (76, "vip_batch_money_ratio_retail", "会员采购成本占比", False, "140px"),
            (77, "vip_batch_money_ratio", "会员采购成本占比（总）", False, "157px"),
            (78, "sal_qty_ratio", "销售数量占比", False, "140px"),
            (79, "receive_money_ratio", "应收金额占比", False, "140px"),
            (80, "real_money_ratio", "实收金额占比", False, "140px"),
            (81, "real_money_ratio_nogross", "实收金额占比(不计毛利)", False, "165px"),
            (82, "real_money_ratio_gross", "实收金额占比(计入毛利)", False, "165px"),
            (83, "batch_gross_ratio", "总毛利占比", False, "140px"),
            (84, "discount_rate", "折扣率", False, "140px"),
            (85, "roy_money", "提成金额", False, "80px"),
            (86,'clerk_user_code','营业员编号', True, '100px'),
            (87,'clerk_user_name','营业员姓名', False, '100px'),
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
        form_data["uriStr"] = "/IBSAST101"
        
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

def reset_set_table(session):
    '''
    重置表格设置
    '''
    try:
        url = f"{BASE_URL}/IBSAST101/resetSetTable"
        headers = API_HEADERS.copy()
        headers["Referer"] = BASE_URL
        headers["Content-Type"] = "application/x-www-form-urlencoded"  # 表单提交
        
        # 表单数据
        data = {
            "tableId": "datagrid1",
            "isApp": "0",
            "uriStr": "/IBSAST101"
        }
        
        response = session.post(url, headers=headers, data=data, timeout=10)
        
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
        url = f"{BASE_URL}/IBSRPTEXP/expByAsyn/IBSAST101"
        
        # 构建导出选项
        option = {
            "spxsfe_class": "PUB_GOODS_DEF_CLASS_SPXSFE_TYPE",
            "spmll_class": "PUB_GOODS_DEF_CLASS_SPMLL_TYPE",
            "resa_type": "RESA_DOC_TYPE",
            "zdya_class": "PUB_GOODS_DEF_CLASS_ZDY1_TYPE",
            "jgglsx_class": "PUB_GOODS_DEF_CLASS_JGGL_TYPE",
            "cpsmzqsx_class": "PUB_GOODS_DEF_CLASS_CPSMZQSX_TYPE",
            "zdyf_class": "PUB_GOODS_DEF_CLASS_ZDY6_TYPE",
            "drug_type": "PUB_GOODS_DRUG_TYPE",
            "zdyc_class": "PUB_GOODS_DEF_CLASS_ZDY3_TYPE",
            "zdyb_class": "PUB_GOODS_DEF_CLASS_ZDY2_TYPE",
            "mlgx_class": "PUB_GOODS_DEF_CLASS_SPMLGX_TYPE",
            "retail_type": "PUB_RETAIL_TYPE",
            "rsa_abc_class": "PUB_GOODS_ABC",
            "social_flag": "PUB_COMMON_BOOLEAN_VIEW",
            "psxs_class": "PUB_GOODS_DEF_CLASS_PSXS_TYPE",
            "zdye_class": "PUB_GOODS_DEF_CLASS_ZDY5_TYPE",
            "retail_abc_class": "PUB_RETAIL_ABC",
            "jyfs_class": "PUB_GOODS_DEF_CLASS_JYFS_TYPE",
            "rx_flag": "PUB_GOODS_RX",
            "goods_level": "PUB_GOODS_LEVEL",
            "zdyd_class": "PUB_GOODS_DEF_CLASS_ZDY4_TYPE",
            "channels": "RSA_RESA_DOC_CHANNEL",
            "abc_class": "PUB_GOODS_ABC",
            "jysx_class": "PUB_GOODS_DEF_CLASS_JYSX_TYPE",
            "goods_type": "PUB_GOODS_TYPE"
        }
        sumcolumns = 'customer_flow,vip_customer_flow,vip_customer_flow_rate,customer_unit_price,vip_customer_unit_price,sal_goods_count,goods_unit_price,cus_goods_count,goods_count,sal_goods_qty,receive_money,real_money,real_money_nogross,real_money_gross,ori_batch_price_money,batch_gross,resa_sk_amount,resa_gross,resa_gross_rate,batch_gross_rate,vip_sal_qty,vip_receive_money,vip_real_money,vip_real_money_nogross,vip_real_money_gross,vip_batch_money,vip_batch_gross,vip_batch_gross_rate,vip_sal_qty_ratio_retail,vip_receive_money_ratio_retail,resa_sk_amount,customer_flow,vip_customer_flow,vip_customer_flow_rate,customer_unit_price,vip_customer_unit_price,sal_goods_count,goods_unit_price,cus_goods_count,goods_count,sal_goods_qty,receive_money,real_money,real_money_nogross,real_money_gross,ori_batch_price_money,batch_gross,resa_sk_amount,resa_gross,resa_gross_rate,batch_gross_rate,vip_sal_qty,vip_receive_money,vip_real_money,vip_real_money_nogross,vip_real_money_gross,vip_batch_money,vip_batch_gross,vip_batch_gross_rate,vip_sal_qty_ratio_retail,vip_receive_money_ratio_retail,resa_sk_amount,customer_flow,vip_customer_flow,vip_customer_flow_rate,customer_unit_price,vip_customer_unit_price,sal_goods_count,goods_unit_price,cus_goods_count,goods_count,sal_goods_qty,receive_money,real_money,real_money_nogross,real_money_gross,ori_batch_price_money,batch_gross,resa_sk_amount,resa_gross,resa_gross_rate,batch_gross_rate,vip_sal_qty,vip_receive_money,vip_real_money,vip_real_money_nogross,vip_real_money_gross,vip_batch_money,vip_batch_gross,vip_batch_gross_rate,vip_sal_qty_ratio_retail,vip_receive_money_ratio_retail,resa_sk_amount,customer_flow,vip_customer_flow,vip_customer_flow_rate,customer_unit_price,vip_customer_unit_price,sal_goods_count,goods_unit_price,cus_goods_count,goods_count,sal_goods_qty,receive_money,real_money,real_money_nogross,real_money_gross,ori_batch_price_money,batch_gross,resa_sk_amount,resa_gross,resa_gross_rate,batch_gross_rate,vip_sal_qty,vip_receive_money,vip_real_money,vip_real_money_nogross,vip_real_money_gross,vip_batch_money,vip_batch_gross,vip_batch_gross_rate,vip_sal_qty_ratio_retail,vip_receive_money_ratio_retail,resa_sk_amount'
        # 获取columns列表
        columns_start = search_result.get("columns", [])
        # 过滤columns
        columns = get_simple_columns(json.dumps(columns_start, ensure_ascii=False))

        # 处理sumDataJson
        sum_data_json = search_result.get("sumDataJson", "{}")
        try:
            # 如果sumDataJson是字符串，尝试解析
            if isinstance(sum_data_json, str):
                sum_data = json.loads(sum_data_json)
            else:
                sum_data = sum_data_json
        except:
            sum_data = {}
        
        # 构建表单数据
        form_data = {
            "type": "excel",
            "columns": json.dumps(columns, ensure_ascii=False),
            "notNullColumns": "",
            "maskColumns": "",
            "comment": "",
            "option": json.dumps(option, ensure_ascii=False),
            "renderField": "vip_batch_gross_rate,batch_gross_rate,busi_week,day_gross_rate",
            "sumColumns": sumcolumns,
            "implService": "rsaSalesAnalyzeReportService",
            "sql": search_result.get("sql", ""),
            "thirdSql": "",
            "filename": "零售决策分析",
            "indexColumn": "",
            "functionCode": "IBSAST101",
            "_fc": "IBSAST101",
            "exportCount": str(search_result.get("total", 0)),
            "sumData": json.dumps(sum_data, ensure_ascii=False)
        }
        
        # 设置Referer
        headers = API_HEADERS.copy()
        headers["Referer"] = f"{BASE_URL}/IBSAST101/"
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


def search_and_export(session, base_url, start_date, end_date, download_path):
    """
    搜索数据并导出Excel的完整流程
    :param session: 登录后的session对象
    :param base_url: 基础URL
    :param start_date: 搜索开始日期
    :param end_date: 搜索结束日期
    :param download_path: 下载路径
    :return: 导出的文件路径，失败返回None
    """
    if not visit_search_page(session):
        print("访问搜索页面失败")
        exit(1)

    # 1. 保存表格配置
    print(f"  [步骤1/5] 保存表格配置...")
    if not save_table_setup(session):
        print("保存表格配置失败，无法继续导出")
        return None
    
    # 2. 重新搜索数据
    print(f"  [步骤2/5] 搜索数据...")
    search_result = search_data(session, start_date, end_date)
    if not search_result:
        print("搜索数据失败，无法继续导出")
        return None

    if search_result.get("total", 0) > 200000:
        print("搜索结果超过20万条，导出可能失败，正在缩小时间范围")
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        # 计算中间日期
        mid_dt = start_dt + (end_dt - start_dt) / 2
        mid_date_str = mid_dt.strftime("%Y-%m-%d")
        
        # 中间日期+1天
        mid_date_plus1 = mid_dt + timedelta(days=1)
        mid_date_plus1_str = mid_date_plus1.strftime("%Y-%m-%d")
        
        # 递归搜索前半段和后半段
        file1 = search_and_export(session, base_url, start_date, mid_date_str, download_path)
        file2 = search_and_export(session, base_url, mid_date_plus1_str, end_date, download_path)
        
        files = []
        if file1:
            files.extend(file1)
        if file2:
            files.extend(file2)
        return files
    # 3. 导出Excel，获取export_id
    print(f"  [步骤3/5] 导出Excel，获取export_id...")
    export_id = export_excel(session, search_result)
    if not export_id:
        print("导出Excel失败，无法继续下载")
        return None
    
    # 4. 使用获取到的export_id下载文件
    print(f"  [步骤4/5] 使用export_id下载文件...")
    target_ids = [export_id]  # 这里export_id就是target_id
    
    # 调用export_file函数下载文件
    file = export_file(session, base_url, target_ids, download_path)
    if not file:
        file = search_and_export(session, base_url, start_date, end_date, download_path)

    # 5.重置表格设置

    if not reset_set_table(session):
        print("重置表格设置失败，请手动检查")
    
    return [file[export_id]]