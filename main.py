from login import login
from sales_data_exporter import export_data_by_range
from inventory_export import inventory_export
from zq_delivery_data import zq_delivery_data_export
from hh_delivery_data import hh_delivery_data_export
from transfer_scheme_processing import complete_workflow
from delivery_data import merge_delivery_tables
from dotenv import load_dotenv
import os
# 配置参数
# 加载 .env 文件
load_dotenv()

ZQ_BASE_URL = os.getenv("ZQ_BASE_URL")
HH_BASE_URL = os.getenv("HH_BASE_URL")

def main(ZQ_USERNAME, ZQ_PASSWORD, HH_USERNAME, HH_PASSWORD, start_date, end_date,DOWNLOAD_PATH, SHORTAGE_FILE, MAPPING_FILE, COLD_CHAIN_FILE, STORE_AREA_FILE,SPLIT_ORDER_PATH):
    """主函数"""

    # 1. 登录
    zq_success, zq_session, zq_message = login(ZQ_BASE_URL, ZQ_USERNAME, ZQ_PASSWORD)
    hh_success, hh_session, hh_message = login(HH_BASE_URL, HH_USERNAME, HH_PASSWORD)
    if not zq_success:
        print(f"登录失败: {zq_message}")
        exit(1)
    if not hh_success:
        print(f"登录失败: {hh_message}")
        exit(1)

    # 2. 分批导出数据并合并（零售决策分析文件）
    sales_file = export_data_by_range(
        session=zq_session,
        base_url=ZQ_BASE_URL,
        start_date=start_date,
        end_date=end_date,
        download_path=DOWNLOAD_PATH,
        range_days=15  # 每段15天
    )

    if not sales_file:
        print("数据导出失败，程序退出")
        exit(1)
    # 3.导出库存文件
    inventory_file = inventory_export(session=zq_session, base_url=ZQ_BASE_URL, download_path=DOWNLOAD_PATH)

    # 4.导出配送在途
    zq_in_transit_file = zq_delivery_data_export(session=zq_session, base_url=ZQ_BASE_URL, download_path=DOWNLOAD_PATH)
    hh_in_transit_file = hh_delivery_data_export(session=hh_session, base_url=HH_BASE_URL, download_path=DOWNLOAD_PATH)

    # 5.在途数据处理
    in_transit_df,in_transit_file = merge_delivery_tables(
        zq_in_transit_file=zq_in_transit_file,
        hh_in_transit_file=hh_in_transit_file,
        split_order_path = SPLIT_ORDER_PATH,
        output_folder = DOWNLOAD_PATH,
    )
    # 6.终极大业务，处理门店调拨
    transfer_scheme_file = complete_workflow(
        shortage_file=SHORTAGE_FILE,
        sales_file=sales_file,
        mapping_file=MAPPING_FILE,
        inventory_file=inventory_file,
        in_transit_file=in_transit_file,
        cold_chain_file=COLD_CHAIN_FILE,
        store_area_file=STORE_AREA_FILE,
        output_folder=DOWNLOAD_PATH,
        in_transit_df=in_transit_df
    )
    print(f"调拨方案处理完成，输出文件: {transfer_scheme_file}")

    # 6. 删除临时文件（销售数据、库存数据、配送在途数据）
    temp_files = [sales_file, inventory_file, in_transit_file,zq_in_transit_file,hh_in_transit_file]
    deleted_count = 0
    
    for temp_file in temp_files:
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
                print(f"✅ 已删除临时文件: {os.path.basename(temp_file)}")
                deleted_count += 1
            except Exception as e:
                print(f"⚠️ 删除文件失败 {os.path.basename(temp_file)}: {e}")
        elif temp_file:
            print(f"⚠️ 文件不存在，跳过删除: {temp_file}")
    
    print(f"🗑️ 共删除 {deleted_count} 个临时文件")
    
    # # 返回最终结果文件路径
    return transfer_scheme_file