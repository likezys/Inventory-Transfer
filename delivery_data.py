import pandas as pd
from datetime import datetime
import os

def merge_delivery_tables(zq_in_transit_file, hh_in_transit_file, split_order_path, output_folder):
    """
    合并三个表格生成配送在途总表
    
    参数:
    zq_in_transit_file: 配送在途商品查询表格路径
    hh_in_transit_file: 销售发货单明细查询表格路径
    split_order_path: 分单表格路径
    output_folder: 输出文件夹路径
    
    返回:
    合并后的DataFrame
    """
    
    try:
        # 1. 处理配送在途商品查询表格
        print("正在处理配送在途商品查询表格...")
        df_in_transit = pd.read_excel(zq_in_transit_file, dtype={'商品编码': str})
        # 保留指定三列并重命名
        df_in_transit = df_in_transit[['商品编码', '收货单位', '配送数量']].copy()
        df_in_transit.columns = ['商品编码', '收货单位', '配送数量']
        
        # 清洗商品编码（去除空格和特殊字符）- 修复float错误
        def clean_code(code):
            """清洗商品编码，处理各种格式"""
            # 先转为字符串
            code_str = str(code).strip()
            
            # 处理空值
            if code_str == '' or code_str.lower() == 'nan':
                return ''
            
            # 处理浮点数格式（如 '10001.0' -> '10001'）
            # 注意：现在code_str是字符串，可以使用replace
            if '.' in code_str:
                try:
                    # 尝试转为浮点数再转整数（如果是整数形式）
                    num = float(code_str)
                    if num.is_integer():
                        return str(int(num))
                    else:
                        return code_str
                except:
                    return code_str
            
            return code_str
        
        df_in_transit['商品编码'] = df_in_transit['商品编码'].apply(clean_code)
        print(f"  配送在途表格处理完成，共 {len(df_in_transit)} 行")
        
        # 2. 处理销售发货单明细查询表格
        print("正在处理销售发货单明细查询表格...")
        df_sales = pd.read_excel(hh_in_transit_file, dtype={'商品编码': str})
        # 保留指定三列
        df_sales = df_sales[['商品编码', '其他信息', '数量']].copy()
        
        # 清洗商品编码
        df_sales['商品编码'] = df_sales['商品编码'].apply(clean_code)
        
        # 处理'其他信息'列：如果不包含'公司'，则在前面补上'厦门祝强大药房有限公司'
        df_sales['其他信息'] = df_sales['其他信息'].apply(
            lambda x: x if pd.isna(x) or '公司' in str(x) else f'厦门祝强大药房有限公司{x}'
        )
        
        # 重命名列
        df_sales.columns = ['商品编码', '收货单位', '配送数量']
        print(f"  销售发货单表格处理完成，共 {len(df_sales)} 行")
        
        # 3. 处理分单表格（合并所有sheet）
        print("正在处理分单表格...")
        # 读取所有sheet
        excel_file = pd.ExcelFile(split_order_path)
        sheet_names = excel_file.sheet_names
        
        df_split_list = []
        for sheet_name in sheet_names:
            df_temp = pd.read_excel(split_order_path, sheet_name=sheet_name, dtype={0: str, 1: str})
            df_split_list.append(df_temp)
        
        # 合并所有sheet
        df_split = pd.concat(df_split_list, ignore_index=True)
        
        # 保留前三列并重命名
        df_split = df_split.iloc[:, :3].copy()
        df_split.columns = ['收货单位', '商品编码', '配送数量']
        
        # 清洗商品编码
        df_split['商品编码'] = df_split['商品编码'].apply(clean_code)
        
        print(f"  分单表格处理完成，合并了 {len(sheet_names)} 个sheet，共 {len(df_split)} 行")
        
        # 4. 合并三个表格
        print("正在合并三个表格...")
        df_final = pd.concat([df_in_transit, df_sales, df_split], ignore_index=True)
        print(f"  合并完成，总行数: {len(df_final)}")
        
        # 5. 按商品编码和收货单位汇总配送数量
        print("正在按商品编码和收货单位汇总配送数量...")
        df_summary = df_final.groupby(['商品编码', '收货单位'], as_index=False)['配送数量'].sum()
        
        # 确保商品编码为字符串类型（关键步骤！）
        df_summary['商品编码'] = df_summary['商品编码'].astype(str)
        
        print(f"  汇总完成，汇总后行数: {len(df_summary)}")
        
        # 6. 保存最终表格
        # 生成带时间的文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f'配送在途总表_{timestamp}.xlsx'
        output_path = os.path.join(output_folder, output_filename)
        
        # 确保输出文件夹存在
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        # 保存为Excel（确保商品编码为字符串）
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # 保存汇总后的数据 - 确保商品编码为字符串
            df_summary_to_save = df_summary.copy()
            df_summary_to_save['商品编码'] = df_summary_to_save['商品编码'].astype(str)
            df_summary_to_save.to_excel(writer, sheet_name='配送在途总表', index=False)
            
            # 保存原始合并数据作为备份
            df_final_to_save = df_final.copy()
            df_final_to_save['商品编码'] = df_final_to_save['商品编码'].astype(str)
            df_final_to_save.to_excel(writer, sheet_name='原始合并数据', index=False)
        
        print(f"\n✅ 处理完成！")
        print(f"  原始合并行数: {len(df_final)}")
        print(f"  汇总后行数: {len(df_summary)}")
        print(f"  保存路径: {output_path}")
        
        # 验证商品编码是否为字符串
        print(f"\n📊 数据类型验证:")
        print(f"  商品编码类型: {df_summary['商品编码'].dtype}")
        print(f"  商品编码示例: {df_summary['商品编码'].head(3).tolist()}")
        
        return df_summary, output_path
        
    except FileNotFoundError as e:
        print(f"❌ 错误：找不到文件 - {e}")
        return None, None
    except KeyError as e:
        print(f"❌ 错误：找不到指定的列 - {e}")
        print("  请检查Excel文件的列名是否正确")
        return None, None
    except Exception as e:
        print(f"❌ 发生未知错误: {e}")
        import traceback
        traceback.print_exc()
        return None, None


