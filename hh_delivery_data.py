import json
import time
import requests
from login import login
from datetime import datetime, timedelta
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
        url = f"{BASE_URL}/IBSSAL202/"
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
        url = f"{BASE_URL}/IBSSAL202/search"
        jsonPage = json.dumps({"draw":11,"columns":[{"data":0,"name":"","searchable":"true","orderable":"false","search":{"value":"","regex":"false"}},{"data":"saDeliveryDoc.busiDate","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"saDeliveryDoc.documentCode","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"saDeliveryDoc.custom.customName","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"taxGrossRate","name":"null","searchable":"true","orderable":"false","search":{"value":"","regex":"false"}},{"data":"goods.goodsName","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"goods.goodsSpec","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"lot.lotNo","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"goods.factory.factoryName","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"goods.approvalNo","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"goods.goodsTypeView","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"goodsQty","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"saDeliveryDoc.sysMemo","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"saDeliveryDoc.infoSummary","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"wfUsestatusView","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"taxGross","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"saDeliveryDoc.customCodeView","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"saDeliveryDoc.settle.settleName","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"saDeliveryDoc.gpcsFlag","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"saDeliveryDoc.staffName","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"staffPrice","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"staffMoney","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"saDeliveryDoc.deptName","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"saDeliveryDoc.customConsigner.consignerName","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"saDeliveryDoc.deputy.deputyName","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"saDeliveryDoc.status","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"goods.goodsCode","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"goods.goodsIncode","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"goods.tradeMark","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"goods.aliasName","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"goods.goodsUnit","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"goods.medicineType","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"goods.prodArea","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"goodsClassName","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"customClassName","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"abcClass","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"packName","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"packQty","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"priceTypeName","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"offsetQty","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"saDeliveryDoc.offsetStatusView","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"saDeliveryDoc.offsetStatus","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"unitPrice","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"skUnitPrice","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"skAmountMoney","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"skCostPrice","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"skCostMoney","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"amountMoney","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"taxRate","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"taxMoney","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"costGross","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"costGrossRate","name":"null","searchable":"true","orderable":"false","search":{"value":"","regex":"false"}},{"data":"giftFlag","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"salPrice","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"rsaPrice","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"salLastPrice","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"salReferencePrice","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"bidPrice","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"otherPriceSummary","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"invflagView","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"blendQty","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"blendMoney","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"noInvMoney","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"lastInvDate","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"store.storeName","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"pos.posCode","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"lot.prodDate","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"lot.invalidDate","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"batch.batchNo","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"batch.unitPrice","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"goodsStatusView","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"saDeliveryDoc.contactPerson","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"saDeliveryDoc.contactTelNo","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"saDeliveryDoc.transAddress","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"saDeliveryDoc.transMode","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"saDeliveryDoc.createUserName","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"saDeliveryDoc.createTime","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"saDeliveryDoc.submitUsera.userName","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"saDeliveryDoc.submitDate","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"printCount","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"lastPrintPeople","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"lastPrintTime","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"goods.goodsModels","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"pieceCount","name":"null","searchable":"true","orderable":"false","search":{"value":"","regex":"false"}},{"data":"costPrice","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"costMoney","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"saDeliveryDoc.memo","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}},{"data":"dtlMemo","name":"null","searchable":"true","orderable":"true","search":{"value":"","regex":"false"}}],"order":[{"column":25,"dir":"asc"}],"start":0,"length":50,"search":{"value":"","regex":"false"}})

        # 构建查询条件
        query_keys = {"jsonPage":jsonPage,"keyword":"","busiDateFrom": f"{start_date}", "busiDateTo": end_date, "disTypeView": "", "goodsIds":"","goodsClassId":"","customClassId":"","customId":"2","arrInvflag":"","qlastInvDate":"","qgoodsType":"","qapprovalNo":"","factoryId":"","staffUserIds":"","staffNames":"","aliasName":""}
        
        # 设置Referer
        headers = API_HEADERS.copy()
        headers["Referer"] = f"{BASE_URL}/IBSSAL202/"
        
        print("[搜索] 发送搜索请求...")
        
        response = session.post(url, data=query_keys, headers=headers, timeout=3600)
        
        print(f"[搜索] 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            # 检查响应内容是否为空
            if not response.text:
                print("[搜索] 响应内容为空")
                return None
            
            # 尝试解析JSON
            try:
                result = response.json()
                print(f"[搜索] 搜索成功，共找到 {result.get('recordsTotal', 0)} 条记录")
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
        url = f"{BASE_URL}/export/expByAsyn"
        
        # 构建表单数据
        form_data = {
            "recordsTotal": search_result.get('recordsTotal',0),
            "exportTitleList": "业务日期,客户,通用名,规格,生产厂商,批准文号,数量,其他信息,其他信息,商品类型,商品类型,系统备注,单据编号,审批状态,审批状态,客户编码,结算方式,配送生成标识,业务员,业务员单价,业务员金额,委托人,联络人,状态,商品编码,內部编码,商标,基本单位,剂型,产地,商品分类,客户分类,ABC分类,包装单位名称,包装数量,价格类型名称,冲差数量,单价,出库成本价,含税出库成本,含税出库金额,无税出库成本,无税成本单价,无税出库金额,无税成本金额,金额,税率,税额,含税毛利,含税毛利率,无税毛利,无税毛利率,赠品,批发价,零售价,上次销价,批发参考价,中标价,其他参考价,已结算数量,已结算金额,核销金额,仓库名称,货架编号,批号,生产日期,有效期至,批次,批次成本价,联系人,联系电话,运输地址,运输方式,制单人,制单时间,提交人,提交日期,打印次数,最后打印人,最后打印时间,器械型号,件数,业务部门,业务部门,冲差状态,冲差状态,备注,结算标识,质量状态,质量状态,明细备注",
            "exportFieldNameList": "saDeliveryDoc,saDeliveryDoc,goods,goods,goodsModel,goodsModel,goodsQty,docExportModel,infoSummary,goodsModel,goodsModel,docExportModel,saDeliveryDoc,exportModel,saDeliveryDoc,docExportModel,saDeliveryDoc,docExportModel,saDeliveryDoc,staffPrice,staffMoney,saDeliveryDoc,saDeliveryDoc,saDeliveryDoc,goods,goodsModel,goodsModel,goods,goodsModel,goodsModel,goodsClassName,exportModel,abcClass,packName,packQty,priceType,offsetQty,unitPrice,priceModel,skUnitPrice,skAmountMoney,skCostPrice,priceModel,skCostMoney,moneyModel,amountMoney,taxRate,taxMoney,taxGross,rateModel,costGross,rateModel,giftFlag,salPrice,rsaPrice,salLastPrice,salReferencePrice,bidPrice,otherModel,qtyModel,moneyModel,blendMoney,store,pos,lot,lot,lot,batch,batchModel,docExportModel,docExportModel,docExportModel,docExportModel,docExportModel,docExportModel,docExportModel,docExportModel,countModel,otherModel,otherModel,goodsModel,pieceCount,docExportModel,saDeliveryDoc,docExportModel,offsetStatus,docExportModel,otherModel,exportModel,goodsStatus,exportModel",
            "exportCheckFlagList": "false,false,false,false,true,true,true,true,false,false,true,true,false,false,false,false,true,true,false,false,false,false,true,true,true,false,false,false,true,true,false,false,false,false,true,true,false,false,false,false,true,true,false,false,false,false,true,true,false,false,false,false,true,true,false,false,false,false,true,true,false,false,false,false,true,true,false,false,false,false,true,true,false,false,false,false,true,true,false,false,false,false,true,true,false,false,false,false,true,true,false",
            "exportFieldTypeList": "com.inca.saas.ibs.entity.sal.SaDeliveryDoc,com.inca.saas.ibs.entity.sal.SaDeliveryDoc,com.inca.saas.ibs.entity.pub.Goods,com.inca.saas.ibs.entity.pub.Goods,com.inca.saas.ibs.pub.goods.GoodsInfo,com.inca.saas.ibs.pub.goods.GoodsInfo,java.math.BigDecimal,com.inca.saas.ibs.sal.saDeliveryDoc.SaDeliveryDocInfo,java.lang.String,com.inca.saas.ibs.pub.goods.GoodsInfo,com.inca.saas.ibs.pub.goods.GoodsInfo,com.inca.saas.ibs.sal.saDeliveryDoc.SaDeliveryDocInfo,com.inca.saas.ibs.entity.sal.SaDeliveryDoc,java.lang.String,com.inca.saas.ibs.entity.sal.SaDeliveryDoc,com.inca.saas.ibs.sal.saDeliveryDoc.SaDeliveryDocInfo,com.inca.saas.ibs.entity.sal.SaDeliveryDoc,com.inca.saas.ibs.sal.saDeliveryDoc.SaDeliveryDocInfo,com.inca.saas.ibs.entity.sal.SaDeliveryDoc,java.math.BigDecimal,java.math.BigDecimal,com.inca.saas.ibs.entity.sal.SaDeliveryDoc,com.inca.saas.ibs.entity.sal.SaDeliveryDoc,com.inca.saas.ibs.entity.sal.SaDeliveryDoc,com.inca.saas.ibs.entity.pub.Goods,com.inca.saas.ibs.pub.goods.GoodsInfo,com.inca.saas.ibs.pub.goods.GoodsInfo,com.inca.saas.ibs.entity.pub.Goods,com.inca.saas.ibs.pub.goods.GoodsInfo,com.inca.saas.ibs.pub.goods.GoodsInfo,java.lang.String,java.lang.String,java.lang.String,java.lang.String,java.math.BigDecimal,com.inca.saas.ibs.entity.pub.PriceType,java.math.BigDecimal,java.math.BigDecimal,java.math.BigDecimal,java.math.BigDecimal,java.math.BigDecimal,java.math.BigDecimal,java.math.BigDecimal,java.math.BigDecimal,java.math.BigDecimal,java.math.BigDecimal,java.math.BigDecimal,java.math.BigDecimal,java.math.BigDecimal,java.math.BigDecimal,java.math.BigDecimal,java.math.BigDecimal,java.lang.Boolean,java.math.BigDecimal,java.math.BigDecimal,java.math.BigDecimal,java.math.BigDecimal,java.math.BigDecimal,java.lang.String,java.math.BigDecimal,java.math.BigDecimal,java.math.BigDecimal,com.inca.saas.ibs.entity.pub.Store,com.inca.saas.ibs.entity.pub.Pos,com.inca.saas.ibs.entity.pub.Lot,com.inca.saas.ibs.entity.pub.Lot,com.inca.saas.ibs.entity.pub.Lot,com.inca.saas.ibs.entity.pub.Batch,com.inca.saas.ibs.entity.pub.Batch,com.inca.saas.ibs.sal.saDeliveryDoc.SaDeliveryDocInfo,com.inca.saas.ibs.sal.saDeliveryDoc.SaDeliveryDocInfo,com.inca.saas.ibs.sal.saDeliveryDoc.SaDeliveryDocInfo,com.inca.saas.ibs.sal.saDeliveryDoc.SaDeliveryDocInfo,com.inca.saas.ibs.sal.saDeliveryDoc.SaDeliveryDocInfo,com.inca.saas.ibs.sal.saDeliveryDoc.SaDeliveryDocInfo,com.inca.saas.ibs.sal.saDeliveryDoc.SaDeliveryDocInfo,com.inca.saas.ibs.sal.saDeliveryDoc.SaDeliveryDocInfo,java.lang.Integer,java.lang.String,java.lang.String,com.inca.saas.ibs.pub.goods.GoodsInfo,java.math.BigDecimal,com.inca.saas.ibs.sal.saDeliveryDoc.SaDeliveryDocInfo,com.inca.saas.ibs.entity.sal.SaDeliveryDoc,com.inca.saas.ibs.sal.saDeliveryDoc.SaDeliveryDocInfo,java.lang.Integer,com.inca.saas.ibs.sal.saDeliveryDoc.SaDeliveryDocInfo,java.lang.String,java.lang.String,java.lang.Integer,java.lang.String",
            "exportForeginNameList": "saDeliveryDoc.busiDate,saDeliveryDoc.custom.customName,goods.goodsName,goods.goodsSpec,goods.factory.factoryName,goods.approvalNo,goodsQty,saDeliveryDoc.infoSummary,infoSummary,goods.goodsType,goods.goodsTypeView,saDeliveryDoc.sysMemo,saDeliveryDoc.documentCode,wfUsestatusView,saDeliveryDoc.wfUsestatus,saDeliveryDoc.customCodeView,saDeliveryDoc.settle.settleName,saDeliveryDoc.gpcsFlag,saDeliveryDoc.staffName,staffPrice,staffMoney,saDeliveryDoc.customConsigner.consignerName,saDeliveryDoc.deputy.deputyName,saDeliveryDoc.status,goods.goodsCode,goods.goodsIncode,goods.tradeMark,goods.goodsUnit,goods.medicineType,goods.prodArea,goodsClassName,customClassName,abcClass,packName,packQty,priceTypeName,offsetQty,unitPrice,skUnitPrice,skUnitPrice,skAmountMoney,skCostPrice,skCostPrice,skCostMoney,skCostMoney,amountMoney,taxRate,taxMoney,taxGross,taxGrossRate,costGross,costGrossRate,giftFlag,salPrice,rsaPrice,salLastPrice,salReferencePrice,bidPrice,otherPriceSummary,blendQty,blendMoney,blendMoney,store.storeName,pos.posCode,lot.lotNo,lot.prodDate,lot.invalidDate,batch.batchNo,batch.unitPrice,saDeliveryDoc.contactPerson,saDeliveryDoc.contactTelNo,saDeliveryDoc.transAddress,saDeliveryDoc.transMode,saDeliveryDoc.createUserName,saDeliveryDoc.createTime,saDeliveryDoc.submitUsera.userName,saDeliveryDoc.submitDate,printCount,lastPrintPeople,lastPrintTime,goods.goodsModels,pieceCount,saDeliveryDoc.deptName,saDeliveryDoc.dept.deptName,saDeliveryDoc.offsetStatusView,offsetStatus,saDeliveryDoc.memo,invflagView,goodsStatusView,goodsStatus,dtlMemo",
            "positions": '[{"field":"saDeliveryDoc","foreginName":"saDeliveryDoc.busiDate","top":0,"left":0,"title":"业务日期"},{"field":"saDeliveryDoc","foreginName":"saDeliveryDoc.custom.customName","top":0,"left":147.75,"title":"客户"},{"field":"goods","foreginName":"goods.goodsName","top":0,"left":295.5,"title":"通用名"},{"field":"goods","foreginName":"goods.goodsSpec","top":0,"left":443.25,"title":"规格"},{"field":"goodsModel","foreginName":"goods.factory.factoryName","top":27.421875,"left":0,"title":"生产厂商"},{"field":"goodsModel","foreginName":"goods.approvalNo","top":27.421875,"left":147.75,"title":"批准文号"},{"field":"goodsQty","foreginName":"goodsQty","top":27.421875,"left":295.5,"title":"数量"},{"field":"docExportModel","foreginName":"saDeliveryDoc.infoSummary","top":27.421875,"left":443.25,"title":"其他信息"},{"field":"infoSummary","foreginName":"infoSummary","top":54.84375,"left":0,"title":"其他信息"},{"field":"goodsModel","foreginName":"goods.goodsType","top":54.84375,"left":147.75,"title":"商品类型"},{"field":"goodsModel","foreginName":"goods.goodsTypeView","top":54.84375,"left":295.5,"title":"商品类型"},{"field":"docExportModel","foreginName":"saDeliveryDoc.sysMemo","top":54.84375,"left":443.25,"title":"系统备注"},{"field":"saDeliveryDoc","foreginName":"saDeliveryDoc.documentCode","top":82.265625,"left":0,"title":"单据编号"},{"field":"exportModel","foreginName":"wfUsestatusView","top":82.265625,"left":147.75,"title":"审批状态"},{"field":"saDeliveryDoc","foreginName":"saDeliveryDoc.wfUsestatus","top":82.265625,"left":295.5,"title":"审批状态"},{"field":"docExportModel","foreginName":"saDeliveryDoc.customCodeView","top":82.265625,"left":443.25,"title":"客户编码"},{"field":"saDeliveryDoc","foreginName":"saDeliveryDoc.settle.settleName","top":109.6875,"left":0,"title":"结算方式"},{"field":"docExportModel","foreginName":"saDeliveryDoc.gpcsFlag","top":109.6875,"left":147.75,"title":"配送生成标识"},{"field":"saDeliveryDoc","foreginName":"saDeliveryDoc.staffName","top":109.6875,"left":295.5,"title":"业务员"},{"field":"staffPrice","foreginName":"staffPrice","top":109.6875,"left":443.25,"title":"业务员单价"},{"field":"staffMoney","foreginName":"staffMoney","top":137.109375,"left":0,"title":"业务员金额"},{"field":"saDeliveryDoc","foreginName":"saDeliveryDoc.customConsigner.consignerName","top":137.109375,"left":147.75,"title":"委托人"},{"field":"saDeliveryDoc","foreginName":"saDeliveryDoc.deputy.deputyName","top":137.109375,"left":295.5,"title":"联络人"},{"field":"saDeliveryDoc","foreginName":"saDeliveryDoc.status","top":137.109375,"left":443.25,"title":"状态"},{"field":"goods","foreginName":"goods.goodsCode","top":164.53125,"left":0,"title":"商品编码"},{"field":"goodsModel","foreginName":"goods.goodsIncode","top":164.53125,"left":147.75,"title":"內部编码"},{"field":"goodsModel","foreginName":"goods.tradeMark","top":164.53125,"left":295.5,"title":"商标"},{"field":"goods","foreginName":"goods.goodsUnit","top":164.53125,"left":443.25,"title":"基本单位"},{"field":"goodsModel","foreginName":"goods.medicineType","top":191.953125,"left":0,"title":"剂型"},{"field":"goodsModel","foreginName":"goods.prodArea","top":191.953125,"left":147.75,"title":"产地"},{"field":"goodsClassName","foreginName":"goodsClassName","top":191.953125,"left":295.5,"title":"商品分类"},{"field":"exportModel","foreginName":"customClassName","top":191.953125,"left":443.25,"title":"客户分类"},{"field":"abcClass","foreginName":"abcClass","top":219.375,"left":0,"title":"ABC分类"},{"field":"packName","foreginName":"packName","top":219.375,"left":147.75,"title":"包装单位名称"},{"field":"packQty","foreginName":"packQty","top":219.375,"left":295.5,"title":"包装数量"},{"field":"priceType","foreginName":"priceTypeName","top":219.375,"left":443.25,"title":"价格类型名称"},{"field":"offsetQty","foreginName":"offsetQty","top":246.796875,"left":0,"title":"冲差数量"},{"field":"unitPrice","foreginName":"unitPrice","top":246.796875,"left":147.75,"title":"单价"},{"field":"priceModel","foreginName":"skUnitPrice","top":246.796875,"left":295.5,"title":"出库成本价"},{"field":"skUnitPrice","foreginName":"skUnitPrice","top":246.796875,"left":443.25,"title":"含税出库成本"},{"field":"skAmountMoney","foreginName":"skAmountMoney","top":274.21875,"left":0,"title":"含税出库金额"},{"field":"skCostPrice","foreginName":"skCostPrice","top":274.21875,"left":147.75,"title":"无税出库成本"},{"field":"priceModel","foreginName":"skCostPrice","top":274.21875,"left":295.5,"title":"无税成本单价"},{"field":"skCostMoney","foreginName":"skCostMoney","top":274.21875,"left":443.25,"title":"无税出库金额"},{"field":"moneyModel","foreginName":"skCostMoney","top":301.640625,"left":0,"title":"无税成本金额"},{"field":"amountMoney","foreginName":"amountMoney","top":301.640625,"left":147.75,"title":"金额"},{"field":"taxRate","foreginName":"taxRate","top":301.640625,"left":295.5,"title":"税率"},{"field":"taxMoney","foreginName":"taxMoney","top":301.640625,"left":443.25,"title":"税额"},{"field":"taxGross","foreginName":"taxGross","top":329.0625,"left":0,"title":"含税毛利"},{"field":"rateModel","foreginName":"taxGrossRate","top":329.0625,"left":147.75,"title":"含税毛利率"},{"field":"costGross","foreginName":"costGross","top":329.0625,"left":295.5,"title":"无税毛利"},{"field":"rateModel","foreginName":"costGrossRate","top":329.0625,"left":443.25,"title":"无税毛利率"},{"field":"giftFlag","foreginName":"giftFlag","top":356.484375,"left":0,"title":"赠品"},{"field":"salPrice","foreginName":"salPrice","top":356.484375,"left":147.75,"title":"批发价"},{"field":"rsaPrice","foreginName":"rsaPrice","top":356.484375,"left":295.5,"title":"零售价"},{"field":"salLastPrice","foreginName":"salLastPrice","top":356.484375,"left":443.25,"title":"上次销价"},{"field":"salReferencePrice","foreginName":"salReferencePrice","top":383.90625,"left":0,"title":"批发参考价"},{"field":"bidPrice","foreginName":"bidPrice","top":383.90625,"left":147.75,"title":"中标价"},{"field":"otherModel","foreginName":"otherPriceSummary","top":383.90625,"left":295.5,"title":"其他参考价"},{"field":"qtyModel","foreginName":"blendQty","top":383.90625,"left":443.25,"title":"已结算数量"},{"field":"moneyModel","foreginName":"blendMoney","top":411.328125,"left":0,"title":"已结算金额"},{"field":"blendMoney","foreginName":"blendMoney","top":411.328125,"left":147.75,"title":"核销金额"},{"field":"store","foreginName":"store.storeName","top":411.328125,"left":295.5,"title":"仓库名称"},{"field":"pos","foreginName":"pos.posCode","top":411.328125,"left":443.25,"title":"货架编号"},{"field":"lot","foreginName":"lot.lotNo","top":438.75,"left":0,"title":"批号"},{"field":"lot","foreginName":"lot.prodDate","top":438.75,"left":147.75,"title":"生产日期"},{"field":"lot","foreginName":"lot.invalidDate","top":438.75,"left":295.5,"title":"有效期至"},{"field":"batch","foreginName":"batch.batchNo","top":438.75,"left":443.25,"title":"批次"},{"field":"batchModel","foreginName":"batch.unitPrice","top":466.171875,"left":0,"title":"批次成本价"},{"field":"docExportModel","foreginName":"saDeliveryDoc.contactPerson","top":466.171875,"left":147.75,"title":"联系人"},{"field":"docExportModel","foreginName":"saDeliveryDoc.contactTelNo","top":466.171875,"left":295.5,"title":"联系电话"},{"field":"docExportModel","foreginName":"saDeliveryDoc.transAddress","top":466.171875,"left":443.25,"title":"运输地址"},{"field":"docExportModel","foreginName":"saDeliveryDoc.transMode","top":493.59375,"left":0,"title":"运输方式"},{"field":"docExportModel","foreginName":"saDeliveryDoc.createUserName","top":493.59375,"left":147.75,"title":"制单人"},{"field":"docExportModel","foreginName":"saDeliveryDoc.createTime","top":493.59375,"left":295.5,"title":"制单时间"},{"field":"docExportModel","foreginName":"saDeliveryDoc.submitUsera.userName","top":493.59375,"left":443.25,"title":"提交人"},{"field":"docExportModel","foreginName":"saDeliveryDoc.submitDate","top":521.015625,"left":0,"title":"提交日期"},{"field":"countModel","foreginName":"printCount","top":521.015625,"left":147.75,"title":"打印次数"},{"field":"otherModel","foreginName":"lastPrintPeople","top":521.015625,"left":295.5,"title":"最后打印人"},{"field":"otherModel","foreginName":"lastPrintTime","top":521.015625,"left":443.25,"title":"最后打印时间"},{"field":"goodsModel","foreginName":"goods.goodsModels","top":548.4375,"left":0,"title":"器械型号"},{"field":"pieceCount","foreginName":"pieceCount","top":548.4375,"left":147.75,"title":"件数"},{"field":"docExportModel","foreginName":"saDeliveryDoc.deptName","top":548.4375,"left":295.5,"title":"业务部门"},{"field":"saDeliveryDoc","foreginName":"saDeliveryDoc.dept.deptName","top":548.4375,"left":443.25,"title":"业务部门"},{"field":"docExportModel","foreginName":"saDeliveryDoc.offsetStatusView","top":575.859375,"left":0,"title":"冲差状态"},{"field":"offsetStatus","foreginName":"offsetStatus","top":575.859375,"left":147.75,"title":"冲差状态"},{"field":"docExportModel","foreginName":"saDeliveryDoc.memo","top":575.859375,"left":295.5,"title":"备注"},{"field":"otherModel","foreginName":"invflagView","top":575.859375,"left":443.25,"title":"结算标识"},{"field":"exportModel","foreginName":"goodsStatusView","top":603.28125,"left":0,"title":"质量状态"},{"field":"goodsStatus","foreginName":"goodsStatus","top":603.28125,"left":147.75,"title":"质量状态"},{"field":"exportModel","foreginName":"dtlMemo","top":603.28125,"left":295.5,"title":"明细备注"}]',
            "checkFlagList":"",
            "fieldNameList": "",
            "selectValueList": "",
            "startWheresList": "",
            "endWheresList": "",
            "foreginNameList": "",
            "fieldTypeList": "",
            "advWheresTypeTableList": "",
            "exportSeacher": "salSaDeliveryDocDtlService",
            "exportClassName": "com.inca.saas.ibs.sal.saDeliveryDocDtl.SaDeliveryDocDtlExportModel",
            "docId":"0",
            "excelTitle":"销售发货单明细查询",
            "exportDatatable":"datatable",
            "exportFunCode":"IBSSAL202",
            "_fc":"IBSSAL202",
            "fileType":"2",
            "queryKey":"sal_saDeliveryDocDtl_query",
            "aysn":"1",
            "specCvsCol":"",
            "advFlag":"false",
            "asyn":"1"
        }
        
        # 设置Referer
        headers = API_HEADERS.copy()
        headers["Referer"] = f"{BASE_URL}/IBSSAL202/"
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


def hh_delivery_data_export(session, base_url, download_path=None):
    """
    搜索数据并导出Excel的完整流程
    :param session: 登录后的session对象
    :param base_url: 基础URL
    :param start_date: 搜索开始日期
    :param download_path: 下载路径
    :return: 导出的文件路径，失败返回None
    """
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    # start_date = end_date
    
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
        file = hh_delivery_data_export(session, base_url, download_path)
        return file

    return file[export_id]
