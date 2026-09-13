import customtkinter as ctk
from tkinter import filedialog, messagebox, Toplevel
import threading
from datetime import datetime, timedelta
import os
import sys
import json
from io import StringIO
from main import main

# 不再需要 tkcalendar，直接设置为不可用
CALENDAR_AVAILABLE = False

# 设置主题和外观
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

def get_app_path():
    """获取应用程序路径（兼容开发环境和打包环境）"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def get_config_path():
    """获取配置文件路径"""
    app_path = get_app_path()
    config_path = os.path.join(app_path, "app_config.json")
    return config_path

# 配置文件路径（兼容打包）
CONFIG_FILE = get_config_path()


class ConfigManager:
    """配置管理类，负责保存和加载配置"""
    
    DEFAULT_CONFIG = {
        "zq_username": "",
        "zq_password": "",
        "hh_username": "",
        "hh_password": "",
        "start_date": "",
        "end_date": "",
        "download_path": os.path.join(os.path.expanduser("~"), "Desktop"),
        "shortage_file": "",
        "mapping_file": "",
        "cold_chain_file": "",
        "store_area_file": "",
        "split_order_file": ""  # 新增：分单文件路径
    }
    
    @classmethod
    def load_config(cls):
        """加载配置文件，如果不存在则使用默认配置"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    merged_config = cls.DEFAULT_CONFIG.copy()
                    merged_config.update(config)
                    return merged_config
            else:
                old_config = cls._load_old_config()
                if old_config:
                    cls.save_config(old_config)
                    return old_config
                else:
                    cls.save_config(cls.DEFAULT_CONFIG)
                    return cls.DEFAULT_CONFIG.copy()
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return cls.DEFAULT_CONFIG.copy()
    
    @classmethod
    def _load_old_config(cls):
        """尝试从旧位置加载配置（兼容旧版本）"""
        try:
            old_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_config.json")
            if old_path != CONFIG_FILE and os.path.exists(old_path):
                with open(old_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    merged_config = cls.DEFAULT_CONFIG.copy()
                    merged_config.update(config)
                    return merged_config
        except:
            pass
        return None
    
    @classmethod
    def save_config(cls, config):
        """保存配置到文件"""
        try:
            config_dir = os.path.dirname(CONFIG_FILE)
            if config_dir:
                os.makedirs(config_dir, exist_ok=True)
            
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    @classmethod
    def get_config_location(cls):
        """获取配置文件位置（用于显示）"""
        return CONFIG_FILE


class DatePickerDialog:
    """日期选择对话框 - 使用纯Tkinter组件，不依赖第三方库"""
    def __init__(self, parent, title="选择日期", initial_date=None):
        self.parent = parent
        self.title = title
        self.initial_date = initial_date
        self.result = None
        self.dialog = None
        self.year_var = None
        self.month_var = None
        self.day_var = None
        
    def show(self):
        """显示日期选择对话框"""
        self.dialog = Toplevel(self.parent)
        self.dialog.title(self.title)
        self.dialog.geometry("320x350")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self.dialog.focus_set()
        
        # 设置窗口居中
        self.dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - 320) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - 350) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        # 主框架
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 标题
        ctk.CTkLabel(
            main_frame,
            text="📅 选择日期",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(0, 15))
        
        # 解析初始日期
        if self.initial_date:
            try:
                date_obj = datetime.strptime(self.initial_date, "%Y-%m-%d")
                default_year = date_obj.year
                default_month = date_obj.month
                default_day = date_obj.day
            except:
                now = datetime.now()
                default_year = now.year
                default_month = now.month
                default_day = now.day
        else:
            now = datetime.now()
            default_year = now.year
            default_month = now.month
            default_day = now.day
        
        # 年份选择
        year_frame = ctk.CTkFrame(main_frame)
        year_frame.pack(pady=8, fill="x")
        ctk.CTkLabel(year_frame, text="年份:", font=ctk.CTkFont(size=14), width=60).pack(side="left", padx=5)
        
        # 年份输入框（带上下按钮）
        year_input_frame = ctk.CTkFrame(year_frame)
        year_input_frame.pack(side="left", fill="x", expand=True, padx=5)
        
        self.year_var = ctk.StringVar(value=str(default_year))
        year_entry = ctk.CTkEntry(year_input_frame, textvariable=self.year_var, width=100)
        year_entry.pack(side="left", padx=2)
        
        # 年份微调按钮
        year_btn_frame = ctk.CTkFrame(year_input_frame)
        year_btn_frame.pack(side="left", padx=2)
        
        ctk.CTkButton(
            year_btn_frame,
            text="▲",
            command=lambda: self.adjust_year(1),
            width=30,
            height=25,
            fg_color="#607D8B",
            hover_color="#455A64"
        ).pack(side="top")
        
        ctk.CTkButton(
            year_btn_frame,
            text="▼",
            command=lambda: self.adjust_year(-1),
            width=30,
            height=25,
            fg_color="#607D8B",
            hover_color="#455A64"
        ).pack(side="top")
        
        # 月份选择
        month_frame = ctk.CTkFrame(main_frame)
        month_frame.pack(pady=8, fill="x")
        ctk.CTkLabel(month_frame, text="月份:", font=ctk.CTkFont(size=14), width=60).pack(side="left", padx=5)
        
        month_input_frame = ctk.CTkFrame(month_frame)
        month_input_frame.pack(side="left", fill="x", expand=True, padx=5)
        
        self.month_var = ctk.StringVar(value=str(default_month).zfill(2))
        month_entry = ctk.CTkEntry(month_input_frame, textvariable=self.month_var, width=100)
        month_entry.pack(side="left", padx=2)
        
        month_btn_frame = ctk.CTkFrame(month_input_frame)
        month_btn_frame.pack(side="left", padx=2)
        
        ctk.CTkButton(
            month_btn_frame,
            text="▲",
            command=lambda: self.adjust_month(1),
            width=30,
            height=25,
            fg_color="#607D8B",
            hover_color="#455A64"
        ).pack(side="top")
        
        ctk.CTkButton(
            month_btn_frame,
            text="▼",
            command=lambda: self.adjust_month(-1),
            width=30,
            height=25,
            fg_color="#607D8B",
            hover_color="#455A64"
        ).pack(side="top")
        
        # 日期选择
        day_frame = ctk.CTkFrame(main_frame)
        day_frame.pack(pady=8, fill="x")
        ctk.CTkLabel(day_frame, text="日期:", font=ctk.CTkFont(size=14), width=60).pack(side="left", padx=5)
        
        day_input_frame = ctk.CTkFrame(day_frame)
        day_input_frame.pack(side="left", fill="x", expand=True, padx=5)
        
        self.day_var = ctk.StringVar(value=str(default_day).zfill(2))
        day_entry = ctk.CTkEntry(day_input_frame, textvariable=self.day_var, width=100)
        day_entry.pack(side="left", padx=2)
        
        day_btn_frame = ctk.CTkFrame(day_input_frame)
        day_btn_frame.pack(side="left", padx=2)
        
        ctk.CTkButton(
            day_btn_frame,
            text="▲",
            command=lambda: self.adjust_day(1),
            width=30,
            height=25,
            fg_color="#607D8B",
            hover_color="#455A64"
        ).pack(side="top")
        
        ctk.CTkButton(
            day_btn_frame,
            text="▼",
            command=lambda: self.adjust_day(-1),
            width=30,
            height=25,
            fg_color="#607D8B",
            hover_color="#455A64"
        ).pack(side="top")
        
        # 显示选中日期
        self.date_display = ctk.CTkLabel(
            main_frame,
            text="",
            font=ctk.CTkFont(size=14),
            text_color="#2196F3"
        )
        self.date_display.pack(pady=10)
        self.update_date_display()
        
        # 绑定输入变化事件
        self.year_var.trace('w', lambda *args: self.update_date_display())
        self.month_var.trace('w', lambda *args: self.update_date_display())
        self.day_var.trace('w', lambda *args: self.update_date_display())
        
        # 分隔线
        ctk.CTkFrame(main_frame, height=2, fg_color="gray").pack(fill="x", pady=10)
        
        # 按钮区域
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", pady=5)
        
        # 今天按钮
        ctk.CTkButton(
            button_frame,
            text="📅 今天",
            command=self.select_today,
            width=80,
            fg_color="#4CAF50",
            hover_color="#388E3C"
        ).pack(side="left", padx=5)
        
        # 确定按钮
        ctk.CTkButton(
            button_frame,
            text="✅ 确定",
            command=self.confirm,
            width=80,
            fg_color="#2196F3",
            hover_color="#1976D2"
        ).pack(side="left", padx=5)
        
        # 取消按钮
        ctk.CTkButton(
            button_frame,
            text="❌ 取消",
            command=self.cancel,
            width=80,
            fg_color="#FF5722",
            hover_color="#D84315"
        ).pack(side="left", padx=5)
        
        # 等待对话框关闭
        self.dialog.wait_window()
        return self.result
    
    def adjust_year(self, delta):
        """调整年份"""
        try:
            current = int(self.year_var.get())
            new_value = current + delta
            # 限制年份范围
            if 1900 <= new_value <= 2100:
                self.year_var.set(str(new_value))
        except:
            pass
    
    def adjust_month(self, delta):
        """调整月份"""
        try:
            current = int(self.month_var.get())
            new_value = current + delta
            if 1 <= new_value <= 12:
                self.month_var.set(str(new_value).zfill(2))
            elif new_value < 1:
                self.month_var.set("12")
                self.adjust_year(-1)
            elif new_value > 12:
                self.month_var.set("01")
                self.adjust_year(1)
        except:
            pass
    
    def adjust_day(self, delta):
        """调整日期"""
        try:
            current = int(self.day_var.get())
            new_value = current + delta
            if 1 <= new_value <= 31:
                self.day_var.set(str(new_value).zfill(2))
        except:
            pass
    
    def update_date_display(self):
        """更新日期显示"""
        try:
            year = int(self.year_var.get())
            month = int(self.month_var.get())
            day = int(self.day_var.get())
            
            # 验证日期是否有效
            date_str = f"{year}-{month:02d}-{day:02d}"
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            
            # 获取星期
            weekdays = ["一", "二", "三", "四", "五", "六", "日"]
            weekday = weekdays[date_obj.weekday()]
            
            self.date_display.configure(
                text=f"📅 {date_str} 星期{weekday}",
                text_color="#2196F3"
            )
        except:
            self.date_display.configure(
                text="⚠️ 无效日期，请检查输入",
                text_color="#FF5722"
            )
    
    def confirm(self):
        """确认选择"""
        try:
            year = int(self.year_var.get())
            month = int(self.month_var.get())
            day = int(self.day_var.get())
            
            # 验证日期有效性
            date_str = f"{year}-{month:02d}-{day:02d}"
            datetime.strptime(date_str, "%Y-%m-%d")
            
            self.result = date_str
            self.dialog.destroy()
        except ValueError:
            messagebox.showerror("错误", "请输入有效的日期！")
    
    def cancel(self):
        """取消选择"""
        self.result = None
        self.dialog.destroy()
    
    def select_today(self):
        """选择今天"""
        today = datetime.now()
        self.year_var.set(str(today.year))
        self.month_var.set(str(today.month).zfill(2))
        self.day_var.set(str(today.day).zfill(2))
        self.update_date_display()


class PrintRedirector:
    """重定向print输出到GUI文本框"""
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.buffer = StringIO()
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
    def write(self, text):
        self.buffer.write(text)
        if self.text_widget:
            self.text_widget.insert("end", text)
            self.text_widget.see("end")
            self.text_widget.update_idletasks()
    
    def flush(self):
        self.buffer.flush()
    
    def start(self):
        sys.stdout = self
        sys.stderr = self
    
    def stop(self):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr


class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("门店大调拨方案 - By lilili")
        self.geometry("1200x750")
        self.minsize(1000, 650)
        
        # 加载配置
        self.config = ConfigManager.load_config()
        
        # 存储路径的变量
        self.download_path_var = ctk.StringVar(value=self.config.get("download_path", ""))
        self.shortage_file_var = ctk.StringVar(value=self.config.get("shortage_file", ""))
        self.mapping_file_var = ctk.StringVar(value=self.config.get("mapping_file", ""))
        self.cold_chain_file_var = ctk.StringVar(value=self.config.get("cold_chain_file", ""))
        self.store_area_file_var = ctk.StringVar(value=self.config.get("store_area_file", ""))
        self.split_order_file_var = ctk.StringVar(value=self.config.get("split_order_file", "")) 
        
        # 状态变量
        self.is_running = False
        self.print_redirector = None
        
        # 创建主框架（左右布局）
        self.create_main_layout()
        
        # 在 __init__ 方法中
        self.log_message("✅ 已加载上次的配置", "INFO")
        self.log_message(f"📁 配置文件位置: {ConfigManager.get_config_location()}", "INFO")
        self.log_message(f"📅 日期范围: {self.config.get('start_date')} ~ {self.config.get('end_date')}", "INFO")
        self.log_message(f"👤 xx账号: {self.config.get('zq_username', '未设置')}", "INFO")
        self.log_message(f"👤 yy账号: {self.config.get('hh_username', '未设置')}", "INFO")
        self.log_message("✅ 使用内置日期选择器（无需额外安装）", "INFO")
        
    def create_main_layout(self):
        """创建左右布局"""
        
        # 主容器 - 使用网格布局
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # ===== 左侧：配置面板 =====
        left_frame = ctk.CTkFrame(self)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        left_frame.grid_columnconfigure(0, weight=1)
        
        # 左侧滚动框架
        left_scroll = ctk.CTkScrollableFrame(left_frame)
        left_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 标题
        title_label = ctk.CTkLabel(
            left_scroll,
            text="⚙️ 系统配置",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(10, 15))
        
        # 分隔线
        ctk.CTkFrame(left_scroll, height=2, fg_color="gray").pack(fill="x", padx=10, pady=5)
        
        # ===== 登录信息 =====
        self.create_login_section(left_scroll)
        
        # ===== 日期范围 =====
        self.create_date_section(left_scroll)
        
        # ===== 文件路径 =====
        self.create_path_section(left_scroll)
        
        # 底部操作按钮
        button_frame = ctk.CTkFrame(left_frame)
        button_frame.pack(fill="x", padx=5, pady=10)
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        
        self.run_button = ctk.CTkButton(
            button_frame,
            text="▶ 运行",
            command=self.run_main,
            height=45,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#5DACEC",
            hover_color="#5DACEC"
        )
        self.run_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.save_config_btn = ctk.CTkButton(
            button_frame,
            text="💾 保存配置",
            command=self.save_current_config,
            height=45,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#78D87B",
            hover_color="#78D87B"
        )
        self.save_config_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # 配置文件位置提示
        config_info = ctk.CTkLabel(
            left_frame,
            text=f"📁 配置: {ConfigManager.get_config_location()}",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        config_info.pack(pady=(0, 5))
        
        # ===== 右侧：日志面板 =====
        right_frame = ctk.CTkFrame(self)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        right_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_rowconfigure(1, weight=1)
        
        # 日志标题
        log_header = ctk.CTkFrame(right_frame)
        log_header.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        ctk.CTkLabel(
            log_header,
            text="📋 运行日志",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(side="left", padx=10)
        
        # 清空日志按钮
        clear_btn = ctk.CTkButton(
            log_header,
            text="清空",
            command=self.clear_log,
            width=60,
            height=30,
            fg_color="#FF5722",
            hover_color="#D84315"
        )
        clear_btn.pack(side="right", padx=10)
        
        # 日志文本框
        self.log_text = ctk.CTkTextbox(
            right_frame,
            font=ctk.CTkFont(size=12),
            wrap="word"
        )
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # 状态栏
        status_frame = ctk.CTkFrame(right_frame)
        status_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        status_frame.grid_columnconfigure(0, weight=1)
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="🟢 就绪",
            font=ctk.CTkFont(size=13)
        )
        self.status_label.pack(side="left", padx=10)
        
        # 进度条
        self.progressbar = ctk.CTkProgressBar(status_frame, height=10)
        self.progressbar.pack(side="right", fill="x", expand=True, padx=10)
        self.progressbar.set(0)
        
        # 重定向print输出
        self.print_redirector = PrintRedirector(self.log_text)
        
        # 初始化日志
        self.log_text.insert("end", "🟢 程序已启动，等待操作...\n")
        self.log_text.insert("end", "=" * 60 + "\n\n")
    
    def create_login_section(self, parent):
        """创建登录信息部分 - 支持xx和yy两个账号"""
        login_frame = ctk.CTkFrame(parent)
        login_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            login_frame,
            text="🔐 登录信息",
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 10))
        
        # ===== xx账号 =====
        zq_label = ctk.CTkLabel(login_frame, text="🏢 xx", font=ctk.CTkFont(size=13, weight="bold"))
        zq_label.pack(anchor="w", padx=10, pady=(5, 0))
        
        # 用户名
        user_frame = ctk.CTkFrame(login_frame)
        user_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(user_frame, text="用户名", width=80).pack(side="left", padx=5)
        self.zq_username_entry = ctk.CTkEntry(user_frame, placeholder_text="请输入xx用户名")
        self.zq_username_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.zq_username_entry.insert(0, self.config.get("zq_username", ""))
        
        # 密码
        pwd_frame = ctk.CTkFrame(login_frame)
        pwd_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(pwd_frame, text="密码", width=80).pack(side="left", padx=5)
        self.zq_password_entry = ctk.CTkEntry(pwd_frame, placeholder_text="请输入xx密码")
        self.zq_password_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.zq_password_entry.insert(0, self.config.get("zq_password", ""))
        
        # ===== yy账号 =====
        hh_label = ctk.CTkLabel(login_frame, text="🏢 yy", font=ctk.CTkFont(size=13, weight="bold"))
        hh_label.pack(anchor="w", padx=10, pady=(10, 0))
        
        # 用户名
        user_frame2 = ctk.CTkFrame(login_frame)
        user_frame2.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(user_frame2, text="用户名", width=80).pack(side="left", padx=5)
        self.hh_username_entry = ctk.CTkEntry(user_frame2, placeholder_text="请输入yy用户名")
        self.hh_username_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.hh_username_entry.insert(0, self.config.get("hh_username", ""))
        
        # 密码
        pwd_frame2 = ctk.CTkFrame(login_frame)
        pwd_frame2.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(pwd_frame2, text="密码", width=80).pack(side="left", padx=5)
        self.hh_password_entry = ctk.CTkEntry(pwd_frame2, placeholder_text="请输入yy密码")
        self.hh_password_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.hh_password_entry.insert(0, self.config.get("hh_password", ""))
    
    def create_date_section(self, parent):
        """创建日期范围部分（带日期选择器）"""
        date_frame = ctk.CTkFrame(parent)
        date_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            date_frame,
            text="📅 日期范围",
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 10))
        
        # 开始日期
        start_frame = ctk.CTkFrame(date_frame)
        start_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(start_frame, text="开始日期", width=80).pack(side="left", padx=5)
        
        # 开始日期输入框
        self.start_date_entry = ctk.CTkEntry(start_frame, placeholder_text="YYYY-MM-DD")
        self.start_date_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.start_date_entry.insert(0, self.config.get("start_date", ""))
        
        # 开始日期选择按钮
        start_cal_btn = ctk.CTkButton(
            start_frame,
            text="📅",
            command=lambda: self.open_date_picker(self.start_date_entry),
            width=40,
            fg_color="#9E9E9E",
            hover_color="#757575"
        )
        start_cal_btn.pack(side="left", padx=2)
        
        # 结束日期
        end_frame = ctk.CTkFrame(date_frame)
        end_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(end_frame, text="结束日期", width=80).pack(side="left", padx=5)
        
        # 结束日期输入框
        self.end_date_entry = ctk.CTkEntry(end_frame, placeholder_text="YYYY-MM-DD")
        self.end_date_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.end_date_entry.insert(0, self.config.get("end_date", ""))
        
        # 结束日期选择按钮
        end_cal_btn = ctk.CTkButton(
            end_frame,
            text="📅",
            command=lambda: self.open_date_picker(self.end_date_entry),
            width=40,
            fg_color="#9E9E9E",
            hover_color="#757575"
        )
        end_cal_btn.pack(side="left", padx=2)
        
        # 快速选择按钮
        quick_frame = ctk.CTkFrame(date_frame)
        quick_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(quick_frame, text="快速选择:", width=80).pack(side="left", padx=5)
        
        # 近两个月（默认）
        two_months_btn = ctk.CTkButton(
            quick_frame,
            text="近两月",
            command=self.set_last_two_months,
            width=70,
            height=28,
            fg_color="#2196F3",
            hover_color="#1976D2"
        )
        two_months_btn.pack(side="left", padx=2)
        
        # 本月
        month_btn = ctk.CTkButton(
            quick_frame,
            text="本月",
            command=self.set_this_month,
            width=70,
            height=28,
            fg_color="#607D8B",
            hover_color="#455A64"
        )
        month_btn.pack(side="left", padx=2)
        
        # 近三个月
        quarter_btn = ctk.CTkButton(
            quick_frame,
            text="近三个月",
            command=self.set_this_quarter,
            width=70,
            height=28,
            fg_color="#607D8B",
            hover_color="#455A64"
        )
        quarter_btn.pack(side="left", padx=2)
        
        # 今年
        year_btn = ctk.CTkButton(
            quick_frame,
            text="今年",
            command=self.set_this_year,
            width=70,
            height=28,
            fg_color="#607D8B",
            hover_color="#455A64"
        )
        year_btn.pack(side="left", padx=2)
    
    def open_date_picker(self, entry_widget):
        """打开日期选择对话框"""
        current_date = entry_widget.get().strip()
        if not current_date:
            current_date = datetime.now().strftime("%Y-%m-%d")
        
        picker = DatePickerDialog(self, "选择日期", current_date)
        selected_date = picker.show()
        
        if selected_date:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, selected_date)
    
    def set_this_month(self):
        """设置日期范围为当前月"""
        now = datetime.now()
        start = now.replace(day=1).strftime("%Y-%m-%d")
        # 获取下个月第一天，然后减一天得到本月最后一天
        if now.month == 12:
            end = now.replace(year=now.year+1, month=1, day=1)
        else:
            end = now.replace(month=now.month+1, day=1)
        end = (end - timedelta(days=1)).strftime("%Y-%m-%d")
        
        self.start_date_entry.delete(0, "end")
        self.start_date_entry.insert(0, start)
        self.end_date_entry.delete(0, "end")
        self.end_date_entry.insert(0, end)
        self.log_message(f"📅 已设置为本月: {start} ~ {end}", "INFO")
    
    def set_last_two_months(self):
        """设置日期范围为最近两个月（从两个月前到今天）"""
        now = datetime.now()
        # 结束日期：今天
        end = now.strftime("%Y-%m-%d")
        # 开始日期：往前推两个月
        start_date = now - timedelta(days=60)
        start = start_date.strftime("%Y-%m-%d")
        
        self.start_date_entry.delete(0, "end")
        self.start_date_entry.insert(0, start)
        self.end_date_entry.delete(0, "end")
        self.end_date_entry.insert(0, end)
        self.log_message(f"📅 已设置为近两个月: {start} ~ {end}", "INFO")
    
    def set_this_quarter(self):
        """设置日期范围为近三个月（从三个月前到今天）"""
        now = datetime.now()
        # 结束日期：今天
        end = now.strftime("%Y-%m-%d")
        # 开始日期：往前推三个月（使用90天近似）
        start_date = now - timedelta(days=90)
        start = start_date.strftime("%Y-%m-%d")
        
        self.start_date_entry.delete(0, "end")
        self.start_date_entry.insert(0, start)
        self.end_date_entry.delete(0, "end")
        self.end_date_entry.insert(0, end)
        self.log_message(f"📅 已设置为近三个月: {start} ~ {end}", "INFO")
    
    def set_this_year(self):
        """设置日期范围为今年"""
        now = datetime.now()
        start = now.replace(month=1, day=1).strftime("%Y-%m-%d")
        end = now.replace(month=12, day=31).strftime("%Y-%m-%d")
        
        self.start_date_entry.delete(0, "end")
        self.start_date_entry.insert(0, start)
        self.end_date_entry.delete(0, "end")
        self.end_date_entry.insert(0, end)
        self.log_message(f"📅 已设置为今年: {start} ~ {end}", "INFO")
    
    def create_path_section(self, parent):
        """创建文件路径部分"""
        path_frame = ctk.CTkFrame(parent)
        path_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            path_frame,
            text="📁 文件路径配置",
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 10))
        
        # 下载路径
        self.create_file_selector(
            path_frame,
            "下载路径",
            self.download_path_var,
            is_folder=True
        )
        
        # 缺货请购单
        self.create_file_selector(
            path_frame,
            "缺货请购单",
            self.shortage_file_var,
            is_folder=False,
            file_types=[("Excel files", "*.xlsx;*.xls"), ("All files", "*.*")]
        )
        
        # 商品编码匹配表
        self.create_file_selector(
            path_frame,
            "匹配表",
            self.mapping_file_var,
            is_folder=False,
            file_types=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        
        # 冷藏药品清单（新增）
        self.create_file_selector(
            path_frame,
            "冷藏药品",
            self.cold_chain_file_var,
            is_folder=False,
            file_types=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        
        # 门店周边店映射表（新增）
        self.create_file_selector(
            path_frame,
            "门店信息",
            self.store_area_file_var,
            is_folder=False,
            file_types=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )

        # ===== 新增：分单文件 =====
        self.create_file_selector(
            path_frame,
            "分单文件",
            self.split_order_file_var,
            is_folder=False,
            file_types=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
    
    def create_file_selector(self, parent, label_text, variable, is_folder=False, file_types=None):
        """创建文件选择器组件"""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(frame, text=label_text, width=80).pack(side="left", padx=5)
        
        entry = ctk.CTkEntry(frame, textvariable=variable)
        entry.pack(side="left", fill="x", expand=True, padx=5)
        
        def browse():
            if is_folder:
                path = filedialog.askdirectory()
            else:
                path = filedialog.askopenfilename(filetypes=file_types)
            if path:
                variable.set(path)
        
        button = ctk.CTkButton(
            frame,
            text="浏览",
            command=browse,
            width=70
        )
        button.pack(side="right", padx=5)
        
        return frame
    
    def get_current_config(self):
        """获取当前所有配置"""
        return {
            "zq_username": self.zq_username_entry.get().strip(),
            "zq_password": self.zq_password_entry.get().strip(),
            "hh_username": self.hh_username_entry.get().strip(),
            "hh_password": self.hh_password_entry.get().strip(),
            "start_date": self.start_date_entry.get().strip(),
            "end_date": self.end_date_entry.get().strip(),
            "download_path": self.download_path_var.get(),
            "shortage_file": self.shortage_file_var.get(),
            "mapping_file": self.mapping_file_var.get(),
            "cold_chain_file": self.cold_chain_file_var.get(),
            "store_area_file": self.store_area_file_var.get(),
            "split_order_file": self.split_order_file_var.get(),  # 新增
        }
    
    def save_current_config(self):
        """保存当前配置"""
        config = self.get_current_config()
        if ConfigManager.save_config(config):
            self.log_message("💾 配置已保存", "SUCCESS")
            messagebox.showinfo("成功", f"配置已保存！\n位置: {ConfigManager.get_config_location()}")
        else:
            self.log_message("❌ 保存配置失败", "ERROR")
            messagebox.showerror("错误", "保存配置失败，请检查文件权限。")
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete("1.0", "end")
        self.log_text.insert("end", "📋 日志已清空\n")
        self.log_text.insert("end", "=" * 60 + "\n\n")
    
    def log_message(self, message, level="INFO"):
        """向日志写入消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        icons = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "WARNING": "⚠️",
            "ERROR": "❌"
        }
        icon = icons.get(level, "ℹ️")
        self.log_text.insert("end", f"[{timestamp}] {icon} {message}\n")
        self.log_text.see("end")
    
    def validate_inputs(self):
        """验证输入参数"""
        try:
            start_date = self.start_date_entry.get().strip()
            end_date = self.end_date_entry.get().strip()
            
            if not start_date or not end_date:
                messagebox.showerror("错误", "请填写开始日期和结束日期")
                return False
            
            datetime.strptime(start_date, "%Y-%m-%d")
            datetime.strptime(end_date, "%Y-%m-%d")
            
            # 验证xx账号
            if not self.zq_username_entry.get().strip():
                messagebox.showerror("错误", "请输入xx用户名")
                return False
            
            if not self.zq_password_entry.get().strip():
                messagebox.showerror("错误", "请输入xx密码")
                return False
            
            # 验证yy账号
            if not self.hh_username_entry.get().strip():
                messagebox.showerror("错误", "请输入yy用户名")
                return False
            
            if not self.hh_password_entry.get().strip():
                messagebox.showerror("错误", "请输入yy密码")
                return False
            
            if not os.path.exists(self.download_path_var.get()):
                messagebox.showerror("错误", "下载路径不存在")
                return False
            
            if not os.path.exists(self.shortage_file_var.get()):
                messagebox.showerror("错误", "缺货请购单文件不存在")
                return False
            
            if not os.path.exists(self.mapping_file_var.get()):
                messagebox.showerror("错误", "商品编码匹配表文件不存在")
                return False
            
            # 检查可选文件
            cold_chain_file = self.cold_chain_file_var.get()
            if cold_chain_file and not os.path.exists(cold_chain_file):
                messagebox.showerror("错误", "冷藏药品文件不存在")
                return False
            
            store_area_file = self.store_area_file_var.get()
            if store_area_file and not os.path.exists(store_area_file):
                messagebox.showerror("错误", "门店周边店映射表文件不存在")
                return False
            
            # 检查分单文件
            split_order_file = self.split_order_file_var.get()
            if split_order_file and not os.path.exists(split_order_file):
                messagebox.showerror("错误", "分单文件不存在")
                return False
            
            return True
            
        except ValueError as e:
            messagebox.showerror("错误", f"日期格式错误，请使用 YYYY-MM-DD 格式\n{str(e)}")
            return False
        except Exception as e:
            messagebox.showerror("错误", f"验证失败: {str(e)}")
            return False
    
    def run_main(self):
        """运行主程序"""
        if self.is_running:
            messagebox.showwarning("提示", "程序正在运行中，请稍候...")
            return
        
        if not self.validate_inputs():
            return
        
        self.save_current_config()
        
        self.log_message("=" * 60)
        self.log_message("🚀 开始运行任务", "INFO")
        
        self.is_running = True
        self.run_button.configure(text="⏳ 运行中...", state="disabled")
        self.save_config_btn.configure(state="disabled")
        self.status_label.configure(text="🟡 运行中", text_color="orange")
        self.progressbar.set(0.2)
        
        self.print_redirector.start()
        
        thread = threading.Thread(target=self._run_main_thread, daemon=True)
        thread.start()
    
    def _run_main_thread(self):
        """在后台线程中运行主程序"""
        try:
            params = {
                "ZQ_USERNAME": self.zq_username_entry.get().strip(),
                "ZQ_PASSWORD": self.zq_password_entry.get().strip(),
                "HH_USERNAME": self.hh_username_entry.get().strip(),
                "HH_PASSWORD": self.hh_password_entry.get().strip(),
                "start_date": self.start_date_entry.get().strip(),
                "end_date": self.end_date_entry.get().strip(),
                "DOWNLOAD_PATH": self.download_path_var.get(),
                "SHORTAGE_FILE": self.shortage_file_var.get(),
                "MAPPING_FILE": self.mapping_file_var.get(),
                "COLD_CHAIN_FILE": self.cold_chain_file_var.get(),
                "STORE_AREA_FILE": self.store_area_file_var.get(),
                "SPLIT_ORDER_PATH": self.split_order_file_var.get(),  # 新增
            }
            
            self.after(0, lambda: self.progressbar.set(0.4))
            self.after(0, lambda: self.log_message("📊 开始执行主程序...", "INFO"))
            
            # 调用main函数
            result = main(**params)
            
            if result:
                self.after(0, lambda: self.log_message(f"📄 输出文件: {result}", "SUCCESS"))
            
            self.after(0, self._on_success)
            
        except Exception as e:
            self.after(0, lambda: self._on_error(str(e)))
        finally:
            self.print_redirector.stop()
    
    def _on_success(self):
        """任务成功完成"""
        self.is_running = False
        self.run_button.configure(text="▶ 运行", state="normal")
        self.save_config_btn.configure(state="normal")
        self.status_label.configure(text="🟢 完成", text_color="green")
        self.progressbar.set(1.0)
        self.log_message("✅ 调拨方案生成已完成！", "SUCCESS")
        self.log_message("=" * 60 + "\n")
        messagebox.showinfo("成功", "调拨方案生成已完成！")
    
    def _on_error(self, error_msg):
        """任务出错"""
        self.is_running = False
        self.run_button.configure(text="▶ 运行", state="normal")
        self.save_config_btn.configure(state="normal")
        self.status_label.configure(text="🔴 错误", text_color="red")
        self.progressbar.set(0)
        self.log_message(f"❌ 错误: {error_msg}", "ERROR")
        self.log_message("=" * 60 + "\n")
        messagebox.showerror("错误", f"程序运行出错:\n{error_msg}")
    
    def on_closing(self):
        """窗口关闭事件"""
        if self.is_running:
            if not messagebox.askyesno("确认", "程序正在运行，确定要退出吗？"):
                return
        
        self.save_current_config()
        self.destroy()


if __name__ == "__main__":
    app = MainApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()