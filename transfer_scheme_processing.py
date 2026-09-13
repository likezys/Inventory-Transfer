import pandas as pd
import os
from datetime import datetime
import math
from typing import Dict, List, Union

def build_sorted_mapping(replace_file):
    """
    读取商品编码匹配表，生成以A列为主键的字典
    返回格式：{商品编码: "匹配编码1/商品编码/匹配编码2/..."}
    """
    # 检查文件是否存在
    if not os.path.exists(replace_file):
        raise FileNotFoundError(f"文件不存在: {replace_file}")
    
    # 读取Excel，不转为字符串，保留原始类型
    df = pd.read_excel(replace_file, engine='openpyxl')
    
    # 清理列名（去除前后空格）
    df.columns = df.columns.str.strip()
    
    # 尝试自动识别列名
    possible_col_a = ['商品编码', '商品编号', '编码', 'code', '商品代码']
    possible_col_b = ['匹配编码', '匹配编号', '匹配码', 'match_code', '对应编码']
    
    col_a = None
    col_b = None
    
    for col in df.columns:
        if col in possible_col_a:
            col_a = col
        if col in possible_col_b:
            col_b = col
    
    # 如果没找到，使用前两列
    if col_a is None and len(df.columns) >= 1:
        col_a = df.columns[0]
        print(f"未找到标准列名，使用第一列作为商品编码: {col_a}")
    
    if col_b is None and len(df.columns) >= 2:
        col_b = df.columns[1]
        print(f"使用第二列作为匹配编码: {col_b}")
    
    if col_a is None:
        raise ValueError("找不到商品编码列，请检查Excel文件")
    
    print(f"使用列: 商品编码='{col_a}', 匹配编码='{col_b if col_b else '无'}'")
    
    # 去除空值
    df = df.dropna(subset=[col_a])
    
    # 构建映射字典
    mapping = {}
    
    for _, row in df.iterrows():
        # 获取商品编码（转为字符串）
        key_val = row[col_a]
        if pd.isna(key_val):
            continue
        
        # 转换为数字（如果是数字类型）或字符串
        try:
            key = str(int(key_val)) if isinstance(key_val, (int, float)) else str(key_val)
        except:
            key = str(key_val)
        key = key.strip()
        
        # 初始化key的集合
        if key not in mapping:
            mapping[key] = {key}  # 始终包含自身
        
        # 如果存在B列且不为空
        if col_b is not None and not pd.isna(row[col_b]):
            match_val = row[col_b]
            try:
                match = str(int(match_val)) if isinstance(match_val, (int, float)) else str(match_val)
            except:
                match = str(match_val)
            match = match.strip()
            
            if match:
                mapping[key].add(match)
    
    # 改进的排序函数：尝试转为数字，如果失败则保留字符串
    def sort_key(x):
        try:
            # 尝试转为整数或浮点数
            num = float(x)
            # 如果是整数，转为int比较
            if num.is_integer():
                return (0, int(num))
            else:
                return (0, num)
        except:
            # 字符串类型用(1, 字符串)
            return (1, str(x))
    
    # 转换为字符串格式 "值1/值2/值3/..."
    result = {}
    for key, val_set in mapping.items():
        # 排序
        items = list(val_set)
        items.sort(key=sort_key)
        # 用斜杠连接成字符串
        result[key] = "/".join(items)
    
    print(f"构建映射完成，共 {len(result)} 条映射")
    return result


def merge_shortage_data(file_path):
    """
    合并缺货数据：读取Excel中'厂家'和'商业'两个sheet，合并并排序
    合并后根据门店名称和商品编码去重，保留第一个出现的行
    
    参数:
        file_path: 缺货数据Excel文件路径
    
    返回:
        DataFrame: 合并后的缺货数据（已去重）
    """
    print("\n" + "=" * 60)
    print("读取并合并缺货数据...")
    print("=" * 60)
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在：{file_path}")
    
    print(f"正在读取文件：{file_path}")
    
    # 读取'厂家'和'商业'两个sheet表
    df_厂家 = pd.read_excel(file_path, sheet_name='厂家')
    df_商业 = pd.read_excel(file_path, sheet_name='商业')
    
    print(f"厂家sheet数据行数：{len(df_厂家)}")
    print(f"商业sheet数据行数：{len(df_商业)}")
    
    # 找出真正的门店名称列（包含"店"字的列，且列名包含"缺货门店"）
    def get_store_name_column(df):
        """自动识别门店名称列"""
        for col in df.columns:
            if '缺货门店' in col and df[col].astype(str).str.contains('店').any():
                return col
        # 如果没找到，返回第一个包含"缺货门店"的列
        for col in df.columns:
            if '缺货门店' in col:
                return col
        return None
    
    # 获取门店名称列
    store_col_厂家 = get_store_name_column(df_厂家)
    store_col_商业 = get_store_name_column(df_商业)
    
    print(f"厂家sheet的门店名称列：{store_col_厂家}")
    print(f"商业sheet的门店名称列：{store_col_商业}")
    
    # 检查商品编码和登记数量列是否存在
    if '商品编码' not in df_厂家.columns:
        raise KeyError("厂家sheet中未找到'商品编码'列")
    if '登记数量' not in df_厂家.columns:
        raise KeyError("厂家sheet中未找到'登记数量'列")
    if '商品编码' not in df_商业.columns:
        raise KeyError("商业sheet中未找到'商品编码'列")
    if '登记数量' not in df_商业.columns:
        raise KeyError("商业sheet中未找到'登记数量'列")
    
    # 只保留需要的列（门店名称、商品编码、登记数量），同时保留原始商品编码
    df_厂家_selected = df_厂家[[store_col_厂家, '商品编码', '登记数量']].copy()
    df_商业_selected = df_商业[[store_col_商业, '商品编码', '登记数量']].copy()
    
    # 统一列名
    df_厂家_selected.columns = ['缺货门店', '商品编码', '登记数量']
    df_商业_selected.columns = ['缺货门店', '商品编码', '登记数量']
    
    # 保存原始商品编码
    df_厂家_selected['源商品编码'] = df_厂家_selected['商品编码']
    df_商业_selected['源商品编码'] = df_商业_selected['商品编码']
    
    # 拼接两个表格（纵向拼接）
    df_combined = pd.concat([df_厂家_selected, df_商业_selected], ignore_index=True)
    
    print(f"合并完成，共 {len(df_combined)} 条记录")
    print(f"  厂家: {len(df_厂家_selected)} 条")
    print(f"  商业: {len(df_商业_selected)} 条")
    
    # ============ 根据门店名称和商品编码去重 ============
    print(f"\n开始根据门店名称和商品编码去重...")
    
    # 标准化门店名称和商品编码
    df_combined['缺货门店'] = df_combined['缺货门店'].astype(str).str.strip()
    df_combined['商品编码'] = df_combined['商品编码'].astype(str).str.strip()
    df_combined['源商品编码'] = df_combined['源商品编码'].astype(str).str.strip()
    
    # 删除空值
    before_drop = len(df_combined)
    df_combined = df_combined[df_combined['缺货门店'] != '']
    df_combined = df_combined[df_combined['缺货门店'] != 'nan']
    df_combined = df_combined[df_combined['商品编码'] != '']
    df_combined = df_combined[df_combined['商品编码'] != 'nan']
    if len(df_combined) < before_drop:
        print(f"已删除 {before_drop - len(df_combined)} 行空值数据")
    
    # 记录去重前的数量
    before_dedup = len(df_combined)
    
    # 按门店名称和商品编码去重，保留第一个出现的行
    df_combined = df_combined.drop_duplicates(
        subset=['缺货门店', '商品编码'], 
        keep='first'
    ).reset_index(drop=True)
    
    after_dedup = len(df_combined)
    
    print(f"  去重前: {before_dedup} 条")
    print(f"  去重后: {after_dedup} 条")
    print(f"  已删除: {before_dedup - after_dedup} 条重复记录")
    
    # 按登记数量降序排序（去重后重新排序）
    df_combined = df_combined.sort_values(by='登记数量', ascending=False).reset_index(drop=True)
    
    print(f"\n缺货数据去重完成！共 {len(df_combined)} 条记录")
    
    # 显示去重后的统计信息
    print(f"\n去重后统计：")
    print(f"  涉及门店数: {df_combined['缺货门店'].nunique()}")
    print(f"  涉及商品数: {df_combined['商品编码'].nunique()}")
    print(f"  总登记数量: {df_combined['登记数量'].sum():.0f}")
    
    return df_combined



def process_inventory_data(inventory_file, sales_summary_df, mapping, cold_chain_df, franchisee_store_df, new_store_df=None):
    """
    处理库存数据：
    1. 读取库存表
    2. 按门店名称和商品编码汇总基本单位数量（新增汇总列，保留原始批次）
    3. 基本单位数量向下取整
    4. 根据门店名称和商品编码匹配销售数据
    5. 应用商品编码映射
    6. 计算'门店库存需要销售月数'
    7. 筛选并删除'门店库存需要销售月数' < 6的行
    
    参数:
        inventory_file: str, 库存文件路径
        sales_summary_df: DataFrame, 销售汇总数据（门店名称、商品编码、销售数量）
        mapping: dict, 商品编码映射字典
        cold_chain_df: DataFrame, 冷链药品数据
        franchisee_store_df: DataFrame, 加盟店数据
        new_store_df: DataFrame, 新门店数据
    返回:
        DataFrame: 处理后的库存数据（保留所有批次效期信息）
    """
    print("\n" + "=" * 60)
    print("处理库存数据...")
    print("=" * 60)
    
    # 检查文件是否存在
    if not os.path.exists(inventory_file):
        raise FileNotFoundError(f"库存文件不存在：{inventory_file}")
    
    print(f"正在读取库存文件：{inventory_file}")
    df_inventory = pd.read_excel(inventory_file, engine='openpyxl')
    print(f"库存数据读取成功: {len(df_inventory)} 行, {len(df_inventory.columns)} 列")
    
    # 检查必需的列是否存在
    required_columns = ['门店名称', '商品编码', '在库天数']
    missing = [col for col in required_columns if col not in df_inventory.columns]
    if missing:
        raise ValueError(f"库存数据表缺少必需列: {missing}")
    
    # 检查基本单位数量列是否存在
    if '基本单位数量' not in df_inventory.columns:
        raise ValueError(f"库存数据表缺少'基本单位数量'列")
    
    # 标准化门店名称和商品编码
    df_inventory['门店名称'] = df_inventory['门店名称'].astype(str).str.strip()
    df_inventory['商品编码'] = df_inventory['商品编码'].astype(str).str.strip()

    # ============ 删除成本单价 ≤ 2 的数据 ============
    if '成本单价' in df_inventory.columns:
        print(f"\n开始删除成本单价 ≤ 2 的记录...")
        df_inventory['成本单价'] = pd.to_numeric(df_inventory['成本单价'], errors='coerce')
        before_delete = len(df_inventory)
        df_inventory = df_inventory[df_inventory['成本单价'].isna() | (df_inventory['成本单价'] > 2)].copy()
        after_delete = len(df_inventory)
        print(f"  已删除成本单价 ≤ 2 的记录: {before_delete - after_delete} 条")
        if after_delete == 0:
            raise ValueError("删除成本单价 ≤ 2 的记录后没有剩余数据，请检查数据")
    else:
        print(f"\n⚠️  库存数据中没有'成本单价'列，跳过删除成本单价 ≤ 2 数据步骤")

    # ============ 删除加盟店数据 ============
    print(f"\n开始删除加盟店的库存数据...")
    
    # 获取加盟店门店名称列表（从franchisee_store_df中提取）
    if franchisee_store_df is not None and len(franchisee_store_df) > 0:
        # 确保加盟店数据格式正确
        if '门店名称' in franchisee_store_df.columns:
            franchisee_stores = franchisee_store_df['门店名称'].astype(str).str.strip().tolist()
        else:
            # 如果没有'门店名称'列，使用第一列
            franchisee_stores = franchisee_store_df.iloc[:, 0].astype(str).str.strip().tolist()
        
        # 过滤掉空值
        franchisee_stores = [s for s in franchisee_stores if s and s != 'nan' and s != '']
        
        print(f"  加盟店列表: {len(franchisee_stores)} 个门店")
        print(f"  加盟店示例: {franchisee_stores[:5]}")
        
        # 记录删除前的数量
        before_delete = len(df_inventory)
        
        # 删除门店名称在加盟店列表中的数据
        df_inventory = df_inventory[~df_inventory['门店名称'].isin(franchisee_stores)].copy()
        
        after_delete = len(df_inventory)
        deleted_count = before_delete - after_delete
        print(f"  已删除加盟店的库存数据: {deleted_count} 条")
        print(f"  删除后剩余数据: {after_delete} 条")
        
        if after_delete == 0:
            raise ValueError("删除加盟店数据后没有剩余数据，请检查数据")
    else:
        print(f"  ⚠️ 加盟店数据为空，跳过删除加盟店数据步骤")

    # ============ 删除减近效期天数 < 180 的数据（新门店特殊处理） ============
    if '减近效期天数' in df_inventory.columns:
        print(f"\n开始删除减近效期天数 < 180 的记录...")
        df_inventory['减近效期天数'] = pd.to_numeric(df_inventory['减近效期天数'], errors='coerce')
        
        before_delete = len(df_inventory)
        
        # 判断是否有新门店数据
        if new_store_df is not None and len(new_store_df) > 0:
            print(f"  ✓ 检测到新门店数据，新门店选定的商品不参与近效期过滤")
            
            # 标准化新门店数据
            new_store_df_copy = new_store_df.copy()
            new_store_df_copy['门店名称'] = new_store_df_copy['门店名称'].astype(str).str.strip()
            new_store_df_copy['商品编码'] = new_store_df_copy['商品编码'].astype(str).str.strip()
            
            # 构建 (门店名称, 商品编码) 的集合
            new_store_keys = set(
                zip(new_store_df_copy['门店名称'], new_store_df_copy['商品编码'])
            )
            
            print(f"    新门店唯一组合数: {len(new_store_keys)}")
            
            # 标记是否是"新门店选定的记录"
            df_inventory['是否新门店'] = df_inventory.apply(
                lambda row: (str(row['门店名称']).strip(), str(row['商品编码']).strip()) in new_store_keys,
                axis=1
            )
            
            matched_count = df_inventory['是否新门店'].sum()
            print(f"    匹配到的新门店库存记录数: {matched_count}")
            
            # 过滤逻辑：新门店记录直接保留，其他记录要求减近效期天数 >= 180 或为空
            df_inventory = df_inventory[
                (df_inventory['是否新门店']) |
                (df_inventory['减近效期天数'].isna()) |
                (df_inventory['减近效期天数'] >= 180)
            ].copy()
            
            # 删除辅助列
            df_inventory = df_inventory.drop('是否新门店', axis=1)
            
            after_delete = len(df_inventory)
            deleted_count = before_delete - after_delete
            print(f"  已删除减近效期天数 < 180 的记录: {deleted_count} 条")
            print(f"    其中新门店记录已豁免（保留）: {matched_count} 条")
            
            if after_delete == 0:
                raise ValueError("删除减近效期天数 < 180 的记录后没有剩余数据，请检查数据")
        else:
            # 原逻辑：没有新门店数据，统一按减近效期天数 >= 180 过滤
            print(f"  ⚠️ 无新门店数据，使用统一规则（减近效期天数 >= 180）")
            
            df_inventory = df_inventory[
                df_inventory['减近效期天数'].isna() | 
                (df_inventory['减近效期天数'] >= 180)
            ].copy()
            
            after_delete = len(df_inventory)
            print(f"  已删除减近效期天数 < 180 的记录: {before_delete - after_delete} 条")
            
            if after_delete == 0:
                raise ValueError("删除减近效期天数 < 180 的记录后没有剩余数据，请检查数据")
    else:
        print(f"\n⚠️  库存数据中没有'减近效期天数'列，跳过删除近效期数据步骤")
    
    # ============ 删除冷链药品 ============
    if cold_chain_df is not None:
        print(f"\n开始删除冷链药品记录...")
        cold_chain_codes = set(cold_chain_df['商品编码'].astype(str).str.strip().dropna().unique())
        before_delete = len(df_inventory)
        df_inventory = df_inventory[~df_inventory['商品编码'].isin(cold_chain_codes)].copy()
        after_delete = len(df_inventory)
        print(f"  已删除冷链药品记录: {before_delete - after_delete} 条")
        if after_delete == 0:
            raise ValueError("删除冷链药品后没有剩余数据，请检查数据")
    else:
        print(f"\n⚠️  未提供冷链药品数据，跳过删除冷链药品步骤")
    
    # 删除空值
    before_drop = len(df_inventory)
    df_inventory = df_inventory[df_inventory['门店名称'] != '']
    df_inventory = df_inventory[df_inventory['门店名称'] != 'nan']
    df_inventory = df_inventory[df_inventory['商品编码'] != '']
    df_inventory = df_inventory[df_inventory['商品编码'] != 'nan']
    if len(df_inventory) < before_drop:
        print(f"已删除 {before_drop - len(df_inventory)} 行空值数据")
    
    # ============ 删除在库天数 < 100 的记录（新门店特殊处理） ============
    print(f"\n开始筛选在库天数...")

    df_inventory['在库天数'] = pd.to_numeric(df_inventory['在库天数'], errors='coerce')

    before_days_filter = len(df_inventory)

    if new_store_df is not None and len(new_store_df) > 0:
        print(f"  ✓ 检测到新门店数据: {len(new_store_df)} 条记录")
        
        # ---------- 步骤1：标记新门店记录 ----------
        print(f"\n  [步骤1] 标记新门店的（门店名称 + 商品编码）组合...")
        
        # 标准化新门店数据
        new_store_df_copy = new_store_df.copy()
        new_store_df_copy['门店名称'] = new_store_df_copy['门店名称'].astype(str).str.strip()
        new_store_df_copy['商品编码'] = new_store_df_copy['商品编码'].astype(str).str.strip()
        
        # 构建 (门店名称, 商品编码) 的集合，用于快速查找
        new_store_keys = set(
            zip(new_store_df_copy['门店名称'], new_store_df_copy['商品编码'])
        )
        
        print(f"    新门店唯一组合数: {len(new_store_keys)}")
        print(f"    示例: {list(new_store_keys)[:3]}")
        
        # 标准化库存表的门店名称和商品编码
        df_inventory['门店名称'] = df_inventory['门店名称'].astype(str).str.strip()
        df_inventory['商品编码'] = df_inventory['商品编码'].astype(str).str.strip()
        
        # 创建标记列：标记该行是否属于新门店
        df_inventory['是否新门店'] = df_inventory.apply(
            lambda row: (row['门店名称'], row['商品编码']) in new_store_keys,
            axis=1
        )
        
        matched_count = df_inventory['是否新门店'].sum()
        print(f"    匹配到的新门店库存记录数: {matched_count}")
        
        # 显示匹配到的门店-商品组合
        if matched_count > 0:
            matched_combos = df_inventory[df_inventory['是否新门店']][['门店名称', '商品编码']].drop_duplicates()
            print(f"    匹配到的门店-商品组合数: {len(matched_combos)}")
            print(f"    匹配明细（前5条）:")
            for _, row in matched_combos.head(5).iterrows():
                print(f"      {row['门店名称'][-15:]} | {row['商品编码']}")
        
        # ---------- 步骤2：筛选在库天数 ----------
        print(f"\n  [步骤2] 筛选在库天数...")
        
        before_filter = len(df_inventory)
        
        # 新门店记录无条件保留，其他记录要求在库天数 >= 100
        df_inventory = df_inventory[
            (df_inventory['是否新门店']) |
            (df_inventory['在库天数'] >= 100)
        ].copy()
        
        # 删除辅助列
        df_inventory = df_inventory.drop('是否新门店', axis=1)
        
        after_filter = len(df_inventory)
        
        print(f"    筛选前: {before_filter} 条")
        print(f"    筛选后: {after_filter} 条")
        print(f"    其中新门店保留: {matched_count} 条")
        print(f"    其他门店删除（在库天数 < 100）: {before_filter - after_filter} 条")

    else:
        print(f"  ⚠️ 无新门店数据，使用统一规则（在库天数 >= 100）")
        
        before_filter = len(df_inventory)
        df_inventory = df_inventory[df_inventory['在库天数'] >= 100].copy()
        after_filter = len(df_inventory)
        
        print(f"  已删除在库天数 < 100 的记录: {before_filter - after_filter} 条")
        print(f"  筛选后剩余: {after_filter} 条")

    after_days_filter = len(df_inventory)
    print(f"\n  筛选后总记录数: {after_days_filter} 条")

    if after_days_filter == 0:
        raise ValueError("筛选后没有符合条件的库存记录，请检查数据")
    
    # ============ ⭐ 新增汇总列：按门店+商品编码汇总库存 ============
    print(f"\n⭐ 计算汇总库存（按门店+商品编码分组汇总）...")
    
    # 确保基本单位数量是数值类型
    df_inventory['基本单位数量'] = pd.to_numeric(df_inventory['基本单位数量'], errors='coerce').fillna(0)
    
    # 计算每个门店+商品编码的汇总库存
    df_inventory['汇总库存'] = df_inventory.groupby(['门店名称', '商品编码'])['基本单位数量'].transform('sum')
    
    # 计算每个门店+商品编码的记录数（用于日志）
    df_inventory['批次数量'] = df_inventory.groupby(['门店名称', '商品编码'])['商品编码'].transform('count')
    
    # 显示汇总统计信息
    total_before = len(df_inventory)
    unique_groups = df_inventory[['门店名称', '商品编码']].drop_duplicates().shape[0]
    avg_batch = df_inventory['批次数量'].mean()
    
    print(f"  原始记录数: {total_before} 条")
    print(f"  唯一商品-门店组合: {unique_groups} 个")
    print(f"  平均每个组合有 {avg_batch:.2f} 个批次")
    print(f"  汇总列已添加，每个批次的'汇总库存'字段都是该商品在该门店的总库存")
    
    # 展示示例数据
    sample = df_inventory[['门店名称', '商品编码', '基本单位数量', '汇总库存', '批次数量']].head(10)
    print(f"\n  示例数据（前10行）：")
    print(sample.to_string(index=False))
    
    # ============ 应用商品编码映射 ============
    print(f"\n应用商品编码映射...")
    
    def apply_mapping(code):
        if isinstance(code, (int, float)):
            code = str(int(code)) if not pd.isna(code) else str(code)
        else:
            code = str(code).strip()
        return mapping.get(code, code)
    
    df_inventory['映射编码'] = df_inventory['商品编码'].apply(apply_mapping)
    df_inventory['在库天数'] = pd.to_numeric(df_inventory['在库天数'], errors='coerce')
    df_inventory = df_inventory.dropna(subset=['在库天数'])
    
    # ============ 匹配销售数据 ============
    sales_summary = sales_summary_df.copy()
    sales_summary['门店名称'] = sales_summary['门店名称'].astype(str).str.strip()
    sales_summary['商品编码'] = sales_summary['商品编码'].astype(str).str.strip()
    
    # 创建匹配键（使用映射编码）
    df_inventory['匹配键'] = df_inventory['门店名称'] + '|' + df_inventory['映射编码']
    sales_summary['匹配键'] = sales_summary['门店名称'] + '|' + sales_summary['商品编码']
    
    # 左连接匹配销售数量
    df_inventory = df_inventory.merge(
        sales_summary[['匹配键', '销售数量']],
        on='匹配键',
        how='left'
    )
    df_inventory = df_inventory.drop('匹配键', axis=1)
    
    # ============ 计算门店库存需要销售月数 ============
    print(f"\n计算'门店库存需要销售月数'和'可支配库存'...")
    
    # 使用汇总库存进行计算
    sales_null_mask = df_inventory['销售数量'].isna()
    
    # 1. 计算可支配库存（使用汇总库存）
    df_inventory['可支配库存'] = df_inventory['汇总库存']
    df_inventory.loc[~sales_null_mask, '可支配库存'] = (
        df_inventory.loc[~sales_null_mask, '汇总库存'] - 
        df_inventory.loc[~sales_null_mask, '销售数量']
    )
    df_inventory['可支配库存'] = df_inventory['可支配库存'].clip(lower=0)
    
    # 2. 计算门店库存需要销售月数（使用可支配库存）
    df_inventory['门店库存需要销售月数'] = df_inventory['可支配库存'] / df_inventory['销售数量']
    df_inventory.loc[sales_null_mask, '门店库存需要销售月数'] = 7
    df_inventory['门店库存需要销售月数'] = df_inventory['门店库存需要销售月数'].replace([float('inf'), float('-inf')], 7)
    df_inventory['门店库存需要销售月数'] = df_inventory['门店库存需要销售月数'].round(2)
    
    # 3. 重命名列
    df_inventory = df_inventory.rename(columns={
        '基本单位数量': '原批次库存',
        '汇总库存': '基本单位数量',
        '可支配库存': '可支配库存'
    })
    
    # ============ 筛选 ============
    before_filter = len(df_inventory)
    df_inventory = df_inventory[df_inventory['门店库存需要销售月数'] >= 6]
    df_inventory = df_inventory[df_inventory['基本单位数量'] >= 1]
    deleted_count = before_filter - len(df_inventory)
    
    print(f"\n筛选条件：门店库存需要销售月数 >= 6")
    print(f"  筛选前: {before_filter} 行")
    print(f"  筛选后: {len(df_inventory)} 行")
    print(f"  已删除: {deleted_count} 行")
    
    # ============ 按门店库存需要销售月数降序排序 ============
    df_inventory = df_inventory.sort_values('门店库存需要销售月数', ascending=False).reset_index(drop=True)
    
    # ============ 最终统计信息 ============
    print(f"\n{'='*60}")
    print("处理完成！")
    print(f"  最终数据: {len(df_inventory)} 行记录")
    print(f"  保留了所有批次的效期信息（共 {df_inventory['批次数量'].sum()} 个批次）")
    print(f"  原批次库存列: '原批次库存'")
    print(f"  汇总库存列: '基本单位数量'")
    print(f"  计算使用的库存: '基本单位数量'（汇总库存）")
    print(f"{'='*60}")
    
    return df_inventory


def process_sales_data_with_mapping(df_sales, mapping, shortage_df=None, inventory_file=None, in_transit_file=None, cold_chain_df=None):
    """
    处理销售数据：
    1. 筛选门店名称（必须包含'公司'和'店'，且不包含'停用'）
    2. 根据映射表替换商品编码
    3. 按门店名称和商品编码汇总销售数量
    4. 销售数量向下取整
    5. 导入库存表，匹配基本单位数量（向下取整）和在库天数
    6. 导入配送在途表，匹配配送数量（向下取整）
    7. 计算可承受销售数量 = 销售数量 - 基本单位数量 - 配送数量
    8. 只保留可承受销售数量 > 0的行
    9. ⭐ 过滤在库天数 > 150天的记录
    10. 筛选每个商品编码销售前十的门店
    11. 如果提供了缺货数据，去除在缺货中已存在的记录
    
    参数:
        df_sales: DataFrame, 销售数据
        mapping: dict, 商品编码映射字典
        shortage_df: DataFrame, 缺货数据（用于去重）
        inventory_file: str, 库存文件路径（原始库存表）
        in_transit_file: str, 配送在途商品文件路径
        cold_chain_df: DataFrame, 冷链药品数据
    返回:
        tuple: (各商品销售前十门店的数据, 所有门店商品汇总数据)
    """
    
    print("\n" + "=" * 60)
    print("处理销售数据...")
    print("=" * 60)
    
    # ============ 0. 筛选门店名称 ============
    print(f"\n开始筛选门店名称...")
    
    # 标准化门店名称
    df_sales['门店名称'] = df_sales['门店名称'].astype(str).str.strip()
    
    # 记录筛选前的数量
    before_filter = len(df_sales)
    
    # 筛选条件：必须包含'公司'，且不包含'停用'
    mask = (
        df_sales['门店名称'].str.contains('公司', na=False) & 
        ~df_sales['门店名称'].str.contains('停用', na=False)
    )
    
    df_sales = df_sales[mask].copy()
    
    after_filter = len(df_sales)
    
    print(f"  筛选前: {before_filter} 条记录")
    print(f"  筛选后: {after_filter} 条记录")
    print(f"  已删除: {before_filter - after_filter} 条记录")
    print(f"  筛选条件: 门店名称必须包含'公司'，且不包含'停用'")
    
    if after_filter == 0:
        raise ValueError("筛选后没有符合条件的门店数据，请检查门店名称格式")
    
    # ============ 1. 检查必需的列是否存在 ============
    required_columns = ['门店名称', '商品编码', '销售数量']
    missing = [col for col in required_columns if col not in df_sales.columns]
    if missing:
        raise ValueError(f"销售数据表缺少必需列: {missing}")
    
    print(f"✅ 列检查通过")

    # ============ 1.5. 删除冷链药品（商品编码在cold_chain_df中存在的记录） ============
    if cold_chain_df is not None:
        print(f"\n开始删除冷链药品记录...")
        
        # 标准化cold_chain_df中的商品编码
        cold_chain_codes = cold_chain_df['商品编码'].astype(str).str.strip().dropna().unique()
        cold_chain_codes = set(cold_chain_codes)
        
        print(f"  冷链药品编码数量: {len(cold_chain_codes)}")
        
        # 记录删除前的数量
        before_delete = len(df_sales)
        
        # 标准化df_sales的商品编码（先转为字符串）
        df_sales['商品编码'] = df_sales['商品编码'].astype(str).str.strip()
        
        # 删除商品编码在冷链列表中的记录
        df_sales = df_sales[~df_sales['商品编码'].isin(cold_chain_codes)].copy()
        
        after_delete = len(df_sales)
        
        print(f"  删除前: {before_delete} 条记录")
        print(f"  删除后: {after_delete} 条记录")
        print(f"  已删除冷链药品记录: {before_delete - after_delete} 条")
        
        if after_delete == 0:
            raise ValueError("删除冷链药品后没有剩余数据，请检查数据")
    else:
        print(f"\n⚠️  未提供冷链药品数据，跳过删除冷链药品步骤")
    
    # ============ 2. 应用映射替换商品编码 ============
    print(f"\n开始应用映射替换商品编码...")
    
    # 标准化商品编码 - 先转为字符串，再去除空值
    df_sales['商品编码_原始'] = df_sales['商品编码']  # 保留原始编码用于追踪
    df_sales['商品编码'] = df_sales['商品编码'].astype(str).str.strip()
    
    # 删除商品编码为空的行
    before_drop = len(df_sales)
    df_sales = df_sales[df_sales['商品编码'] != '']
    df_sales = df_sales[df_sales['商品编码'] != 'nan']
    if len(df_sales) < before_drop:
        print(f"已删除 {before_drop - len(df_sales)} 行商品编码为空的数据")
    
    # 应用映射
    def apply_mapping(code):
        # 如果是数字类型，转为字符串
        if isinstance(code, (int, float)):
            code = str(int(code)) if not pd.isna(code) else str(code)
        else:
            code = str(code).strip()
        
        # 查找映射
        if code in mapping:
            return mapping[code]
        else:
            return code  # 如果没有映射，保留原值
    
    df_sales['商品编码'] = df_sales['商品编码'].apply(apply_mapping)
    
    # 删除门店名称为空的行（再次确保）
    before_drop = len(df_sales)
    df_sales = df_sales[df_sales['门店名称'] != '']
    df_sales = df_sales[df_sales['门店名称'] != 'nan']
    if len(df_sales) < before_drop:
        print(f"已删除 {before_drop - len(df_sales)} 行门店名称为空的数据")
    
    # 确保销售数量是数值类型
    df_sales['销售数量'] = pd.to_numeric(df_sales['销售数量'], errors='coerce')
    
    # 删除销售数量为空的行
    before_drop = len(df_sales)
    df_sales = df_sales.dropna(subset=['销售数量'])
    if len(df_sales) < before_drop:
        print(f"已删除 {before_drop - len(df_sales)} 行销售数量为空的数据")
    
    # 再次删除商品编码为空的行（映射后可能产生空值）
    df_sales = df_sales[df_sales['商品编码'] != '']
    df_sales = df_sales[df_sales['商品编码'] != 'nan']
    
    print(f"应用映射后，数据行数: {len(df_sales)}")
    print(f"商品编码唯一值数量: {df_sales['商品编码'].nunique()}")
    
    # ============ 3. 按门店名称和商品编码汇总销售数量 ============
    print(f"\n开始汇总销售数据...")

    # 确保商品编码和门店名称都是字符串类型
    df_sales['商品编码'] = df_sales['商品编码'].astype(str)
    df_sales['门店名称'] = df_sales['门店名称'].astype(str)

    # ⭐ 先保存基础汇总数据（只经过前4步处理）
    df_summary_base = df_sales.groupby(['门店名称', '商品编码'], as_index=False)['销售数量'].sum()

    # ⭐ 销售数量向下取整（基础数据也取整）
    import math
    df_summary_base['销售数量'] = df_summary_base['销售数量'].apply(lambda x: math.floor(x) if x > 0 else 0)
    df_summary_base = df_summary_base[df_summary_base['销售数量'] > 0]

    print(f"基础汇总完成，共 {len(df_summary_base)} 条记录")

    # 分组汇总（这是完整的汇总数据，用于后续处理）
    df_summary_all = df_sales.groupby(['门店名称', '商品编码'], as_index=False)['销售数量'].sum()
    
    print(f"汇总完成，共 {len(df_summary_all)} 条记录")
    print(f"  涉及门店数: {df_summary_all['门店名称'].nunique()}")
    print(f"  涉及商品数: {df_summary_all['商品编码'].nunique()}")
    
    # ⭐ 销售数量向下取整
    import math
    print(f"\n销售数量向下取整...")
    df_summary_all['销售数量'] = df_summary_all['销售数量'].apply(lambda x: math.floor(x) if x > 0 else 0)
    
    # 删除销售数量为0的行（取整后可能为0）
    before_drop = len(df_summary_all)
    df_summary_all = df_summary_all[df_summary_all['销售数量'] > 0]
    if len(df_summary_all) < before_drop:
        print(f"已删除 {before_drop - len(df_summary_all)} 行销售数量为0的数据")
    
    print(f"取整后记录数: {len(df_summary_all)}")
    print(f"  总销售数量: {df_summary_all['销售数量'].sum():.0f}")
    
    # ============ 4. 导入库存表，匹配基本单位数量和在库天数 ============
    df_summary_all['基本单位数量'] = 0  # 初始化列
    df_summary_all['在库天数'] = None   # 初始化在库天数列
    
    if inventory_file and os.path.exists(inventory_file):
        print(f"\n导入库存表匹配基本单位数量和在库天数...")
        print(f"  读取库存文件：{inventory_file}")
        
        df_inventory_raw = pd.read_excel(inventory_file, engine='openpyxl')
        print(f"  库存数据读取成功: {len(df_inventory_raw)} 行")
        
        # 检查必需的列
        if '门店名称' not in df_inventory_raw.columns:
            raise ValueError(f"库存表缺少'门店名称'列")
        if '商品编码' not in df_inventory_raw.columns:
            raise ValueError(f"库存表缺少'商品编码'列")
        if '基本单位数量' not in df_inventory_raw.columns:
            raise ValueError(f"库存表缺少'基本单位数量'列")
        
        # 标准化门店名称和商品编码
        df_inventory_raw['门店名称'] = df_inventory_raw['门店名称'].astype(str).str.strip()
        df_inventory_raw['商品编码'] = df_inventory_raw['商品编码'].astype(str).str.strip()
        
        # 应用商品编码映射（库存表的商品编码也需要映射）
        df_inventory_raw['商品编码'] = df_inventory_raw['商品编码'].apply(apply_mapping)
        
        # 确保基本单位数量是数值类型
        df_inventory_raw['基本单位数量'] = pd.to_numeric(df_inventory_raw['基本单位数量'], errors='coerce').fillna(0)
        
        # ⭐ 处理在库天数列（如果存在）
        if '在库天数' in df_inventory_raw.columns:
            df_inventory_raw['在库天数'] = pd.to_numeric(df_inventory_raw['在库天数'], errors='coerce')
        else:
            print(f"  ⚠️ 库存表没有'在库天数'列，将使用默认值0")
            df_inventory_raw['在库天数'] = 0
        
        # ⭐ 按门店名称和商品编码汇总（同时汇总基本单位数量和在库天数）
        # 使用max作为在库天数的聚合方式（取最久的库存天数）
        inventory_summary = df_inventory_raw.groupby(['门店名称', '商品编码'], as_index=False).agg({
            '基本单位数量': 'sum',
            '在库天数': 'max'  # 使用最大值，表示这批货中最久的在库天数
        })
        
        # 基本单位数量向下取整
        inventory_summary['基本单位数量'] = inventory_summary['基本单位数量'].apply(lambda x: math.floor(x) if x > 0 else 0)
        
        # 删除基本单位数量为0的行
        inventory_summary = inventory_summary[inventory_summary['基本单位数量'] > 0]
        
        print(f"  库存汇总后: {len(inventory_summary)} 条记录")
        print(f"  总库存数量: {inventory_summary['基本单位数量'].sum():.0f}")
        print(f"  在库天数范围: {inventory_summary['在库天数'].min():.0f} ~ {inventory_summary['在库天数'].max():.0f} 天")
        
        # ⭐ 匹配库存到销售数据（同时匹配基本单位数量和库存天数）
        df_summary_all = df_summary_all.merge(
            inventory_summary[['门店名称', '商品编码', '基本单位数量', '在库天数']],
            on=['门店名称', '商品编码'],
            how='left',
            suffixes=('', '_库存')
        )
        
        # 如果存在重复列，使用库存列覆盖
        if '基本单位数量_库存' in df_summary_all.columns:
            df_summary_all['基本单位数量'] = df_summary_all['基本单位数量_库存'].fillna(0)
            df_summary_all = df_summary_all.drop('基本单位数量_库存', axis=1)
        else:
            df_summary_all['基本单位数量'] = df_summary_all['基本单位数量'].fillna(0)
        
        # ⭐ 处理在库天数（合并后可能有两列）
        if '在库天数_库存' in df_summary_all.columns:
            df_summary_all['在库天数'] = df_summary_all['在库天数_库存']
            df_summary_all = df_summary_all.drop('在库天数_库存', axis=1)
        
        # 填充在库天数为空的值（没有库存匹配的，在库天数为空）
        print(f"  匹配后记录数: {len(df_summary_all)}")
        print(f"  有库存匹配的行数: {(df_summary_all['基本单位数量'] > 0).sum()}")
        print(f"  无库存匹配的行数: {(df_summary_all['基本单位数量'] == 0).sum()}")
        print(f"  有在库天数的行数: {df_summary_all['在库天数'].notna().sum()}")
    else:
        print(f"\n⚠️ 未提供库存文件或文件不存在，跳过库存匹配")
        # 如果没有库存文件，在库天数设为None
        df_summary_all['在库天数'] = None
    
    # ============ 5. 导入配送在途表，匹配配送数量 ============
    df_summary_all['配送数量'] = 0  # 初始化列
    
    if in_transit_file and os.path.exists(in_transit_file):
        print(f"\n导入配送在途表匹配配送数量...")
        print(f"  读取配送在途文件：{in_transit_file}")
        
        df_in_transit = pd.read_excel(
            in_transit_file, 
            engine='openpyxl',
            dtype={
                '商品编码': str,
                '收货单位': str,
                '配送数量': float  # 数量列保持数值类型
            }
        )
        print(f"  配送在途数据读取成功: {len(df_in_transit)} 行")
        
        # 检查必需的列
        required_in_transit = ['商品编码', '收货单位', '配送数量']
        missing_in_transit = [col for col in required_in_transit if col not in df_in_transit.columns]
        if missing_in_transit:
            raise ValueError(f"配送在途表缺少必需列: {missing_in_transit}")
        
        # 标准化列名和数据
        df_in_transit['商品编码'] = df_in_transit['商品编码'].astype(str).str.strip()
        df_in_transit['收货单位'] = df_in_transit['收货单位'].astype(str).str.strip()
        
        # 应用商品编码映射（配送在途表的商品编码也需要映射）
        df_in_transit['商品编码'] = df_in_transit['商品编码'].apply(apply_mapping)
        
        # 确保配送数量是数值类型
        df_in_transit['配送数量'] = pd.to_numeric(df_in_transit['配送数量'], errors='coerce').fillna(0)
        
        # 按收货单位（门店名称）和商品编码汇总配送数量
        in_transit_summary = df_in_transit.groupby(['收货单位', '商品编码'], as_index=False)['配送数量'].sum()
        
        # 配送数量向下取整
        in_transit_summary['配送数量'] = in_transit_summary['配送数量'].apply(lambda x: math.floor(x) if x > 0 else 0)
        
        # 重命名列
        in_transit_summary.columns = ['门店名称', '商品编码', '配送数量']
        
        # 删除配送数量为0的行
        in_transit_summary = in_transit_summary[in_transit_summary['配送数量'] > 0]
        
        print(f"  配送在途汇总后: {len(in_transit_summary)} 条记录")
        print(f"  总配送数量: {in_transit_summary['配送数量'].sum():.0f}")
        
        # 匹配配送数量到销售数据
        df_summary_all = df_summary_all.merge(
            in_transit_summary[['门店名称', '商品编码', '配送数量']],
            on=['门店名称', '商品编码'],
            how='left',
            suffixes=('', '_在途')
        )
        
        # 如果存在重复列，使用在途列覆盖
        if '配送数量_在途' in df_summary_all.columns:
            df_summary_all['配送数量'] = df_summary_all['配送数量_在途'].fillna(0)
            df_summary_all = df_summary_all.drop('配送数量_在途', axis=1)
        else:
            df_summary_all['配送数量'] = df_summary_all['配送数量'].fillna(0)
        
        print(f"  匹配后记录数: {len(df_summary_all)}")
        print(f"  有配送匹配的行数: {(df_summary_all['配送数量'] > 0).sum()}")
        print(f"  无配送匹配的行数: {(df_summary_all['配送数量'] == 0).sum()}")
    else:
        print(f"\n⚠️ 未提供配送在途文件或文件不存在，跳配送在途匹配")
    
    # ============ 6. 计算可承受销售数量 ============
    print(f"\n计算可承受销售数量...")
    print(f"  公式: 可承受销售数量 = 销售数量 - 基本单位数量 - 配送数量")
    
    import numpy as np
    
    # 计算差值，使用 numpy 的 floor 处理浮点数精度问题
    df_summary_all['可承受销售数量'] = np.floor(
        df_summary_all['销售数量'] - df_summary_all['基本单位数量'] - df_summary_all['配送数量'] + 0.001
    )
    
    # 确保负数变为0，并转换为整数
    df_summary_all['可承受销售数量'] = df_summary_all['可承受销售数量'].apply(
        lambda x: max(0, int(x))
    )
    
    print(f"  可承受销售数量统计：")
    print(f"    最大值: {df_summary_all['可承受销售数量'].max():.0f}")
    print(f"    最小值: {df_summary_all['可承受销售数量'].min():.0f}")
    print(f"    平均值: {df_summary_all['可承受销售数量'].mean():.2f}")
    
    # 只保留可承受销售数量 > 0 的行
    before_filter = len(df_summary_all)
    df_summary_all = df_summary_all[df_summary_all['可承受销售数量'] > 0]
    after_filter = len(df_summary_all)
    
    print(f"\n筛选可承受销售数量 > 0：")
    print(f"  筛选前: {before_filter} 条")
    print(f"  筛选后: {after_filter} 条")
    print(f"  已删除: {before_filter - after_filter} 条")
    print(f"  总可承受销售数量: {df_summary_all['可承受销售数量'].sum():.0f}")
    
    # ============ 6.5 过滤在库天数 > 150天的记录 ============
    print(f"\n过滤在库天数 > 150天的记录...")
    
    # 检查是否有在库天数列
    if '在库天数' in df_summary_all.columns:
        # 确保在库天数是数值类型
        df_summary_all['在库天数'] = pd.to_numeric(df_summary_all['在库天数'], errors='coerce')
        
        before_filter = len(df_summary_all)
        
        # 统计在库天数 > 150 的记录数（用于日志）
        old_stock_count = (df_summary_all['在库天数'] > 150).sum()
        
        # 只保留在库天数 <= 150 或 在库天数为空（无库存）的记录
        # 无库存的记录（在库天数为空）应该保留，因为它们是真正的需求
        df_summary_all = df_summary_all[
            (df_summary_all['在库天数'].isna()) | (df_summary_all['在库天数'] <= 150)
        ].copy()
        
        after_filter = len(df_summary_all)
        print(f"  过滤前: {before_filter} 条")
        print(f"  其中在库天数 > 150天: {old_stock_count} 条")
        print(f"  过滤后: {after_filter} 条")
        print(f"  已删除: {before_filter - after_filter} 条（在库天数 > 150天）")
    else:
        print(f"  ⚠️ 没有'在库天数'列，跳过过滤")
    
    # ============ 7. 筛选每个商品编码销售前十的门店 ============
    print(f"\n开始筛选各商品销售前十的门店...")
    
    # 确保商品编码是字符串类型
    df_summary_all['商品编码'] = df_summary_all['商品编码'].astype(str)
    
    # 先按商品编码和可承受销售数量排序
    df_sorted = df_summary_all.sort_values(['商品编码', '可承受销售数量'], ascending=[True, False])
    
    # 对每个商品编码，取前10条
    top10_by_product = df_sorted.groupby('商品编码', group_keys=False).head(10).reset_index(drop=True)
    
    # 为每个商品添加排名
    top10_by_product['排名'] = top10_by_product.groupby('商品编码', group_keys=False).cumcount() + 1
    
    # 按商品编码和排名排序
    top10_by_product = top10_by_product.sort_values(['商品编码', '排名'])
    
    print(f"筛选完成，共 {len(top10_by_product)} 条记录")
    print(f"  涉及商品数: {top10_by_product['商品编码'].nunique()}")
    
    # ============ 8. 去除在缺货中已存在的记录 ============
    if shortage_df is not None and len(shortage_df) > 0:
        print(f"\n开始去除在缺货中已存在的记录...")
        
        # 从缺货数据中提取需要排除的组合（门店名称 + 映射编码）
        shortage_exclude = shortage_df[['缺货门店', '映射编码']].copy()
        shortage_exclude.columns = ['门店名称', '商品编码']
        shortage_exclude['门店名称'] = shortage_exclude['门店名称'].astype(str).str.strip()
        shortage_exclude['商品编码'] = shortage_exclude['商品编码'].astype(str).str.strip()
        
        # 创建排除键
        shortage_exclude['排除键'] = shortage_exclude['门店名称'] + '|' + shortage_exclude['商品编码']
        exclude_keys = set(shortage_exclude['排除键'].tolist())
        
        print(f"  缺货数据中需要排除的组合数: {len(exclude_keys)}")
        
        # 创建销售前十的键
        top10_by_product['组合键'] = top10_by_product['门店名称'] + '|' + top10_by_product['商品编码']
        
        # 统计排除前的数量
        before_exclude = len(top10_by_product)
        
        # 过滤掉在缺货中出现的组合
        top10_by_product = top10_by_product[~top10_by_product['组合键'].isin(exclude_keys)].copy()
        
        # 删除辅助列
        top10_by_product = top10_by_product.drop('组合键', axis=1)
        
        after_exclude = len(top10_by_product)
        print(f"  排除前: {before_exclude} 条")
        print(f"  排除后: {after_exclude} 条")
        print(f"  已排除: {before_exclude - after_exclude} 条（这些门店已在缺货列表中）")
        
        # 如果排除后某个商品编码的记录少于10条，重新排名
        if after_exclude < before_exclude:
            print(f"\n重新计算排名...")
            top10_by_product['排名'] = top10_by_product.groupby('商品编码', group_keys=False).cumcount() + 1
            top10_by_product = top10_by_product.sort_values(['商品编码', '排名'])
    else:
        print(f"\n未提供缺货数据，跳过去重步骤")
    
    # 显示前5个商品的示例
    print(f"\n示例数据（前5个商品的前3名）:")
    for product in top10_by_product['商品编码'].unique()[:5]:
        product_data = top10_by_product[top10_by_product['商品编码'] == product].head(3)
        print(f"  商品: {product}")
        for _, row in product_data.iterrows():
            print(f"    第{row['排名']}名: {row['门店名称']} - 可承受销售数量: {row['可承受销售数量']}")
    
    print("\n" + "=" * 60)
    print("销售数据处理完成!")
    print("=" * 60)
    
    return top10_by_product, df_summary_all, df_summary_base


def process_shortage_data_with_mapping(shortage_df, mapping, in_transit_df):
    """
    处理缺货数据：应用商品编码映射，并匹配配送在途数据
    
    参数:
        shortage_df: DataFrame, 缺货数据框（包含'商品编码'、'缺货门店'、'登记数量'列）
        mapping: dict, 商品编码映射字典
        in_transit_df: DataFrame, 配送在途数据框（包含'商品编码'、'收货单位'、'配送数量'列）
    
    返回:
        DataFrame: 处理后的缺货数据（包含'源商品编码'、'映射编码'、'原登记数量'、'配送数量'、'登记数量'等列）
    """
    print("\n" + "=" * 60)
    print("处理缺货数据 - 应用商品编码映射并匹配配送在途...")
    print("=" * 60)
    
    # 1. 处理缺货数据
    shortage_df = shortage_df.copy()
    
    # 确保源商品编码保留
    if '源商品编码' not in shortage_df.columns:
        shortage_df['源商品编码'] = shortage_df['商品编码']
    
    # 标准化商品编码
    shortage_df['商品编码'] = shortage_df['商品编码'].astype(str).str.strip()
    
    # 应用映射
    def apply_mapping(code):
        if isinstance(code, (int, float)):
            code = str(int(code)) if not pd.isna(code) else str(code)
        else:
            code = str(code).strip()
        
        if code in mapping:
            return mapping[code]
        else:
            return code
    
    shortage_df['映射编码'] = shortage_df['商品编码'].apply(apply_mapping)
    
    # 按登记数量降序排列
    shortage_df = shortage_df.sort_values('登记数量', ascending=False)
    
    # 按商品编码和门店去重（保留第一条，即登记数量最大的）
    shortage_df = shortage_df.drop_duplicates(subset=['映射编码', '缺货门店'], keep='first')
    
    print(f"缺货数据映射完成，共 {len(shortage_df)} 条记录")
    
    # 2. 处理配送在途数据
    print("\n" + "-" * 40)
    print("处理配送在途数据...")
    
    in_transit_df = in_transit_df.copy()
    
    # 标准化商品编码
    in_transit_df['商品编码'] = in_transit_df['商品编码'].astype(str).str.strip()

    # 打印前10条商品编码
    print("前10条配送在途商品编码:")
    print(in_transit_df['商品编码'].head(10))
    
    # 应用映射
    in_transit_df['映射编码'] = in_transit_df['商品编码'].apply(apply_mapping)
    
    # 根据映射编码和收货单位对配送数量进行聚合
    in_transit_agg = in_transit_df.groupby(['映射编码', '收货单位'], as_index=False)['配送数量'].sum()
    
    print(f"配送在途数据聚合完成，共 {len(in_transit_agg)} 条记录")
    
    # 3. 匹配配送数量到缺货数据
    print("\n" + "-" * 40)
    print("匹配配送数量到缺货数据...")
    
    # 重命名列以便匹配
    shortage_df = shortage_df.rename(columns={'缺货门店': '收货单位'})
    
    # 左连接匹配配送数量
    shortage_df = shortage_df.merge(
        in_transit_agg[['映射编码', '收货单位', '配送数量']],
        on=['映射编码', '收货单位'],
        how='left'
    )
    
    # 填充缺失的配送数量为0
    shortage_df['配送数量'] = shortage_df['配送数量'].fillna(0)
    
    # 4. 计算新的登记数量
    # 将原登记数量列改名
    shortage_df = shortage_df.rename(columns={'登记数量': '原登记数量'})
    
    # 计算新登记数量 = 原登记数量 - 配送数量
    shortage_df['登记数量'] = shortage_df['原登记数量'] - shortage_df['配送数量']
    
    # 删除登记数量 <= 0 的行
    shortage_df = shortage_df[shortage_df['登记数量'] > 0]
    
    print(f"匹配完成，剩余 {len(shortage_df)} 条记录（已删除登记数量<=0的行）")
    
    # 5. 统计信息
    print("\n" + "-" * 40)
    print("统计信息:")
    print(f"  总配送数量: {in_transit_agg['配送数量'].sum():.2f}")
    print(f"  匹配到的配送数量: {shortage_df['配送数量'].sum():.2f}")
    print(f"  剩余登记数量: {shortage_df['登记数量'].sum():.2f}")
    
    # 将收货单位改回缺货门店（保持列名一致）
    shortage_df = shortage_df.rename(columns={'收货单位': '缺货门店'})
    
    print("\n" + "=" * 60)
    print("处理完成！")
    print("=" * 60)
    
    return shortage_df

def process_store_area(file_path: str, sheet_name: str = 0) -> Dict[str, List[str]]:
    """
    处理门店数据，删除没有周边店的行，并转换为字典格式
    
    Args:
        file_path: 表格文件路径（支持.xlsx, .csv等）
        sheet_name: 工作表名称或索引，默认为第一个工作表
    
    Returns:
        Dict[str, List[str]]: 格式为 {门店名: [周边店列表], ...}
    """
    # 读取表格数据
    if file_path.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(file_path, sheet_name=sheet_name)
    else:
        df = pd.read_csv(file_path)
    
    # 获取列名
    columns = df.columns.tolist()
    
    # 第一列作为门店列，其余作为周边店列
    store_col = columns[0]
    neighbor_cols = columns[1:]
    
    result = {}
    
    for _, row in df.iterrows():
        # 获取门店名称
        store_name = str(row[store_col]).strip() if pd.notna(row[store_col]) else ''
        
        # 跳过空门店名称
        if not store_name:
            continue
        
        # 获取所有周边店（去除空值）
        neighbors = []
        for col in neighbor_cols:
            value = row[col]
            # 检查是否为空值（None, NaN, 空字符串, 空白字符串）
            if pd.notna(value) and str(value).strip() != '':
                neighbors.append(str(value).strip())
        
        # 如果有周边店，则添加到结果中
        if neighbors:
            result[store_name] = neighbors
    
    return result

def generate_allocation_plan(shortage_df, inventory_df, store_area_dict):
    """
    生成调拨方案（优化版）：
    1. 按登记数量降序处理缺货记录
    2. 优先从周边门店调拨（按字典顺序），周边门店不足时按'在库天数'降序调拨
    3. 实时扣减库存，库存为0时自动删除该行
    4. 生成门店调拨方案和总部调拨方案
    
    参数:
        shortage_df: DataFrame, 缺货数据（包含'映射编码', '缺货门店', '登记数量'）
        inventory_df: DataFrame, 库存数据（包含'商品编码', '映射编码', '门店名称', '基本单位数量', '在库天数'）
        store_area_dict: dict, 门店周边店映射字典，格式为 {门店名: [周边店列表]}
    
    返回:
        tuple: (更新后的缺货DataFrame, 更新后的库存DataFrame)
    """
    print("\n" + "=" * 60)
    print("生成调拨方案（优化版）...")
    print("=" * 60)
    
    import time
    start_time = time.time()
    
    # 复制数据
    shortage_work = shortage_df.copy()
    inventory_work = inventory_df.copy()
    
    # 确保数值类型正确
    shortage_work['登记数量'] = pd.to_numeric(shortage_work['登记数量'], errors='coerce').fillna(0)
    inventory_work['基本单位数量'] = pd.to_numeric(inventory_work['基本单位数量'], errors='coerce').fillna(0)
    
    # 过滤无效数据
    shortage_work = shortage_work[shortage_work['登记数量'] > 0].reset_index(drop=True)
    inventory_work = inventory_work[inventory_work['基本单位数量'] > 0].reset_index(drop=True)
    
    if len(shortage_work) == 0:
        print("⚠️ 没有缺货记录")
        return shortage_work, inventory_work
    
    # ============ 内部库存消化（向量化优化） ============
    print("\n" + "-" * 60)
    print("开始内部库存消化（优先使用本店滞销库存）...")
    print("-" * 60)
    
    # 初始化内部消化相关列
    shortage_work['内部消化数量'] = 0
    shortage_work['实际调拨需求'] = shortage_work['登记数量']
    shortage_work['消化状态'] = '未消化'
    
    # ========== 向量化优化：使用groupby聚合库存 ==========
    # 1. 聚合库存数据：按(门店名称, 映射编码)分组，汇总库存
    inventory_agg = inventory_work.groupby(['门店名称', '映射编码'], as_index=False).agg({
        '商品编码': 'first',  # 取第一个商品编码
        '基本单位数量': 'sum',
        '在库天数': 'first'
    })
    
    # 重命名列以避免冲突
    inventory_agg = inventory_agg.rename(columns={
        '商品编码': '商品编码_inv',
        '基本单位数量': '库存数量',
        '在库天数': '在库天数_inv'
    })
    
    # 2. 合并缺货和库存数据（左连接）
    merged = shortage_work.merge(
        inventory_agg,
        left_on=['缺货门店', '映射编码'],
        right_on=['门店名称', '映射编码'],
        how='left'
    )
    
    # 3. 计算可消化数量
    # 将NaN库存视为0
    merged['库存数量'] = merged['库存数量'].fillna(0)
    merged['可消化数量'] = merged[['登记数量', '库存数量']].min(axis=1)
    merged['内部消化数量'] = merged['可消化数量']
    merged['实际调拨需求'] = merged['登记数量'] - merged['可消化数量']
    
    # 4. 更新库存数据：扣除被消化的库存
    # 找出有内部消化的记录
    digest_mask = merged['可消化数量'] > 0
    
    if digest_mask.any():
        # 准备需要扣减的库存数据
        digest_records = merged[digest_mask][['缺货门店', '映射编码', '可消化数量']].copy()
        digest_records = digest_records.rename(columns={
            '缺货门店': '门店名称',
            '映射编码': '映射编码',
            '可消化数量': '扣减数量'
        })
        
        # 使用向量化操作更新库存
        # 方法：按(门店名称, 映射编码)分组计算总扣减量
        digest_summary = digest_records.groupby(['门店名称', '映射编码'], as_index=False)['扣减数量'].sum()
        
        # 合并到库存数据
        inventory_work = inventory_work.merge(
            digest_summary,
            on=['门店名称', '映射编码'],
            how='left'
        )
        
        # 计算扣减后的库存
        inventory_work['扣减数量'] = inventory_work['扣减数量'].fillna(0)
        inventory_work['基本单位数量'] = inventory_work['基本单位数量'] - inventory_work['扣减数量']
        inventory_work = inventory_work.drop('扣减数量', axis=1)
        
        # 过滤掉库存为0的记录
        inventory_work = inventory_work[inventory_work['基本单位数量'] > 0].reset_index(drop=True)
        
        # 统计消化数量
        total_digested = digest_summary['扣减数量'].sum()
        total_digested_rows = len(digest_summary)
        
        print(f"\n内部消化完成（向量化处理）：")
        print(f"  消化总数量: {total_digested}")
        print(f"  消化记录数: {total_digested_rows}")
        
        # 更新缺货数据的消化状态
        merged.loc[merged['可消化数量'] > 0, '消化状态'] = merged.loc[merged['可消化数量'] > 0, '实际调拨需求'].apply(
            lambda x: '完全消化' if x == 0 else '部分消化'
        )
    
    # 5. 更新缺货数据
    # 保留所有需要的列
    result_columns = ['缺货门店', '映射编码', '登记数量', '内部消化数量', '实际调拨需求', '消化状态']
    # 如果有其他列需要保留
    for col in shortage_work.columns:
        if col not in result_columns:
            result_columns.append(col)
    
    # 更新短缺数据
    shortage_work_all = merged[result_columns].copy()
    
    # 准备需要调拨的数据（实际调拨需求 > 0）
    shortage_work = merged[merged['实际调拨需求'] > 0][result_columns].copy()
    
    # 统计信息
    total_shortage_records = len(shortage_work_all)
    fully_digested = (shortage_work_all['消化状态'] == '完全消化').sum()
    partially_digested = (shortage_work_all['消化状态'] == '部分消化').sum()
    not_digested = (shortage_work_all['消化状态'] == '未消化').sum()
    
    print(f"  总缺货记录: {total_shortage_records}")
    print(f"  完全消化记录: {fully_digested}")
    print(f"  部分消化记录: {partially_digested}")
    print(f"  未消化记录: {not_digested}")
    print(f"  需要调拨记录: {len(shortage_work)}")
    print(f"  剩余库存记录: {len(inventory_work)}")
    print("-" * 60)
    
    # 如果消化后没有需要调拨的缺货了，直接返回所有数据
    if len(shortage_work) == 0:
        print("✅ 所有缺货已被内部库存消化，无需调拨！")
        return shortage_work_all, inventory_work
    
    # ============ 继续处理门店调拨和总部调拨 ============
    # 初始化调拨方案列（只对需要调拨的记录）
    shortage_work['门店调拨方案'] = pd.Series(dtype='object')
    shortage_work['总部调拨方案'] = pd.Series(dtype='object')
    
    # 按实际调拨需求降序排序（大需求优先）
    shortage_work = shortage_work.sort_values('实际调拨需求', ascending=False).reset_index(drop=True)
    
    print(f"\n📊 正在处理 {len(shortage_work)} 条缺货记录，{len(inventory_work)} 条库存...")
    
    # ============ 构建库存索引 ============
    # 使用字典: key=(映射编码, 门店名称), value=库存信息
    inventory_dict = {}
    for _, row in inventory_work.iterrows():
        key = (row['映射编码'], row['门店名称'])
        inventory_dict[key] = {
            '商品编码': row['商品编码'],
            '库存': row['基本单位数量'],
            '在库天数': row.get('在库天数', 0)
        }
    
    # ============ 按映射编码分组库存门店 ============
    product_stores_dict = {}
    for _, row in inventory_work.iterrows():
        mapped_code = row['映射编码']
        store = row['门店名称']
        qty = row['基本单位数量']
        days = row.get('在库天数', 0)
        
        if mapped_code not in product_stores_dict:
            product_stores_dict[mapped_code] = []
        product_stores_dict[mapped_code].append({
            '门店名称': store,
            '商品编码': row['商品编码'],
            '库存': qty,
            '在库天数': days
        })
    
    print(f"✅ 索引构建完成，共 {len(product_stores_dict)} 个商品有库存")
    print(f"✅ 调拨优先级: 优先周边门店（按字典顺序），再按在库天数降序")
    
    # 统计变量
    total_shortage = 0
    total_allocated_from_store = 0
    total_allocated_from_hq = 0
    processed_count = 0
    
    # ============ 主循环 ============
    for idx, row in shortage_work.iterrows():
        mapped_code = row['映射编码']
        demand_qty = row['实际调拨需求']
        store_name = row['缺货门店']
        
        if demand_qty <= 0:
            continue
        
        processed_count += 1
        total_shortage += demand_qty
        
        # 检查该商品是否有库存
        if mapped_code not in product_stores_dict:
            shortage_work.loc[idx, '门店调拨方案'] = None
            shortage_work.loc[idx, '总部调拨方案'] = int(demand_qty)
            total_allocated_from_hq += demand_qty
            continue
        
        # 获取该商品的所有库存门店（排除自身门店）
        all_stores = [s for s in product_stores_dict[mapped_code] if s['门店名称'] != store_name]
        
        # 如果排除自身后没有其他门店有库存
        if not all_stores:
            shortage_work.loc[idx, '门店调拨方案'] = None
            shortage_work.loc[idx, '总部调拨方案'] = int(demand_qty)
            total_allocated_from_hq += demand_qty
            continue
        
        # ============ 核心优化：构建调拨优先级列表 ============
        # 1. 获取周边门店列表（按字典顺序）
        nearby_stores = store_area_dict.get(store_name, [])
        
        # 2. 将库存门店分为两组：周边门店和其他门店
        nearby_stores_with_stock = []
        other_stores_with_stock = []
        
        # 创建门店名称到库存信息的映射（快速查找）
        store_info_map = {s['门店名称']: s for s in all_stores}
        
        # 按周边门店列表顺序提取
        for nearby_store in nearby_stores:
            if nearby_store in store_info_map:
                nearby_stores_with_stock.append(store_info_map[nearby_store])
                # 从映射中移除，避免后续重复处理
                store_info_map.pop(nearby_store, None)
        
        # 剩余的门店作为其他门店
        other_stores_with_stock = list(store_info_map.values())
        
        # 3. 对其他门店按在库天数降序排序
        other_stores_with_stock.sort(
            key=lambda x: (x['在库天数'], x['库存']),
            reverse=True
        )
        
        # 4. 合并优先级列表：周边门店（保持字典顺序）+ 其他门店（按在库天数降序）
        priority_stores = nearby_stores_with_stock + other_stores_with_stock
        
        # 打印优先级示例（仅第一个缺货记录）
        if processed_count == 1:
            print(f"\n📋 调拨优先级示例（缺货门店: {store_name}）:")
            print(f"  周边门店列表: {nearby_stores}")
            print(f"  有库存的周边门店: {[s['门店名称'] for s in nearby_stores_with_stock]}")
            print(f"  其他可调拨门店（按在库天数降序）:")
            for i, s in enumerate(other_stores_with_stock[:5], 1):
                print(f"    第{i}优先: {s['门店名称']} (在库{s['在库天数']}天, 库存{s['库存']})")
            if len(other_stores_with_stock) > 5:
                print(f"    ... 还有 {len(other_stores_with_stock) - 5} 个门店")
        
        remaining_demand = demand_qty
        store_allocation = []
        seq_num = 1
        
        # ============ 按优先级遍历门店分配 ============
        for store_info in priority_stores:
            if remaining_demand <= 0:
                break
            
            from_store = store_info['门店名称']
            current_stock = store_info['库存']
            product_code_original = store_info['商品编码']
            
            if current_stock <= 0:
                continue
            
            # 计算可调拨数量（取库存和需求的较小值）
            allocate_qty = min(current_stock, remaining_demand)
            
            if allocate_qty > 0:
                # 记录调拨方案（标记是否为周边门店）
                is_nearby = from_store in nearby_stores
                nearby_tag = "【周边】" if is_nearby else ""
                store_allocation.append(
                    f"{seq_num}.{from_store}调拨{product_code_original}数量{int(allocate_qty)}{nearby_tag}"
                )
                seq_num += 1
                
                # 更新库存
                store_info['库存'] = current_stock - allocate_qty
                
                # 更新字典中的库存
                key = (mapped_code, from_store)
                if store_info['库存'] <= 0:
                    inventory_dict[key]['库存'] = 0
                else:
                    inventory_dict[key]['库存'] = store_info['库存']
                
                remaining_demand -= allocate_qty
                total_allocated_from_store += allocate_qty
        
        # 生成门店调拨方案
        if store_allocation:
            shortage_work.loc[idx, '门店调拨方案'] = '；'.join(store_allocation)
        else:
            shortage_work.loc[idx, '门店调拨方案'] = None
        
        # 总部调拨
        if remaining_demand > 0:
            shortage_work.loc[idx, '总部调拨方案'] = int(remaining_demand)
            total_allocated_from_hq += remaining_demand
        else:
            shortage_work.loc[idx, '总部调拨方案'] = 0
    
    elapsed_time = time.time() - start_time
    
    print(f"\n调拨方案生成完成！")
    print(f"  处理缺货记录数: {processed_count}")
    print(f"  总需求数量: {total_shortage}")
    print(f"  门店调拨数量: {total_allocated_from_store}")
    print(f"  总部调拨数量: {total_allocated_from_hq}")
    if total_shortage > 0:
        print(f"  满足率: {total_allocated_from_store/total_shortage*100:.1f}%")
    print(f"  ⏱️ 耗时: {elapsed_time:.2f} 秒")
    
    # ============ 合并所有缺货数据（包括完全消化的） ============
    # 如果 shortage_work 中有调拨方案，需要合并回去
    if len(shortage_work) > 0:
        # 创建调拨方案的映射字典
        transfer_map = {}
        for _, row in shortage_work.iterrows():
            key = (row['缺货门店'], row['映射编码'])
            transfer_map[key] = {
                '门店调拨方案': row.get('门店调拨方案', None),
                '总部调拨方案': row.get('总部调拨方案', 0)
            }
        
        # 确保 shortage_work_all 有调拨方案列
        if '门店调拨方案' not in shortage_work_all.columns:
            shortage_work_all['门店调拨方案'] = None
        if '总部调拨方案' not in shortage_work_all.columns:
            shortage_work_all['总部调拨方案'] = 0
        
        # 更新所有记录中的调拨方案
        for idx, row in shortage_work_all.iterrows():
            key = (row['缺货门店'], row['映射编码'])
            if key in transfer_map:
                shortage_work_all.at[idx, '门店调拨方案'] = transfer_map[key]['门店调拨方案']
                shortage_work_all.at[idx, '总部调拨方案'] = transfer_map[key]['总部调拨方案']
            else:
                # 完全消化的记录，没有调拨方案
                shortage_work_all.at[idx, '门店调拨方案'] = None
                shortage_work_all.at[idx, '总部调拨方案'] = 0
    
    print("\n" + "=" * 60)
    print("调拨方案生成完成!")
    print("=" * 60)
    
    return shortage_work_all, inventory_work


def generate_store_transfer_table(shortage_df, inventory_df):
    """
    生成门店调拨明细表（优化版）
    
    参数:
        shortage_df: DataFrame, 缺货数据（包含'映射编码', '缺货门店', '登记数量', '门店调拨方案'）
        inventory_df: DataFrame, 库存数据（包含'商品编码', '映射编码', '门店名称', '通用名', '规格', '生产厂商', '商品级别','在库天数',
                                     '生产日期', '有效期至', '减近效期天数'）
    
    返回:
        DataFrame: 门店调拨明细表（商品编码、通用名、规格、生产厂商、调出门店、调入门店、数量、是否周边调拨、
                                  生产日期、有效期至、减近效期天数）
    """
    print("\n" + "=" * 60)
    print("生成门店调拨明细表（优化版）...")
    print("=" * 60)
    
    import time
    import re
    start_time = time.time()
    
    # 预编译正则表达式（性能优化）
    # 修改正则表达式以支持可选的【周边】标记
    pattern = re.compile(r'(\d+)\.(.+?)调拨(.+?)数量(\d+)(?:【周边】)?')
    
    transfer_records = []
    
    # 过滤有门店调拨方案的记录
    has_allocation = shortage_df['门店调拨方案'].notna() & (shortage_df['门店调拨方案'] != '') & (shortage_df['门店调拨方案'] != 'None')
    filtered_df = shortage_df[has_allocation].copy()
    
    if len(filtered_df) == 0:
        print("⚠️ 没有门店调拨记录")
        return pd.DataFrame(columns=['商品编码', '通用名', '规格', '生产厂商', '商品级别', '调出门店', '调入门店', '数量', 
                                     '是否周边调拨', '生产日期', '有效期至', '减近效期天数', '在库天数'])
    
    print(f"📊 正在解析 {len(filtered_df)} 条调拨方案...")
    
    # ============ 构建商品信息映射字典（优化性能） ============
    print("正在构建商品信息映射...")
    
    # 从inventory_df中提取商品信息（按门店+商品编码去重）
    # 注意：同一个商品在不同门店可能有不同的生产日期/有效期
    product_store_info_df = inventory_df[['商品编码', '门店名称', '通用名', '规格', '生产厂商', '商品级别','在库天数',
                                          '生产日期', '有效期至', '减近效期天数']].drop_duplicates(subset=['商品编码', '门店名称'])
    
    # 创建复合键映射字典：(商品编码, 门店名称) -> 商品信息
    product_store_info_dict = {}
    for _, row in product_store_info_df.iterrows():
        product_code = str(row['商品编码']).strip()
        store_name = str(row['门店名称']).strip()
        key = (product_code, store_name)
        product_store_info_dict[key] = {
            '通用名': row.get('通用名', ''),
            '规格': row.get('规格', ''),
            '生产厂商': row.get('生产厂商', ''),
            '商品级别': row.get('商品级别', ''),
            '生产日期': row.get('生产日期', ''),
            '有效期至': row.get('有效期至', ''),
            '减近效期天数': row.get('减近效期天数', ''),
            '在库天数': row.get('在库天数', '')
        }
    
    # 修正上面的统计打印
    print(f"  已构建 {len(product_store_info_dict)} 个门店-商品组合的信息映射")
    
    # 统计缺失信息的记录
    missing_info_count = 0
    missing_store_product_count = 0
    
    # ============ 批量解析 ============
    for _, row in filtered_df.iterrows():
        shortage_store = row['缺货门店']
        allocation_plan = row['门店调拨方案']
        
        # 使用预编译的正则表达式
        items = allocation_plan.split('；')
        
        for item in items:
            if not item.strip():
                continue
            
            match = pattern.search(item)
            if match:
                # 序号 = match.group(1)  # 不使用，但保留
                from_store = match.group(2).strip()
                product_code = match.group(3).strip()
                quantity = int(match.group(4))
                
                # 检查是否包含【周边】标记
                is_nearby = '【周边】' in item
                
                # 使用复合键获取商品信息（需要同时匹配商品编码和门店名称）
                key = (product_code, from_store)
                product_info = product_store_info_dict.get(key, {})
                
                generic_name = product_info.get('通用名', '')
                specification = product_info.get('规格', '')
                manufacturer = product_info.get('生产厂商', '')
                prod_date = product_info.get('生产日期', '')
                invalid_date = product_info.get('有效期至', '')
                jxq_days = product_info.get('减近效期天数', '')
                in_stock_days = product_info.get('在库天数', '')
                product_level = product_info.get('商品级别', '')
                
                # 如果找不到该门店的商品信息，记录警告
                if not product_info:
                    missing_store_product_count += 1
                elif not generic_name and not specification and not manufacturer:
                    missing_info_count += 1
                
                transfer_records.append({
                    '商品编码': product_code,
                    '通用名': generic_name,
                    '规格': specification,
                    '生产厂商': manufacturer,
                    '生产日期': prod_date,
                    '商品级别': product_level,
                    '有效期至': invalid_date,
                    '减近效期天数': jxq_days,
                    '在库天数': in_stock_days,
                    '调出门店': from_store,
                    '调入门店': shortage_store,
                    '数量': quantity,
                    '是否周边调拨': '是' if is_nearby else '否'
                })
    
    elapsed_time = time.time() - start_time
    
    # 创建DataFrame
    transfer_df = pd.DataFrame(transfer_records)
    
    if len(transfer_df) > 0:
        # 按商品编码和调出门店排序
        transfer_df = transfer_df.sort_values(['商品编码', '调出门店']).reset_index(drop=True)
        
        print(f"✅ 门店调拨明细表生成完成！")
        print(f"  调拨记录数: {len(transfer_df)}")
        print(f"  涉及调出门店数: {transfer_df['调出门店'].nunique()}")
        print(f"  涉及调入门店数: {transfer_df['调入门店'].nunique()}")
        print(f"  涉及商品数: {transfer_df['商品编码'].nunique()}")
        
        # 统计周边调拨情况
        nearby_count = transfer_df[transfer_df['是否周边调拨'] == '是'].shape[0]
        if nearby_count > 0:
            nearby_qty = transfer_df[transfer_df['是否周边调拨'] == '是']['数量'].sum()
            total_qty = transfer_df['数量'].sum()
            print(f"  周边调拨记录数: {nearby_count} 条，数量: {nearby_qty} ({nearby_qty/total_qty*100:.1f}%)")
        
        # 统计商品信息缺失情况
        if missing_store_product_count > 0:
            print(f"  ⚠️ 有 {missing_store_product_count} 条记录在库存表中找不到对应的（商品编码+门店名称）组合")
        if missing_info_count > 0:
            print(f"  ⚠️ 有 {missing_info_count} 条记录的商品信息缺失（通用名/规格/生产厂商）")
        
        # 统计日期信息完整性
        date_missing = transfer_df['生产日期'].isna().sum() + (transfer_df['生产日期'] == '').sum()
        if date_missing > 0:
            print(f"  ⚠️ 有 {date_missing} 条记录缺少生产日期")
        
        print(f"  ⏱️ 耗时: {elapsed_time:.2f} 秒")
        
        # 显示汇总信息（前10条）
        print("\n各调出门店调拨汇总（前10）：")
        summary_by_store = transfer_df.groupby('调出门店')['数量'].sum().sort_values(ascending=False).head(10)
        for store, qty in summary_by_store.items():
            # 检查该门店是否有周边调拨
            nearby_qty_store = transfer_df[(transfer_df['调出门店'] == store) & (transfer_df['是否周边调拨'] == '是')]['数量'].sum()
            if nearby_qty_store > 0:
                print(f"  {store}: {qty} (周边调拨: {nearby_qty_store})")
            else:
                print(f"  {store}: {qty}")
        
        # 显示商品信息示例
        print("\n调拨明细示例（前5条）：")
        display_cols = ['商品编码', '通用名', '规格', '生产厂商', '商品级别', '生产日期', '有效期至', '减近效期天数', '在库天数', '调出门店', '调入门店', '数量', 
                       '是否周边调拨']
        print(transfer_df[display_cols].head(5).to_string(index=False))
        
    else:
        print("⚠️ 没有生成任何调拨记录（所有缺货都由总部调拨）")
    
    print("\n" + "=" * 60)
    
    return transfer_df

def generate_top10_transfer_table(sales_top10_df, inventory_df, store_area_dict):
    """
    生成销售前十调拨明细表（优化版）
    
    参数:
        sales_top10_df: DataFrame, 销售前十数据（包含'商品编码', '门店名称', '可承受销售数量'）
        inventory_df: DataFrame, 库存数据（包含'商品编码', '门店名称', '基本单位数量', '在库天数','商品级别' 
                                    '通用名', '规格', '生产厂商', '生产日期', '有效期至', '减近效期天数'）
        store_area_dict: dict, 门店周边店映射字典，格式为 {门店名: [周边店列表]}
    
    返回:
        DataFrame: 前十调拨明细表（商品编码、通用名、规格、生产厂商、商品级别、调出门店、调入门店、数量、是否周边调拨、
                                  生产日期、有效期至、减近效期天数）
    """
    print("\n" + "=" * 60)
    print("生成销售前十调拨明细表（优化版）...")
    print("=" * 60)
    
    import time
    start_time = time.time()
    
    # 复制数据
    sales_work = sales_top10_df.copy()
    inventory_work = inventory_df.copy()
    
    # 确保数值类型正确
    sales_work['可承受销售数量'] = pd.to_numeric(sales_work['可承受销售数量'], errors='coerce').fillna(0)
    inventory_work['基本单位数量'] = pd.to_numeric(inventory_work['基本单位数量'], errors='coerce').fillna(0)
    
    # 确保在库天数列存在，如果不存在则创建默认值
    if '在库天数' not in inventory_work.columns:
        print("⚠️ 库存数据中没有'在库天数'列，使用默认值0")
        inventory_work['在库天数'] = 0
    else:
        inventory_work['在库天数'] = pd.to_numeric(inventory_work['在库天数'], errors='coerce').fillna(0)
    
    # 确保日期列存在
    date_columns = ['生产日期', '有效期至', '减近效期天数','商品级别']
    for col in date_columns:
        if col not in inventory_work.columns:
            print(f"⚠️ 库存数据中没有'{col}'列，使用默认空值")
            inventory_work[col] = ''
    
    # 过滤无效数据
    sales_work = sales_work[sales_work['可承受销售数量'] > 0].copy()
    inventory_work = inventory_work[inventory_work['基本单位数量'] > 0].copy()
    
    if len(sales_work) == 0:
        print("⚠️ 没有需要调拨的需求")
        return pd.DataFrame(columns=['商品编码', '通用名', '规格', '生产厂商', '商品级别', '在库天数','调出门店', '调入门店', '数量', 
                                     '是否周边调拨', '生产日期', '有效期至', '减近效期天数'])
    
    # 按可承受销售数量降序排序（大需求优先）
    sales_work = sales_work.sort_values('可承受销售数量', ascending=False).reset_index(drop=True)
    
    print(f"📊 正在处理 {len(sales_work)} 条需求，{len(inventory_work)} 条库存...")
    
    # ============ 构建商品信息映射字典（包含日期信息） ============
    print("正在构建商品信息映射...")
    
    # 构建复合键映射：(商品编码, 门店名称) -> 商品信息（包含日期）
    product_store_info_dict = {}
    for _, row in inventory_work.iterrows():
        product_code = str(row['商品编码']).strip()
        store_name = str(row['门店名称']).strip()
        key = (product_code, store_name)
        
        product_store_info_dict[key] = {
            '通用名': row.get('通用名', ''),
            '规格': row.get('规格', ''),
            '生产厂商': row.get('生产厂商', ''),
            '生产日期': row.get('生产日期', ''),
            '商品级别': row.get('商品级别', ''),
            '有效期至': row.get('有效期至', ''),
            '减近效期天数': row.get('减近效期天数', ''),
            '库存': row.get('基本单位数量', 0),
            '在库天数': row.get('在库天数', 0)
        }
    
    print(f"  已构建 {len(product_store_info_dict)} 个门店-商品组合的信息映射")
    
    # ============ 构建库存字典 ============
    # 使用字典: key=(商品编码, 门店名称), value=库存信息
    inventory_dict = {}
    for _, row in inventory_work.iterrows():
        key = (row['商品编码'], row['门店名称'])
        inventory_dict[key] = {
            '商品编码': row['商品编码'],
            '库存': row['基本单位数量'],
            '在库天数': row['在库天数'],
        }
    
    # ============ 按商品分组库存门店 ============
    # 每个商品有哪些门店有库存
    product_stores_dict = {}
    for _, row in inventory_work.iterrows():
        product = row['商品编码']
        store = row['门店名称']
        qty = row['基本单位数量']
        days = row['在库天数']
        
        if product not in product_stores_dict:
            product_stores_dict[product] = []
        product_stores_dict[product].append({
            '门店名称': store,
            '商品编码': row['商品编码'],
            '库存': qty,
            '在库天数': days
        })
    
    print(f"✅ 索引构建完成，共 {len(product_stores_dict)} 个商品有库存")
    print(f"✅ 调拨优先级: 优先周边门店（按字典顺序），再按在库天数降序")
    
    # 调拨明细记录
    transfer_records = []
    total_demand = 0
    total_allocated = 0
    total_nearby_allocated = 0
    processed_count = 0
    skipped_count = 0
    missing_info_count = 0
    missing_date_count = 0
    nearby_store_count = 0
    other_store_count = 0
    
    # ============ 主循环 ============
    for _, sales_row in sales_work.iterrows():
        product_code = sales_row['商品编码']
        demand_qty = sales_row['可承受销售数量']
        demand_store = sales_row['门店名称']
        
        if demand_qty <= 0:
            continue
        
        processed_count += 1
        total_demand += demand_qty
        
        # 检查该商品是否有库存
        if product_code not in product_stores_dict:
            skipped_count += 1
            continue
        
        # 获取该商品的所有库存门店
        all_stores = product_stores_dict[product_code]
        
        # ============ 核心优化：构建调拨优先级列表 ============
        # 1. 获取周边门店列表（按字典顺序）
        nearby_stores = store_area_dict.get(demand_store, [])
        
        # 2. 将库存门店分为两组：周边门店和其他门店
        nearby_stores_with_stock = []
        other_stores_with_stock = []
        
        # 创建门店名称到库存信息的映射（快速查找）
        store_info_map = {s['门店名称']: s for s in all_stores}
        
        # 按周边门店列表顺序提取
        for nearby_store in nearby_stores:
            if nearby_store in store_info_map:
                nearby_stores_with_stock.append(store_info_map[nearby_store])
                # 从映射中移除，避免后续重复处理
                store_info_map.pop(nearby_store, None)
        
        # 剩余的门店作为其他门店
        other_stores_with_stock = list(store_info_map.values())
        
        # 3. 对其他门店按在库天数降序排序
        other_stores_with_stock.sort(
            key=lambda x: (x['在库天数'], x['库存']),
            reverse=True
        )
        
        # 4. 合并优先级列表：周边门店（保持字典顺序）+ 其他门店（按在库天数降序）
        priority_stores = nearby_stores_with_stock + other_stores_with_stock
        
        # 打印优先级示例（仅第一个缺货记录）
        if processed_count == 1:
            print(f"\n📋 调拨优先级示例（需求门店: {demand_store}）:")
            print(f"  周边门店列表: {nearby_stores}")
            print(f"  有库存的周边门店: {[s['门店名称'] for s in nearby_stores_with_stock]}")
            print(f"  其他可调拨门店（按在库天数降序）:")
            for i, s in enumerate(other_stores_with_stock[:5], 1):
                print(f"    第{i}优先: {s['门店名称']} (在库{s['在库天数']}天, 库存{s['库存']})")
            if len(other_stores_with_stock) > 5:
                print(f"    ... 还有 {len(other_stores_with_stock) - 5} 个门店")
        
        remaining_demand = demand_qty
        
        # ============ 按优先级遍历门店分配 ============
        for store_info in priority_stores:
            if remaining_demand <= 0:
                break
            
            from_store = store_info['门店名称']
            current_stock = store_info['库存']
            
            if current_stock <= 0:
                continue
            
            # 计算可调拨数量（取库存和需求的较小值）
            allocate_qty = min(current_stock, remaining_demand)
            
            if allocate_qty > 0:
                # 判断是否为周边门店
                is_nearby = from_store in nearby_stores
                
                if is_nearby:
                    nearby_store_count += 1
                    total_nearby_allocated += allocate_qty
                else:
                    other_store_count += 1
                
                # 获取该门店的商品信息（包含日期）
                key = (product_code, from_store)
                product_info = product_store_info_dict.get(key, {})
                
                generic_name = product_info.get('通用名', '')
                specification = product_info.get('规格', '')
                manufacturer = product_info.get('生产厂商', '')
                prod_date = product_info.get('生产日期', '')
                invalid_date = product_info.get('有效期至', '')
                jxq_days = product_info.get('减近效期天数', '')
                product_level = product_info.get('商品级别', '')
                in_stock_days = product_info.get('在库天数', '')
                
                # 如果商品信息为空，记录警告
                if not generic_name and not specification and not manufacturer:
                    missing_info_count += 1
                
                # 检查日期信息是否缺失
                if not prod_date or not invalid_date:
                    missing_date_count += 1
                
                # 记录调拨明细
                transfer_records.append({
                    '商品编码': product_code,
                    '通用名': generic_name,
                    '规格': specification,
                    '商品级别': product_level,
                    '生产厂商': manufacturer,
                    '生产日期': prod_date,
                    '有效期至': invalid_date,
                    '减近效期天数': jxq_days,
                    '在库天数': in_stock_days,  # 保留用于统计
                    '调出门店': from_store,
                    '调入门店': demand_store,
                    '数量': int(allocate_qty),
                    '是否周边调拨': '是' if is_nearby else '否'
                })
                
                # ============ 更新库存 ============
                # 更新store_info中的库存
                store_info['库存'] = current_stock - allocate_qty
                
                # 同时更新字典中的库存（保持一致性）
                dict_key = (product_code, from_store)
                if store_info['库存'] <= 0:
                    inventory_dict[dict_key]['库存'] = 0
                else:
                    inventory_dict[dict_key]['库存'] = store_info['库存']
                
                remaining_demand -= allocate_qty
                total_allocated += allocate_qty
    
    elapsed_time = time.time() - start_time
    
    # 创建调拨明细表
    transfer_df = pd.DataFrame(transfer_records)
    if len(transfer_df) > 0:
        # 按商品编码和是否周边调拨排序（周边调拨优先显示）
        transfer_df = transfer_df.sort_values(
            ['商品编码', '是否周边调拨', '在库天数'], 
            ascending=[True, False, False]
        ).reset_index(drop=True)
    
    print(f"\n前十调拨明细表生成完成！")
    print(f"  处理记录数: {processed_count}")
    print(f"  跳过记录数: {skipped_count} (无库存)")
    print(f"  总需求数量: {total_demand}")
    print(f"  调拨数量: {total_allocated}")
    if total_demand > 0:
        print(f"  满足率: {total_allocated/total_demand*100:.1f}%")
    print(f"  周边调拨数量: {total_nearby_allocated}")
    if total_allocated > 0:
        print(f"  周边调拨占比: {total_nearby_allocated/total_allocated*100:.1f}%")
    print(f"  周边调拨记录数: {nearby_store_count}")
    print(f"  其他调拨记录数: {other_store_count}")
    if missing_info_count > 0:
        print(f"  ⚠️ 有 {missing_info_count} 条记录的商品信息缺失（通用名/规格/生产厂商）")
    if missing_date_count > 0:
        print(f"  ⚠️ 有 {missing_date_count} 条记录的生产日期或有效期信息缺失")
    print(f"  调拨明细记录数: {len(transfer_df)}")
    print(f"  ⏱️ 耗时: {elapsed_time:.2f} 秒")
    
    # 显示调拨统计（按商品）
    if len(transfer_df) > 0:
        print(f"\n📊 调拨统计（前10个商品）:")
        summary = transfer_df.groupby('商品编码').agg({
            '数量': ['sum', 'count'],
            '调入门店': 'nunique',
            '是否周边调拨': lambda x: (x == '是').sum()  # 统计周边调拨记录数
        }).round(2)
        summary.columns = ['总调拨数', '明细条数', '调入门店数', '周边调拨条数']
        print(summary.head(10))
        
        # 显示在库天数分布
        print(f"\n📊 调拨商品的在库天数分布:")
        days_distribution = transfer_df['在库天数'].describe()
        print(f"  最小值: {days_distribution['min']:.0f}天")
        print(f"  平均值: {days_distribution['mean']:.0f}天")
        print(f"  最大值: {days_distribution['max']:.0f}天")
        
        # 显示调拨明细示例
        print(f"\n调拨明细示例（前5条）：")
        display_cols = ['商品编码', '通用名', '规格','商品级别', '生产厂商', '生产日期', '有效期至', '减近效期天数', '在库天数', '调出门店', '调入门店', '数量', '是否周边调拨']
        print(transfer_df[display_cols].head(5).to_string(index=False))
    
    print("\n" + "=" * 60)
    print("前十调拨明细表生成完成!")
    print("=" * 60)
    
    return transfer_df

def save_final_result(shortage_df, sales_top10_df, inventory_df, shortage_transfer_df, 
                      top10_transfer_df, output_path):
    """
    保存最终结果到Excel文件
    
    参数:
        shortage_df: DataFrame, 缺货数据（包含调拨方案）
        sales_top10_df: DataFrame, 销售前十原始数据
        inventory_df: DataFrame, 库存数据（已扣减）
        shortage_transfer_df: DataFrame, 缺货调拨明细表
        top10_transfer_df: DataFrame, 前十调拨明细表
        output_path: str, 输出文件路径
    """
    print("\n" + "=" * 60)
    print("保存最终结果到Excel...")
    print("=" * 60)
    
    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    try:
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # ============ Sheet1: 缺货数据（包含调拨方案和内部消化信息） ============
            # 检查是否有内部消化相关列
            has_digest_cols = all(col in shortage_df.columns for col in ['内部消化数量', '实际调拨需求', '消化状态'])
            
            if has_digest_cols:
                # 构建包含消化信息的显示数据
                shortage_display = shortage_df[
                    ['源商品编码', '映射编码', '缺货门店', '原登记数量','配送数量','登记数量', '内部消化数量', '实际调拨需求', '消化状态', '门店调拨方案', '总部调拨方案']
                ].copy()
                shortage_display.columns = ['源商品编码', '映射编码', '缺货门店', '原登记数量','配送数量','登记数量', '内部消化数量', '实际调拨需求', '消化状态', '门店调拨方案', '总部调拨方案']
                
                # 转换数据类型
                shortage_display['门店调拨方案'] = shortage_display['门店调拨方案'].fillna('').astype(str)
                shortage_display['总部调拨方案'] = shortage_display['总部调拨方案'].fillna(0).astype(str)
                shortage_display['内部消化数量'] = shortage_display['内部消化数量'].fillna(0).astype(int)
                shortage_display['实际调拨需求'] = shortage_display['实际调拨需求'].fillna(0).astype(int)
            else:
                # 没有消化信息，使用原有格式
                shortage_display = shortage_df[
                    ['源商品编码', '映射编码', '缺货门店','原登记数量','配送数量', '登记数量', '门店调拨方案', '总部调拨方案']
                ].copy()
                shortage_display.columns = ['源商品编码', '映射编码', '缺货门店', '原登记数量','配送数量','登记数量', '门店调拨方案', '总部调拨方案']
                
                # 转换数据类型
                shortage_display['门店调拨方案'] = shortage_display['门店调拨方案'].fillna('').astype(str)
                shortage_display['总部调拨方案'] = shortage_display['总部调拨方案'].fillna(0).astype(str)
            
            shortage_display.to_excel(writer, sheet_name='缺货数据', index=False)
            
            # ============ Sheet2: 销售前十门店数据 ============
            sales_top10_df.to_excel(writer, sheet_name='销售前十门店', index=False)
            
            # ============ Sheet3: 可调拨库存数据 ============
            column_order = [
                '门店名称',
                '商品编码',
                '映射编码',
                '通用名',
                '规格',
                '商品级别',
                '生产厂商',
                '基本单位',
                '成本单价',
                '原始库存',
                '基本单位数量',
                '包装规格',
                '入库日期',
                '商品名',
                '生产日期',
                '有效期至',
                '减近效期天数',
                '在库天数',
                '销售数量',
                '门店库存需要销售月数'
            ]
            
            existing_columns = [col for col in column_order if col in inventory_df.columns]
            other_columns = [col for col in inventory_df.columns if col not in column_order]
            final_columns = existing_columns + other_columns
            
            inventory_display = inventory_df[final_columns].copy()
            
            for col in column_order:
                if col not in inventory_display.columns:
                    inventory_display[col] = ''
            
            inventory_display = inventory_display[column_order]
            inventory_display.to_excel(writer, sheet_name='可调拨库存', index=False)
            
            # ============ Sheet4: 缺货门店调拨表 ============
            if len(shortage_transfer_df) > 0:
                shortage_transfer_df.to_excel(writer, sheet_name='缺货调拨表', index=False)
                print(f"  ✅ 缺货调拨表已保存，共 {len(shortage_transfer_df)} 条记录")
            else:
                empty_df = pd.DataFrame({'说明': ['无门店调拨记录，所有缺货由总部调拨']})
                empty_df.to_excel(writer, sheet_name='缺货调拨表', index=False)
                print(f"  ⚠️ 缺货调拨表为空")
            
            # ============ Sheet5: 前十调拨明细表 ============
            if len(top10_transfer_df) > 0:
                top10_transfer_df.to_excel(writer, sheet_name='前十调拨表', index=False)
                print(f"  ✅ 前十调拨表已保存，共 {len(top10_transfer_df)} 条记录")
            else:
                empty_df = pd.DataFrame({'说明': ['无前十调拨记录']})
                empty_df.to_excel(writer, sheet_name='前十调拨表', index=False)
                print(f"  ⚠️ 前十调拨表为空")
        
        print(f"\n✅ 结果已保存到: {output_path}")
        print(f"  包含sheet: 缺货数据, 销售前十门店, 可调拨库存, 缺货调拨表, 前十调拨表")
        
        # ============ 显示内部消化统计信息 ============
        if has_digest_cols and len(shortage_df) > 0:
            total_digested = shortage_df['内部消化数量'].sum()
            total_original = shortage_df['登记数量'].sum()
            total_actual = shortage_df['实际调拨需求'].sum()
            
            fully_digested = len(shortage_df[shortage_df['消化状态'] == '完全消化'])
            partial_digested = len(shortage_df[shortage_df['消化状态'] == '部分消化'])
            not_digested = len(shortage_df[shortage_df['消化状态'] == '未消化'])
            
            print(f"\n📊 内部消化统计：")
            print(f"  原始总需求: {total_original}")
            print(f"  消化总数量: {total_digested}")
            print(f"  实际调拨需求: {total_actual}")
            if total_original > 0:
                print(f"  消化率: {total_digested/total_original*100:.1f}%")
            print(f"  完全消化记录: {fully_digested} 条")
            print(f"  部分消化记录: {partial_digested} 条")
            print(f"  未消化记录: {not_digested} 条")
        
    except Exception as e:
        raise Exception(f"保存文件失败: {e}")

def complete_workflow(shortage_file=None, sales_file=None, mapping_file=None, 
                      inventory_file=None, in_transit_file=None, cold_chain_file=None, store_area_file=None, output_folder=None,in_transit_df=None):
    """
    完整工作流程（不生成任何临时文件）：
    1. 读取并合并缺货数据
    2. 构建商品编码映射
    3. 处理缺货数据（应用映射）
    4. 读取销售数据并处理（传入缺货数据、库存文件、配送在途文件）
    5. 处理库存数据（用于调拨的库存）
    6. 生成缺货调拨方案
    7. 生成缺货调拨明细表
    8. 生成销售前十调拨明细表
    9. 将数据保存到同一个Excel文件的不同sheet
    
    参数:
        shortage_file: str, 缺货数据文件路径
        sales_file: str, 销售数据文件路径
        mapping_file: str, 商品编码映射文件路径
        inventory_file: str, 库存文件路径
        in_transit_file: str, 配送在途商品文件路径
        cold_chain_file: str, 冷链药品文件路径
        store_area_file: str, 门店区域文件路径
        output_folder: str, 输出文件夹路径（默认为桌面）
    
    返回:
        str: 生成的输出文件路径
    """
    
    print("=" * 60)
    print("开始执行完整工作流程...")
    print("=" * 60)
    
    # ============ 设置默认路径 ============
    if output_folder is None:
        output_folder = os.path.expanduser("~/Desktop")
    
    # 确保输出文件夹存在
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # 生成带时间戳的输出文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(output_folder, f"调拨结果文件_{timestamp}.xlsx")
    
    print(f"\n输出文件夹: {output_folder}")
    print(f"输出文件名: {os.path.basename(output_file)}")
    
    try:
        # ============ 步骤1: 读取并合并缺货数据 ============
        shortage_df = merge_shortage_data(shortage_file)
        
        # ============ 步骤2: 构建商品编码映射 ============
        print("\n" + "=" * 60)
        print("构建商品编码映射...")
        print("=" * 60)
        mapping = build_sorted_mapping(mapping_file)
        
        # ============ 步骤3: 处理缺货数据（应用映射） ============
        if in_transit_df is None:
            in_transit_df=pd.read_excel(
                    in_transit_file, 
                    engine='openpyxl',
                    dtype={
                        '商品编码': str,
                        '收货单位': str,
                        '配送数量': float  # 数量列保持数值类型
                    }
                )
        shortage_mapped = process_shortage_data_with_mapping(shortage_df, mapping,in_transit_df)

        # ============ 补充步骤: 读取冷链药品数据    ============
        print("\n" + "=" * 60)
        print("读取冷链药品数据...")
        print("=" * 60)
        cold_chain_df = pd.read_excel(cold_chain_file)
        # ============ 步骤4: 读取销售数据并处理 ============
        print("\n" + "=" * 60)
        print("读取销售数据...")
        print("=" * 60)
        df_sales = pd.read_excel(sales_file)
        print(f"读取销售数据成功: {len(df_sales)} 行, {len(df_sales.columns)} 列")
        
        # 传入缺货数据、库存文件和配送在途文件
        sales_top10_df, sales_summary_df, sales_base_df = process_sales_data_with_mapping(
            df_sales, 
            mapping,
            shortage_mapped,      # 传入缺货数据用于去重
            inventory_file,       # 传入原始库存文件路径
            in_transit_file,      # 传入配送在途文件路径
            cold_chain_df         # 传入冷链药品数据
        )
        
        # ============ 步骤5: 处理库存数据（用于调拨） ============
        # 2026.9.9新增加盟店去除、新门店在库时间>30即可调拨的逻辑
        franchisee_store_df = pd.read_excel(
            store_area_file, 
            sheet_name='加盟店',
            usecols=[0],
            names=['门店名称']  # 自定义列名
        )
        print(f"  ✓ 加盟店数据读取成功: {len(franchisee_store_df)} 行")
        try:
            new_store_df = pd.read_excel(
                store_area_file,
                sheet_name='新门店',
                usecols=['门店名称', '商品编码'],  # 只有两列
                dtype={'商品编码': str}
            )

            # 清洗商品编码（处理浮点数等问题）
            def clean_code(code):
                """清洗商品编码，处理各种格式"""
                code_str = str(code).strip()
                if code_str == '' or code_str.lower() == 'nan':
                    return ''
                if '.' in code_str:
                    try:
                        num = float(code_str)
                        if num.is_integer():
                            return str(int(num))
                        else:
                            return code_str
                    except:
                        return code_str
                return code_str

            new_store_df['商品编码'] = new_store_df['商品编码'].apply(clean_code)
            new_store_df['门店名称'] = new_store_df['门店名称'].astype(str).str.strip()

            # 判断是否有数据（过滤掉空行后）
            new_store_df = new_store_df[
                (new_store_df['门店名称'] != '') & 
                (new_store_df['门店名称'].str.lower() != 'nan') &
                (new_store_df['商品编码'] != '')
            ].copy()

            # 如果过滤后没有数据，设置为None
            if len(new_store_df) == 0:
                print("  ⚠️ 新门店sheet只有列名，没有数据，new_store_df设置为None")
                new_store_df = None
            else:
                print(f"  ✓ 新门店数据读取成功: {len(new_store_df)} 行")
                print(f"  涉及门店数: {new_store_df['门店名称'].nunique()}")
                print(f"  涉及商品数: {new_store_df['商品编码'].nunique()}")
                print(f"  前3行预览:")
                print(new_store_df.head(3))

        except Exception as e:
            print(f"  ⚠️ 读取新门店数据失败: {e}")
            new_store_df = None
        #开始传递对库存数据进行处理
        inventory_df = process_inventory_data(inventory_file, sales_base_df, mapping, cold_chain_df, franchisee_store_df, new_store_df)

        # ============= 补充步骤：处理门店区域（用于调拨） ===============
        store_area_dict = process_store_area(store_area_file,'周边门店')
        # ============ 步骤6: 生成缺货调拨方案 ============
        shortage_with_allocation, inventory_after_shortage = generate_allocation_plan(
            shortage_mapped, 
            inventory_df,
            store_area_dict=store_area_dict
        )
        
        # ============ 步骤7: 生成缺货调拨明细表 ============
        shortage_transfer_df = generate_store_transfer_table(
            shortage_with_allocation,
            inventory_after_shortage
        )
        
        # ============ 步骤8: 生成销售前十调拨明细表 ============
        top10_transfer_df = generate_top10_transfer_table(
            sales_top10_df,
            inventory_after_shortage,
            store_area_dict=store_area_dict
        )
        
        # ============ 步骤9: 保存最终结果 ============
        save_final_result(
            shortage_with_allocation,
            sales_top10_df,
            inventory_after_shortage,
            shortage_transfer_df,
            top10_transfer_df,
            output_file
        )
        
        print("\n" + "=" * 60)
        print("全部工作流程完成!")
        print("=" * 60)
        print(f"\n✅ 最终生成文件: {output_file}")
        
        return output_file
        
    except Exception as e:
        print(f"\n❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # 执行完整流程
    # ============ 文件路径 ============
    shortage_file = r"C:\Users\Administrator\Desktop\调拨\祝强缺货请购单.xlsx"
    sales_file = r"C:\Users\Administrator\Desktop\调拨\销售数据_2026-08-11_至_2026-09-09.xlsx"
    mapping_file = r"C:\Users\Administrator\Desktop\调拨\商品编码匹配表.xlsx"
    inventory_file = r"C:\Users\Administrator\Desktop\调拨\2026-09-09库存数据.xlsx"
    in_transit_file = r"C:\Users\Administrator\Desktop\调拨\配送在途总表_20260909_103548.xlsx" 
    cold_chain_file = r"C:\Users\Administrator\Desktop\调拨\冷藏药品.xlsx"
    store_area_file = r"C:\Users\Administrator\Desktop\调拨\门店信息.xlsx"
    in_transit_df =  pd.read_excel(r"C:\Users\Administrator\Desktop\调拨\分单.xlsx")
    output_folder = r"C:\Users\Administrator\Desktop\调拨"

    # 执行完整流程
    complete_workflow(
        shortage_file=shortage_file,
        sales_file=sales_file,
        mapping_file=mapping_file,
        inventory_file=inventory_file,
        in_transit_file=in_transit_file,
        cold_chain_file=cold_chain_file,
        store_area_file=store_area_file,
        output_folder=output_folder,
        in_transit_df =in_transit_df
    )