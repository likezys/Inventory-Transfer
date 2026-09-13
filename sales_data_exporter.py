"""
数据分批导出和合并模块
功能：将大时间范围的数据分批导出，并自动合并去重
"""

import pandas as pd
import os
from datetime import datetime, timedelta
from sales_data import search_and_export,reset_set_table


def split_date_range(start_date, end_date, days=15):
    """
    将日期范围按指定天数拆分
    :param start_date: 开始日期 (格式: "YYYY-MM-DD")
    :param end_date: 结束日期 (格式: "YYYY-MM-DD")
    :param days: 每段的天数，默认15天（半个月）
    :return: 日期段列表，每个元素为 (start, end)
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    date_ranges = []
    current_start = start
    
    while current_start <= end:
        current_end = min(current_start + timedelta(days=days - 1), end)
        date_ranges.append((
            current_start.strftime("%Y-%m-%d"),
            current_end.strftime("%Y-%m-%d")
        ))
        current_start = current_end + timedelta(days=1)
    
    return date_ranges


def remove_last_row(df, file_name=""):
    """
    删除DataFrame的最后一行（通常是总和行）
    :param df: 要处理的DataFrame
    :param file_name: 文件名，用于日志输出
    :return: 删除最后一行后的DataFrame
    """
    if len(df) == 0:
        return df
    # 删除最后一行
    df_without_last = df.iloc[:-1]
    return df_without_last


def aggregate_sales_by_store_and_product(df_or_path, save_path=None):
    """
    根据门店名称和商品编码汇总销售数量
    
    支持两种调用方式：
    1. 传入DataFrame：处理并保存到save_path指定的路径
    2. 传入文件路径：读取文件，处理并覆盖原文件
    
    在汇总前，会先删除会员卡号为 '88880006' 和 '88880005' 的数据，
    以及指定门店和营业员编号的数据
    
    Args:
        df_or_path: Excel文件路径 或 DataFrame对象
        save_path: 当传入DataFrame时，需要指定保存路径；传入文件路径时忽略
    
    Returns:
        tuple: (汇总后的DataFrame, 是否成功)
    """
    try:
        # 判断参数类型
        if isinstance(df_or_path, pd.DataFrame):
            # 直接使用传入的DataFrame
            df = df_or_path.copy()
            print(f"接收到DataFrame，原始数据行数: {len(df)}")
            
            # 必须指定保存路径
            if save_path is None:
                print("错误：传入DataFrame时必须指定save_path参数")
                return None, False
                
        elif isinstance(df_or_path, str):
            # 检查文件是否存在
            if not os.path.exists(df_or_path):
                print(f"错误：文件不存在 - {df_or_path}")
                return None, False
            
            # 读取Excel文件
            print(f"正在读取文件: {df_or_path}")
            df = pd.read_excel(df_or_path)
            
            # 保存路径就是原文件路径（覆盖）
            save_path = df_or_path
            
        else:
            print(f"错误：不支持的参数类型 - {type(df_or_path)}")
            return None, False
        
        # 检查必要的列是否存在
        required_columns = ['门店名称', '商品编码', '销售数量', '会员卡号', '营业员编号']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"错误：缺少必要的列 - {missing_columns}")
            print(f"当前列: {df.columns.tolist()}")
            return None, False
        
        # 记录原始行数
        original_count = len(df)
        print(f"原始数据行数: {original_count}")
        
        # 第一步：删除指定会员卡号的数据
        exclude_card_numbers = ['xxx', 'xxx']
        df_filtered = df[~df['会员卡号'].isin(exclude_card_numbers)]
        
        removed_count = original_count - len(df_filtered)
        if removed_count > 0:
            print(f"已删除会员卡号为 {exclude_card_numbers} 的数据: {removed_count} 行")
        else:
            print(f"未找到需要删除的会员卡号数据")
        
        # 第二步：删除指定门店和营业员编号的数据
        condition1 = (df_filtered['门店名称'] == 'xxx店') & (df_filtered['营业员编号'] == 'xxx')
        condition2 = (df_filtered['门店名称'] == 'xxx店') & (df_filtered['营业员编号'] == 'xxx')
        
        before_remove_employee = len(df_filtered)
        df_filtered = df_filtered[~(condition1 | condition2)]
        
        removed_employee_count = before_remove_employee - len(df_filtered)
        if removed_employee_count > 0:
            print(f"已删除指定门店和营业员编号的数据: {removed_employee_count} 行")
            if condition1.sum() > 0:
                print(f"  - 删除 'xxx店' 营业员编号'xxx': {condition1.sum()} 行")
            if condition2.sum() > 0:
                print(f"  - 删除 'xxx店' 营业员编号'xxx': {condition2.sum()} 行")
        else:
            print(f"未找到需要删除的指定门店和营业员编号数据")
        
        # 按门店名称和商品编码分组，汇总销售数量
        print("正在汇总数据...")
        df_aggregated = df_filtered.groupby(['门店名称', '商品编码'], as_index=False)['销售数量'].sum()
        
        # 保存结果
        print(f"正在保存文件: {save_path}")
        df_aggregated.to_excel(save_path, index=False)
        
        print(f"✅ 数据汇总完成！")
        print(f"过滤后数据行数: {len(df_filtered)}")
        print(f"汇总后行数: {len(df_aggregated)}")
        
        return df_aggregated, True
        
    except Exception as e:
        print(f"错误：处理数据时发生异常 - {e}")
        import traceback
        traceback.print_exc()
        return None, False


def merge_excel_files(file_list, output_path):
    """
    合并多个Excel文件并汇总（优化版）
    
    流程：
    1. 逐个读取文件，删除最后一行（总和行）
    2. 合并所有数据（内存中操作）
    3. 直接调用汇总函数处理（传入DataFrame，指定保存路径）
    4. 汇总函数负责保存最终结果
    
    Args:
        file_list: Excel文件路径列表
        output_path: 最终输出文件路径
    
    Returns:
        str: 合并后的文件路径
    """
    if not file_list:
        print("没有需要合并的文件")
        return None
    
    print(f"\n[合并] 开始合并 {len(file_list)} 个Excel文件...")
    print("=" * 60)
    
    all_dfs = []
    total_rows_before = 0
    total_rows_after = 0
    processed_files = 0
    
    for i, file_path in enumerate(file_list, 1):
        try:
            print(f"  读取文件 {i}/{len(file_list)}: {os.path.basename(file_path)}")
            df = pd.read_excel(file_path)
            original_rows = len(df)
            total_rows_before += original_rows
            
            # 删除最后一行（总和行）
            df = remove_last_row(df, os.path.basename(file_path))
            
            total_rows_after += len(df)
            all_dfs.append(df)
            processed_files += 1
            
        except Exception as e:
            print(f"  ⚠️ 读取文件失败 {os.path.basename(file_path)}: {e}")
            continue
    
    if not all_dfs:
        print("❌ 没有成功读取任何文件")
        return None
    
    # 合并所有DataFrame（内存中操作）
    print("\n正在合并DataFrame...")
    merged_df = pd.concat(all_dfs, ignore_index=True)
    print(f"  合并后DataFrame行数: {len(merged_df)}")
    
    # 释放原始DataFrame列表的内存
    all_dfs.clear()
    
    # 直接调用汇总函数，传入DataFrame和保存路径
    print("\n" + "=" * 60)
    print("开始数据过滤和汇总...")
    print("=" * 60)
    
    df_result, success = aggregate_sales_by_store_and_product(merged_df, save_path=output_path)
    
    if not success or df_result is None:
        print("❌ 数据汇总失败")
        return None
    
    print(f"\n" + "=" * 60)
    print("✅ 合并汇总完成！")
    print("=" * 60)
    print(f"  最终输出文件: {output_path}")
    print(f"  汇总后记录数: {len(df_result)}")
    print(f"  销售总数量: {df_result['销售数量'].sum():.0f}")
    print(f"  涉及门店数: {df_result['门店名称'].nunique()}")
    print(f"  涉及商品数: {df_result['商品编码'].nunique()}")
    
    return output_path


def export_data_by_range(session, base_url, start_date, end_date, download_path, range_days=15):
    """
    按时间段分批导出数据并合并（每导出立即下载）
    :param session: 登录后的session
    :param base_url: 基础URL
    :param start_date: 开始日期
    :param end_date: 结束日期
    :param download_path: 下载路径
    :param range_days: 每段的天数，默认15天
    :return: 合并后的文件路径
    """
    # 1. 拆分日期范围
    date_ranges = split_date_range(start_date, end_date, range_days)
    print(f"\n[分批导出] 将日期范围 {start_date} 至 {end_date} 拆分为 {len(date_ranges)} 段:")
    for i, (s, e) in enumerate(date_ranges, 1):
        print(f"  第{i}段: {s} 至 {e}")
    
    # 2. 存储已下载的文件路径
    exported_files = []
    
    # 3. 逐段导出并立即下载
    for i, (seg_start, seg_end) in enumerate(date_ranges, 1):
        print(f"\n{'='*50}")
        print(f"[分批导出] 第 {i}/{len(date_ranges)} 段: {seg_start} 至 {seg_end}")
        print(f"{'='*50}")
        
        try:
            file_paths_list = search_and_export(
                session=session,
                base_url=base_url,
                start_date=seg_start,
                end_date=seg_end,
                download_path=download_path 
            )   
            
            # 处理下载结果
            if file_paths_list and isinstance(file_paths_list, list):
                for file_path in file_paths_list:
                    if file_path and os.path.exists(file_path):
                        exported_files.append(file_path)
                        print(f"  ✅ 第{i}段下载成功: {os.path.basename(file_path)}")
                    else:
                        print(f"  ⚠️ 第{i}段文件下载失败: {file_path}")
            else:
                print(f"  ❌ 第{i}段下载失败")
                continue
            
            print(f"  [步骤6/6] 第{i}段处理完成")
            
        except Exception as e:
            print(f"  ❌ 第{i}段导出异常: {e}")
            continue
    reset_set_table(session)  # 重置表格设置，避免影响后续操作
    if not exported_files:
        print("\n❌ 没有成功下载任何文件")
        return None
    
    print(f"\n[分批导出] 成功下载 {len(exported_files)}/{len(date_ranges)} 个文件")
    
    # 4. 合并所有文件（会自动去掉每个文件的最后一行总和）
    if len(exported_files) == 1:
        print("\n[合并] 只有一个文件，将删除其最后一行总和后使用")
        # 即使是单个文件，也要删除最后一行
        df = pd.read_excel(exported_files[0])
        df = remove_last_row(df, os.path.basename(exported_files[0]))
        
        # 创建新文件
        merged_filename = f"销售数据_{start_date}_至_{end_date}.xlsx"
        merged_path = os.path.join(download_path, merged_filename)
        df.to_excel(merged_path, index=False)
        print(f"[合并] 已保存到: {merged_path}")
        return merged_path
    
    # 生成合并后的文件名
    merged_filename = f"销售数据_{start_date}_至_{end_date}.xlsx"
    merged_path = os.path.join(download_path, merged_filename)
    
    # 合并文件
    merged_file = merge_excel_files(exported_files, merged_path)
    
    # 删除原始分段文件
    if merged_file:
        print("\n[提示] 分段文件已保留在下载目录中，如需删除请手动清理")
        for file in exported_files:
            try:
                os.remove(file)
                print(f"  已删除: {file}")
            except Exception as e:
                print(f"  删除失败 {file}: {e}")
    
    return merged_file