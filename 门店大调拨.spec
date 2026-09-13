# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_data_files

datas = [('C:\\Users\\Administrator\\Desktop\\总部调拨方案\\venv\\Lib\\site-packages\\ddddocr', 'ddddocr'), 
         ('C:\\Users\\Administrator\\Desktop\\总部调拨方案\\venv\\Lib\\site-packages\\onnxruntime', 'onnxruntime'), 
         ('C:\\Users\\Administrator\\Desktop\\总部调拨方案\\venv\\Lib\\site-packages\\numpy.libs', 'numpy.libs')]
binaries = []

hiddenimports = [
    'ddddocr', 
    'PIL', 
    'requests', 
    'pandas', 
    'numpy', 
    'onnxruntime', 
    'login', 
    'transfer_scheme_processing', 
    'sales_data', 
    'sales_data_exporter', 
    'delivery_data', 
    'inventory_export', 
    'export_file',
    'xlrd',
    'openpyxl',
    'pandas.io.excel._xlrd',
    'pandas.io.excel._openpyxl',
    'pandas.io.excel.ExcelFile',  # 确保 ExcelFile 类被导入
]

# 收集 xlrd 数据文件
datas += collect_data_files('xlrd')
datas += collect_data_files('openpyxl')

tmp_ret = collect_all('customtkinter')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

tmp_ret = collect_all('ddddocr')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

tmp_ret = collect_all('onnxruntime')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

tmp_ret = collect_all('numpy')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['ui.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='门店大调拨方案生成工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\Users\\Administrator\\Desktop\\总部调拨方案\\超人.ico'],
)