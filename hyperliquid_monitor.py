"""
Hyperliquid 数据监控工具
用于实时获取 Coinglass Hyperliquid 页面数据
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from datetime import datetime, timedelta
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import re
import webbrowser
import matplotlib
matplotlib.use('TkAgg')  # 使用TkAgg后端
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.font_manager as fm
from PIL import Image, ImageTk
import requests
import numpy as np
import squarify  # 用于树状图（热力图）
from okx_trader import OKXTrader  # OKX交易模块
from language_config import get_language_manager  # 语言管理器
from address_favorites import AddressFavorites  # 地址收藏管理

# 配置matplotlib中文字体（全局设置）
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')


# ==================== 深色主题配色方案 ====================
# DeFi/FinTech 专业深色主题（类似 Debank/Zerion）
COLORS = {
    # 背景色
    'bg_primary': '#0d0d0d',      # 深黑背景
    'bg_secondary': '#1a1a1a',    # 深灰卡片
    'bg_tertiary': '#252525',     # 次级卡片
    'bg_hover': '#2a2a2a',        # 悬停背景

    # 文字色
    'text_primary': '#ffffff',    # 主要白色文字
    'text_secondary': '#a3a3a3',  # 次要灰色文字
    'text_muted': '#737373',      # 弱化文字

    # 盈亏色
    'profit': '#10b981',          # 绿色（盈利）
    'loss': '#ef4444',            # 红色（亏损）
    'profit_bg': '#10b98115',     # 绿色背景（10%透明度）
    'loss_bg': '#ef444415',       # 红色背景（10%透明度）

    # 强调色
    'accent': '#0ea5e9',          # 蓝色按钮/强调
    'accent_hover': '#0284c7',    # 蓝色悬停
    'accent_bg': '#0ea5e915',     # 蓝色背景（10%透明度）

    # 边框色
    'border': '#2a2a2a',          # 边框
    'border_light': '#3a3a3a',    # 浅边框

    # 其他
    'warning': '#f59e0b',         # 警告橙色
    'success': '#10b981',         # 成功绿色
    'info': '#0ea5e9',            # 信息蓝色
}

# 字体配置
FONTS = {
    'title': ('SF Pro Display', 18, 'bold'),        # 标题
    'heading': ('SF Pro Display', 14, 'bold'),      # 二级标题
    'body': ('SF Pro Text', 11),                    # 正文
    'body_bold': ('SF Pro Text', 11, 'bold'),       # 正文加粗
    'number': ('JetBrains Mono', 11),               # 数字等宽
    'number_large': ('JetBrains Mono', 14, 'bold'), # 大号数字
    'small': ('SF Pro Text', 9),                    # 小字
}

# ==================== OKX 主流币配置 ====================
# 按市值从高到低排序的主流币列表（前50个）
MAIN_COINS = [
    'BTC-USDT-SWAP', 'ETH-USDT-SWAP', 'BNB-USDT-SWAP', 'SOL-USDT-SWAP',
    'XRP-USDT-SWAP', 'ADA-USDT-SWAP', 'DOGE-USDT-SWAP', 'AVAX-USDT-SWAP',
    'DOT-USDT-SWAP', 'MATIC-USDT-SWAP', 'LINK-USDT-SWAP', 'UNI-USDT-SWAP',
    'LTC-USDT-SWAP', 'ATOM-USDT-SWAP', 'BCH-USDT-SWAP', 'ETC-USDT-SWAP',
    'FIL-USDT-SWAP', 'APT-USDT-SWAP', 'ARB-USDT-SWAP', 'OP-USDT-SWAP',
    'SUI-USDT-SWAP', 'INJ-USDT-SWAP', 'TIA-USDT-SWAP', 'HBAR-USDT-SWAP',
    'IMX-USDT-SWAP', 'RUNE-USDT-SWAP', 'STX-USDT-SWAP', 'NEAR-USDT-SWAP',
    'FTM-USDT-SWAP', 'ALGO-USDT-SWAP', 'XLM-USDT-SWAP', 'VET-USDT-SWAP',
    'GRT-USDT-SWAP', 'SAND-USDT-SWAP', 'MANA-USDT-SWAP', 'AAVE-USDT-SWAP',
    'AXS-USDT-SWAP', 'THETA-USDT-SWAP', 'XTZ-USDT-SWAP', 'EOS-USDT-SWAP',
    'FLOW-USDT-SWAP', 'ICP-USDT-SWAP', 'APE-USDT-SWAP', 'CHZ-USDT-SWAP',
    'QNT-USDT-SWAP', 'EGLD-USDT-SWAP', 'LDO-USDT-SWAP', 'CFX-USDT-SWAP',
    'CRV-USDT-SWAP', 'MKR-USDT-SWAP'
]


# ==================== OKX API 客户端类 ====================
class OKXAPIClient:
    """OKX API 客户端类 - 用于获取加密货币行情数据"""

    def __init__(self):
        self.base_url = "https://www.okx.com/api/v5"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_tickers(self, inst_type="SWAP"):
        """
        获取所有行情数据

        Args:
            inst_type: 产品类型 SPOT-币币 SWAP-永续合约 FUTURES-交割合约

        Returns:
            list: 行情数据列表
        """
        try:
            url = f"{self.base_url}/market/tickers"
            params = {"instType": inst_type}
            response = self.session.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get('code') == '0':
                    return data.get('data', [])
            return []
        except Exception as e:
            print(f"获取行情失败: {str(e)}")
            return []

    def get_ticker(self, inst_id):
        """
        获取单个交易对行情

        Args:
            inst_id: 产品ID，如 BTC-USDT-SWAP

        Returns:
            dict: 行情数据
        """
        try:
            url = f"{self.base_url}/market/ticker"
            params = {"instId": inst_id}
            response = self.session.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get('code') == '0':
                    tickers = data.get('data', [])
                    return tickers[0] if tickers else {}
            return {}
        except Exception as e:
            print(f"获取单个行情失败: {str(e)}")
            return {}

    def parse_ticker_data(self, tickers, filter_usdt=True, top_n=50):
        """
        解析并格式化行情数据（按市值排序）

        Args:
            tickers: 原始行情数据
            filter_usdt: 是否只保留USDT永续合约
            top_n: 返回前N个（按主流币市值顺序）

        Returns:
            list: 格式化后的数据列表（按市值从高到低）
        """
        # 第1步：只保留主流币
        main_tickers = [t for t in tickers if t.get('instId', '') in MAIN_COINS]

        # 第2步：创建字典，方便后续按顺序提取
        ticker_dict = {t.get('instId'): t for t in main_tickers}

        # 第3步：按主流币列表顺序处理数据（即按市值排序）
        parsed_data = []

        for inst_id in MAIN_COINS[:top_n]:  # 只取前top_n个主流币
            if inst_id not in ticker_dict:
                continue  # 如果该币种数据不存在，跳过

            ticker = ticker_dict[inst_id]

            try:
                # 提取币种名称（如 BTC-USDT-SWAP -> BTC）
                symbol = inst_id.split('-')[0] if '-' in inst_id else inst_id

                # 解析数据
                last_price = float(ticker.get('last', 0))
                sod_utc8 = float(ticker.get('sodUtc8', 0))  # UTC+8 0点开盘价

                # 计算24H涨跌幅: (当前价 - 开盘价) / 开盘价 * 100
                if sod_utc8 > 0:
                    change_24h = (last_price - sod_utc8) / sod_utc8 * 100
                else:
                    change_24h = 0

                high_24h = float(ticker.get('high24h', 0))
                low_24h = float(ticker.get('low24h', 0))
                vol_24h = float(ticker.get('vol24h', 0))  # 币的数量
                vol_ccy_24h = float(ticker.get('volCcy24h', 0))  # USDT金额

                parsed_data.append({
                    'symbol': symbol,
                    'inst_id': inst_id,
                    'price': last_price,
                    'change': change_24h,
                    'high': high_24h,
                    'low': low_24h,
                    'volume': vol_24h,
                    'volume_usd': vol_ccy_24h,
                    'timestamp': ticker.get('ts', ''),
                    'market_cap_rank': MAIN_COINS.index(inst_id) + 1  # 市值排名
                })
            except Exception as e:
                continue

        # 返回数据（已经按市值顺序）
        return parsed_data


class HyperliquidMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Hyperliquid 大户持仓监控 - DeFi Dashboard")
        self.root.geometry("1850x900")  # 增加宽度以完整显示所有信息（包括地址提示）
        self.root.configure(bg=COLORS['bg_primary'])  # 深黑背景

        # 语言管理器
        self.lang = get_language_manager()

        # 地址收藏管理器
        self.favorites = AddressFavorites()

        # 数据存储
        self.data = {}
        self.is_loading = False

        # 币种选择变量（单选模式）
        self.all_coins = ['BTC', 'ETH', 'SOL']
        self.selected_coin = tk.StringVar(value='BTC')  # 默认选择BTC

        # 调试模式（显示浏览器窗口）
        self.debug_mode = tk.BooleanVar(value=False)

        # 时间筛选变量（最近多少天）
        self.time_filter = tk.StringVar(value="7")  # all, 1, 3, 7, 31 (默认7天用于测试)

        # 仓位金额筛选变量
        self.amount_filter = tk.StringVar(value="all")  # all, 5000w, 1y

        # OKX 相关变量
        self.okx_client = OKXAPIClient()
        self.okx_data = []
        self.okx_auto_refresh = tk.BooleanVar(value=False)
        self.okx_refresh_interval = 10000  # 10秒刷新一次
        self.okx_is_loading = False

        # 用户详情实时监控相关变量
        self.user_detail_driver = None  # 保持浏览器会话
        self.user_detail_window = None  # 详情窗口引用
        self.user_detail_data = {}  # 当前用户详情数据
        self.user_detail_auto_refresh = tk.BooleanVar(value=False)  # 自动刷新开关
        self.user_detail_refresh_interval = 10000  # 10秒刷新一次

        # 用户详情UI组件引用（用于局部更新，避免窗口闪烁）
        self.detail_ui_refs = {
            'pnl_labels': {},  # 盈亏数据标签 {'total_pnl': Label, 'pnl_24h': Label, ...}
            'update_time_label': None,  # 最后更新时间标签
            'position_tree': None,  # 持仓表格
            'order_tree': None,  # 委托表格
            'trade_tree': None,  # 交易表格
            'deposit_tree': None,  # 充值表格
            'withdraw_tree': None,  # 提现表格
            'position_frame_label': None,  # 持仓框架标题（显示数量）
            'order_frame_label': None,  # 委托框架标题
            'trade_frame_label': None,  # 交易框架标题
            'deposit_frame_label': None,  # 充提框架标题
        }

        # 主界面自动刷新相关变量
        self.main_auto_refresh = tk.BooleanVar(value=False)  # 主界面自动刷新开关
        self.main_refresh_interval = 900000  # 15分钟 = 900000毫秒
        self.main_last_update_time = None  # 最后更新时间

        # OKX交易相关变量
        self.okx_trader = None  # OKX交易客户端
        self.okx_config = {
            'api_key': '',
            'secret_key': '',
            'passphrase': '',
            'is_demo': True  # 默认使用模拟盘
        }
        self.okx_config_file = 'okx_config.json'  # 配置文件路径
        self.load_okx_config()  # 加载配置

        # 创建界面
        self.create_widgets()

        # 注册语言切换观察者（必须在create_widgets之后）
        self.lang.add_observer(self.on_language_changed)

        # 初始化自动跟单管理器
        self.auto_copy_trader = None  # 延迟初始化，等OKX配置完成后
        if self.okx_trader:
            try:
                self.auto_copy_trader = AutoCopyTrader(self)
                self.add_message("自动跟单系统已就绪", "success")
            except Exception as e:
                print(f"[Error] 初始化自动跟单失败: {e}")

    def create_widgets(self):
        """创建界面组件"""
        # 顶部控制栏
        control_frame = tk.Frame(self.root, bg=COLORS['bg_secondary'], height=70)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        control_frame.pack_propagate(False)

        # 标题
        self.title_label = tk.Label(
            control_frame,
            text="Hyperliquid 大户监控",
            font=FONTS['title'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary']
        )
        self.title_label.pack(side=tk.LEFT, padx=10)

        # 右侧容器（语言切换 + 作者标注）
        right_frame = tk.Frame(control_frame, bg=COLORS['bg_secondary'])
        right_frame.pack(side=tk.RIGHT, padx=10)

        # 语言切换按钮
        self.lang_btn = tk.Button(
            right_frame,
            text="🌐 English",
            command=self.toggle_language,
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_secondary'],
            font=FONTS['body'],
            activebackground=COLORS['bg_hover'],
            relief=tk.FLAT,
            bd=0,
            padx=15,
            pady=10,
            cursor='hand2'
        )
        self.lang_btn.pack(side=tk.TOP, pady=(0, 5))

        # 作者标注
        author_label = tk.Label(
            right_frame,
            text="👨‍💻 Author: Howard Zeng",
            font=FONTS['small'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_muted']
        )
        author_label.pack(side=tk.TOP)

        # 刷新按钮
        self.refresh_btn = tk.Button(
            control_frame,
            text="🔄 刷新数据",
            command=self.refresh_data,
            bg=COLORS['accent'],
            fg=COLORS['text_primary'],
            font=FONTS['body_bold'],
            activebackground=COLORS['accent_hover'],
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=12,
            cursor='hand2'
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=10)

        # 导出按钮
        self.export_btn = tk.Button(
            control_frame,
            text="💾 导出数据",
            command=self.export_data,
            bg=COLORS['accent'],
            fg=COLORS['text_primary'],
            font=FONTS['body_bold'],
            activebackground=COLORS['accent_hover'],
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=12,
            cursor='hand2'
        )
        self.export_btn.pack(side=tk.LEFT, padx=10)

        # OKX配置按钮
        self.okx_config_btn = tk.Button(
            control_frame,
            text="⚙️ OKX配置",
            command=self.show_okx_config_window,
            bg=COLORS['warning'],
            fg=COLORS['text_primary'],
            font=FONTS['body_bold'],
            activebackground='#d97706',
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=12,
            cursor='hand2'
        )
        self.okx_config_btn.pack(side=tk.LEFT, padx=10)

        # OKX手动交易按钮
        self.okx_trade_btn = tk.Button(
            control_frame,
            text="💹 手动交易",
            command=self.show_okx_trading_window,
            bg=COLORS['success'],
            fg=COLORS['text_primary'],
            font=FONTS['body_bold'],
            activebackground='#059669',
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=12,
            cursor='hand2'
        )
        self.okx_trade_btn.pack(side=tk.LEFT, padx=10)

        # 自动跟单按钮
        self.auto_copy_btn = tk.Button(
            control_frame,
            text="🤖 启动跟单",
            command=self.toggle_auto_copy_trading,
            bg='#6366f1',  # 蓝紫色
            fg=COLORS['text_primary'],
            font=FONTS['body_bold'],
            activebackground='#4f46e5',
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=12,
            cursor='hand2'
        )
        self.auto_copy_btn.pack(side=tk.LEFT, padx=10)

        # 调试模式复选框
        debug_cb = tk.Checkbutton(
            control_frame,
            text="调试模式",
            variable=self.debug_mode,
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_secondary'],
            font=FONTS['body'],
            selectcolor=COLORS['bg_tertiary'],
            activebackground=COLORS['bg_hover'],
            activeforeground=COLORS['text_primary']
        )
        debug_cb.pack(side=tk.LEFT, padx=10)

        # 主界面自动刷新复选框
        auto_refresh_cb = tk.Checkbutton(
            control_frame,
            text="自动刷新 (15分钟)",
            variable=self.main_auto_refresh,
            command=self.toggle_main_auto_refresh,
            bg=COLORS['bg_secondary'],
            fg=COLORS['accent'],
            font=FONTS['body_bold'],
            selectcolor=COLORS['bg_tertiary'],
            activebackground=COLORS['bg_hover'],
            activeforeground=COLORS['accent']
        )
        auto_refresh_cb.pack(side=tk.LEFT, padx=10)

        # 最后更新时间标签
        self.main_update_time_label = tk.Label(
            control_frame,
            text="",
            font=FONTS['small'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_muted']
        )
        self.main_update_time_label.pack(side=tk.LEFT, padx=5)

        # 状态标签
        self.status_label = tk.Label(
            control_frame,
            text="就绪",
            font=FONTS['body'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_secondary']
        )
        self.status_label.pack(side=tk.RIGHT, padx=10)

        # 创建主容器（左右布局）
        main_container = tk.Frame(self.root, bg=COLORS['bg_primary'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # 左侧筛选面板（增加宽度以容纳更多选项）
        filter_frame = tk.Frame(
            main_container,
            bg=COLORS['bg_secondary'],
            width=220,
            highlightbackground=COLORS['border'],
            highlightthickness=1,
            bd=0
        )
        filter_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        filter_frame.pack_propagate(False)

        # 筛选面板标题
        self.filter_coin_label = tk.Label(
            filter_frame,
            text="📊 币种筛选（单选）",
            font=FONTS['heading'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary']
        )
        self.filter_coin_label.pack(pady=(10, 5))

        # 币种单选按钮容器
        coin_radio_frame = tk.Frame(filter_frame, bg=COLORS['bg_secondary'])
        coin_radio_frame.pack(fill=tk.X, padx=15, pady=10)

        # 创建币种单选按钮
        for coin in self.all_coins:
            rb = tk.Radiobutton(
                coin_radio_frame,
                text=coin,
                variable=self.selected_coin,
                value=coin,
                bg=COLORS['bg_secondary'],
                fg=COLORS['text_primary'],
                font=FONTS['body_bold'],
                selectcolor=COLORS['bg_tertiary'],
                activebackground=COLORS['bg_hover'],
                activeforeground=COLORS['accent'],
                command=self.on_filter_change
            )
            rb.pack(anchor=tk.W, padx=10, pady=5)

        # 添加分隔线
        separator1 = ttk.Separator(filter_frame, orient='horizontal')
        separator1.pack(fill=tk.X, padx=5, pady=10)

        # 时间筛选区域
        self.filter_time_label = tk.Label(
            filter_frame,
            text="⏰ 开仓时间",
            font=FONTS['heading'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary']
        )
        self.filter_time_label.pack(pady=(5, 5))

        self.time_option_keys = ['filter_time_all', 'filter_time_1d', 'filter_time_3d', 'filter_time_7d', 'filter_time_31d']
        time_options = [
            ("全部时间", "all", 'filter_time_all'),
            ("最近1天", "1", 'filter_time_1d'),
            ("最近3天", "3", 'filter_time_3d'),
            ("最近7天", "7", 'filter_time_7d'),
            ("最近31天", "31", 'filter_time_31d')
        ]

        self.time_filter_radios = []
        for text, value, key in time_options:
            rb = tk.Radiobutton(
                filter_frame,
                text=text,
                variable=self.time_filter,
                value=value,
                bg=COLORS['bg_secondary'],
                fg=COLORS['text_primary'],
                font=FONTS['body'],
                selectcolor=COLORS['bg_tertiary'],
                activebackground=COLORS['bg_hover'],
                activeforeground=COLORS['text_primary']
            )
            rb.pack(anchor=tk.W, padx=15, pady=2)
            self.time_filter_radios.append((rb, key))

        # 添加分隔线
        separator2 = ttk.Separator(filter_frame, orient='horizontal')
        separator2.pack(fill=tk.X, padx=5, pady=10)

        # 仓位金额筛选区域
        self.filter_amount_label = tk.Label(
            filter_frame,
            text="💰 仓位金额",
            font=FONTS['heading'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary']
        )
        self.filter_amount_label.pack(pady=(5, 5))

        amount_options = [
            ("全部金额", "all", 'filter_amount_all'),
            (">5000万", "5000w", 'filter_amount_50m'),
            (">1亿", "1y", 'filter_amount_100m')
        ]

        self.amount_filter_radios = []
        for text, value, key in amount_options:
            rb = tk.Radiobutton(
                filter_frame,
                text=text,
                variable=self.amount_filter,
                value=value,
                bg=COLORS['bg_secondary'],
                fg=COLORS['text_primary'],
                font=FONTS['body'],
                selectcolor=COLORS['bg_tertiary'],
                activebackground=COLORS['bg_hover'],
                activeforeground=COLORS['text_primary']
            )
            rb.pack(anchor=tk.W, padx=15, pady=2)
            self.amount_filter_radios.append((rb, key))

        # 应用筛选按钮
        apply_btn = tk.Button(
            filter_frame,
            text="🔍 应用筛选",
            command=self.apply_filter,
            bg=COLORS['accent'],
            fg=COLORS['text_primary'],
            font=FONTS['body_bold'],
            activebackground=COLORS['accent_hover'],
            relief=tk.FLAT,
            bd=0,
            cursor='hand2',
            pady=10
        )
        apply_btn.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=10)

        # 右侧内容区域
        content_frame = tk.Frame(main_container, bg=COLORS['bg_primary'])
        content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 创建笔记本（标签页）
        self.notebook = ttk.Notebook(content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # 原始数据标签页
        raw_frame = tk.Frame(self.notebook, bg=COLORS['bg_secondary'])
        self.notebook.add(raw_frame, text="原始数据")

        # 文本显示区域（可滚动）
        self.text_area = scrolledtext.ScrolledText(
            raw_frame,
            wrap=tk.WORD,
            font=FONTS['body'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary'],
            insertbackground=COLORS['text_primary']
        )
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 持仓表格标签页
        table_frame = tk.Frame(self.notebook, bg=COLORS['bg_secondary'])
        self.notebook.add(table_frame, text="持仓数据")

        # 配置表格样式（必须在创建表格之前）
        style = ttk.Style()
        style.theme_use('default')

        # 表格主体样式
        style.configure(
            "Treeview",
            background=COLORS['bg_secondary'],
            foreground=COLORS['text_primary'],
            fieldbackground=COLORS['bg_secondary'],
            borderwidth=0,
            rowheight=32,
            font=FONTS['body']
        )

        # 表头样式
        style.configure(
            "Treeview.Heading",
            background=COLORS['bg_tertiary'],
            foreground=COLORS['text_primary'],
            borderwidth=0,
            relief=tk.FLAT,
            font=FONTS['body_bold']
        )

        # 选中行样式
        style.map(
            "Treeview",
            background=[('selected', COLORS['accent_bg'])],
            foreground=[('selected', COLORS['text_primary'])]
        )

        # 滚动条样式
        style.configure(
            "Vertical.TScrollbar",
            background=COLORS['bg_tertiary'],
            troughcolor=COLORS['bg_primary'],
            borderwidth=0,
            arrowsize=14
        )

        style.configure(
            "Horizontal.TScrollbar",
            background=COLORS['bg_tertiary'],
            troughcolor=COLORS['bg_primary'],
            borderwidth=0,
            arrowsize=14
        )

        # 创建表格 - 包含所有字段
        # 使用列键而不是直接的中文文本
        self.position_table_column_keys = [
            'col_rank', 'col_user_address', 'col_symbol', 'col_direction', 'col_position',
            'col_unrealized_pnl', 'col_entry_price', 'col_liquidation_price', 'col_margin',
            'col_funding', 'col_current_price', 'col_open_time'
        ]
        columns = tuple([self.lang.get_text(key) for key in self.position_table_column_keys])
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)

        # 设置列标题和宽度（确保能显示完整信息）
        self.position_table_column_widths = {
            'col_rank': 50,
            'col_user_address': 200,  # 增加宽度显示英文提示
            'col_symbol': 60,
            'col_direction': 70,
            'col_position': 180,  # "$1.86亿 1747.18 BTC"
            'col_unrealized_pnl': 160,  # "$837.16万 +4.49%"
            'col_entry_price': 180,  # "$111468.5 10X 全仓"
            'col_liquidation_price': 100,
            'col_margin': 100,
            'col_funding': 100,
            'col_current_price': 100,
            'col_open_time': 120  # "08:18 05-09"
        }

        for i, col in enumerate(columns):
            col_key = self.position_table_column_keys[i]
            self.tree.heading(col, text=col)
            width = self.position_table_column_widths.get(col_key, 100)
            self.tree.column(col, width=width, anchor='center')

        # 绑定双击事件
        self.tree.bind('<Double-Button-1>', self.on_row_double_click)

        # 添加垂直滚动条
        vsb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        # 添加横向滚动条
        hsb = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)

        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # 布局
        self.tree.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        # 配置表格框架的网格权重
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # ==================== OKX 标签页 ====================
        # OKX 数据表格标签页
        self.create_okx_table_tab(self.notebook)

        # OKX 热力图标签页
        self.create_okx_heatmap_tab(self.notebook)

        # OKX 当前持仓标签页
        self.create_okx_positions_tab(self.notebook)

        # OKX 当前委托标签页
        self.create_okx_orders_tab(self.notebook)

        # 自动跟单监控标签页
        self.create_auto_copy_monitor_tab(self.notebook)

        # ==================== 收藏地址标签页 ====================
        self.create_favorites_tab(self.notebook)

        # 消息提醒面板
        message_panel_frame = tk.LabelFrame(
            self.root,
            text="📢 消息提醒",
            font=FONTS['heading'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary'],
            padx=5,
            pady=5
        )
        message_panel_frame.pack(fill=tk.BOTH, padx=10, pady=(0, 5), expand=False)

        # 消息列表（使用ScrolledText）
        self.message_text = scrolledtext.ScrolledText(
            message_panel_frame,
            wrap=tk.WORD,
            font=FONTS['small'],
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary'],
            insertbackground=COLORS['text_primary'],
            height=6,
            state=tk.DISABLED  # 只读
        )
        self.message_text.pack(fill=tk.BOTH, expand=True)

        # 配置消息颜色标签
        self.message_text.tag_config('success', foreground=COLORS['profit'])
        self.message_text.tag_config('warning', foreground=COLORS['warning'])
        self.message_text.tag_config('error', foreground=COLORS['loss'])
        self.message_text.tag_config('info', foreground=COLORS['text_secondary'])

        # 底部信息栏
        info_frame = tk.Frame(self.root, bg=COLORS['bg_secondary'], height=30)
        info_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        info_frame.pack_propagate(False)

        self.info_label = tk.Label(
            info_frame,
            text="等待数据...",
            font=FONTS['small'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_muted']
        )
        self.info_label.pack(side=tk.LEFT, padx=10)

    def refresh_data(self):
        """刷新数据（在新线程中运行）"""
        if self.is_loading:
            messagebox.showwarning("提示", "正在加载数据，请稍候...")
            return

        # 在新线程中执行，避免界面卡顿
        thread = threading.Thread(target=self.fetch_data)
        thread.daemon = True
        thread.start()

    def fetch_data(self):
        """获取网页数据"""
        self.is_loading = True
        self.update_status("正在获取数据...")
        self.refresh_btn.config(state=tk.DISABLED)

        driver = None
        try:
            # 配置 Chrome 选项（反检测配置）
            chrome_options = Options()

            # 如果不是调试模式，使用无头模式
            if not self.debug_mode.get():
                chrome_options.add_argument('--headless=new')  # 使用新版headless模式

            # 基础配置
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--lang=zh-CN')

            # 反检测配置
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')  # 禁用自动化控制标志
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])  # 移除自动化提示
            chrome_options.add_experimental_option('useAutomationExtension', False)  # 禁用自动化扩展

            # 更真实的User-Agent
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')

            # 创建浏览器实例
            self.update_status("正在启动浏览器...")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)

            # 通过JavaScript隐藏webdriver属性
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    window.navigator.chrome = {
                        runtime: {}
                    };
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['zh-CN', 'zh', 'en']
                    });
                '''
            })

            # 访问页面
            self.update_status("正在访问页面...")
            url = "https://www.coinglass.com/zh/hyperliquid"
            driver.get(url)

            # 等待页面加载
            self.update_status("正在等待页面加载...")
            time.sleep(5)  # 等待动态内容加载

            # 应用币种筛选
            selected_coins = self.get_selected_coins()
            if selected_coins and len(selected_coins) < len(self.all_coins):
                self.update_status("正在应用币种筛选...")
                self.apply_coin_filter_on_page(driver, selected_coins)

            # 获取页面源代码
            page_source = driver.page_source

            # 尝试获取页面标题
            try:
                title = driver.title
                self.data['title'] = title
            except:
                self.data['title'] = "Hyperliquid"

            # 尝试获取可见文本
            try:
                body = driver.find_element(By.TAG_NAME, 'body')
                visible_text = body.text
                self.data['visible_text'] = visible_text
            except Exception as e:
                self.data['visible_text'] = f"无法获取文本: {str(e)}"

            # 尝试查找表格数据
            try:
                self.update_status("正在解析表格数据...")

                # 先尝试直接查找所有包含用户地址的链接
                print("\n===== 查找用户详情链接 =====")
                all_links = driver.find_elements(By.TAG_NAME, 'a')
                print(f"页面上总共有 {len(all_links)} 个链接")

                user_link_count = 0
                # 放宽链接验证规则 - 只要包含hyperliquid和完整地址即可
                valid_link_pattern = re.compile(r'(0x[a-fA-F0-9]{40})')
                for link in all_links:
                    href = link.get_attribute('href')
                    text = link.text
                    if href and 'hyperliquid' in href and '0x' in href:
                        # 提取地址
                        match = valid_link_pattern.search(href)
                        if match:
                            full_address = match.group(1)
                            print(f"找到有效用户链接: {text[:30]} -> {href}")
                            if text:  # 如果链接有文本
                                self.data.setdefault('user_links', {})[text] = href
                                user_link_count += 1
                            if user_link_count >= 5:  # 打印前5个
                                print("...")
                                break
                        else:
                            if user_link_count < 3:  # 只在前期打印无效链接
                                print(f"跳过无效链接格式: {href}")

                tables = driver.find_elements(By.TAG_NAME, 'table')
                self.data['tables_count'] = len(tables)
                self.data['tables_data'] = []
                if 'user_links' not in self.data:
                    self.data['user_links'] = {}  # 存储用户地址链接

                for idx, table in enumerate(tables):
                    try:
                        rows = table.find_elements(By.TAG_NAME, 'tr')
                        table_data = []

                        # 调试：打印第一行数据看结构
                        if idx == 0 and len(rows) > 0:
                            first_row = rows[0]
                            first_cells = first_row.find_elements(By.TAG_NAME, 'td')
                            if not first_cells:
                                first_cells = first_row.find_elements(By.TAG_NAME, 'th')
                            print(f"\n表格第一行有 {len(first_cells)} 列:")
                            for i, cell in enumerate(first_cells):
                                print(f"  列{i}: {cell.text[:30]}")

                        for row_idx, row in enumerate(rows):
                            cells = row.find_elements(By.TAG_NAME, 'td')
                            if not cells:
                                cells = row.find_elements(By.TAG_NAME, 'th')

                            row_data = []
                            for col_idx, cell in enumerate(cells):
                                # 获取单元格文本
                                cell_text = cell.text
                                row_data.append(cell_text)

                                # 尝试从所有列中查找包含地址的链接
                                if row_idx > 0:  # 跳过表头
                                    try:
                                        link = cell.find_element(By.TAG_NAME, 'a')
                                        href = link.get_attribute('href')
                                        # 验证是否是有效的用户详情链接（包含完整40位地址）
                                        if href and '/hyperliquid/' in href:
                                            match = valid_link_pattern.search(href)
                                            if match:
                                                # 存储：简写地址 -> 完整URL
                                                self.data['user_links'][cell_text] = href
                                                if row_idx <= 3:  # 只打印前3行
                                                    print(f"[列{col_idx}] 提取到用户链接: {cell_text} -> {href}")
                                    except:
                                        pass  # 这个单元格没有链接

                            if row_data:
                                table_data.append(row_data)
                        if table_data:
                            self.data['tables_data'].append(table_data)
                    except:
                        continue
            except Exception as e:
                self.data['tables_data'] = []
                self.data['user_links'] = {}
                self.data['error'] = f"表格解析错误: {str(e)}"

            # 获取时间戳
            self.data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # 更新界面
            self.update_display()
            self.update_status(f"数据更新成功 - {self.data['timestamp']}")

        except Exception as e:
            error_msg = f"获取数据失败: {str(e)}"
            self.update_status(error_msg)
            messagebox.showerror("错误", error_msg)

        finally:
            if driver:
                driver.quit()
            self.is_loading = False
            self.refresh_btn.config(state=tk.NORMAL)

            # 更新最后刷新时间
            self.main_last_update_time = datetime.now()
            update_text = f"最后更新: {self.main_last_update_time.strftime('%H:%M:%S')}"
            self.main_update_time_label.config(text=update_text)

    def update_display(self):
        """更新显示的数据"""
        # 更新文本区域
        self.text_area.delete(1.0, tk.END)

        display_text = f"=" * 80 + "\n"
        display_text += f"更新时间: {self.data.get('timestamp', 'N/A')}\n"
        display_text += f"页面标题: {self.data.get('title', 'N/A')}\n"
        display_text += f"=" * 80 + "\n\n"

        # 显示可见文本
        display_text += "【页面内容】\n"
        display_text += "-" * 80 + "\n"
        display_text += self.data.get('visible_text', '暂无数据')
        display_text += "\n\n"

        # 显示表格数据
        if self.data.get('tables_data'):
            display_text += f"\n{'=' * 80}\n"
            display_text += f"【表格数据】 (共 {len(self.data['tables_data'])} 个表格)\n"
            display_text += f"{'=' * 80}\n\n"

            for idx, table in enumerate(self.data['tables_data'], 1):
                display_text += f"\n--- 表格 {idx} ---\n"

                # 显示表头
                if len(table) > 0:
                    display_text += "表头: " + " | ".join(table[0]) + "\n"
                    display_text += "-" * 80 + "\n"

                # 显示数据行
                for row_idx, row in enumerate(table[1:], start=1):
                    display_text += f"行{row_idx}: "
                    # 显示每列的索引和值
                    for col_idx, cell in enumerate(row):
                        if cell:  # 只显示非空的列
                            display_text += f"[{col_idx}:{cell}] "
                    display_text += "\n"

                display_text += "\n"

        self.text_area.insert(1.0, display_text)

        # 更新表格（如果有合适的数据）
        self.tree.delete(*self.tree.get_children())
        selected_coins = self.get_selected_coins()
        total_rows = 0
        filtered_rows = 0

        # 获取筛选条件
        time_filter_value = self.time_filter.get()
        amount_filter_value = self.amount_filter.get()

        # 首先收集所有符合条件的行（用于排序）
        rows_to_display = []

        if self.data.get('tables_data'):
            for table in self.data['tables_data']:
                # 第一行通常是表头，从第二行开始是数据
                for row_idx, row in enumerate(table[1:], start=1):
                    if len(row) >= 3:  # 确保有足够的列
                        total_rows += 1

                        # 表格列索引（根据网页HTML结构）:
                        # 0: 空（复选框）
                        # 1: 排名 (#)
                        # 2: 用户地址
                        # 3: 币种
                        # 4: 方向（多/空）
                        # 5: 仓位
                        # 6: 未实现盈亏(%)
                        # 7: 开仓价格
                        # 8: 爆仓价格
                        # 9: 保证金
                        # 10: 资金费
                        # 11: 当前价格
                        # 12: 开仓时间

                        # 获取币种列（索引3）
                        coin_symbol = ''
                        if len(row) > 3:
                            coin_text = str(row[3]).strip().upper()
                            # 尝试匹配币种
                            for coin in self.all_coins:
                                if coin in coin_text:
                                    coin_symbol = coin
                                    break

                        # 币种筛选
                        if selected_coins and coin_symbol not in selected_coins and coin_symbol != '':
                            continue

                        # 提取仓位金额和开仓时间用于筛选
                        position_amount_str = row[5] if len(row) > 5 else ''
                        open_time_str = row[12] if len(row) > 12 else ''

                        # 解析金额（美元）
                        position_amount = self.parse_amount(position_amount_str)

                        # 解析开仓时间（距今天数）
                        days_ago = self.parse_open_time(open_time_str)

                        # 应用仓位金额筛选
                        if amount_filter_value == '5000w':
                            if position_amount < 50000000:  # 5000万
                                continue
                        elif amount_filter_value == '1y':
                            if position_amount < 100000000:  # 1亿
                                continue

                        # 应用时间筛选
                        if time_filter_value != 'all':
                            max_days = int(time_filter_value)
                            if days_ago > max_days:
                                continue

                        # 提取需要的12列数据（跳过第0列的空列）
                        display_row = []
                        for i in range(1, 14):  # 索引1到13，共12列
                            if i < len(row):
                                cell_value = row[i]
                                # 将换行符替换为空格，保持所有信息在一行显示
                                if isinstance(cell_value, str):
                                    cell_value = cell_value.replace('\n', ' ')
                                display_row.append(cell_value)
                            else:
                                display_row.append('')

                        # 保存行数据和金额（用于排序）
                        rows_to_display.append((position_amount, display_row))

        # 按金额从大到小排序
        rows_to_display.sort(key=lambda x: x[0], reverse=True)

        # 插入排序后的数据到表格
        for amount, display_row in rows_to_display:
            self.tree.insert('', tk.END, values=display_row)
            filtered_rows += 1

        # 更新信息栏
        table_count = len(self.data.get('tables_data', []))
        selected_count = len(selected_coins)
        filter_info = f"时间:{time_filter_value}天" if time_filter_value != 'all' else "时间:全部"
        if amount_filter_value == '5000w':
            filter_info += " | 金额:>5000万"
        elif amount_filter_value == '1y':
            filter_info += " | 金额:>1亿"
        else:
            filter_info += " | 金额:全部"

        self.info_label.config(
            text=f"最后更新: {self.data.get('timestamp', 'N/A')} | 总数据: {total_rows} | 已筛选: {filtered_rows} | {filter_info}"
        )

        # 调试：打印提取到的链接
        user_links = self.data.get('user_links', {})
        print(f"\n========== 用户链接调试信息 ==========")
        print(f"总共提取到 {len(user_links)} 个用户链接:")
        for addr, url in list(user_links.items())[:5]:  # 只打印前5个
            print(f"  {addr} -> {url}")
        if len(user_links) > 5:
            print(f"  ... 还有 {len(user_links) - 5} 个链接")
        print("=" * 40 + "\n")

    def update_status(self, message):
        """更新状态栏"""
        self.status_label.config(text=message)
        self.root.update_idletasks()

    def add_message(self, message, msg_type='info'):
        """
        添加消息到消息提醒面板

        Args:
            message: 消息内容
            msg_type: 消息类型 ('success', 'warning', 'error', 'info')
        """
        try:
            timestamp = datetime.now().strftime('%H:%M:%S')

            # 消息类型图标
            icons = {
                'success': '✅',
                'warning': '⚠️',
                'error': '❌',
                'info': 'ℹ️'
            }
            icon = icons.get(msg_type, 'ℹ️')

            # 格式化消息
            formatted_msg = f"[{timestamp}] {icon} {message}\n"

            # 添加到消息面板
            self.message_text.config(state=tk.NORMAL)
            self.message_text.insert(tk.END, formatted_msg, msg_type)
            self.message_text.see(tk.END)  # 滚动到最后
            self.message_text.config(state=tk.DISABLED)

            # 同时打印到控制台
            print(f"[Message] {formatted_msg.strip()}")

        except Exception as e:
            print(f"[Error] Failed to add message: {e}")

    def on_filter_change(self):
        """币种筛选变化时的回调"""
        pass  # 可以在这里添加实时筛选逻辑

    def apply_filter(self):
        """应用筛选"""
        if self.data:
            self.update_display()
            selected = self.get_selected_coins()
            messagebox.showinfo("筛选已应用", f"已选择 {len(selected)} 个币种")

    def get_selected_coins(self):
        """获取选中的币种（单选模式，返回列表格式以保持兼容性）"""
        selected_coin = self.selected_coin.get()
        return [selected_coin] if selected_coin else []

    def parse_amount(self, amount_str):
        """
        解析仓位金额字符串，转换为美元数值
        例如: "$1.86亿 1747.18 BTC" -> 186000000
        """
        try:
            if not amount_str or not isinstance(amount_str, str):
                return 0

            # 提取金额部分（$符号后的数字和单位）
            # 匹配模式: $数字.数字 + 单位（万或亿）
            match = re.search(r'\$([0-9.]+)(万|亿)?', amount_str)
            if not match:
                return 0

            number = float(match.group(1))
            unit = match.group(2)

            # 转换为美元
            if unit == '亿':
                return number * 100000000
            elif unit == '万':
                return number * 10000
            else:
                return number

        except Exception as e:
            return 0

    def parse_open_time(self, time_str):
        """
        解析开仓时间字符串，计算距离现在的天数
        例如: "08:18 05-09" -> 计算距今天数
        """
        try:
            if not time_str or not isinstance(time_str, str):
                return 999  # 返回一个很大的数表示无效

            # 提取时间和日期部分
            # 格式: "HH:MM MM-DD"
            match = re.search(r'(\d{2}):(\d{2})\s+(\d{2})-(\d{2})', time_str)
            if not match:
                return 999

            hour = int(match.group(1))
            minute = int(match.group(2))
            month = int(match.group(3))
            day = int(match.group(4))

            # 获取当前时间
            now = datetime.now()
            current_year = now.year

            # 尝试构建日期（假设是今年）
            try:
                open_date = datetime(current_year, month, day, hour, minute)
            except ValueError:
                # 日期无效
                return 999

            # 如果开仓日期在未来，说明是去年的
            if open_date > now:
                open_date = datetime(current_year - 1, month, day, hour, minute)

            # 计算天数差
            days_diff = (now - open_date).days

            return days_diff

        except Exception as e:
            return 999

    def apply_coin_filter_on_page(self, driver, selected_coins):
        """在网页上应用币种筛选"""
        try:
            # 等待页面完全加载
            time.sleep(3)
            self.update_status("页面加载完成，开始查找币种筛选器...")

            # 使用精确的选择器查找 MuiAutocomplete 组件
            try:
                # 方法1: 通过类名查找
                autocomplete = driver.find_element(By.CLASS_NAME, "MuiAutocomplete-root")
                self.update_status("找到币种筛选器 (MuiAutocomplete)")
            except:
                try:
                    # 方法2: 通过XPath查找
                    autocomplete = driver.find_element(By.XPATH, "//div[contains(@class, 'MuiAutocomplete-root')]")
                    self.update_status("找到币种筛选器 (XPath)")
                except:
                    self.update_status("未找到币种筛选器，使用客户端筛选")
                    return

            # 查找输入框
            try:
                input_box = autocomplete.find_element(By.CLASS_NAME, "MuiAutocomplete-input")
                self.update_status(f"找到输入框，当前值: {input_box.get_attribute('value')}")
            except:
                self.update_status("未找到输入框")
                return

            # 只处理单个币种选择（如果选择了多个币种，只用第一个）
            if len(selected_coins) == 0:
                self.update_status("未选择任何币种，显示全部数据")
                return

            target_coin = selected_coins[0] if len(selected_coins) == 1 else selected_coins[0]
            self.update_status(f"准备选择币种: {target_coin}")

            # 点击输入框打开下拉列表
            try:
                input_box.click()
                time.sleep(1.5)
                self.update_status("已点击输入框，等待下拉列表...")
            except:
                # 尝试点击下拉按钮
                try:
                    popup_button = autocomplete.find_element(By.CLASS_NAME, "MuiAutocomplete-popupIndicator")
                    popup_button.click()
                    time.sleep(1.5)
                    self.update_status("已点击下拉按钮")
                except:
                    self.update_status("无法打开下拉列表")
                    return

            # 等待下拉选项出现
            time.sleep(2)

            # 查找下拉列表中的选项
            try:
                # 尝试多种方式查找选项
                option_selectors = [
                    f"//li[contains(text(), '{target_coin}')]",
                    f"//li[@role='option' and contains(., '{target_coin}')]",
                    f"//div[@role='option' and contains(., '{target_coin}')]",
                    f"//*[@role='option'][contains(text(), '{target_coin}')]",
                ]

                coin_option = None
                for selector in option_selectors:
                    try:
                        coin_option = driver.find_element(By.XPATH, selector)
                        if coin_option:
                            self.update_status(f"找到 {target_coin} 选项")
                            break
                    except:
                        continue

                if not coin_option:
                    # 尝试获取所有选项看看有什么
                    try:
                        all_options = driver.find_elements(By.XPATH, "//li[@role='option']")
                        self.update_status(f"找到 {len(all_options)} 个选项")
                        # 遍历查找包含目标币种的选项
                        for option in all_options:
                            if target_coin in option.text:
                                coin_option = option
                                self.update_status(f"在选项列表中找到: {option.text}")
                                break
                    except:
                        pass

                if coin_option:
                    # 点击选项
                    try:
                        coin_option.click()
                        time.sleep(2)
                        self.update_status(f"已选择币种: {target_coin}")
                    except:
                        # 使用JavaScript点击
                        driver.execute_script("arguments[0].click();", coin_option)
                        time.sleep(2)
                        self.update_status(f"已选择币种(JS): {target_coin}")

                    # 等待数据刷新
                    time.sleep(3)
                    self.update_status(f"币种 {target_coin} 筛选已应用，等待数据刷新...")
                else:
                    self.update_status(f"未找到币种 {target_coin} 的选项")

            except Exception as e:
                self.update_status(f"选择币种时出错: {str(e)}")

        except Exception as e:
            self.update_status(f"应用筛选失败: {str(e)}")

    def on_row_double_click(self, event):
        """处理表格行双击事件 - 只响应地址列"""
        try:
            # 获取点击的列
            region = self.tree.identify_region(event.x, event.y)
            if region != "cell":
                return

            column = self.tree.identify_column(event.x)
            # 列索引：#0是tree列，#1是第一列（排名），#2是第二列（用户地址）
            if column != "#2":  # 只响应用户地址列
                return

            # 获取选中的行
            selected_item = self.tree.selection()
            if not selected_item:
                return

            # 获取行数据
            item = self.tree.item(selected_item[0])
            values = item['values']

            if len(values) < 2:
                return

            # 获取用户地址（第2列，索引1）
            user_address = values[1]

            # 从user_links字典中查找对应的URL
            user_links = self.data.get('user_links', {})

            if user_address in user_links:
                url = user_links[user_address]
                print(f"双击用户地址: {user_address}")
                print(f"准备访问URL: {url}")
                self.update_status(f"正在爬取用户详情: {url}")
                # 直接在新线程中爬取详情
                thread = threading.Thread(target=self.fetch_user_details, args=(url, user_address))
                thread.daemon = True
                thread.start()
            else:
                print(f"未找到用户地址 {user_address} 的链接")
                print(f"可用的链接: {list(user_links.keys())}")
                messagebox.showinfo("提示", f"未找到用户地址 {user_address} 的详情链接")

        except Exception as e:
            messagebox.showerror("错误", f"操作失败: {str(e)}")

    def fetch_user_details(self, url, user_address):
        """爬取用户详情页数据并显示可视化"""
        driver = None
        debug_log = []  # 收集调试日志

        def log(msg):
            """添加日志"""
            debug_log.append(msg)
            self.update_status(msg)
            print(msg)  # 同时输出到控制台

        try:
            log(f"===== 开始爬取用户详情 =====")
            log(f"用户地址: {user_address}")
            log(f"目标URL: {url}")

            # 验证URL格式
            if not url.startswith('http'):
                log(f"⚠ 警告: URL格式不正确，尝试补全...")
                if url.startswith('/'):
                    url = 'https://www.coinglass.com' + url
                    log(f"补全后的URL: {url}")
                else:
                    log(f"✗ 错误: 无法处理的URL格式")
                    raise Exception(f"无效的URL格式: {url}")

            # 配置浏览器（反检测配置）
            chrome_options = Options()
            if not self.debug_mode.get():
                chrome_options.add_argument('--headless=new')  # 使用新版headless模式

            # 基础配置
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--lang=zh-CN')

            # 反检测配置
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # 更真实的User-Agent
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')

            log(f"正在启动浏览器...")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)

            # 通过JavaScript隐藏webdriver属性
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    window.navigator.chrome = {
                        runtime: {}
                    };
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['zh-CN', 'zh', 'en']
                    });
                '''
            })

            # 先访问首页建立session（模拟真实用户行为）
            log("先访问首页建立session...")
            driver.get("https://www.coinglass.com/zh/hyperliquid")
            time.sleep(3)  # 等待首页加载
            log("✓ Session已建立")

            # 再访问用户详情页
            driver.get(url)
            log("页面已打开，等待加载...")

            # 显示实际访问到的URL（可能经过重定向）
            actual_url = driver.current_url
            log(f"实际访问的URL: {actual_url}")

            # 等待SPA应用渲染（增加等待时间）
            log("等待页面JavaScript执行和内容渲染...")
            time.sleep(5)  # 给SPA应用足够时间执行JavaScript

            # 尝试等待React/Next.js应用的根元素加载
            try:
                WebDriverWait(driver, 8).until(
                    lambda d: len(d.find_element(By.TAG_NAME, 'body').text) > 100
                )
                log("✓ 页面内容已加载")
            except:
                log("⚠ 等待超时，但继续尝试...")
                pass

            # 额外等待确保所有动态内容渲染完成
            time.sleep(2)

            # 检查是否返回404（改进检测逻辑）
            page_text = driver.find_element(By.TAG_NAME, 'body').text
            log(f"页面文本长度: {len(page_text)} 字符")
            log(f"页面前100字符: {page_text[:100]}")

            # 保存调试截图（只在headless模式且内容少时保存）
            if not self.debug_mode.get() and len(page_text) < 200:
                try:
                    screenshot_path = f"debug_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    driver.save_screenshot(screenshot_path)
                    log(f"✓ 已保存调试截图: {screenshot_path}")
                except:
                    pass

            # 更严格的404判断：文本很短 + 包含404关键字
            is_404 = (len(page_text) < 100 and ('404' in page_text or 'Not Found' in page_text)) or \
                     (page_text.strip() == '404 Not Found\nnginx')

            if is_404:
                log("⚠ 检测到404错误，尝试使用其他URL格式...")

                # 尝试其他可能的URL格式
                alt_urls = []

                # 从原URL提取地址部分
                if '0x' in url:
                    address_match = re.search(r'(0x[a-fA-F0-9]{40})', url)
                    if address_match:
                        full_address = address_match.group(1)
                        log(f"提取到完整地址: {full_address}")

                        # 尝试不同的URL格式
                        alt_urls = [
                            f"https://www.coinglass.com/hyperliquid/{full_address}",  # 无zh
                            f"https://www.coinglass.com/zh/pro/futures/hyperliquid/{full_address}",  # 添加pro/futures
                            f"https://www.coinglass.com/pro/futures/hyperliquid/{full_address}",
                        ]

                # 尝试每个备选URL
                found_valid_page = False
                for alt_url in alt_urls:
                    log(f"尝试访问: {alt_url}")
                    driver.get(alt_url)
                    # 等待SPA应用渲染（增加等待时间）
                    time.sleep(5)  # 给足够时间执行JavaScript
                    try:
                        WebDriverWait(driver, 8).until(
                            lambda d: len(d.find_element(By.TAG_NAME, 'body').text) > 100
                        )
                        log("  ✓ 页面内容已加载")
                    except:
                        log("  ⚠ 等待超时")
                        pass

                    # 额外等待确保渲染完成
                    time.sleep(2)

                    page_text_check = driver.find_element(By.TAG_NAME, 'body').text
                    log(f"  页面文本长度: {len(page_text_check)} 字符")

                    # 改进的404检测
                    is_404_alt = (len(page_text_check) < 100 and ('404' in page_text_check or 'Not Found' in page_text_check)) or \
                                 (page_text_check.strip() == '404 Not Found\nnginx')

                    if not is_404_alt:
                        log(f"✓ 成功访问: {alt_url}")
                        actual_url = driver.current_url
                        log(f"实际URL: {actual_url}")
                        # 更新page_text为当前有效页面
                        page_text = page_text_check
                        found_valid_page = True
                        break
                    else:
                        log(f"  这个URL也是404")

                if not found_valid_page:
                    log("✗ 所有URL格式都失败，该地址在CoinGlass上没有详情页")
                    log("可能原因：1) 地址不存在 2) 地址已失效 3) CoinGlass未索引该地址")
                    # 提前退出，不继续尝试提取数据
                    user_details_404 = {
                        'address': user_address,
                        'error': '404 - 页面不存在',
                        'debug_log': debug_log
                    }
                    # 在主线程中显示
                    self.root.after(0, lambda: self.show_user_details_window(user_details_404))
                    return

            # 等待页面完全加载（Ant Design动态渲染）
            log("等待页面动态内容加载...")
            try:
                # 等待Ant Design表格出现（减少等待时间到10秒）
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "ant-table-row"))
                )
                log("✓ 检测到Ant Design表格已加载")
                # 额外等待1秒确保数据渲染
                time.sleep(1)
            except:
                log("⚠ 未检测到ant-table-row，可能页面结构不同")
                # 即使没有表格，也等待2秒让页面加载
                time.sleep(2)

            user_details = {
                'address': user_address,
                'full_address': '',
                'total_pnl': '',
                'pnl_24h': '',
                'pnl_48h': '',
                'pnl_7d': '',
                'pnl_30d': '',
                'position_value': '',
                'positions': [],  # 当前持仓
                'trades': [],  # 交易历史
                'open_orders': [],  # 当前委托
                'deposits': [],  # 充值记录
                'withdrawals': [],  # 提现记录
                'debug_log': debug_log  # 保存调试日志
            }

            # 尝试提取完整地址
            try:
                # 查找包含完整地址的元素
                address_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '0x')]")
                for elem in address_elements:
                    text = elem.text
                    if text.startswith('0x') and len(text) == 42:
                        user_details['full_address'] = text
                        break
            except:
                pass

            # 提取盈亏数据 - 使用精确的选择器
            try:
                # 等待用户详情数据加载完成 - 使用显式等待（优化时间）
                log("等待页面数据加载完成...")
                try:
                    # 等待用户详情区域出现（不是header的全局统计）
                    WebDriverWait(driver, 15).until(
                        lambda d: len(d.find_elements(By.CLASS_NAME, "Number")) > 10
                    )
                    log("✓ 检测到多个数据元素已加载")
                    # 减少额外等待时间
                    time.sleep(2)
                except Exception as e:
                    log(f"⚠ 等待超时，但继续尝试提取: {str(e)}")
                    # 即使超时也等待2秒
                    time.sleep(2)

                # 保存页面HTML用于调试
                try:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    html_filename = f"debug_page_{timestamp}.html"
                    with open(html_filename, 'w', encoding='utf-8') as f:
                        f.write(driver.page_source)
                    log(f"✓ 页面HTML已保存到: {html_filename}")
                except Exception as e:
                    log(f"保存HTML失败: {str(e)}")

                # 获取页面文本内容，用于调试
                body_text = driver.find_element(By.TAG_NAME, 'body').text
                log(f"✓ 页面已加载，文本长度: {len(body_text)}")

                # 检查关键字是否存在
                if '总盈亏' in body_text:
                    log("✓ 找到'总盈亏'关键字")
                else:
                    log("✗ 未找到'总盈亏'关键字")
                    # 显示页面前500个字符
                    log(f"页面开头内容: {body_text[:500]}")

                # 尝试使用JavaScript一次性获取所有盈亏数据
                try:
                    js_all_data = """
                    var data = {};
                    var labels = ['总盈亏', '24小时盈亏', '48小时盈亏', '7天盈亏', '30天盈亏', '永续合约仓位价值'];

                    labels.forEach(function(label) {
                        var elements = Array.from(document.querySelectorAll('*'));
                        for (var i = 0; i < elements.length; i++) {
                            var elem = elements[i];

                            // 跳过header和导航栏中的元素
                            var parentHeader = elem.closest('header, nav, .cg-header, .cg-top-data');
                            if (parentHeader) {
                                continue;
                            }

                            // 检查元素文本是否包含标签
                            if (elem.textContent.trim() === label ||
                                (elem.innerText && elem.innerText.trim() === label)) {

                                // 方法1: 查找父元素中的Number类
                                var parent = elem.parentElement;
                                if (parent) {
                                    var numberElems = parent.querySelectorAll('.Number, [class*="Number"], [class*="rise"], [class*="fall"]');
                                    for (var j = 0; j < numberElems.length; j++) {
                                        var numElem = numberElems[j];
                                        var numText = numElem.textContent.trim();
                                        // 确保是金额格式（包含$或万或亿）
                                        if (numText && (numText.includes('$') || numText.includes('万') || numText.includes('亿'))) {
                                            data[label] = numText;
                                            break;
                                        }
                                    }
                                    if (data[label]) break;
                                }

                                // 方法2: 查找后续兄弟元素
                                var sibling = elem.nextElementSibling;
                                var attempts = 0;
                                while (sibling && attempts < 5) {
                                    if (sibling.className && sibling.className.includes('Number')) {
                                        var sibText = sibling.textContent.trim();
                                        if (sibText && (sibText.includes('$') || sibText.includes('万') || sibText.includes('亿'))) {
                                            data[label] = sibText;
                                            break;
                                        }
                                    }
                                    sibling = sibling.nextElementSibling;
                                    attempts++;
                                }
                                if (data[label]) break;
                            }
                        }
                    });
                    return JSON.stringify(data);
                    """
                    js_result = driver.execute_script(js_all_data)
                    if js_result:
                        js_data = json.loads(js_result)
                        log(f"✓ JavaScript一次性提取结果: {js_data}")
                        # 如果JavaScript成功获取了数据，直接使用
                        if js_data.get('总盈亏'):
                            user_details['total_pnl'] = js_data.get('总盈亏', 'N/A')
                            user_details['pnl_24h'] = js_data.get('24小时盈亏', 'N/A')
                            user_details['pnl_48h'] = js_data.get('48小时盈亏', 'N/A')
                            user_details['pnl_7d'] = js_data.get('7天盈亏', 'N/A')
                            user_details['pnl_30d'] = js_data.get('30天盈亏', 'N/A')
                            user_details['position_value'] = js_data.get('永续合约仓位价值', 'N/A')
                            log("✓ 使用JavaScript一次性提取的数据")
                            # 跳过后续的逐个提取
                            skip_individual_extraction = True
                        else:
                            skip_individual_extraction = False
                    else:
                        skip_individual_extraction = False
                except Exception as e:
                    log(f"JavaScript一次性提取失败: {str(e)}")
                    skip_individual_extraction = False

                # 使用多种方法尝试提取数据
                def extract_pnl(label, xpath_patterns):
                    """尝试多种XPath模式提取数据，排除header区域"""
                    # 方法1: XPath选择器（排除header）
                    for i, xpath in enumerate(xpath_patterns):
                        try:
                            # 修改XPath以排除header区域
                            safe_xpath = xpath + "[not(ancestor::header) and not(ancestor::*[contains(@class, 'cg-header')]) and not(ancestor::*[contains(@class, 'cg-top-data')])]"
                            elem = driver.find_element(By.XPATH, safe_xpath)
                            text = elem.text.strip()
                            # 验证是金额格式
                            if text and ('$' in text or '万' in text or '亿' in text):
                                log(f"✓ {label}: {text} (XPath方法{i+1})")
                                return text
                        except Exception as e:
                            log(f"  XPath方法{i+1}失败: {str(e)[:50]}")
                            continue

                    # 方法2: 使用JavaScript直接查询DOM（排除header）
                    try:
                        js_script = f"""
                        var elements = document.querySelectorAll('*');
                        var result = '';
                        for (var i = 0; i < elements.length; i++) {{
                            var elem = elements[i];

                            // 跳过header区域
                            var inHeader = elem.closest('header, nav, .cg-header, .cg-top-data');
                            if (inHeader) continue;

                            if (elem.textContent.trim() === '{label}') {{
                                var parent = elem.parentElement;
                                if (parent) {{
                                    var numberElems = parent.querySelectorAll('.Number, [class*="Number"]');
                                    for (var j = 0; j < numberElems.length; j++) {{
                                        var numText = numberElems[j].textContent.trim();
                                        if (numText && (numText.includes('$') || numText.includes('万') || numText.includes('亿'))) {{
                                            result = numText;
                                            break;
                                        }}
                                    }}
                                    if (result) break;
                                }}
                            }}
                        }}
                        return result;
                        """
                        result = driver.execute_script(js_script)
                        if result:
                            log(f"✓ {label}: {result} (JavaScript方法)")
                            return result
                    except Exception as e:
                        log(f"  JavaScript方法失败: {str(e)[:50]}")

                    # 方法3: 正则表达式从页面文本提取（更严格的模式）
                    try:
                        # 使用更精确的模式，确保匹配的是标签后面的金额
                        pattern = rf'{label}[^\n]*?(-?\$[0-9.,]+[万亿]?)'
                        match = re.search(pattern, body_text)
                        if match:
                            text = match.group(1)
                            log(f"✓ {label}: {text} (正则表达式)")
                            return text
                    except Exception as e:
                        log(f"  正则表达式失败: {str(e)}")

                    log(f"✗ {label}: 未找到数据")
                    return 'N/A'  # 返回N/A而不是None

                # 如果JavaScript一次性提取失败，则逐个提取
                if not skip_individual_extraction:
                    log("开始逐个提取数据...")

                    # 总盈亏
                    user_details['total_pnl'] = extract_pnl('总盈亏', [
                        "//div[contains(text(), '总盈亏')]/following-sibling::div[contains(@class, 'Number')]",
                        "//*[contains(text(), '总盈亏')]/..//div[contains(@class, 'Number')]",
                        "//*[text()='总盈亏']/following::div[contains(@class, 'Number')][1]"
                    ])

                    # 24小时盈亏
                    user_details['pnl_24h'] = extract_pnl('24小时盈亏', [
                        "//div[contains(text(), '24小时盈亏')]/following-sibling::div[contains(@class, 'Number')]",
                        "//*[contains(text(), '24小时盈亏')]/..//div[contains(@class, 'Number')]",
                        "//*[text()='24小时盈亏']/following::div[contains(@class, 'Number')][1]"
                    ])

                    # 48小时盈亏
                    user_details['pnl_48h'] = extract_pnl('48小时盈亏', [
                        "//div[contains(text(), '48小时盈亏')]/following-sibling::div[contains(@class, 'Number')]",
                        "//*[contains(text(), '48小时盈亏')]/..//div[contains(@class, 'Number')]",
                        "//*[text()='48小时盈亏']/following::div[contains(@class, 'Number')][1]"
                    ])

                    # 7天盈亏
                    user_details['pnl_7d'] = extract_pnl('7天盈亏', [
                        "//div[contains(text(), '7天盈亏')]/following-sibling::div[contains(@class, 'Number')]",
                        "//*[contains(text(), '7天盈亏')]/..//div[contains(@class, 'Number')]",
                        "//*[text()='7天盈亏']/following::div[contains(@class, 'Number')][1]"
                    ])

                    # 30天盈亏
                    user_details['pnl_30d'] = extract_pnl('30天盈亏', [
                        "//div[contains(text(), '30天盈亏')]/following-sibling::div[contains(@class, 'Number')]",
                        "//*[contains(text(), '30天盈亏')]/..//div[contains(@class, 'Number')]",
                        "//*[text()='30天盈亏']/following::div[contains(@class, 'Number')][1]"
                    ])

                    # 永续合约仓位价值
                    user_details['position_value'] = extract_pnl('永续合约仓位价值', [
                        "//div[contains(text(), '永续合约仓位价值')]/following-sibling::div[contains(@class, 'Number')]",
                        "//*[contains(text(), '永续合约仓位价值')]/..//div[contains(@class, 'Number')]",
                        "//*[contains(text(), '仓位价值')]/..//div[contains(@class, 'Number')]"
                    ])

                log("✓ 数据提取完成")

            except Exception as e:
                log(f"✗ 提取盈亏数据异常: {str(e)}")

            # 提取所有Ant Design表格数据 - 通过点击标签页分别提取
            try:
                log("开始提取Ant Design表格数据...")

                # 定义标签页名称和提取函数
                tabs_config = [
                    {'name': '仓位', 'data_key': 'positions'},
                    {'name': '交易', 'data_key': 'trades'},
                    {'name': '当前委托', 'data_key': 'open_orders'},
                    {'name': '充值 & 提现', 'data_key': 'deposits_withdrawals'},
                ]

                def click_tab(tab_name):
                    """点击指定名称的标签页，返回是否成功"""
                    try:
                        log(f"尝试点击标签页: {tab_name}")

                        # 方法1: 使用MuiTab选择器 + 文本内容
                        # 处理特殊字符（如"充值 & 提现"中的&）
                        search_text = tab_name.replace(' & ', '').replace('&', '')

                        # 查找所有MuiTab按钮
                        tab_buttons = driver.find_elements(By.CSS_SELECTOR, "button[role='tab'].MuiTab-root")
                        log(f"找到 {len(tab_buttons)} 个Tab按钮")

                        for i, tab_btn in enumerate(tab_buttons):
                            btn_text = tab_btn.text.strip()
                            # 移除数字计数（如"当前委托(2)"中的"(2)"）
                            clean_text = re.sub(r'\([0-9]+\)', '', btn_text).strip()
                            # 移除空格和特殊字符进行匹配
                            clean_text = clean_text.replace(' ', '').replace('&', '')

                            log(f"  Tab{i}: 原始文本='{btn_text}', 清理后='{clean_text}'")

                            if search_text in clean_text or clean_text in search_text:
                                log(f"✓ 找到匹配的Tab: {btn_text}")
                                try:
                                    # 使用JavaScript点击以避免元素被遮挡
                                    driver.execute_script("arguments[0].click();", tab_btn)
                                    log(f"✓ 已点击标签页: {tab_name}")

                                    # 等待aria-selected变为true（优化等待）
                                    time.sleep(0.3)
                                    for attempt in range(8):
                                        is_selected = tab_btn.get_attribute('aria-selected')
                                        if is_selected == 'true':
                                            log(f"✓ 标签页已激活")
                                            break
                                        time.sleep(0.2)

                                    # 减少内容加载等待时间
                                    time.sleep(1)
                                    return True
                                except Exception as e:
                                    log(f"  点击失败: {str(e)}")
                                    continue

                        # 方法2: 如果上面失败，尝试XPath
                        log(f"方法1失败，尝试XPath查找...")
                        tabs = driver.find_elements(By.XPATH, f"//button[@role='tab' and contains(text(), '{tab_name.split()[0]}')]")
                        if tabs:
                            for tab in tabs:
                                if tab.is_displayed():
                                    driver.execute_script("arguments[0].click();", tab)
                                    log(f"✓ 已点击标签页(XPath): {tab_name}")
                                    time.sleep(1)  # 减少等待时间
                                    return True

                        log(f"✗ 未找到标签页: {tab_name}")
                        return False

                    except Exception as e:
                        log(f"✗ 点击标签页异常: {str(e)}")
                        return False

                for tab_config in tabs_config:
                    tab_name = tab_config['name']

                    # 点击标签页
                    if not click_tab(tab_name):
                        log(f"⚠ 跳过标签页: {tab_name}")
                        continue

                    # 提取当前标签页的数据
                    all_rows = driver.find_elements(By.CLASS_NAME, "ant-table-row")
                    visible_rows = [row for row in all_rows if row.get_attribute('aria-hidden') != 'true']
                    log(f"  {tab_name} 标签页找到 {len(visible_rows)} 行数据")

                    for row_idx, row in enumerate(visible_rows):
                        try:
                            cells = row.find_elements(By.TAG_NAME, 'td')
                            if len(cells) == 0:
                                continue

                            cell_texts = [cell.text.strip() for cell in cells]

                            # 根据标签页类型提取数据
                            if tab_name == '仓位':
                                # 持仓数据：代币 方向 杠杆 价值 数量 开仓价格 盈亏(PnL) 资金费 爆仓价格
                                if len(cells) >= 7:  # 至少要有前7列
                                    position = {
                                        '代币': cells[0].text.strip(),
                                        '方向': cells[1].text.strip(),
                                        '杠杆': cells[2].text.strip(),
                                        '价值': cells[3].text.strip(),
                                        '数量': cells[4].text.strip(),
                                        '开仓价格': cells[5].text.strip(),
                                        '盈亏(PnL)': cells[6].text.strip(),
                                        '资金费': cells[7].text.strip() if len(cells) > 7 else '',
                                        '爆仓价格': cells[8].text.strip() if len(cells) > 8 else ''
                                    }
                                    if position['代币'] and position['方向']:
                                        user_details['positions'].append(position)

                            elif tab_name == '交易':
                                # 交易数据：可能包含 哈希、方向、时间、盈亏、代币、价格、数量等
                                if len(cells) >= 4:
                                    # 动态提取所有列
                                    trade = {}
                                    # 常见的列名映射
                                    column_names = ['交易哈希', '方向', '时间', '盈亏', '代币', '价格', '数量', '手续费', '其他']
                                    for i, cell in enumerate(cells):
                                        col_name = column_names[i] if i < len(column_names) else f'列{i+1}'
                                        trade[col_name] = cell.text.strip()

                                    # 至少要有时间或哈希
                                    if trade.get('交易哈希') or trade.get('时间'):
                                        user_details['trades'].append(trade)

                            elif tab_name == '当前委托':
                                # 委托数据：时间、代币、类型、方向、数量、价格、已成交等
                                if len(cells) >= 4:
                                    order = {}
                                    # 常见的列名
                                    column_names = ['时间', '代币', '类型', '方向', '数量', '价格', '已成交', '订单ID']
                                    for i, cell in enumerate(cells):
                                        col_name = column_names[i] if i < len(column_names) else f'列{i+1}'
                                        order[col_name] = cell.text.strip()
                                    user_details['open_orders'].append(order)

                            elif tab_name == '充值 & 提现':
                                # 充提数据：时间、类型、金额、代币、交易哈希等
                                if len(cells) >= 3:
                                    record = {}
                                    # 常见的列名
                                    column_names = ['时间', '类型', '金额', '代币', '交易哈希', '状态']
                                    for i, cell in enumerate(cells):
                                        col_name = column_names[i] if i < len(column_names) else f'列{i+1}'
                                        record[col_name] = cell.text.strip()

                                    # 根据类型分类
                                    record_type = record.get('类型', '')
                                    if '充值' in record_type or '转入' in record_type or 'Deposit' in record_type:
                                        user_details['deposits'].append(record)
                                    elif '提现' in record_type or '转出' in record_type or 'Withdraw' in record_type:
                                        user_details['withdrawals'].append(record)
                                    else:
                                        # 如果类型不明确，都加到充值里
                                        user_details['deposits'].append(record)

                        except Exception as e:
                            log(f"  处理 {tab_name} 第 {row_idx + 1} 行时出错: {str(e)}")
                            continue

                log(f"✓ 提取完成: {len(user_details['positions'])} 个持仓, {len(user_details['trades'])} 条交易, {len(user_details['open_orders'])} 个委托, {len(user_details['deposits'])} 条充值, {len(user_details['withdrawals'])} 条提现")

                # 调试：打印第一个持仓的结构
                if user_details['positions']:
                    log(f"持仓数据示例（第1个）: {user_details['positions'][0]}")

            except Exception as e:
                log(f"✗ 提取Ant Design表格数据失败: {str(e)}")

            # 保存浏览器实例用于实时数据更新（不关闭）
            if driver:
                # 关闭旧的浏览器实例（如果存在）
                if self.user_detail_driver:
                    try:
                        self.user_detail_driver.quit()
                    except:
                        pass

                # 保存新的浏览器实例
                self.user_detail_driver = driver
                self.user_detail_data = user_details
                log("✓ 浏览器会话已保存，用于实时数据更新")

            # 在主线程中显示详情窗口（Tkinter不是线程安全的）
            self.root.after(0, lambda: self.show_user_details_window(user_details))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"爬取详情失败: {str(e)}"))
            # 如果出错，关闭浏览器
            if driver:
                try:
                    driver.quit()
                except:
                    pass
        finally:
            self.root.after(0, lambda: self.update_status("详情爬取完成"))

    def smart_refresh_page_data(self, driver):
        """
        智能刷新页面数据（优化方案）

        原理：
        1. 使用 JavaScript 触发页面的数据重新加载
        2. 而不是 driver.refresh()（会重载所有资源）
        3. 只刷新数据部分
        """

        try:
            # 方案1：查找并点击页面上的刷新按钮
            print("尝试方案1：查找刷新按钮...")
            refresh_button = driver.find_element(By.XPATH,
                """//button[
                    contains(text(), '刷新') or
                    contains(text(), 'Refresh') or
                    contains(@aria-label, '刷新') or
                    contains(@class, 'refresh')
                ]"""
            )
            refresh_button.click()
            print("✓ 点击了刷新按钮")
            time.sleep(2)  # 等待数据更新
            return True

        except:
            pass

        try:
            # 方案2：使用JavaScript查找并触发刷新
            print("尝试方案2：JavaScript触发刷新...")
            result = driver.execute_script("""
                // 查找所有可能的刷新按钮
                const buttons = Array.from(document.querySelectorAll('button, a, div[role="button"]'));

                for (let btn of buttons) {
                    const text = btn.textContent || '';
                    const className = btn.className || '';
                    const ariaLabel = btn.getAttribute('aria-label') || '';

                    if (text.includes('刷新') ||
                        text.includes('Refresh') ||
                        text.includes('更新') ||
                        className.includes('refresh') ||
                        ariaLabel.includes('刷新')) {

                        btn.click();
                        return true;
                    }
                }

                return false;
            """)

            if result:
                print("✓ JavaScript触发了刷新")
                time.sleep(2)
                return True

        except:
            pass

        try:
            # 方案3：执行页面可能的刷新函数
            print("尝试方案3：调用可能的刷新函数...")
            driver.execute_script("""
                // 常见的刷新函数名
                const refreshFunctions = [
                    'refreshData',
                    'updateData',
                    'reload',
                    'refresh',
                    'fetchData',
                    'loadData'
                ];

                for (let funcName of refreshFunctions) {
                    if (typeof window[funcName] === 'function') {
                        window[funcName]();
                        console.log('调用了: ' + funcName);
                        return true;
                    }
                }

                return false;
            """)
            time.sleep(2)
            return True

        except:
            pass

        # 方案4：使用浏览器的location.reload()但保留缓存
        print("尝试方案4：location.reload(保留缓存)...")
        try:
            # 使用软刷新（保留缓存）
            driver.execute_script("location.reload(true);")
            # 等待页面重新加载
            time.sleep(5)
            return True
        except:
            pass

        print("⚠️ 所有方案都失败，回退到driver.refresh()")
        driver.refresh()
        time.sleep(5)
        return True

    def extract_table_data(self, driver):
        """
        提取所有表格数据（持仓、交易、委托、充值提现）
        """
        table_data = {
            'positions': [],
            'trades': [],
            'open_orders': [],
            'deposits': [],
            'withdrawals': []
        }

        try:
            print("开始提取表格数据...")

            # 定义标签页配置
            tabs_config = [
                {'name': '仓位', 'data_key': 'positions'},
                {'name': '交易', 'data_key': 'trades'},
                {'name': '当前委托', 'data_key': 'open_orders'},
                {'name': '充值 & 提现', 'data_key': 'deposits_withdrawals'},
            ]

            def click_tab(tab_name):
                """点击指定名称的标签页"""
                try:
                    print(f"尝试点击标签页: {tab_name}")

                    # 查找所有Tab按钮
                    tab_buttons = driver.find_elements(By.CSS_SELECTOR, "button[role='tab'].MuiTab-root")

                    for tab_btn in tab_buttons:
                        btn_text = tab_btn.text.strip()
                        clean_text = re.sub(r'\([0-9]+\)', '', btn_text).strip()
                        clean_text = clean_text.replace(' ', '').replace('&', '')
                        search_text = tab_name.replace(' & ', '').replace('&', '')

                        if search_text in clean_text or clean_text in search_text:
                            driver.execute_script("arguments[0].click();", tab_btn)
                            print(f"✓ 已点击标签页: {tab_name}")
                            time.sleep(0.5)
                            return True

                    return False

                except Exception as e:
                    print(f"✗ 点击标签页异常: {str(e)}")
                    return False

            for tab_config in tabs_config:
                tab_name = tab_config['name']

                # 点击标签页
                if not click_tab(tab_name):
                    print(f"⚠ 跳过标签页: {tab_name}")
                    continue

                # 提取当前标签页的数据
                all_rows = driver.find_elements(By.CLASS_NAME, "ant-table-row")
                visible_rows = [row for row in all_rows if row.get_attribute('aria-hidden') != 'true']
                print(f"  {tab_name} 标签页找到 {len(visible_rows)} 行数据")

                for row_idx, row in enumerate(visible_rows):
                    try:
                        cells = row.find_elements(By.TAG_NAME, 'td')
                        if len(cells) == 0:
                            continue

                        # 根据标签页类型提取数据
                        if tab_name == '仓位':
                            if len(cells) >= 7:
                                position = {
                                    '代币': cells[0].text.strip(),
                                    '方向': cells[1].text.strip(),
                                    '杠杆': cells[2].text.strip(),
                                    '价值': cells[3].text.strip(),
                                    '数量': cells[4].text.strip(),
                                    '开仓价格': cells[5].text.strip(),
                                    '盈亏(PnL)': cells[6].text.strip(),
                                    '资金费': cells[7].text.strip() if len(cells) > 7 else '',
                                    '爆仓价格': cells[8].text.strip() if len(cells) > 8 else ''
                                }
                                if position['代币'] and position['方向']:
                                    table_data['positions'].append(position)

                        elif tab_name == '交易':
                            if len(cells) >= 4:
                                trade = {}
                                column_names = ['交易哈希', '方向', '时间', '盈亏', '代币', '价格', '数量', '手续费', '其他']
                                for i, cell in enumerate(cells):
                                    col_name = column_names[i] if i < len(column_names) else f'列{i+1}'
                                    trade[col_name] = cell.text.strip()
                                if trade.get('交易哈希') or trade.get('时间'):
                                    table_data['trades'].append(trade)

                        elif tab_name == '当前委托':
                            if len(cells) >= 4:
                                order = {}
                                column_names = ['时间', '代币', '类型', '方向', '数量', '价格', '已成交', '订单ID']
                                for i, cell in enumerate(cells):
                                    col_name = column_names[i] if i < len(column_names) else f'列{i+1}'
                                    order[col_name] = cell.text.strip()
                                table_data['open_orders'].append(order)

                        elif tab_name == '充值 & 提现':
                            if len(cells) >= 3:
                                record = {}
                                column_names = ['时间', '类型', '金额', '代币', '交易哈希', '状态']
                                for i, cell in enumerate(cells):
                                    col_name = column_names[i] if i < len(column_names) else f'列{i+1}'
                                    record[col_name] = cell.text.strip()

                                record_type = record.get('类型', '')
                                if '充值' in record_type or '转入' in record_type or 'Deposit' in record_type:
                                    table_data['deposits'].append(record)
                                elif '提现' in record_type or '转出' in record_type or 'Withdraw' in record_type:
                                    table_data['withdrawals'].append(record)
                                else:
                                    table_data['deposits'].append(record)

                    except Exception as e:
                        print(f"  处理 {tab_name} 第 {row_idx + 1} 行时出错: {str(e)}")
                        continue

            print(f"✓ 表格数据提取完成: {len(table_data['positions'])} 个持仓, {len(table_data['trades'])} 条交易, {len(table_data['open_orders'])} 个委托, {len(table_data['deposits'])} 条充值, {len(table_data['withdrawals'])} 条提现")

        except Exception as e:
            print(f"✗ 提取表格数据失败: {str(e)}")

        return table_data

    def check_page_update_mechanism(self, driver):
        """
        检查页面的更新机制
        """

        result = driver.execute_script("""
            return {
                // 检查WebSocket
                hasWebSocket: typeof WebSocket !== 'undefined' && window.WebSocket !== undefined,

                // 检查是否有定时器
                hasInterval: window.setInterval !== undefined,

                // 检查框架
                hasReact: window.React !== undefined || window.__REACT_DEVTOOLS_GLOBAL_HOOK__ !== undefined,
                hasVue: window.Vue !== undefined,
                hasAngular: window.angular !== undefined,

                // 检查是否有刷新按钮
                hasRefreshButton: document.querySelector('[class*="refresh"], [aria-label*="刷新"]') !== null,

                // 检查URL
                currentUrl: window.location.href
            };
        """)

        print("页面更新机制分析:")
        print(f"  WebSocket支持: {result.get('hasWebSocket')}")
        print(f"  定时器支持: {result.get('hasInterval')}")
        print(f"  React框架: {result.get('hasReact')}")
        print(f"  Vue框架: {result.get('hasVue')}")
        print(f"  刷新按钮: {result.get('hasRefreshButton')}")

        return result

    def refresh_user_details_data_from_page(self):
        """
        智能刷新用户详情数据（真正的实时更新）

        步骤：
        1. 检查页面更新机制
        2. 使用最优方案刷新页面数据
        3. 等待数据更新
        4. 提取新数据
        """
        if not self.user_detail_driver:
            print("⚠️ 浏览器会话不存在，无法刷新数据")
            return None

        try:
            print(f"===== 智能刷新用户详情数据 =====")
            print(f"用户地址: {self.user_detail_data.get('address', 'N/A')}")

            # 1. 检查页面机制
            page_info = self.check_page_update_mechanism(self.user_detail_driver)

            # 2. 刷新页面数据（触发页面的更新机制）
            success = self.smart_refresh_page_data(self.user_detail_driver)

            if not success:
                print("❌ 刷新失败")
                return None

            # 3. 等待数据更新完成
            try:
                WebDriverWait(self.user_detail_driver, 10).until(
                    lambda d: len(d.find_elements(By.CLASS_NAME, "Number")) > 0
                )
                print("✓ 数据已更新")
            except:
                print("⚠️ 等待超时，但继续提取数据")

            # 4. 使用JavaScript从页面提取最新数据
            js_extract_data = """
            var data = {};
            var labels = ['总盈亏', '24小时盈亏', '48小时盈亏', '7天盈亏', '30天盈亏', '永续合约仓位价值'];

            labels.forEach(function(label) {
                var elements = Array.from(document.querySelectorAll('*'));
                for (var i = 0; i < elements.length; i++) {
                    var elem = elements[i];

                    // 跳过header和导航栏中的元素
                    var parentHeader = elem.closest('header, nav, .cg-header, .cg-top-data');
                    if (parentHeader) {
                        continue;
                    }

                    // 检查元素文本是否包含标签
                    if (elem.textContent.trim() === label ||
                        (elem.innerText && elem.innerText.trim() === label)) {

                        // 查找父元素中的Number类
                        var parent = elem.parentElement;
                        if (parent) {
                            var numberElems = parent.querySelectorAll('.Number, [class*="Number"], [class*="rise"], [class*="fall"]');
                            for (var j = 0; j < numberElems.length; j++) {
                                var numElem = numberElems[j];
                                var numText = numElem.textContent.trim();
                                // 确保是金额格式
                                if (numText && (numText.includes('$') || numText.includes('万') || numText.includes('亿'))) {
                                    data[label] = numText;
                                    break;
                                }
                            }
                        }
                        break;
                    }
                }
            });

            return data;
            """

            # 执行JavaScript获取数据
            extracted_data = self.user_detail_driver.execute_script(js_extract_data)
            print(f"✓ 提取到数据: {extracted_data}")

            # 5. 更新盈亏数据
            if extracted_data:
                self.user_detail_data['total_pnl'] = extracted_data.get('总盈亏', 'N/A')
                self.user_detail_data['pnl_24h'] = extracted_data.get('24小时盈亏', 'N/A')
                self.user_detail_data['pnl_48h'] = extracted_data.get('48小时盈亏', 'N/A')
                self.user_detail_data['pnl_7d'] = extracted_data.get('7天盈亏', 'N/A')
                self.user_detail_data['pnl_30d'] = extracted_data.get('30天盈亏', 'N/A')
                self.user_detail_data['position_value'] = extracted_data.get('永续合约仓位价值', 'N/A')

                print(f"✓ 盈亏数据已更新")
            else:
                print("⚠️ 未提取到盈亏数据")

            # 6. 提取并更新表格数据（持仓、交易、委托、充值提现）
            table_data = self.extract_table_data(self.user_detail_driver)

            # 更新表格数据到 user_detail_data
            self.user_detail_data['positions'] = table_data['positions']
            self.user_detail_data['trades'] = table_data['trades']
            self.user_detail_data['open_orders'] = table_data['open_orders']
            self.user_detail_data['deposits'] = table_data['deposits']
            self.user_detail_data['withdrawals'] = table_data['withdrawals']

            # 7. 添加更新时间
            self.user_detail_data['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            print(f"✓ 所有数据已更新，最后更新时间: {self.user_detail_data['last_update']}")
            return self.user_detail_data

        except Exception as e:
            print(f"❌ 刷新数据失败: {str(e)}")
            return None

    def start_user_detail_auto_refresh(self):
        """启动用户详情自动刷新"""
        if not self.user_detail_auto_refresh.get():
            return

        if not self.user_detail_driver:
            print("浏览器会话已关闭，停止自动刷新")
            self.user_detail_auto_refresh.set(False)
            return

        # 刷新数据
        updated_data = self.refresh_user_details_data_from_page()

        # 如果窗口还在，更新UI
        if updated_data and self.user_detail_window and self.user_detail_window.winfo_exists():
            self.root.after(0, lambda: self.update_user_details_ui(updated_data))

        # 继续下一次刷新
        if self.user_detail_auto_refresh.get():
            self.root.after(self.user_detail_refresh_interval, self.start_user_detail_auto_refresh)

    def update_user_details_ui(self, details):
        """更新用户详情窗口的UI显示（局部更新，不重建窗口）"""
        if not self.user_detail_window or not self.user_detail_window.winfo_exists():
            return

        print(f"✓ 开始局部更新UI，数据时间: {details.get('last_update', 'N/A')}")

        try:
            # 1. 更新盈亏数据标签
            pnl_mapping = {
                'total_pnl': details.get('total_pnl', 'N/A'),
                'pnl_24h': details.get('pnl_24h', 'N/A'),
                'pnl_48h': details.get('pnl_48h', 'N/A'),
                'pnl_7d': details.get('pnl_7d', 'N/A'),
                'pnl_30d': details.get('pnl_30d', 'N/A'),
                'position_value': details.get('position_value', 'N/A'),
            }

            for key, value in pnl_mapping.items():
                if key in self.detail_ui_refs['pnl_labels']:
                    label = self.detail_ui_refs['pnl_labels'][key]
                    label.config(text=value)
                    # 更新颜色
                    value_color = '#27ae60' if value != 'N/A' and ('+' in value or (value.startswith('$') and '-' not in value)) else '#e74c3c' if '-' in value else '#34495e'
                    label.config(fg=value_color)

            # 2. 更新最后更新时间
            if self.detail_ui_refs['update_time_label']:
                self.detail_ui_refs['update_time_label'].config(
                    text=f"最后更新: {details.get('last_update', 'N/A')}"
                )

            # 3. 更新持仓表格
            if self.detail_ui_refs['position_tree']:
                tree = self.detail_ui_refs['position_tree']
                # 清空现有数据
                for item in tree.get_children():
                    tree.delete(item)
                # 插入新数据
                for pos in details.get('positions', []):
                    tree.insert('', tk.END, values=tuple(pos.values()))

            # 更新持仓框架标题
            if self.detail_ui_refs['position_frame']:
                pos_count = len(details.get('positions', []))
                self.detail_ui_refs['position_frame'].config(text=f"📦 当前持仓 ({pos_count} 个)")

            # 4. 更新委托表格
            if self.detail_ui_refs['order_tree']:
                tree = self.detail_ui_refs['order_tree']
                # 清空现有数据
                for item in tree.get_children():
                    tree.delete(item)
                # 插入新数据
                for order in details.get('open_orders', []):
                    tree.insert('', tk.END, values=tuple(order.values()))

            # 更新委托框架标题
            if self.detail_ui_refs['order_frame']:
                order_count = len(details.get('open_orders', []))
                self.detail_ui_refs['order_frame'].config(text=f"📝 当前委托 ({order_count} 条)")

            # 5. 更新交易历史表格
            if self.detail_ui_refs['trade_tree']:
                tree = self.detail_ui_refs['trade_tree']
                # 清空现有数据
                for item in tree.get_children():
                    tree.delete(item)
                # 插入新数据（限制最近100条）
                for trade in details.get('trades', [])[:100]:
                    tree.insert('', tk.END, values=tuple(trade.values()))

            # 更新交易框架标题
            if self.detail_ui_refs['trade_frame']:
                trade_count = len(details.get('trades', []))
                self.detail_ui_refs['trade_frame'].config(text=f"🔄 交易历史 ({trade_count} 条)")

            # 6. 更新充值&提现表格
            if self.detail_ui_refs['transfer_tree']:
                tree = self.detail_ui_refs['transfer_tree']
                # 清空现有数据
                for item in tree.get_children():
                    tree.delete(item)

                # 合并充值和提现记录
                all_transfers = []
                for deposit in details.get('deposits', []):
                    transfer = deposit.copy()
                    if '类型' not in transfer or not transfer['类型']:
                        transfer['类型'] = '充值'
                    all_transfers.append(transfer)
                for withdrawal in details.get('withdrawals', []):
                    transfer = withdrawal.copy()
                    if '类型' not in transfer or not transfer['类型']:
                        transfer['类型'] = '提现'
                    all_transfers.append(transfer)

                # 插入新数据
                for transfer in all_transfers:
                    tree.insert('', tk.END, values=tuple(transfer.values()))

            # 更新充提框架标题
            if self.detail_ui_refs['transfer_frame']:
                total_count = len(details.get('deposits', [])) + len(details.get('withdrawals', []))
                self.detail_ui_refs['transfer_frame'].config(text=f"💰 充值 & 提现 ({total_count} 条)")

            print("✓ UI局部更新完成，无闪烁")

        except Exception as e:
            print(f"❌ 局部更新UI失败: {str(e)}")
            # 如果局部更新失败，回退到重建窗口
            print("  回退到重建窗口...")
            self.rebuild_detail_window(details)

    def rebuild_detail_window(self, updated_details):
        """重建详情窗口以显示更新的数据"""
        if self.user_detail_window and self.user_detail_window.winfo_exists():
            # 关闭旧窗口
            self.user_detail_window.destroy()

        # 显示新窗口
        self.show_user_details_window(updated_details)

    def show_user_details_window(self, details):
        """显示用户详情窗口（包含可视化图表和实时数据更新）"""
        # 保存窗口引用
        self.user_detail_window = tk.Toplevel(self.root)
        self.user_detail_window.title(f"{self.lang.get_text('detail_window_title')} - {details['address']}")
        self.user_detail_window.geometry("1200x900")  # 增加窗口大小以容纳更多内容
        self.user_detail_window.configure(bg=COLORS['bg_primary'])

        # 保存当前用户地址以便语言切换时更新窗口标题
        self.user_detail_address = details['address']

        # 窗口关闭时清理
        def on_window_close():
            self.user_detail_auto_refresh.set(False)  # 停止自动刷新
            if self.user_detail_driver:
                try:
                    self.user_detail_driver.quit()
                    print("✓ 浏览器已关闭")
                except:
                    pass
                self.user_detail_driver = None
            self.user_detail_window.destroy()

        self.user_detail_window.protocol("WM_DELETE_WINDOW", on_window_close)

        # 创建滚动区域
        canvas = tk.Canvas(self.user_detail_window, bg=COLORS['bg_primary'], highlightthickness=0)
        scrollbar = tk.Scrollbar(self.user_detail_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS['bg_primary'])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # 显示用户地址
        addr_frame = tk.Frame(scrollable_frame, bg=COLORS['bg_secondary'], pady=10)
        addr_frame.pack(fill=tk.X, padx=10, pady=5)

        self.detail_address_label = tk.Label(
            addr_frame,
            text=f"{self.lang.get_text('detail_user_address')} {details.get('full_address') or details['address']}",
            font=FONTS['heading'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary']
        )
        self.detail_address_label.pack()
        self.detail_ui_refs['address_label'] = self.detail_address_label

        # ==================== 实时数据控制栏 ====================
        control_frame = tk.Frame(scrollable_frame, bg=COLORS['bg_tertiary'], pady=10)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        # 提示信息
        self.detail_session_tip = tk.Label(
            control_frame,
            text=self.lang.get_text('detail_session_tip'),
            font=FONTS['small'],
            bg=COLORS['bg_tertiary'],
            fg=COLORS['info']
        )
        self.detail_session_tip.pack(side=tk.LEFT, padx=10)
        self.detail_ui_refs['session_tip'] = self.detail_session_tip

        # 刷新按钮
        def manual_refresh():
            if not self.user_detail_driver:
                messagebox.showwarning(
                    self.lang.get_text('msg_refresh_title'),
                    self.lang.get_text('msg_browser_closed')
                )
                return

            # 在新线程中刷新数据
            def refresh_thread():
                updated_data = self.refresh_user_details_data_from_page()
                if updated_data:
                    # 更新窗口显示（需要重建窗口）
                    self.root.after(0, lambda: self.rebuild_detail_window(updated_data))
                    self.root.after(0, lambda: messagebox.showinfo(
                        self.lang.get_text('msg_update_title'),
                        self.lang.get_text('msg_update_success')
                    ))
                else:
                    self.root.after(0, lambda: messagebox.showerror(
                        self.lang.get_text('msg_update_failed_title'),
                        self.lang.get_text('msg_update_failed')
                    ))

            thread = threading.Thread(target=refresh_thread)
            thread.daemon = True
            thread.start()

        self.detail_refresh_btn = tk.Button(
            control_frame,
            text=f"🔄 {self.lang.get_text('detail_manual_refresh')}",
            command=manual_refresh,
            bg=COLORS['accent'],
            fg=COLORS['text_primary'],
            font=FONTS['body_bold'],
            activebackground=COLORS['accent_hover'],
            relief=tk.FLAT,
            bd=0,
            padx=15,
            pady=8,
            cursor='hand2'
        )
        self.detail_refresh_btn.pack(side=tk.LEFT, padx=5)
        self.detail_ui_refs['refresh_btn'] = self.detail_refresh_btn

        # 自动刷新开关
        self.detail_auto_refresh_cb = tk.Checkbutton(
            control_frame,
            text=self.lang.get_text('detail_auto_refresh'),
            variable=self.user_detail_auto_refresh,
            command=lambda: self.start_user_detail_auto_refresh() if self.user_detail_auto_refresh.get() else None,
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary'],
            font=FONTS['body'],
            selectcolor=COLORS['bg_secondary'],
            activebackground=COLORS['bg_hover'],
            activeforeground=COLORS['text_primary']
        )
        self.detail_auto_refresh_cb.pack(side=tk.LEFT, padx=5)
        self.detail_ui_refs['auto_refresh_cb'] = self.detail_auto_refresh_cb

        # 收藏按钮
        user_address = details.get('full_address') or details['address']
        is_favorited = self.favorites.is_favorite(user_address)

        def toggle_favorite():
            addr = details.get('full_address') or details['address']
            if self.favorites.is_favorite(addr):
                # 移除收藏
                if self.favorites.remove_favorite(addr):
                    self.add_message(self.lang.get_text('msg_favorite_removed'), 'success')
                    favorite_btn.config(text=f"⭐ {self.lang.get_text('btn_add_favorite')}")
                    # 刷新收藏列表显示
                    if hasattr(self, 'favorites_tree'):
                        self.refresh_favorites_display()
            else:
                # 添加收藏
                if self.favorites.add_favorite(
                    address=addr,
                    note="",
                    tags=[],
                    metadata={
                        'pnl_24h': details.get('pnl', {}).get('pnl_24h', 0),
                        'total_pnl': details.get('pnl', {}).get('total_pnl', 0)
                    }
                ):
                    self.add_message(self.lang.get_text('msg_favorite_added'), 'success')
                    favorite_btn.config(text=f"❌ {self.lang.get_text('btn_remove_favorite')}")
                    # 刷新收藏列表显示
                    if hasattr(self, 'favorites_tree'):
                        self.refresh_favorites_display()

        favorite_btn_text = (
            f"❌ {self.lang.get_text('btn_remove_favorite')}" if is_favorited
            else f"⭐ {self.lang.get_text('btn_add_favorite')}"
        )

        favorite_btn = tk.Button(
            control_frame,
            text=favorite_btn_text,
            command=toggle_favorite,
            bg=COLORS['warning'] if is_favorited else COLORS['accent'],
            fg=COLORS['text_primary'],
            font=FONTS['body_bold'],
            relief=tk.FLAT,
            bd=0,
            padx=15,
            pady=8,
            cursor='hand2'
        )
        favorite_btn.pack(side=tk.LEFT, padx=5)

        # 最后更新时间
        last_update_text = details.get('last_update', self.lang.get_text('detail_first_load'))
        self.update_time_label = tk.Label(
            control_frame,
            text=f"{self.lang.get_text('detail_last_update')} {last_update_text}",
            font=FONTS['small'],
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_muted']
        )
        self.update_time_label.pack(side=tk.LEFT, padx=10)

        # 保存更新时间标签引用和最后更新时间文本
        self.detail_ui_refs['update_time_label'] = self.update_time_label
        self.detail_last_update_text = last_update_text

        # 如果有错误，显示错误信息并提前返回
        if details.get('error'):
            error_frame = tk.LabelFrame(
                scrollable_frame,
                text=self.lang.get_text('detail_error_title'),
                font=FONTS['heading'],
                padx=10,
                pady=10,
                bg=COLORS['loss_bg'],
                fg=COLORS['loss']
            )
            error_frame.pack(fill=tk.X, padx=10, pady=5)
            self.detail_ui_refs['error_frame'] = error_frame

            tk.Label(
                error_frame,
                text=details['error'],
                font=FONTS['body_bold'],
                fg=COLORS['loss'],
                bg=COLORS['loss_bg']
            ).pack(pady=10)

            tk.Label(
                error_frame,
                text="该地址在CoinGlass上可能：\n• 不存在或已被删除\n• 尚未被索引\n• 长时间未活跃",
                font=FONTS['body'],
                justify=tk.LEFT,
                bg=COLORS['loss_bg'],
                fg=COLORS['text_secondary']
            ).pack(pady=5)

        # 显示调试日志（如果存在）
        if details.get('debug_log'):
            debug_frame = tk.LabelFrame(
                scrollable_frame,
                text=self.lang.get_text('detail_debug_log'),
                font=FONTS['heading'],
                padx=10,
                pady=10,
                bg=COLORS['bg_secondary'],
                fg=COLORS['text_primary']
            )
            debug_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            self.detail_ui_refs['debug_frame'] = debug_frame

            debug_text = scrolledtext.ScrolledText(
                debug_frame,
                wrap=tk.WORD,
                font=FONTS['body'],
                bg=COLORS['bg_tertiary'],
                fg=COLORS['profit'],
                insertbackground=COLORS['text_primary'],
                height=10
            )
            debug_text.pack(fill=tk.BOTH, expand=True)

            for log_msg in details['debug_log']:
                debug_text.insert(tk.END, log_msg + '\n')

            debug_text.config(state=tk.DISABLED)  # 只读

        # 显示盈亏数据（美化版）
        self.detail_pnl_frame = tk.LabelFrame(
            scrollable_frame,
            text=self.lang.get_text('detail_pnl_stats'),
            font=FONTS['heading'],
            padx=15,
            pady=15,
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary']
        )
        self.detail_pnl_frame.pack(fill=tk.X, padx=10, pady=10)
        self.detail_ui_refs['pnl_frame'] = self.detail_pnl_frame

        # 使用翻译键定义 PnL 数据标签
        pnl_data = [
            ('detail_total_pnl', 'total_pnl', details.get('total_pnl', 'N/A')),
            ('detail_pnl_24h', 'pnl_24h', details.get('pnl_24h', 'N/A')),
            ('detail_pnl_48h', 'pnl_48h', details.get('pnl_48h', 'N/A')),
            ('detail_pnl_7d', 'pnl_7d', details.get('pnl_7d', 'N/A')),
            ('detail_pnl_30d', 'pnl_30d', details.get('pnl_30d', 'N/A')),
            ('detail_position_value', 'position_value', details.get('position_value', 'N/A')),
        ]

        # 清空之前的引用
        self.detail_ui_refs['pnl_labels'] = {}
        self.detail_ui_refs['pnl_text_labels'] = {}  # 存储文本标签引用

        # 创建网格布局（2列）
        for idx, (label_key, data_key, value) in enumerate(pnl_data):
            row_idx = idx // 2
            col_idx = idx % 2

            # 创建单元格框架
            cell_frame = tk.Frame(
                self.detail_pnl_frame,
                bg=COLORS['bg_tertiary'],
                highlightbackground=COLORS['border'],
                highlightthickness=1,
                bd=0
            )
            cell_frame.grid(row=row_idx, column=col_idx, padx=5, pady=5, sticky='ew')

            # 标签（使用翻译）
            text_label = tk.Label(
                cell_frame,
                text=self.lang.get_text(label_key),
                width=15,
                anchor='w',
                font=FONTS['body'],
                bg=COLORS['bg_tertiary'],
                fg=COLORS['text_secondary']
            )
            text_label.pack(side=tk.LEFT, padx=10, pady=8)

            # 保存文本标签引用用于语言切换
            self.detail_ui_refs['pnl_text_labels'][data_key] = (text_label, label_key)

            # 数值（根据正负显示颜色）
            if value != 'N/A' and ('+' in value or (value.startswith('$') and '-' not in value)):
                value_color = COLORS['profit']
            elif '-' in value:
                value_color = COLORS['loss']
            else:
                value_color = COLORS['text_primary']

            value_label = tk.Label(
                cell_frame,
                text=value,
                font=FONTS['number_large'],
                bg=COLORS['bg_tertiary'],
                fg=value_color
            )
            value_label.pack(side=tk.RIGHT, padx=10, pady=8)

            # 保存标签引用
            self.detail_ui_refs['pnl_labels'][data_key] = value_label

        # 配置网格权重
        self.detail_pnl_frame.grid_columnconfigure(0, weight=1)
        self.detail_pnl_frame.grid_columnconfigure(1, weight=1)

        # 创建可视化图表（ECharts风格）
        if any([details.get('total_pnl'), details.get('pnl_24h'), details.get('pnl_7d'), details.get('pnl_30d')]):
            self.detail_chart_frame = tk.LabelFrame(
                scrollable_frame,
                text=self.lang.get_text('detail_pnl_chart'),
                font=FONTS['heading'],
                bg=COLORS['bg_secondary'],
                fg=COLORS['text_primary'],
                padx=5,
                pady=5
            )
            self.detail_chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            self.detail_ui_refs['chart_frame'] = self.detail_chart_frame

            # 准备数据（使用翻译）
            periods = []
            values = []

            pnl_mapping = [
                ('detail_period_24h', details.get('pnl_24h')),
                ('detail_period_48h', details.get('pnl_48h')),
                ('detail_period_7d', details.get('pnl_7d')),
                ('detail_period_30d', details.get('pnl_30d')),
            ]

            for period_key, value in pnl_mapping:
                if value and value != 'N/A':
                    periods.append(self.lang.get_text(period_key))
                    # 解析数值
                    num_value = self.parse_amount(value)
                    values.append(num_value / 10000)  # 转换为万

            if periods and values:
                # 关闭matplotlib的交互模式，避免线程问题
                plt.ioff()

                # 创建matplotlib图表（ECharts风格）
                fig, ax = plt.subplots(figsize=(10, 4.5), facecolor='#ffffff')

                # 设置中文字体
                plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
                plt.rcParams['axes.unicode_minus'] = False
                plt.rcParams['toolbar'] = 'None'  # 禁用工具栏

                # 创建渐变色柱状图
                bars = []
                for i, (period, value) in enumerate(zip(periods, values)):
                    if value >= 0:
                        # 正值：绿色渐变
                        color = '#52c41a'
                        edge_color = '#389e0d'
                    else:
                        # 负值：红色渐变
                        color = '#ff4d4f'
                        edge_color = '#cf1322'

                    bar = ax.bar(i, value, width=0.6, color=color,
                                edgecolor=edge_color, linewidth=1.5,
                                alpha=0.85, zorder=3)
                    bars.append(bar)

                # 设置X轴
                ax.set_xticks(range(len(periods)))
                ax.set_xticklabels(periods, fontsize=11, color='#666')

                # 设置Y轴
                ax.set_ylabel(self.lang.get_text('detail_pnl_unit'), fontsize=11, color='#666', labelpad=10)
                ax.tick_params(axis='y', labelsize=10, colors='#666')

                # 添加零线
                ax.axhline(y=0, color='#bfbfbf', linestyle='-', linewidth=1.5, zorder=2)

                # 网格线样式（ECharts风格）
                ax.grid(axis='y', alpha=0.2, linestyle='--', linewidth=0.8, color='#d9d9d9', zorder=1)
                ax.set_axisbelow(True)

                # 设置背景色
                ax.set_facecolor('#fafafa')

                # 移除顶部和右侧边框
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['left'].set_color('#d9d9d9')
                ax.spines['bottom'].set_color('#d9d9d9')

                # 在柱子顶部显示数值
                for i, (bar_container, value) in enumerate(zip(bars, values)):
                    height = bar_container[0].get_height()
                    # 判断标签位置（正值在上方，负值在下方）
                    if height >= 0:
                        va = 'bottom'
                        y_offset = height + (max(values) - min(values)) * 0.02
                    else:
                        va = 'top'
                        y_offset = height - (max(values) - min(values)) * 0.02

                    # 格式化显示（万为单位）
                    if abs(value) >= 100:
                        label = f'{value:.0f}万' if self.lang.current_language == 'zh' else f'${value:.0f}0k'
                    elif abs(value) >= 10:
                        label = f'{value:.1f}万' if self.lang.current_language == 'zh' else f'${value:.1f}0k'
                    else:
                        label = f'{value:.2f}万' if self.lang.current_language == 'zh' else f'${value:.2f}0k'

                    ax.text(i, y_offset, label,
                           ha='center', va=va, fontsize=10,
                           color='#52c41a' if value >= 0 else '#ff4d4f',
                           fontweight='bold')

                # 标题
                ax.set_title(self.lang.get_text('detail_chart_title'), fontsize=13, color='#2c3e50',
                           fontweight='bold', pad=15)

                # 调整布局
                plt.tight_layout()

                # 嵌入到tkinter窗口（不添加工具栏，避免线程问题）
                chart_canvas = FigureCanvasTkAgg(fig, master=self.detail_chart_frame)
                chart_canvas.draw()
                chart_widget = chart_canvas.get_tk_widget()
                chart_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

                # 禁用所有鼠标事件，防止线程冲突
                chart_widget.configure(cursor="")

        # 显示持仓信息（包括空数据）
        pos_count = len(details.get('positions', []))
        self.detail_position_frame = tk.LabelFrame(
            scrollable_frame,
            text=f"{self.lang.get_text('detail_positions')} ({pos_count})",
            font=FONTS['heading'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary'],
            padx=5,
            pady=5
        )
        self.detail_position_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 保存持仓框架引用和持仓数量（用于更新标题）
        self.detail_ui_refs['position_frame'] = self.detail_position_frame
        self.detail_position_count = pos_count

        if pos_count > 0:
            first_pos = details['positions'][0]
            columns = tuple(first_pos.keys())
            tree = ttk.Treeview(self.detail_position_frame, columns=columns, show='headings', height=10)

            # 保存持仓表格引用
            self.detail_ui_refs['position_tree'] = tree
            self.detail_ui_refs['position_columns'] = columns

            # 为不同列设置合适的宽度（使用翻译键映射）
            column_width_mapping = {
                '代币': ('detail_col_token', 80),
                '方向': ('detail_col_direction', 60),
                '杠杆': ('detail_col_leverage', 60),
                '价值': ('detail_col_value', 120),
                '数量': ('detail_col_size', 100),
                '开仓价格': ('detail_col_entry_price', 100),
                '盈亏(PnL)': ('detail_col_pnl', 120),
                '资金费': ('detail_col_funding', 100),
                '爆仓价格': ('detail_col_liq_price', 100)
            }

            for col in columns:
                tree.heading(col, text=col)
                # 查找对应的宽度，默认100
                width = 100
                for cn_col, (key, w) in column_width_mapping.items():
                    if col == cn_col:
                        width = w
                        break
                tree.column(col, width=width, anchor='center')

            for pos in details['positions']:
                tree.insert('', tk.END, values=tuple(pos.values()))

            # 添加滚动条
            pos_scrollbar = ttk.Scrollbar(self.detail_position_frame, orient=tk.HORIZONTAL, command=tree.xview)
            tree.configure(xscrollcommand=pos_scrollbar.set)
            tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
            pos_scrollbar.pack(side=tk.BOTTOM, fill=tk.X, padx=5)
        else:
            tk.Label(
                self.detail_position_frame,
                text=self.lang.get_text('detail_no_positions'),
                font=FONTS['body'],
                fg=COLORS['text_muted'],
                bg=COLORS['bg_secondary']
            ).pack(pady=20)

        # 显示当前委托（包括空数据）
        order_count = len(details.get('open_orders', []))
        self.detail_order_frame = tk.LabelFrame(
            scrollable_frame,
            text=f"{self.lang.get_text('detail_orders')} ({order_count})",
            font=FONTS['heading'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary'],
            padx=5,
            pady=5
        )
        self.detail_order_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 保存委托框架引用和数量
        self.detail_ui_refs['order_frame'] = self.detail_order_frame
        self.detail_order_count = order_count

        if order_count > 0:
            first_order = details['open_orders'][0]
            columns = tuple(first_order.keys())
            tree = ttk.Treeview(self.detail_order_frame, columns=columns, show='headings', height=8)

            # 保存委托表格引用
            self.detail_ui_refs['order_tree'] = tree
            self.detail_ui_refs['order_columns'] = columns

            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=120, anchor='center')

            for order in details['open_orders']:
                tree.insert('', tk.END, values=tuple(order.values()))

            tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        else:
            tk.Label(
                self.detail_order_frame,
                text=self.lang.get_text('detail_no_orders'),
                font=FONTS['body'],
                fg=COLORS['text_muted'],
                bg=COLORS['bg_secondary']
            ).pack(pady=20)

        # 显示交易历史（包括空数据）
        trade_count = len(details.get('trades', []))
        self.detail_trade_frame = tk.LabelFrame(
            scrollable_frame,
            text=f"{self.lang.get_text('detail_trades')} ({trade_count})",
            font=FONTS['heading'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary'],
            padx=5,
            pady=5
        )
        self.detail_trade_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 保存交易框架引用和数量
        self.detail_ui_refs['trade_frame'] = self.detail_trade_frame
        self.detail_trade_count = trade_count

        if trade_count > 0:
            first_trade = details['trades'][0]
            columns = tuple(first_trade.keys())
            tree = ttk.Treeview(self.detail_trade_frame, columns=columns, show='headings', height=10)

            # 保存交易表格引用
            self.detail_ui_refs['trade_tree'] = tree
            self.detail_ui_refs['trade_columns'] = columns

            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=120, anchor='center')

            # 限制显示最近100条交易
            for trade in details['trades'][:100]:
                tree.insert('', tk.END, values=tuple(trade.values()))

            # 添加滚动条
            trade_scrollbar = ttk.Scrollbar(self.detail_trade_frame, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=trade_scrollbar.set)
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
            trade_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        else:
            tk.Label(
                self.detail_trade_frame,
                text=self.lang.get_text('detail_no_trades'),
                font=FONTS['body'],
                fg=COLORS['text_muted'],
                bg=COLORS['bg_secondary']
            ).pack(pady=20)

        # 显示充值 & 提现记录（合并显示）
        deposit_count = len(details.get('deposits', []))
        withdrawal_count = len(details.get('withdrawals', []))
        total_transfer_count = deposit_count + withdrawal_count

        self.detail_transfer_frame = tk.LabelFrame(
            scrollable_frame,
            text=f"{self.lang.get_text('detail_transfers')} ({total_transfer_count})",
            font=FONTS['heading'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary'],
            padx=5,
            pady=5
        )
        self.detail_transfer_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 保存充提框架引用和数量
        self.detail_ui_refs['transfer_frame'] = self.detail_transfer_frame
        self.detail_deposit_count = deposit_count
        self.detail_withdrawal_count = withdrawal_count

        if total_transfer_count > 0:
            # 合并充值和提现记录
            all_transfers = []

            # 添加充值记录（标记类型）
            for deposit in details.get('deposits', []):
                transfer = deposit.copy()
                # 确保有类型字段
                if '类型' not in transfer or not transfer['类型']:
                    transfer['类型'] = self.lang.get_text('detail_deposit')
                all_transfers.append(transfer)

            # 添加提现记录
            for withdrawal in details.get('withdrawals', []):
                transfer = withdrawal.copy()
                # 确保有类型字段
                if '类型' not in transfer or not transfer['类型']:
                    transfer['类型'] = self.lang.get_text('detail_withdrawal')
                all_transfers.append(transfer)

            # 创建表格
            if all_transfers:
                first_transfer = all_transfers[0]
                columns = tuple(first_transfer.keys())
                tree = ttk.Treeview(self.detail_transfer_frame, columns=columns, show='headings', height=8)

                # 保存充提表格引用
                self.detail_ui_refs['transfer_tree'] = tree
                self.detail_ui_refs['transfer_columns'] = columns

                for col in columns:
                    tree.heading(col, text=col)
                    tree.column(col, width=150, anchor='center')

                # 插入所有记录
                for transfer in all_transfers:
                    tree.insert('', tk.END, values=tuple(transfer.values()))

                # 添加滚动条
                transfer_scrollbar = ttk.Scrollbar(self.detail_transfer_frame, orient=tk.VERTICAL, command=tree.yview)
                tree.configure(yscrollcommand=transfer_scrollbar.set)
                tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
                transfer_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

                # 添加统计信息
                self.detail_transfer_stats_label = tk.Label(
                    self.detail_transfer_frame,
                    text=self.lang.get_text('detail_transfer_stats', deposit=deposit_count, withdrawal=withdrawal_count),
                    font=FONTS['small'],
                    fg=COLORS['text_secondary'],
                    bg=COLORS['bg_secondary']
                )
                self.detail_transfer_stats_label.pack(side=tk.BOTTOM, pady=5)
                self.detail_ui_refs['transfer_stats_label'] = self.detail_transfer_stats_label
        else:
            tk.Label(
                self.detail_transfer_frame,
                text=self.lang.get_text('detail_no_transfers'),
                font=FONTS['body'],
                fg=COLORS['text_muted'],
                bg=COLORS['bg_secondary']
            ).pack(pady=20)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def export_data(self):
        """导出数据到文件"""
        if not self.data:
            messagebox.showwarning("提示", "暂无数据可导出")
            return

        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"hyperliquid_data_{timestamp}.txt"

            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.text_area.get(1.0, tk.END))

            # 同时保存 JSON 格式
            json_filename = f"hyperliquid_data_{timestamp}.json"
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)

            messagebox.showinfo("成功", f"数据已导出到:\n{filename}\n{json_filename}")

        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")

    # ==================== OKX 相关方法 ====================
    def create_okx_table_tab(self, notebook):
        """创建 OKX 数据表格标签页"""
        okx_table_frame = tk.Frame(notebook, bg='#0a0e27')
        notebook.add(okx_table_frame, text="OKX 数据表格")

        # 顶部控制栏
        control_bar = tk.Frame(okx_table_frame, bg='#1a1f3a', height=60)
        control_bar.pack(fill=tk.X, padx=5, pady=5)
        control_bar.pack_propagate(False)

        # 标题
        title = tk.Label(
            control_bar,
            text="OKX 永续合约实时行情",
            font=('Arial', 14, 'bold'),
            bg='#1a1f3a',
            fg='#00d4ff'
        )
        title.pack(side=tk.LEFT, padx=15)

        # 刷新按钮
        self.okx_refresh_btn = tk.Button(
            control_bar,
            text="🔄 刷新",
            command=self.refresh_okx_data,
            bg='#00d4ff',
            fg='#0a0e27',
            font=('Arial', 11, 'bold'),
            padx=15,
            pady=5,
            cursor='hand2',
            relief=tk.FLAT
        )
        self.okx_refresh_btn.pack(side=tk.LEFT, padx=10)

        # 自动刷新开关
        auto_refresh_cb = tk.Checkbutton(
            control_bar,
            text="自动刷新",
            variable=self.okx_auto_refresh,
            command=self.toggle_okx_auto_refresh,
            bg='#1a1f3a',
            fg='#ffffff',
            selectcolor='#0a0e27',
            font=('Arial', 10),
            activebackground='#1a1f3a',
            activeforeground='#00d4ff'
        )
        auto_refresh_cb.pack(side=tk.LEFT, padx=10)

        # 状态标签
        self.okx_status_label = tk.Label(
            control_bar,
            text="就绪",
            font=('Arial', 10),
            bg='#1a1f3a',
            fg='#888'
        )
        self.okx_status_label.pack(side=tk.RIGHT, padx=15)

        # 数据表格
        columns = ('排名', '币种', '价格', '24H涨跌', '24H最高', '24H最低', '24H成交量(USDT)')

        # 创建样式
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("OKX.Treeview",
                       background="#1a1f3a",
                       foreground="#ffffff",
                       fieldbackground="#1a1f3a",
                       borderwidth=0,
                       rowheight=30)
        style.configure("OKX.Treeview.Heading",
                       background="#0a0e27",
                       foreground="#00d4ff",
                       borderwidth=1,
                       font=('Arial', 11, 'bold'))
        style.map('OKX.Treeview', background=[('selected', '#00d4ff')])

        self.okx_tree = ttk.Treeview(
            okx_table_frame,
            columns=columns,
            show='headings',
            height=25,
            style="OKX.Treeview"
        )

        # 设置列
        column_widths = {
            '排名': 60,
            '币种': 100,
            '价格': 150,
            '24H涨跌': 120,
            '24H最高': 150,
            '24H最低': 150,
            '24H成交量(USDT)': 180
        }

        for col in columns:
            self.okx_tree.heading(col, text=col)
            self.okx_tree.column(col, width=column_widths.get(col, 100), anchor='center')

        # 滚动条
        vsb = ttk.Scrollbar(okx_table_frame, orient=tk.VERTICAL, command=self.okx_tree.yview)
        self.okx_tree.configure(yscrollcommand=vsb.set)

        # 布局
        self.okx_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)
        vsb.pack(side=tk.RIGHT, fill=tk.Y, pady=5, padx=(0, 5))

    def create_okx_heatmap_tab(self, notebook):
        """创建 OKX 热力图标签页"""
        okx_heatmap_frame = tk.Frame(notebook, bg='#0a0e27')
        notebook.add(okx_heatmap_frame, text="OKX 市值热力图")

        # 顶部控制栏
        control_bar = tk.Frame(okx_heatmap_frame, bg='#1a1f3a', height=60)
        control_bar.pack(fill=tk.X, padx=5, pady=5)
        control_bar.pack_propagate(False)

        # 标题
        title = tk.Label(
            control_bar,
            text="市值热力图 (TOP 20)",
            font=('Arial', 14, 'bold'),
            bg='#1a1f3a',
            fg='#00d4ff'
        )
        title.pack(side=tk.LEFT, padx=15)

        # 刷新按钮
        refresh_btn = tk.Button(
            control_bar,
            text="🔄 刷新",
            command=self.refresh_okx_heatmap,
            bg='#00d4ff',
            fg='#0a0e27',
            font=('Arial', 11, 'bold'),
            padx=15,
            pady=5,
            cursor='hand2',
            relief=tk.FLAT
        )
        refresh_btn.pack(side=tk.LEFT, padx=10)

        # 图表容器
        chart_frame = tk.Frame(okx_heatmap_frame, bg='#0a0e27')
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 创建matplotlib图表
        self.okx_heatmap_fig, self.okx_heatmap_ax = plt.subplots(figsize=(12, 8), facecolor='#0a0e27')
        self.okx_heatmap_ax.set_facecolor('#0a0e27')

        self.okx_heatmap_canvas = FigureCanvasTkAgg(self.okx_heatmap_fig, chart_frame)
        self.okx_heatmap_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 初始化显示提示
        self.okx_heatmap_ax.text(0.5, 0.5, '点击刷新按钮加载数据',
                                ha='center', va='center',
                                fontsize=20, color='#ffffff',
                                transform=self.okx_heatmap_ax.transAxes)
        self.okx_heatmap_ax.axis('off')
        self.okx_heatmap_canvas.draw()

    def create_okx_positions_tab(self, notebook):
        """创建 OKX 当前持仓标签页"""
        positions_frame = tk.Frame(notebook, bg=COLORS['bg_secondary'])
        notebook.add(positions_frame, text="OKX 当前持仓")

        # 顶部控制栏
        control_bar = tk.Frame(positions_frame, bg=COLORS['bg_tertiary'], height=60)
        control_bar.pack(fill=tk.X, padx=5, pady=5)
        control_bar.pack_propagate(False)

        # 标题
        title = tk.Label(
            control_bar,
            text="💼 当前持仓",
            font=FONTS['title'],
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary']
        )
        title.pack(side=tk.LEFT, padx=15)

        # 刷新按钮
        refresh_btn = tk.Button(
            control_bar,
            text="🔄 刷新持仓",
            command=self.refresh_okx_positions,
            bg=COLORS['accent'],
            fg=COLORS['text_primary'],
            font=FONTS['body_bold'],
            activebackground=COLORS['accent_hover'],
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=8,
            cursor='hand2'
        )
        refresh_btn.pack(side=tk.LEFT, padx=10)

        # 自动刷新开关（默认关闭，启动跟单时自动开启）
        self.okx_positions_auto_refresh = tk.BooleanVar(value=False)
        auto_refresh_cb = tk.Checkbutton(
            control_bar,
            text="实时刷新 (2秒)",
            variable=self.okx_positions_auto_refresh,
            command=self.toggle_okx_positions_auto_refresh,
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary'],
            font=FONTS['body'],
            selectcolor=COLORS['bg_secondary'],
            activebackground=COLORS['bg_hover'],
            activeforeground=COLORS['text_primary']
        )
        auto_refresh_cb.pack(side=tk.LEFT, padx=10)

        # 注意：不在这里启动自动刷新，等启动跟单时再开启

        # 状态标签
        self.okx_positions_status_label = tk.Label(
            control_bar,
            text="",
            font=FONTS['small'],
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_muted']
        )
        self.okx_positions_status_label.pack(side=tk.RIGHT, padx=15)

        # 持仓表格容器
        table_frame = tk.Frame(positions_frame, bg=COLORS['bg_secondary'])
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 定义表格列
        columns = (
            '交易品种', '保证金模式', '持仓量', '标记价格', '开仓均价', '预估强平价',
            '盈亏平衡价', '浮动收益', '维持保证金率', '保证金'
        )

        # 创建表格
        self.okx_positions_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show='headings',
            height=20
        )

        # 设置列标题和宽度
        column_widths = {
            '交易品种': 150,
            '保证金模式': 90,
            '持仓量': 100,
            '标记价格': 120,
            '开仓均价': 120,
            '预估强平价': 120,
            '盈亏平衡价': 120,
            '浮动收益': 150,
            '维持保证金率': 120,
            '保证金': 120
        }

        for col in columns:
            self.okx_positions_tree.heading(col, text=col)
            width = column_widths.get(col, 100)
            self.okx_positions_tree.column(col, width=width, anchor='center')

        # 添加滚动条
        vsb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.okx_positions_tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.okx_positions_tree.xview)

        self.okx_positions_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # 布局
        self.okx_positions_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        # 配置表格框架的网格权重
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # 底部操作按钮区域
        action_frame = tk.Frame(positions_frame, bg=COLORS['bg_tertiary'], height=60)
        action_frame.pack(fill=tk.X, padx=5, pady=5)
        action_frame.pack_propagate(False)

        # 平仓按钮
        close_position_btn = tk.Button(
            action_frame,
            text="📉 平仓选中",
            command=self.close_selected_position,
            bg=COLORS['loss'],
            fg=COLORS['text_primary'],
            font=FONTS['body_bold'],
            activebackground='#dc2626',
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=8,
            cursor='hand2'
        )
        close_position_btn.pack(side=tk.LEFT, padx=10)

        # 全部平仓按钮
        close_all_btn = tk.Button(
            action_frame,
            text="⚠️ 全部平仓",
            command=self.close_all_positions,
            bg=COLORS['warning'],
            fg=COLORS['text_primary'],
            font=FONTS['body_bold'],
            activebackground='#d97706',
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=8,
            cursor='hand2'
        )
        close_all_btn.pack(side=tk.LEFT, padx=10)

        # 设置止盈止损按钮
        set_tpsl_btn = tk.Button(
            action_frame,
            text="🎯 设置止盈止损",
            command=self.show_set_tpsl_window,
            bg=COLORS['success'],
            fg=COLORS['text_primary'],
            font=FONTS['body_bold'],
            activebackground='#059669',
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=8,
            cursor='hand2'
        )
        set_tpsl_btn.pack(side=tk.LEFT, padx=10)

        # 提示信息
        tip_label = tk.Label(
            action_frame,
            text="💡 双击行可查看详细信息 | 选中行后点击按钮进行操作",
            font=FONTS['small'],
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_secondary']
        )
        tip_label.pack(side=tk.RIGHT, padx=15)

    def create_okx_orders_tab(self, notebook):
        """创建 OKX 当前委托标签页"""
        orders_frame = tk.Frame(notebook, bg=COLORS['bg_secondary'])
        notebook.add(orders_frame, text="OKX 当前委托")

        # 顶部控制栏
        control_bar = tk.Frame(orders_frame, bg=COLORS['bg_tertiary'], height=60)
        control_bar.pack(fill=tk.X, padx=5, pady=5)
        control_bar.pack_propagate(False)

        # 标题
        title = tk.Label(
            control_bar,
            text="📋 当前委托",
            font=FONTS['title'],
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary']
        )
        title.pack(side=tk.LEFT, padx=15)

        # 刷新按钮
        refresh_btn = tk.Button(
            control_bar,
            text="🔄 刷新委托",
            command=self.refresh_okx_orders,
            bg=COLORS['accent'],
            fg=COLORS['text_primary'],
            font=FONTS['body_bold'],
            activebackground=COLORS['accent_hover'],
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=8,
            cursor='hand2'
        )
        refresh_btn.pack(side=tk.LEFT, padx=10)

        # 自动刷新开关（默认关闭，启动跟单时自动开启）
        self.okx_orders_auto_refresh = tk.BooleanVar(value=False)
        auto_refresh_cb = tk.Checkbutton(
            control_bar,
            text="实时刷新 (2秒)",
            variable=self.okx_orders_auto_refresh,
            command=self.toggle_okx_orders_auto_refresh,
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary'],
            font=FONTS['body'],
            selectcolor=COLORS['bg_secondary'],
            activebackground=COLORS['bg_hover'],
            activeforeground=COLORS['text_primary']
        )
        auto_refresh_cb.pack(side=tk.LEFT, padx=10)

        # 状态标签
        self.okx_orders_status_label = tk.Label(
            control_bar,
            text="",
            font=FONTS['small'],
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_muted']
        )
        self.okx_orders_status_label.pack(side=tk.RIGHT, padx=15)

        # 委托单表格容器
        table_frame = tk.Frame(orders_frame, bg=COLORS['bg_secondary'])
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 定义表格列
        columns = (
            '委托类型', '交易品种', '方向', '委托价格', '委托数量',
            '已成交', '状态', '创建时间', '订单ID'
        )

        # 创建表格
        self.okx_orders_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show='headings',
            height=20
        )

        # 设置列标题和宽度
        column_widths = {
            '委托类型': 120,
            '交易品种': 140,
            '方向': 80,
            '委托价格': 120,
            '委托数量': 100,
            '已成交': 100,
            '状态': 100,
            '创建时间': 150,
            '订单ID': 180
        }

        for col in columns:
            self.okx_orders_tree.heading(col, text=col)
            width = column_widths.get(col, 100)
            self.okx_orders_tree.column(col, width=width, anchor='center')

        # 添加滚动条
        vsb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.okx_orders_tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.okx_orders_tree.xview)

        self.okx_orders_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # 布局
        self.okx_orders_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        # 配置表格框架的网格权重
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # 底部操作按钮区域
        action_frame = tk.Frame(orders_frame, bg=COLORS['bg_tertiary'], height=60)
        action_frame.pack(fill=tk.X, padx=5, pady=5)
        action_frame.pack_propagate(False)

        # 撤单按钮
        cancel_order_btn = tk.Button(
            action_frame,
            text="❌ 撤销选中",
            command=self.cancel_selected_order,
            bg=COLORS['loss'],
            fg=COLORS['text_primary'],
            font=FONTS['body_bold'],
            activebackground='#dc2626',
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=8,
            cursor='hand2'
        )
        cancel_order_btn.pack(side=tk.LEFT, padx=10)

        # 全部撤单按钮
        cancel_all_btn = tk.Button(
            action_frame,
            text="⚠️ 全部撤单",
            command=self.cancel_all_orders,
            bg=COLORS['warning'],
            fg=COLORS['text_primary'],
            font=FONTS['body_bold'],
            activebackground='#d97706',
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=8,
            cursor='hand2'
        )
        cancel_all_btn.pack(side=tk.LEFT, padx=10)

        # 提示信息
        tip_label = tk.Label(
            action_frame,
            text="💡 选中委托单后点击按钮进行撤单操作",
            font=FONTS['small'],
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_secondary']
        )
        tip_label.pack(side=tk.RIGHT, padx=15)

        # 注意：不在这里启动自动刷新，等启动跟单时再开启

    def create_auto_copy_monitor_tab(self, notebook):
        """创建自动跟单监控标签页"""
        monitor_frame = tk.Frame(notebook, bg=COLORS['bg_secondary'])
        notebook.add(monitor_frame, text="🤖 自动跟单监控")

        # 使用PanedWindow分割左右面板
        paned = tk.PanedWindow(monitor_frame, orient=tk.HORIZONTAL, bg=COLORS['bg_secondary'],
                               sashwidth=5, sashrelief=tk.RAISED)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ==================== 左侧面板：监控列表 ====================
        left_frame = tk.Frame(paned, bg=COLORS['bg_secondary'])
        paned.add(left_frame, width=800)

        # 顶部统计信息
        stats_frame = tk.Frame(left_frame, bg=COLORS['bg_tertiary'], height=100)
        stats_frame.pack(fill=tk.X, padx=5, pady=5)
        stats_frame.pack_propagate(False)

        # 第一行：跟单状态
        status_row = tk.Frame(stats_frame, bg=COLORS['bg_tertiary'])
        status_row.pack(fill=tk.X, padx=10, pady=(10, 5))

        tk.Label(
            status_row,
            text="跟单状态:",
            font=FONTS['body_bold'],
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary']
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.auto_copy_status_label = tk.Label(
            status_row,
            text="● 未启动",
            font=FONTS['body_bold'],
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_muted']
        )
        self.auto_copy_status_label.pack(side=tk.LEFT)

        # 第二行：统计数字
        stats_row = tk.Frame(stats_frame, bg=COLORS['bg_tertiary'])
        stats_row.pack(fill=tk.X, padx=10, pady=5)

        # 监控大户数
        traders_stat = tk.Frame(stats_row, bg=COLORS['bg_secondary'], relief=tk.FLAT, bd=1)
        traders_stat.pack(side=tk.LEFT, padx=(0, 15), pady=5, ipadx=10, ipady=5)

        tk.Label(
            traders_stat,
            text="监控大户",
            font=FONTS['small'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_secondary']
        ).pack()

        self.monitored_traders_count = tk.Label(
            traders_stat,
            text="0",
            font=FONTS['title'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['accent']
        )
        self.monitored_traders_count.pack()

        # 跟单成功数
        success_stat = tk.Frame(stats_row, bg=COLORS['bg_secondary'], relief=tk.FLAT, bd=1)
        success_stat.pack(side=tk.LEFT, padx=15, pady=5, ipadx=10, ipady=5)

        tk.Label(
            success_stat,
            text="跟单成功",
            font=FONTS['small'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_secondary']
        ).pack()

        self.copy_success_count = tk.Label(
            success_stat,
            text="0",
            font=FONTS['title'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['profit']
        )
        self.copy_success_count.pack()

        # 上次刷新
        refresh_stat = tk.Frame(stats_row, bg=COLORS['bg_secondary'], relief=tk.FLAT, bd=1)
        refresh_stat.pack(side=tk.LEFT, padx=15, pady=5, ipadx=10, ipady=5)

        tk.Label(
            refresh_stat,
            text="上次刷新",
            font=FONTS['small'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_secondary']
        ).pack()

        self.last_refresh_label = tk.Label(
            refresh_stat,
            text="--:--:--",
            font=FONTS['body_bold'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary']
        )
        self.last_refresh_label.pack()

        # 监控大户列表
        list_frame = tk.LabelFrame(
            left_frame,
            text="📊 监控大户列表",
            font=FONTS['heading'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary']
        )
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 表格容器
        table_container = tk.Frame(list_frame, bg=COLORS['bg_secondary'])
        table_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 定义列
        columns = ('地址', '币种', '方向', '持仓价值', '持仓数量', '盈亏', '跟单状态', '最后更新')

        # 创建表格
        self.monitor_tree = ttk.Treeview(
            table_container,
            columns=columns,
            show='headings',
            height=15
        )

        # 设置列
        column_widths = {
            '地址': 120,
            '币种': 60,
            '方向': 60,
            '持仓价值': 120,
            '持仓数量': 120,
            '盈亏': 120,
            '跟单状态': 100,
            '最后更新': 120
        }

        for col in columns:
            self.monitor_tree.heading(col, text=col)
            self.monitor_tree.column(col, width=column_widths.get(col, 100), anchor='center')

        # 滚动条
        vsb = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.monitor_tree.yview)
        hsb = ttk.Scrollbar(table_container, orient=tk.HORIZONTAL, command=self.monitor_tree.xview)
        self.monitor_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # 布局
        self.monitor_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        # 绑定选中事件
        self.monitor_tree.bind('<<TreeviewSelect>>', self.on_monitor_trader_select)

        # ==================== 右侧面板：详情 ====================
        right_frame = tk.Frame(paned, bg=COLORS['bg_secondary'])
        paned.add(right_frame, width=500)

        # 大户详情
        detail_frame = tk.LabelFrame(
            right_frame,
            text="📋 大户详情",
            font=FONTS['heading'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary'],
            height=300
        )
        detail_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        detail_frame.pack_propagate(False)

        # 详情文本框
        self.trader_detail_text = scrolledtext.ScrolledText(
            detail_frame,
            wrap=tk.WORD,
            font=FONTS['small'],
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary'],
            insertbackground=COLORS['text_primary'],
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.trader_detail_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.trader_detail_text.insert('1.0', '👈 请选择左侧的大户查看详情')
        self.trader_detail_text.config(state=tk.DISABLED)

        # 我的跟单情况
        my_copy_frame = tk.LabelFrame(
            right_frame,
            text="💼 我的跟单情况",
            font=FONTS['heading'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary'],
            height=250
        )
        my_copy_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        my_copy_frame.pack_propagate(False)

        # 跟单情况文本框
        self.my_copy_text = scrolledtext.ScrolledText(
            my_copy_frame,
            wrap=tk.WORD,
            font=FONTS['small'],
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary'],
            insertbackground=COLORS['text_primary'],
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.my_copy_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.my_copy_text.insert('1.0', '等待跟单数据...')
        self.my_copy_text.config(state=tk.DISABLED)

        # 记录当前选中的大户地址（用于自动更新详情）
        self.selected_trader_address = None

        # 启动定时更新
        self.update_monitor_display()

    def create_favorites_tab(self, notebook):
        """创建收藏地址标签页"""
        favorites_frame = tk.Frame(notebook, bg=COLORS['bg_secondary'])
        notebook.add(favorites_frame, text=self.lang.get_text('tab_favorites'))

        # 顶部工具栏
        toolbar_frame = tk.Frame(favorites_frame, bg=COLORS['bg_tertiary'], height=60)
        toolbar_frame.pack(fill=tk.X, padx=5, pady=5)
        toolbar_frame.pack_propagate(False)

        # 左侧搜索框
        search_container = tk.Frame(toolbar_frame, bg=COLORS['bg_tertiary'])
        search_container.pack(side=tk.LEFT, padx=10, pady=10)

        tk.Label(
            search_container,
            text=self.lang.get_text('favorite_search') + ':',
            font=FONTS['body'],
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary']
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.favorite_search_var = tk.StringVar()
        self.favorite_search_var.trace('w', lambda *args: self.refresh_favorites_display())
        search_entry = tk.Entry(
            search_container,
            textvariable=self.favorite_search_var,
            font=FONTS['body'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary'],
            insertbackground=COLORS['text_primary'],
            width=30
        )
        search_entry.pack(side=tk.LEFT)

        # 右侧按钮组
        button_container = tk.Frame(toolbar_frame, bg=COLORS['bg_tertiary'])
        button_container.pack(side=tk.RIGHT, padx=10, pady=10)

        # 刷新按钮
        refresh_btn = tk.Button(
            button_container,
            text=self.lang.get_text('btn_favorite_refresh'),
            command=self.refresh_favorites_display,
            font=FONTS['body'],
            bg=COLORS['accent'],
            fg=COLORS['text_primary'],
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor='hand2'
        )
        refresh_btn.pack(side=tk.LEFT, padx=5)

        # 导出按钮
        export_btn = tk.Button(
            button_container,
            text=self.lang.get_text('btn_favorite_export'),
            command=self.export_favorites,
            font=FONTS['body'],
            bg=COLORS['bg_primary'],
            fg=COLORS['text_primary'],
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor='hand2'
        )
        export_btn.pack(side=tk.LEFT, padx=5)

        # 导入按钮
        import_btn = tk.Button(
            button_container,
            text=self.lang.get_text('btn_favorite_import'),
            command=self.import_favorites,
            font=FONTS['body'],
            bg=COLORS['bg_primary'],
            fg=COLORS['text_primary'],
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor='hand2'
        )
        import_btn.pack(side=tk.LEFT, padx=5)

        # 收藏列表区域
        list_frame = tk.Frame(favorites_frame, bg=COLORS['bg_secondary'])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 创建收藏列表表格
        columns = (
            self.lang.get_text('favorite_address'),
            self.lang.get_text('favorite_note'),
            self.lang.get_text('favorite_tags'),
            self.lang.get_text('favorite_created_at'),
            self.lang.get_text('favorite_updated_at')
        )

        self.favorites_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show='headings',
            height=20
        )

        # 设置列标题和宽度
        column_widths = [250, 300, 200, 150, 150]
        for i, col in enumerate(columns):
            self.favorites_tree.heading(col, text=col)
            self.favorites_tree.column(col, width=column_widths[i], anchor='w')

        # 添加滚动条
        vsb = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.favorites_tree.yview)
        hsb = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.favorites_tree.xview)
        self.favorites_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # 布局
        self.favorites_tree.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        # 双击查看详情
        self.favorites_tree.bind('<Double-Button-1>', self.on_favorite_double_click)

        # 右键菜单
        self.favorites_context_menu = tk.Menu(self.favorites_tree, tearoff=0)
        self.favorites_context_menu.add_command(
            label=self.lang.get_text('favorite_view_details'),
            command=self.view_favorite_details
        )
        self.favorites_context_menu.add_command(
            label=self.lang.get_text('favorite_edit_title'),
            command=self.edit_favorite
        )
        self.favorites_context_menu.add_separator()
        self.favorites_context_menu.add_command(
            label=self.lang.get_text('btn_remove_favorite'),
            command=self.remove_favorite
        )

        self.favorites_tree.bind('<Button-3>', self.show_favorites_context_menu)

        # 底部统计信息
        stats_frame = tk.Frame(favorites_frame, bg=COLORS['bg_tertiary'], height=40)
        stats_frame.pack(fill=tk.X, padx=5, pady=5)
        stats_frame.pack_propagate(False)

        self.favorites_stats_label = tk.Label(
            stats_frame,
            text=self.lang.get_text('total_records', count=0),
            font=FONTS['body'],
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_secondary']
        )
        self.favorites_stats_label.pack(side=tk.LEFT, padx=15, pady=10)

        # 初始化显示
        self.refresh_favorites_display()

    def refresh_favorites_display(self):
        """刷新收藏列表显示"""
        try:
            # 清空当前显示
            for item in self.favorites_tree.get_children():
                self.favorites_tree.delete(item)

            # 获取搜索关键词
            keyword = self.favorite_search_var.get() if hasattr(self, 'favorite_search_var') else ''

            # 搜索收藏
            favorites = self.favorites.search_favorites(keyword=keyword)

            # 显示收藏列表
            for fav in favorites:
                # 格式化时间显示（只显示日期部分）
                created_at = fav.get('created_at', '')[:10] if fav.get('created_at') else ''
                updated_at = fav.get('updated_at', '')[:10] if fav.get('updated_at') else ''

                # 格式化标签
                tags_str = ', '.join(fav.get('tags', []))

                self.favorites_tree.insert(
                    '',
                    'end',
                    iid=fav['address'],  # 使用地址作为唯一标识
                    values=(
                        fav['address'],
                        fav.get('note', ''),
                        tags_str,
                        created_at,
                        updated_at
                    )
                )

            # 更新统计信息
            self.favorites_stats_label.config(
                text=self.lang.get_text('total_records', count=len(favorites))
            )

        except Exception as e:
            print(f"刷新收藏列表失败: {e}")

    def on_favorite_double_click(self, event):
        """双击收藏地址查看详情"""
        self.view_favorite_details()

    def view_favorite_details(self):
        """查看收藏地址的详细信息"""
        try:
            selection = self.favorites_tree.selection()
            if not selection:
                return

            address = selection[0]  # iid 就是地址

            # 查找该地址在 user_links 中的详情页 URL
            if hasattr(self, 'data') and 'user_links' in self.data:
                user_links = self.data['user_links']
                if address in user_links:
                    url = user_links[address]
                    # 使用现有的详情查看功能
                    thread = threading.Thread(
                        target=self.fetch_user_details,
                        args=(url, address),
                        daemon=True
                    )
                    thread.start()
                else:
                    messagebox.showinfo(
                        self.lang.get_text('msg_refresh_title'),
                        f"暂无该地址的详情页链接，请先在持仓数据中刷新。\n地址: {address}"
                    )
            else:
                messagebox.showinfo(
                    self.lang.get_text('msg_refresh_title'),
                    "请先刷新持仓数据以获取地址详情链接。"
                )

        except Exception as e:
            print(f"查看收藏详情失败: {e}")

    def edit_favorite(self):
        """编辑收藏地址"""
        try:
            selection = self.favorites_tree.selection()
            if not selection:
                return

            address = selection[0]
            fav = self.favorites.get_favorite(address)
            if not fav:
                return

            # 创建编辑对话框
            self.show_add_favorite_dialog(edit_mode=True, existing_data=fav)

        except Exception as e:
            print(f"编辑收藏失败: {e}")

    def remove_favorite(self):
        """移除收藏地址"""
        try:
            selection = self.favorites_tree.selection()
            if not selection:
                return

            address = selection[0]

            # 确认对话框
            confirm = messagebox.askyesno(
                self.lang.get_text('msg_favorite_confirm_remove'),
                self.lang.get_text('msg_favorite_confirm_remove_text')
            )

            if confirm:
                if self.favorites.remove_favorite(address):
                    self.add_message(self.lang.get_text('msg_favorite_removed'), 'success')
                    self.refresh_favorites_display()
                else:
                    messagebox.showerror("错误", "移除收藏失败")

        except Exception as e:
            print(f"移除收藏失败: {e}")

    def show_favorites_context_menu(self, event):
        """显示右键菜单"""
        try:
            # 选中点击的项
            item = self.favorites_tree.identify_row(event.y)
            if item:
                self.favorites_tree.selection_set(item)
                self.favorites_context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            print(f"显示右键菜单失败: {e}")

    def show_add_favorite_dialog(self, edit_mode=False, existing_data=None):
        """显示添加/编辑收藏对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title(
            self.lang.get_text('favorite_edit_title') if edit_mode
            else self.lang.get_text('favorite_add_title')
        )
        dialog.geometry("500x300")
        dialog.configure(bg=COLORS['bg_secondary'])
        dialog.transient(self.root)
        dialog.grab_set()

        # 地址输入
        tk.Label(
            dialog,
            text=self.lang.get_text('favorite_input_address'),
            font=FONTS['body'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary']
        ).pack(padx=20, pady=(20, 5), anchor='w')

        address_var = tk.StringVar(value=existing_data['address'] if existing_data else '')
        address_entry = tk.Entry(
            dialog,
            textvariable=address_var,
            font=FONTS['body'],
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary'],
            insertbackground=COLORS['text_primary'],
            state='readonly' if edit_mode else 'normal'
        )
        address_entry.pack(padx=20, pady=5, fill=tk.X)

        # 备注输入
        tk.Label(
            dialog,
            text=self.lang.get_text('favorite_input_note'),
            font=FONTS['body'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary']
        ).pack(padx=20, pady=(10, 5), anchor='w')

        note_var = tk.StringVar(value=existing_data.get('note', '') if existing_data else '')
        note_entry = tk.Entry(
            dialog,
            textvariable=note_var,
            font=FONTS['body'],
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary'],
            insertbackground=COLORS['text_primary']
        )
        note_entry.pack(padx=20, pady=5, fill=tk.X)

        # 标签输入
        tk.Label(
            dialog,
            text=self.lang.get_text('favorite_input_tags'),
            font=FONTS['body'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary']
        ).pack(padx=20, pady=(10, 5), anchor='w')

        tags_str = ', '.join(existing_data.get('tags', [])) if existing_data else ''
        tags_var = tk.StringVar(value=tags_str)
        tags_entry = tk.Entry(
            dialog,
            textvariable=tags_var,
            font=FONTS['body'],
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary'],
            insertbackground=COLORS['text_primary']
        )
        tags_entry.pack(padx=20, pady=5, fill=tk.X)

        # 按钮
        button_frame = tk.Frame(dialog, bg=COLORS['bg_secondary'])
        button_frame.pack(pady=20)

        def on_save():
            address = address_var.get().strip()
            note = note_var.get().strip()
            tags_input = tags_var.get().strip()
            tags = [t.strip() for t in tags_input.split(',') if t.strip()]

            if not address:
                messagebox.showerror("错误", "请输入地址")
                return

            if self.favorites.add_favorite(address, note, tags):
                self.add_message(self.lang.get_text('msg_favorite_added'), 'success')
                self.refresh_favorites_display()
                dialog.destroy()
            else:
                messagebox.showerror("错误", "保存收藏失败")

        save_btn = tk.Button(
            button_frame,
            text="保存",
            command=on_save,
            font=FONTS['body'],
            bg=COLORS['accent'],
            fg=COLORS['text_primary'],
            relief=tk.FLAT,
            padx=20,
            pady=5,
            cursor='hand2'
        )
        save_btn.pack(side=tk.LEFT, padx=10)

        cancel_btn = tk.Button(
            button_frame,
            text="取消",
            command=dialog.destroy,
            font=FONTS['body'],
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary'],
            relief=tk.FLAT,
            padx=20,
            pady=5,
            cursor='hand2'
        )
        cancel_btn.pack(side=tk.LEFT, padx=10)

    def export_favorites(self):
        """导出收藏到CSV"""
        try:
            from tkinter import filedialog
            filepath = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile="favorites_export.csv"
            )

            if filepath:
                if self.favorites.export_to_csv(filepath):
                    self.add_message(
                        self.lang.get_text('msg_favorite_export_success') + filepath,
                        'success'
                    )
                else:
                    messagebox.showerror("错误", "导出失败")

        except Exception as e:
            print(f"导出收藏失败: {e}")
            messagebox.showerror("错误", f"导出失败: {e}")

    def import_favorites(self):
        """从CSV导入收藏"""
        try:
            from tkinter import filedialog
            filepath = filedialog.askopenfilename(
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )

            if filepath:
                count = self.favorites.import_from_csv(filepath)
                if count > 0:
                    self.add_message(
                        self.lang.get_text('msg_favorite_import_success', count=count),
                        'success'
                    )
                    self.refresh_favorites_display()
                else:
                    messagebox.showwarning("警告", "未导入任何数据")

        except Exception as e:
            print(f"导入收藏失败: {e}")
            messagebox.showerror("错误", f"导入失败: {e}")

    def on_monitor_trader_select(self, event):
        """当选中监控列表中的大户时，显示详情"""
        try:
            selection = self.monitor_tree.selection()
            if not selection:
                self.selected_trader_address = None
                return

            # 使用 iid 获取完整地址，而不是从 values 中获取截断的地址
            trader_address = selection[0]  # iid 就是完整地址

            # 保存选中的地址，用于自动更新
            self.selected_trader_address = trader_address

            # 更新显示
            self.update_trader_detail_display(trader_address)

        except Exception as e:
            print(f"[Monitor] 显示大户详情失败: {e}")
            import traceback
            traceback.print_exc()

    def update_trader_detail_display(self, trader_address):
        """更新大户详情显示（独立方法，可被定时调用）"""
        try:
            # 获取大户详细信息
            if not self.auto_copy_trader or trader_address not in self.auto_copy_trader.followed_traders:
                return

            trader_info = self.auto_copy_trader.followed_traders[trader_address]

            # 更新大户详情显示
            self.trader_detail_text.config(state=tk.NORMAL)
            self.trader_detail_text.delete('1.0', tk.END)

            detail_text = f"{'='*40}\n"
            detail_text += f"大户地址: {trader_address}\n"
            detail_text += f"跟单开始时间: {trader_info.get('start_time_str', 'N/A')}\n"
            detail_text += f"{'='*40}\n\n"

            # 持仓信息
            positions = trader_info.get('positions', [])
            detail_text += f"📈 当前持仓 ({len(positions)}个):\n\n"
            for idx, pos in enumerate(positions, 1):
                detail_text += f"[{idx}] {pos.get('代币', 'N/A')} {pos.get('方向', 'N/A')}\n"
                detail_text += f"    杠杆: {pos.get('杠杆', 'N/A')}\n"
                detail_text += f"    价值: {pos.get('价值', 'N/A')}\n"
                detail_text += f"    数量: {pos.get('数量', 'N/A')}\n"
                detail_text += f"    开仓价: {pos.get('开仓价格', 'N/A')}\n"
                detail_text += f"    盈亏: {pos.get('盈亏(PnL)', 'N/A')}\n\n"

            # 最新交易
            trades = trader_info.get('last_trades', [])[:3]  # 只显示最近3笔
            if trades:
                detail_text += f"\n🔄 最新交易 (最近3笔):\n\n"
                for idx, trade in enumerate(trades, 1):
                    detail_text += f"[{idx}] {trade.get('时间', 'N/A')}\n"
                    detail_text += f"    {trade.get('代币', 'N/A')} - {trade.get('方向', 'N/A')}\n"
                    detail_text += f"    价格: {trade.get('价格', 'N/A')}\n"
                    detail_text += f"    数量: {trade.get('数量', 'N/A')}\n\n"

            self.trader_detail_text.insert('1.0', detail_text)
            self.trader_detail_text.config(state=tk.DISABLED)

            # 更新我的跟单情况
            self.update_my_copy_status(trader_address)

        except Exception as e:
            print(f"[Monitor] 更新大户详情失败: {e}")
            import traceback
            traceback.print_exc()

    def update_my_copy_status(self, trader_address):
        """更新我的跟单情况显示"""
        try:
            self.my_copy_text.config(state=tk.NORMAL)
            self.my_copy_text.delete('1.0', tk.END)

            copy_text = f"{'='*40}\n"
            copy_text += f"跟单大户: {trader_address[:8]}...\n"
            copy_text += f"{'='*40}\n\n"

            # 获取OKX持仓
            okx_positions_map = {}  # {币种: {持仓数据}}
            if self.okx_trader:
                result = self.okx_trader.get_positions()
                if result.get('code') == '0' and result.get('data'):
                    positions = result['data']

                    copy_text += f"💼 我的OKX持仓:\n\n"
                    has_positions = False
                    for pos in positions:
                        if float(pos.get('pos', '0')) == 0:
                            continue

                        has_positions = True
                        inst_id = pos.get('instId', 'N/A')
                        pos_qty = pos.get('pos', '0')
                        avg_px = pos.get('avgPx', '0')
                        upl = pos.get('upl', '0')
                        upl_ratio = float(pos.get('uplRatio', '0')) * 100
                        mark_px = pos.get('markPx', '0')
                        lever = pos.get('lever', '1')  # 杠杆倍数
                        margin = pos.get('margin', '0')  # 保证金
                        notional_usd = pos.get('notionalUsd', '0')  # 名义价值

                        # 提取币种名称 (BTC-USDT-SWAP -> BTC)
                        coin = inst_id.split('-')[0] if '-' in inst_id else inst_id

                        # 保存持仓数据到映射
                        okx_positions_map[coin] = {
                            'inst_id': inst_id,
                            'pos': abs(float(pos_qty)),  # 持仓数量（取绝对值）
                            'avg_px': float(avg_px) if avg_px else 0,
                            'mark_px': float(mark_px) if mark_px else 0,
                            'upl': float(upl) if upl else 0,
                            'upl_ratio': upl_ratio,
                            'lever': float(lever) if lever else 1,  # 杠杆倍数
                            'margin': float(margin) if margin else 0,  # 保证金（USDT）
                            'notional_usd': abs(float(notional_usd)) if notional_usd else 0  # 名义价值（美元）
                        }

                        copy_text += f"品种: {inst_id}\n"
                        copy_text += f"持仓: {pos_qty}\n"
                        copy_text += f"杠杆: {lever}x\n"
                        copy_text += f"保证金: ${margin}\n"
                        copy_text += f"均价: ${avg_px}\n"
                        copy_text += f"盈亏: ${upl} ({upl_ratio:+.2f}%)\n\n"

                    if not has_positions:
                        copy_text += "当前无持仓\n\n"
                else:
                    copy_text += "⚠️ 无法获取OKX持仓数据\n\n"

            # 获取跟单比例信息 - 只显示实际跟单的币种
            if self.auto_copy_trader and trader_address in self.auto_copy_trader.followed_traders:
                trader_info = self.auto_copy_trader.followed_traders[trader_address]
                trader_positions = trader_info.get('positions', [])

                if trader_positions and okx_positions_map:
                    copy_text += f"\n📊 跟单比例 (按保证金计算):\n\n"

                    for trader_pos in trader_positions:
                        coin = trader_pos.get('代币', 'N/A')

                        # 只显示我实际持有的币种
                        if coin not in okx_positions_map:
                            continue

                        trader_value_str = trader_pos.get('价值', 'N/A')
                        trader_qty_str = trader_pos.get('数量', 'N/A')
                        trader_leverage_str = trader_pos.get('杠杆', 'N/A')  # 如 "15X 全仓"

                        # 解析大户持仓价值（名义价值）
                        try:
                            trader_notional_usd = self.auto_copy_trader.parse_position_value(trader_value_str)
                        except:
                            trader_notional_usd = None

                        # 解析大户杠杆倍数
                        trader_leverage = 1
                        try:
                            if 'X' in trader_leverage_str:
                                trader_leverage = float(trader_leverage_str.split('X')[0].strip())
                        except:
                            trader_leverage = 1

                        # 计算大户保证金
                        if trader_notional_usd and trader_leverage > 0:
                            trader_margin = trader_notional_usd / trader_leverage
                        else:
                            trader_margin = None

                        # 获取我的持仓数据
                        my_pos = okx_positions_map[coin]
                        my_margin = my_pos['margin']  # 我的保证金
                        my_notional = my_pos['notional_usd']  # 我的名义价值
                        my_leverage = my_pos['lever']  # 我的杠杆

                        # 如果API没有返回notional_usd，手动计算
                        if my_notional == 0:
                            my_notional = my_pos['pos'] * my_pos['mark_px']

                        # 如果API没有返回margin，手动计算
                        if my_margin == 0 and my_leverage > 0:
                            my_margin = my_notional / my_leverage

                        # 计算实际跟单比例（基于保证金）
                        if trader_margin and trader_margin > 0 and my_margin > 0:
                            ratio = (my_margin / trader_margin) * 100
                            ratio_text = f"{ratio:.4f}%"
                        else:
                            ratio_text = "无法计算"

                        copy_text += f"{coin}:\n"
                        copy_text += f"  大户名义价值: {trader_value_str} ({trader_qty_str})\n"
                        copy_text += f"  大户杠杆: {trader_leverage_str}\n"
                        if trader_margin:
                            copy_text += f"  大户保证金: ${trader_margin:,.2f}\n"
                        copy_text += f"\n"
                        copy_text += f"  我的持仓: {my_pos['pos']:.4f} {coin}\n"
                        copy_text += f"  我的杠杆: {my_leverage:.0f}x\n"
                        copy_text += f"  我的名义价值: ${my_notional:,.2f}\n"
                        copy_text += f"  我的保证金: ${my_margin:,.2f}\n"
                        copy_text += f"  \n"
                        copy_text += f"  跟单比例: {ratio_text}\n\n"

            self.my_copy_text.insert('1.0', copy_text)
            self.my_copy_text.config(state=tk.DISABLED)

        except Exception as e:
            print(f"[Monitor] 更新跟单状态失败: {e}")

    def update_monitor_display(self):
        """定时更新监控显示"""
        try:
            if not hasattr(self, 'monitor_tree'):
                return

            # 更新统计信息
            if self.auto_copy_trader:
                # 跟单状态
                if hasattr(self, 'auto_copy_status_label'):
                    if self.auto_copy_trader.is_running:
                        status_text = "● 运行中"
                        status_color = COLORS['profit']
                    else:
                        status_text = "● 未启动"
                        status_color = COLORS['text_muted']

                    # 更新状态标签
                    for widget in self.root.winfo_children():
                        if isinstance(widget, tk.Frame):
                            self._update_status_label_recursive(widget, status_text, status_color)

                # 监控大户数
                trader_count = len(self.auto_copy_trader.followed_traders)
                self.monitored_traders_count.config(text=str(trader_count))

                # 跟单成功数
                success_count = self.auto_copy_trader.successful_copies
                self.copy_success_count.config(text=str(success_count))

                # 上次刷新时间
                if self.auto_copy_trader.last_refresh_time:
                    refresh_time = self.auto_copy_trader.last_refresh_time.strftime('%H:%M:%S')
                    self.last_refresh_label.config(text=refresh_time)

                # 更新监控列表
                self.monitor_tree.delete(*self.monitor_tree.get_children())

                for trader_address, info in self.auto_copy_trader.followed_traders.items():
                    if not info.get('active'):
                        continue

                    # 获取最新的持仓信息
                    positions = info.get('positions', [])
                    if positions:
                        main_pos = positions[0]  # 主要持仓

                        coin = main_pos.get('代币', 'N/A')
                        direction = main_pos.get('方向', 'N/A')
                        value = main_pos.get('价值', 'N/A')
                        quantity = main_pos.get('数量', 'N/A')
                        pnl = main_pos.get('盈亏(PnL)', 'N/A')
                    else:
                        coin = 'N/A'
                        direction = 'N/A'
                        value = 'N/A'
                        quantity = 'N/A'
                        pnl = 'N/A'

                    # 跟单状态
                    copy_status = "✅ 已跟单" if info.get('active') else "⏸️ 暂停"

                    # 最后更新时间
                    last_update = info.get('start_time_str', 'N/A')
                    if last_update != 'N/A':
                        last_update = last_update.split(' ')[1]  # 只显示时间部分

                    # 插入数据 - 使用完整地址作为iid，显示截断地址
                    self.monitor_tree.insert('', 'end', iid=trader_address, values=(
                        trader_address[:10] + '...',
                        coin,
                        direction,
                        value,
                        quantity,
                        pnl,
                        copy_status,
                        last_update
                    ))

                # 如果有选中的大户，自动更新其详情
                if hasattr(self, 'selected_trader_address') and self.selected_trader_address:
                    if self.selected_trader_address in self.auto_copy_trader.followed_traders:
                        self.update_trader_detail_display(self.selected_trader_address)

        except Exception as e:
            print(f"[Monitor] 更新监控显示失败: {e}")

        # 每2秒更新一次
        self.root.after(2000, self.update_monitor_display)

    def _update_status_label_recursive(self, widget, text, color):
        """递归查找并更新状态标签"""
        try:
            if hasattr(widget, 'auto_copy_status_label'):
                widget.auto_copy_status_label.config(text=text, fg=color)
                return

            for child in widget.winfo_children():
                if isinstance(child, (tk.Frame, tk.LabelFrame)):
                    self._update_status_label_recursive(child, text, color)
        except:
            pass

    def refresh_okx_data(self):
        """刷新 OKX 数据表格"""
        if self.okx_is_loading:
            messagebox.showwarning("提示", "正在加载数据，请稍候...")
            return

        thread = threading.Thread(target=self._fetch_okx_data)
        thread.daemon = True
        thread.start()

    def _fetch_okx_data(self):
        """后台获取 OKX 数据"""
        self.okx_is_loading = True
        self.root.after(0, lambda: self.okx_status_label.config(text="正在获取数据..."))
        self.root.after(0, lambda: self.okx_refresh_btn.config(state=tk.DISABLED))

        try:
            # 获取行情数据
            tickers = self.okx_client.get_tickers("SWAP")
            if tickers:
                # 解析数据
                self.okx_data = self.okx_client.parse_ticker_data(tickers, filter_usdt=True, top_n=50)

                # 更新UI（必须在主线程）
                self.root.after(0, self._update_okx_table)
                self.root.after(0, lambda: self.okx_status_label.config(
                    text=f"更新成功 - {datetime.now().strftime('%H:%M:%S')}"
                ))
            else:
                self.root.after(0, lambda: self.okx_status_label.config(text="获取数据失败"))
                self.root.after(0, lambda: messagebox.showerror("错误", "无法获取 OKX 数据"))

        except Exception as e:
            self.root.after(0, lambda: self.okx_status_label.config(text=f"错误: {str(e)}"))
            self.root.after(0, lambda: messagebox.showerror("错误", f"获取数据失败:\n{str(e)}"))

        finally:
            self.okx_is_loading = False
            self.root.after(0, lambda: self.okx_refresh_btn.config(state=tk.NORMAL))

    def _update_okx_table(self):
        """更新 OKX 数据表格（主线程）"""
        # 清空表格
        for item in self.okx_tree.get_children():
            self.okx_tree.delete(item)

        # 填充数据
        for idx, data in enumerate(self.okx_data, 1):
            price = f"${data['price']:,.4f}" if data['price'] < 100 else f"${data['price']:,.2f}"
            change = data['change']
            change_text = f"+{change:.2f}%" if change >= 0 else f"{change:.2f}%"

            high = f"${data['high']:,.4f}" if data['high'] < 100 else f"${data['high']:,.2f}"
            low = f"${data['low']:,.4f}" if data['low'] < 100 else f"${data['low']:,.2f}"
            volume = f"${data['volume_usd']:,.0f}"

            # 插入数据，使用tag标记涨跌
            tag = 'up' if change >= 0 else 'down'
            self.okx_tree.insert('', tk.END, values=(
                idx,
                data['symbol'],
                price,
                change_text,
                high,
                low,
                volume
            ), tags=(tag,))

        # 配置颜色
        self.okx_tree.tag_configure('up', foreground='#00ff88')
        self.okx_tree.tag_configure('down', foreground='#ff4444')

    def refresh_okx_heatmap(self):
        """刷新热力图"""
        if not self.okx_data:
            # 如果没有数据，先获取
            self.refresh_okx_data()
            # 等待数据加载后再绘制
            self.root.after(2000, self._draw_okx_heatmap)
        else:
            self._draw_okx_heatmap()

    def _draw_okx_heatmap(self):
        """绘制热力图（方块大小=市值，颜色=涨跌幅）"""
        if not self.okx_data:
            return

        # 清空画布
        self.okx_heatmap_ax.clear()
        self.okx_heatmap_ax.set_facecolor('#0a0e27')

        # 取前20个（已按市值排序）
        top_data = self.okx_data[:20]

        # 准备数据
        # 方块大小：按市值排名赋予权重（排名越高权重越大）
        # 使用反向权重：第1名权重最大，第20名权重最小
        sizes = []
        for i, d in enumerate(top_data):
            # 使用指数递减：第1名=100, 第2名=95, 第3名=90...
            # 这样能更好地反映市值差距
            weight = 100 - (i * 3)  # 每个排名减少3个单位
            if weight < 10:
                weight = 10  # 最小权重为10，确保都能显示
            sizes.append(weight)

        labels = [f"{d['symbol']}\n{d['change']:+.2f}%" for d in top_data]
        changes = [d['change'] for d in top_data]

        # 颜色映射（根据涨跌幅）
        colors = []
        for change in changes:
            if change > 5:
                colors.append('#00ff88')  # 大涨
            elif change > 0:
                colors.append('#88ffaa')  # 小涨
            elif change > -5:
                colors.append('#ffaa88')  # 小跌
            else:
                colors.append('#ff4444')  # 大跌

        # 绘制树状图
        squarify.plot(sizes=sizes, label=labels, color=colors,
                     alpha=0.8, text_kwargs={'fontsize': 10, 'color': '#0a0e27', 'weight': 'bold'},
                     ax=self.okx_heatmap_ax)

        self.okx_heatmap_ax.axis('off')
        self.okx_heatmap_fig.tight_layout()
        self.okx_heatmap_canvas.draw()

    # ==================== OKX 持仓管理相关方法 ====================

    def refresh_okx_positions(self):
        """刷新OKX持仓"""
        if not self.okx_trader or not self.okx_config.get('api_key'):
            messagebox.showwarning("提示", "请先配置OKX API密钥")
            return

        # 在新线程中获取持仓
        def fetch_positions():
            try:
                # 检查状态标签是否存在
                if hasattr(self, 'okx_positions_status_label'):
                    self.okx_positions_status_label.config(
                        text="正在获取持仓...",
                        fg=COLORS['info']
                    )

                # 获取持仓数据
                result = self.okx_trader.get_positions(inst_type="SWAP")

                if result.get('code') == '0':
                    positions = result.get('data', [])

                    # 调试信息：打印持仓详情
                    active_positions = [p for p in positions if float(p.get('pos', '0')) != 0]
                    print(f"[OKX] Fetched {len(active_positions)} active positions:")
                    for idx, pos in enumerate(active_positions):
                        inst_id = pos.get('instId')
                        pos_qty = pos.get('pos')
                        pos_side = pos.get('posSide', 'net')
                        print(f"  [{idx+1}] {inst_id}: pos={pos_qty}, posSide={pos_side}")

                    # 在主线程更新UI
                    self.root.after(0, lambda: self.update_positions_table(positions))
                else:
                    error_msg = result.get('msg', '获取失败')
                    print(f"[OKX] Failed to fetch positions: {error_msg}")
                    if hasattr(self, 'okx_positions_status_label'):
                        self.root.after(0, lambda: self.okx_positions_status_label.config(
                            text=f"❌ {error_msg}",
                            fg=COLORS['loss']
                        ))

            except Exception as e:
                error_msg = str(e)
                print(f"[OKX Positions] Exception: {error_msg}")
                import traceback
                traceback.print_exc()
                if hasattr(self, 'okx_positions_status_label'):
                    self.root.after(0, lambda msg=error_msg: self.okx_positions_status_label.config(
                        text=f"❌ 异常: {msg}",
                        fg=COLORS['loss']
                    ))

        thread = threading.Thread(target=fetch_positions)
        thread.daemon = True
        thread.start()

    def update_positions_table(self, positions):
        """更新持仓表格"""
        # 保存当前选中的持仓（用于刷新后恢复选中状态）
        selected_inst_id = None
        selected_mgn_mode = None
        selected_items = self.okx_positions_tree.selection()
        if selected_items:
            try:
                item = self.okx_positions_tree.item(selected_items[0])
                values = item['values']
                if values and len(values) >= 2:
                    selected_inst_id = values[0]  # 交易品种
                    # 将中文保证金模式转换回英文用于匹配
                    selected_mgn_mode = 'cross' if values[1] == '全仓' else 'isolated'
            except Exception as e:
                print(f"[OKX Positions] Failed to save selection: {e}")

        # 清空表格
        for item in self.okx_positions_tree.get_children():
            self.okx_positions_tree.delete(item)

        if not positions:
            if hasattr(self, 'okx_positions_status_label'):
                self.okx_positions_status_label.config(
                    text="当前无持仓",
                    fg=COLORS['text_muted']
                )
            return

        # 添加持仓数据
        for pos in positions:
            # 只显示有持仓的数据
            if float(pos.get('pos', '0')) == 0:
                continue

            inst_id = pos.get('instId', 'N/A')  # 交易品种
            mgn_mode = pos.get('mgnMode', 'cross')  # 保证金模式
            pos_qty = pos.get('pos', '0') or '0'  # 持仓量
            mark_px = pos.get('markPx', '0') or '0'  # 标记价格
            avg_px = pos.get('avgPx', '0') or '0'  # 开仓均价
            liq_px = pos.get('liqPx', '') or ''  # 预估强平价
            break_even_px = pos.get('bePx', '') or ''  # 盈亏平衡价
            upl = pos.get('upl', '0') or '0'  # 浮动收益
            upl_ratio = pos.get('uplRatio', '0') or '0'  # 浮动收益率
            mmr = pos.get('mmr', '0') or '0'  # 维持保证金率
            margin = pos.get('margin', '') or ''  # 保证金

            # 格式化保证金模式显示
            mgn_mode_text = '全仓' if mgn_mode == 'cross' else '逐仓'

            # 格式化浮动收益（带颜色）
            try:
                upl_float = float(upl)
                upl_ratio_float = float(upl_ratio) * 100
                upl_text = f"${upl_float:.2f} ({upl_ratio_float:+.2f}%)"
                upl_color = COLORS['profit'] if upl_float >= 0 else COLORS['loss']
            except:
                upl_text = upl
                upl_color = COLORS['text_primary']

            # 格式化维持保证金率
            try:
                mmr_float = float(mmr)
                mmr_text = f"{mmr_float:.4f}"
            except:
                mmr_text = mmr

            values = (
                inst_id,
                mgn_mode_text,  # 保证金模式
                pos_qty,
                f"${float(mark_px):.4f}" if mark_px and mark_px != '0' else 'N/A',
                f"${float(avg_px):.4f}" if avg_px and avg_px != '0' else 'N/A',
                f"${float(liq_px):.4f}" if liq_px and liq_px != '0' else 'N/A',
                f"${float(break_even_px):.4f}" if break_even_px and break_even_px != 'N/A' and break_even_px != '0' else 'N/A',
                upl_text,
                mmr_text,
                f"${float(margin):.2f}" if margin and margin != '0' else 'N/A'
            )

            # 插入行并设置标签
            item_id = self.okx_positions_tree.insert('', tk.END, values=values)

            # 根据盈亏设置行颜色
            try:
                if float(upl) > 0:
                    self.okx_positions_tree.item(item_id, tags=('profit',))
                elif float(upl) < 0:
                    self.okx_positions_tree.item(item_id, tags=('loss',))
            except:
                pass

        # 配置标签颜色
        self.okx_positions_tree.tag_configure('profit', foreground=COLORS['profit'])
        self.okx_positions_tree.tag_configure('loss', foreground=COLORS['loss'])

        # 恢复之前的选中状态
        if selected_inst_id and selected_mgn_mode:
            try:
                for item in self.okx_positions_tree.get_children():
                    values = self.okx_positions_tree.item(item)['values']
                    if values and len(values) >= 2:
                        item_inst_id = values[0]
                        item_mgn_mode = 'cross' if values[1] == '全仓' else 'isolated'
                        # 匹配交易品种和保证金模式
                        if item_inst_id == selected_inst_id and item_mgn_mode == selected_mgn_mode:
                            self.okx_positions_tree.selection_set(item)
                            self.okx_positions_tree.see(item)  # 滚动到可见区域
                            break
            except Exception as e:
                print(f"[OKX Positions] Failed to restore selection: {e}")

        # 更新状态
        pos_count = len([p for p in positions if float(p.get('pos', '0')) != 0])
        if hasattr(self, 'okx_positions_status_label'):
            self.okx_positions_status_label.config(
                text=f"✓ 共 {pos_count} 个持仓 | 更新时间: {datetime.now().strftime('%H:%M:%S')}",
                fg=COLORS['success']
            )

    def toggle_okx_positions_auto_refresh(self):
        """切换持仓自动刷新"""
        if self.okx_positions_auto_refresh.get():
            print("[OKX Positions] Real-time refresh enabled (2s)")
            self.start_okx_positions_auto_refresh()
        else:
            print("[OKX Positions] Auto-refresh disabled")

    def start_okx_positions_auto_refresh(self):
        """启动持仓自动刷新"""
        if not self.okx_positions_auto_refresh.get():
            return

        # 刷新持仓
        self.refresh_okx_positions()

        # 2秒后继续刷新（实时更新）
        if self.okx_positions_auto_refresh.get():
            self.root.after(2000, self.start_okx_positions_auto_refresh)

    def close_selected_position(self):
        """平仓选中的持仓"""
        # 获取选中的行
        selection = self.okx_positions_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要平仓的持仓")
            return

        # 获取持仓数据
        item = selection[0]
        values = self.okx_positions_tree.item(item, 'values')

        inst_id = values[0]  # 交易品种
        mgn_mode_text = values[1]  # 保证金模式
        pos_qty = values[2]  # 持仓量

        # 确认平仓
        confirm_msg = f"确认平仓？\n\n"
        confirm_msg += f"交易对: {inst_id}\n"
        confirm_msg += f"保证金模式: {mgn_mode_text}\n"
        confirm_msg += f"持仓量: {pos_qty}\n\n"
        confirm_msg += f"{'[模拟盘]' if self.okx_config.get('is_demo') else '[实盘]'}"

        if not messagebox.askyesno("确认平仓", confirm_msg):
            return

        # 获取持仓完整数据以确定保证金模式
        pos_result = self.okx_trader.get_positions(inst_type="SWAP", inst_id=inst_id)
        if pos_result.get('code') != '0':
            messagebox.showerror("失败", f"无法获取持仓信息: {pos_result.get('msg')}")
            return

        positions_data = pos_result.get('data', [])
        if not positions_data:
            messagebox.showerror("失败", "未找到该持仓")
            return

        # 找到对应的持仓记录
        position = None
        for pos in positions_data:
            if float(pos.get('pos', '0')) != 0:
                position = pos
                break

        if not position:
            messagebox.showerror("失败", "持仓数量为0")
            return

        # 执行平仓（市价单，reduce_only=True）
        try:
            # 读取持仓的保证金模式
            mgn_mode = position.get('mgnMode', 'cross')  # 'cross' 或 'isolated'

            # 判断方向：正数为多仓，需要卖出平仓；负数为空仓，需要买入平仓
            pos_qty_float = float(pos_qty)
            if pos_qty_float > 0:
                side = 'sell'  # 平多
                size = str(pos_qty_float)
            else:
                side = 'buy'   # 平空
                size = str(abs(pos_qty_float))  # 取绝对值

            print(f"[OKX] Closing position: {inst_id} {side} {size} contracts, mode: {mgn_mode}")

            result = self.okx_trader.place_market_order(
                inst_id=inst_id,
                side=side,
                size=size,
                trade_mode=mgn_mode,  # 使用持仓的保证金模式
                reduce_only=True  # 只减仓
            )

            if result.get('code') == '0':
                order_id = result.get('data', [{}])[0].get('ordId', 'N/A')
                print(f"[OKX] Position closed successfully: {inst_id}, orderId: {order_id}")
                messagebox.showinfo("成功", f"平仓订单已提交！\n\n订单ID: {order_id}")
                # 刷新持仓
                self.refresh_okx_positions()
            else:
                error_msg = result.get('msg', '未知错误')
                error_code = result.get('code', 'N/A')
                print(f"[OKX] Failed to close position: {inst_id}, code: {error_code}, msg: {error_msg}")
                messagebox.showerror("失败", f"平仓失败\n\n错误代码: {error_code}\n错误信息: {error_msg}")

        except Exception as e:
            print(f"[OKX] Exception in close_selected_position: {e}")
            messagebox.showerror("异常", f"平仓异常: {str(e)}")

    def close_all_positions(self):
        """全部平仓"""
        if not self.okx_trader or not self.okx_config.get('api_key'):
            messagebox.showwarning("提示", "请先配置OKX API密钥")
            return

        # 确认操作
        confirm_msg = "⚠️ 警告：将平掉所有持仓！\n\n"
        confirm_msg += "此操作不可撤销，请确认：\n\n"
        confirm_msg += f"{'[模拟盘]' if self.okx_config.get('is_demo') else '[实盘]'}"

        if not messagebox.askyesno("确认全部平仓", confirm_msg):
            return

        # 获取所有持仓
        result = self.okx_trader.get_positions(inst_type="SWAP")

        if result.get('code') != '0':
            messagebox.showerror("失败", f"获取持仓失败: {result.get('msg')}")
            return

        positions = result.get('data', [])
        positions_to_close = [p for p in positions if float(p.get('pos', '0')) != 0]

        if not positions_to_close:
            messagebox.showinfo("提示", "当前无持仓")
            return

        # 按保证金模式和币种分组持仓
        # Key: (inst_id, mgn_mode), Value: {'qty': total_qty, 'data': position_data}
        grouped_positions = {}
        for pos in positions_to_close:
            inst_id = pos.get('instId')
            mgn_mode = pos.get('mgnMode', 'cross')  # 获取保证金模式
            pos_qty = float(pos.get('pos', '0'))

            key = (inst_id, mgn_mode)

            # 如果该键已存在，累加持仓量（考虑多空方向）
            if key in grouped_positions:
                existing_qty = grouped_positions[key]['qty']
                grouped_positions[key]['qty'] = existing_qty + pos_qty
            else:
                grouped_positions[key] = {
                    'qty': pos_qty,
                    'data': pos
                }

        print(f"[OKX] Total unique positions to close: {len(grouped_positions)}")

        # 逐个平仓
        success_count = 0
        fail_count = 0

        for (inst_id, mgn_mode), pos_info in grouped_positions.items():
            try:
                pos_qty = pos_info['qty']

                # 如果累计持仓为0，跳过
                if pos_qty == 0:
                    print(f"[OKX] Skipping {inst_id} ({mgn_mode}): net position is 0")
                    continue

                if pos_qty > 0:
                    side = 'sell'
                    size = str(pos_qty)
                else:
                    side = 'buy'
                    size = str(abs(pos_qty))

                print(f"[OKX] Closing {inst_id}: {side} {size} contracts, mode: {mgn_mode}")

                close_result = self.okx_trader.place_market_order(
                    inst_id=inst_id,
                    side=side,
                    size=size,
                    trade_mode=mgn_mode,  # 使用持仓的保证金模式
                    reduce_only=True
                )

                if close_result.get('code') == '0':
                    success_count += 1
                    print(f"[OKX] Closed position: {inst_id}")
                else:
                    fail_count += 1
                    error_msg = close_result.get('msg', 'Unknown error')
                    print(f"[OKX] Failed to close {inst_id}: {error_msg}")

                # 避免请求过快
                time.sleep(0.3)

            except Exception as e:
                fail_count += 1
                print(f"[OKX] Exception closing {inst_id}: {e}")

        # 显示结果
        result_msg = f"平仓完成！\n\n"
        result_msg += f"成功: {success_count}\n"
        result_msg += f"失败: {fail_count}"

        messagebox.showinfo("结果", result_msg)

        # 刷新持仓
        self.refresh_okx_positions()

    def show_set_tpsl_window(self):
        """显示设置止盈止损窗口"""
        try:
            if not self.okx_trader or not self.okx_config.get('api_key'):
                messagebox.showwarning("提示", "请先配置OKX API密钥")
                return

            # 获取选中的持仓
            selected = self.okx_positions_tree.selection()
            if not selected:
                messagebox.showwarning("提示", "请先选择一个持仓")
                return

            # 获取选中行的数据
            item = self.okx_positions_tree.item(selected[0])
            values = item['values']

            if not values:
                messagebox.showerror("错误", "无法获取持仓数据")
                return
        except Exception as e:
            print(f"[OKX TP/SL] Error at start: {e}")
            messagebox.showerror("错误", f"获取持仓数据异常: {str(e)}")
            return

        # 解析持仓数据
        inst_id = values[0]  # 交易品种
        mgn_mode_text = values[1]  # 保证金模式
        pos_qty = values[2]  # 持仓量
        mark_px = values[3]  # 标记价格
        avg_px = values[4]   # 开仓均价

        # 调试输出
        print(f"[OKX TP/SL] Selected position: {inst_id}")
        print(f"[OKX TP/SL] Values: {values}")
        print(f"[OKX TP/SL] mark_px: {mark_px}, avg_px: {avg_px}")

        # 从API重新获取持仓数据以获得准确的价格
        try:
            pos_result = self.okx_trader.get_positions(inst_type="SWAP", inst_id=inst_id)
            if pos_result.get('code') != '0':
                messagebox.showerror("失败", f"无法获取持仓信息: {pos_result.get('msg')}")
                return

            positions_data = pos_result.get('data', [])
            if not positions_data:
                messagebox.showerror("失败", "未找到该持仓")
                return

            # 找到对应的持仓记录
            position = None
            for pos in positions_data:
                if float(pos.get('pos', '0')) != 0:
                    position = pos
                    break

            if not position:
                messagebox.showerror("失败", "持仓数量为0")
                return

            # 从API数据中获取准确的价格
            pos_qty_float = float(position.get('pos', '0'))
            mark_px_clean = position.get('markPx', '0')
            avg_px_clean = position.get('avgPx', '0')

            if pos_qty_float == 0:
                messagebox.showwarning("提示", "该持仓数量为0")
                return

            is_long = pos_qty_float > 0

            # 获取实际的持仓方向模式
            actual_pos_side = position.get('posSide', 'net')

            # 根据持仓方向模式设置参数
            if actual_pos_side == 'net':
                # 非双向持仓模式，pos_side 为空
                pos_side = ""
            else:
                # 双向持仓模式
                pos_side = "long" if is_long else "short"

            close_side = "sell" if is_long else "buy"

            print(f"[OKX TP/SL] API data - pos: {pos_qty_float}, mark: {mark_px_clean}, avg: {avg_px_clean}")
            print(f"[OKX TP/SL] Position mode - actual_pos_side: {actual_pos_side}, pos_side for order: '{pos_side}'")

        except Exception as e:
            print(f"[OKX TP/SL] Error getting position data: {e}")
            messagebox.showerror("错误", f"获取持仓数据失败: {str(e)}")
            return

        # 创建设置窗口
        tpsl_window = tk.Toplevel(self.root)
        tpsl_window.title("设置止盈止损")
        tpsl_window.geometry("600x700")  # 增大窗口尺寸
        tpsl_window.configure(bg=COLORS['bg_primary'])
        tpsl_window.resizable(True, True)  # 允许调整大小

        # 标题
        title_label = tk.Label(
            tpsl_window,
            text="🎯 设置止盈止损",
            font=FONTS['title'],
            bg=COLORS['bg_primary'],
            fg=COLORS['text_primary']
        )
        title_label.pack(pady=20)

        # 持仓信息框
        info_frame = tk.Frame(tpsl_window, bg=COLORS['bg_secondary'], relief=tk.RIDGE, bd=2)
        info_frame.pack(fill=tk.X, padx=20, pady=10)

        info_text = f"""持仓信息:

交易品种: {inst_id}
保证金模式: {mgn_mode_text}
持仓方向: {'做多 (Long)' if is_long else '做空 (Short)'}
持仓量: {pos_qty_float}
标记价格: ${mark_px_clean}
开仓均价: ${avg_px_clean}
"""
        info_label = tk.Label(
            info_frame,
            text=info_text,
            font=FONTS['body'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary'],
            justify=tk.LEFT,
            wraplength=550,  # 自动换行
            anchor='w'
        )
        info_label.pack(padx=15, pady=15, fill=tk.BOTH, expand=True)

        # 输入框架
        input_frame = tk.Frame(tpsl_window, bg=COLORS['bg_primary'])
        input_frame.pack(fill=tk.X, padx=20, pady=10)

        # 止盈价格
        tp_label = tk.Label(
            input_frame,
            text="止盈价格 (Take Profit):",
            font=FONTS['body'],
            bg=COLORS['bg_primary'],
            fg=COLORS['text_primary']
        )
        tp_label.grid(row=0, column=0, sticky=tk.W, pady=10)

        tp_entry = tk.Entry(
            input_frame,
            font=FONTS['body_bold'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary'],
            insertbackground=COLORS['text_primary'],
            relief=tk.SOLID,
            bd=2,
            width=30
        )
        tp_entry.grid(row=0, column=1, pady=15, padx=10, sticky='ew')

        # 止盈提示
        tp_hint = tk.Label(
            input_frame,
            text=f"({'>' if is_long else '<'} {mark_px_clean})",
            font=FONTS['small'],
            bg=COLORS['bg_primary'],
            fg=COLORS['text_muted']
        )
        tp_hint.grid(row=0, column=2, pady=10)

        # 止损价格
        sl_label = tk.Label(
            input_frame,
            text="止损价格 (Stop Loss):",
            font=FONTS['body'],
            bg=COLORS['bg_primary'],
            fg=COLORS['text_primary']
        )
        sl_label.grid(row=1, column=0, sticky=tk.W, pady=10)

        sl_entry = tk.Entry(
            input_frame,
            font=FONTS['body_bold'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary'],
            insertbackground=COLORS['text_primary'],
            relief=tk.SOLID,
            bd=2,
            width=30
        )
        sl_entry.grid(row=1, column=1, pady=15, padx=10, sticky='ew')

        # 止损提示
        sl_hint = tk.Label(
            input_frame,
            text=f"({'<' if is_long else '>'} {mark_px_clean})",
            font=FONTS['small'],
            bg=COLORS['bg_primary'],
            fg=COLORS['text_muted']
        )
        sl_hint.grid(row=1, column=2, pady=10)

        # 提示信息
        hint_frame = tk.Frame(tpsl_window, bg=COLORS['bg_tertiary'], relief=tk.FLAT, bd=1)
        hint_frame.pack(fill=tk.X, padx=20, pady=10)

        hint_text = """
💡 提示:
• 可以只设置止盈或只设置止损
• 两者都设置时将使用OCO订单（双向触发）
• 触发后将使用市价单平仓
• 留空表示不设置该项
"""
        hint_label = tk.Label(
            hint_frame,
            text=hint_text,
            font=FONTS['small'],
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_secondary'],
            justify=tk.LEFT
        )
        hint_label.pack(padx=15, pady=10)

        # 按钮框架
        button_frame = tk.Frame(tpsl_window, bg=COLORS['bg_primary'])
        button_frame.pack(fill=tk.X, padx=20, pady=20)

        def submit_tpsl():
            """提交止盈止损订单"""
            tp_price = tp_entry.get().strip()
            sl_price = sl_entry.get().strip()

            if not tp_price and not sl_price:
                messagebox.showwarning("提示", "请至少设置止盈或止损价格")
                return

            # 验证价格格式
            try:
                mark_price_float = float(mark_px_clean.replace('$', '').replace(',', ''))

                if tp_price:
                    tp_float = float(tp_price)
                    # 验证止盈逻辑
                    if is_long and tp_float <= mark_price_float:
                        messagebox.showerror("错误", "做多时，止盈价格必须高于当前价格")
                        return
                    if not is_long and tp_float >= mark_price_float:
                        messagebox.showerror("错误", "做空时，止盈价格必须低于当前价格")
                        return

                if sl_price:
                    sl_float = float(sl_price)
                    # 验证止损逻辑
                    if is_long and sl_float >= mark_price_float:
                        messagebox.showerror("错误", "做多时，止损价格必须低于当前价格")
                        return
                    if not is_long and sl_float <= mark_price_float:
                        messagebox.showerror("错误", "做空时，止损价格必须高于当前价格")
                        return

            except ValueError:
                messagebox.showerror("错误", "价格格式不正确，请输入数字")
                return

            # 确认提交
            confirm_msg = f"确认设置止盈止损？\n\n"
            confirm_msg += f"交易品种: {inst_id}\n"
            confirm_msg += f"持仓方向: {'做多' if is_long else '做空'}\n"
            confirm_msg += f"持仓量: {pos_qty}\n\n"
            if tp_price:
                confirm_msg += f"止盈价格: ${tp_price}\n"
            if sl_price:
                confirm_msg += f"止损价格: ${sl_price}\n"
            confirm_msg += f"\n{'[模拟盘]' if self.okx_config.get('is_demo') else '[实盘]'}"

            if not messagebox.askyesno("确认", confirm_msg):
                return

            # 提交订单
            try:
                # 获取持仓的保证金模式
                mgn_mode = position.get('mgnMode', 'cross')

                print(f"[OKX TP/SL] Submitting order:")
                print(f"  inst_id: {inst_id}")
                print(f"  side: {close_side}")
                print(f"  size: {abs(pos_qty_float)}")
                print(f"  tp_price: {tp_price if tp_price else 'None'}")
                print(f"  sl_price: {sl_price if sl_price else 'None'}")
                print(f"  trade_mode: {mgn_mode}")
                print(f"  pos_side: {pos_side}")

                result = self.okx_trader.place_tp_sl_order(
                    inst_id=inst_id,
                    side=close_side,
                    size=str(abs(pos_qty_float)),
                    tp_price=tp_price if tp_price else "",
                    sl_price=sl_price if sl_price else "",
                    trade_mode=mgn_mode,  # 使用持仓的保证金模式
                    pos_side=pos_side
                )

                print(f"[OKX TP/SL] API Response: {result}")

                if result.get('code') == '0':
                    order_data = result.get('data', [{}])[0]
                    algo_id = order_data.get('algoId', 'N/A')
                    print(f"[OKX TP/SL] Success! Algo ID: {algo_id}")
                    messagebox.showinfo("成功", f"止盈止损订单已设置！\n\n算法订单ID: {algo_id}")
                    tpsl_window.destroy()
                else:
                    error_code = result.get('code', 'N/A')
                    error_msg = result.get('msg', '未知错误')
                    print(f"[OKX TP/SL] Failed! Code: {error_code}, Msg: {error_msg}")
                    messagebox.showerror("失败", f"设置失败\n\n错误代码: {error_code}\n错误信息: {error_msg}")

            except Exception as e:
                print(f"[OKX TP/SL] Exception: {e}")
                import traceback
                traceback.print_exc()
                messagebox.showerror("异常", f"设置异常: {str(e)}")

        # 确认按钮
        submit_btn = tk.Button(
            button_frame,
            text="✓ 确认设置",
            command=submit_tpsl,
            bg=COLORS['success'],
            fg=COLORS['text_primary'],
            font=FONTS['heading'],  # 使用更大的字体
            activebackground='#059669',
            relief=tk.RAISED,
            bd=2,
            padx=40,
            pady=15,
            cursor='hand2'
        )
        submit_btn.pack(side=tk.LEFT, padx=15, pady=10)

        # 取消按钮
        cancel_btn = tk.Button(
            button_frame,
            text="✗ 取消",
            command=tpsl_window.destroy,
            bg=COLORS['loss'],
            fg=COLORS['text_primary'],
            font=FONTS['heading'],  # 使用更大的字体
            activebackground='#dc2626',
            relief=tk.RAISED,
            bd=2,
            padx=40,
            pady=15,
            cursor='hand2'
        )
        cancel_btn.pack(side=tk.LEFT, padx=15, pady=10)

        print(f"[OKX TP/SL] Window created with buttons")

    # ==================== OKX 委托单管理相关方法 ====================

    def refresh_okx_orders(self):
        """刷新OKX委托单"""
        if not self.okx_trader:
            messagebox.showerror("错误", "OKX交易未配置！")
            return

        print("[OKX Orders] Refreshing orders...")
        if hasattr(self, 'okx_orders_status_label'):
            self.okx_orders_status_label.config(
                text="正在刷新...",
                fg=COLORS['text_muted']
            )

        # 在后台线程中获取数据
        def fetch_orders():
            try:
                # 获取普通委托单
                pending_result = self.okx_trader.get_pending_orders(inst_type="SWAP")
                pending_orders = pending_result.get('data', []) if pending_result.get('code') == '0' else []
                print(f"[OKX Orders] Pending orders result: code={pending_result.get('code')}, count={len(pending_orders)}")

                # 获取策略委托单（止盈止损等）
                print("[OKX Orders] Fetching algo orders...")
                algo_result = self.okx_trader.get_algo_orders(inst_type="SWAP")
                algo_orders = algo_result.get('data', []) if algo_result.get('code') == '0' else []
                print(f"[OKX Orders] Algo orders result: code={algo_result.get('code')}, count={len(algo_orders)}")

                # 如果API调用失败，打印错误信息
                if algo_result.get('code') != '0':
                    print(f"[OKX Orders] Algo orders API failed: {algo_result.get('msg', 'Unknown error')}")
                elif len(algo_orders) == 0:
                    print(f"[OKX Orders] No algo orders found")

                # 调试：打印策略委托单的详细信息
                if algo_orders:
                    print(f"[OKX Orders] First algo order sample:")
                    import pprint
                    pprint.pprint(algo_orders[0])

                # 合并所有委托单
                all_orders = []

                # 处理普通委托单
                for order in pending_orders:
                    all_orders.append({
                        'type': 'normal',
                        'data': order
                    })

                # 处理策略委托单
                for order in algo_orders:
                    all_orders.append({
                        'type': 'algo',
                        'data': order
                    })

                # 在主线程中更新UI
                self.root.after(0, lambda: self.update_orders_table(all_orders))

            except Exception as e:
                print(f"[OKX Orders] Error: {e}")
                import traceback
                traceback.print_exc()
                if hasattr(self, 'okx_orders_status_label'):
                    self.root.after(0, lambda: self.okx_orders_status_label.config(
                        text=f"刷新失败: {str(e)}",
                        fg=COLORS['loss']
                    ))

        thread = threading.Thread(target=fetch_orders)
        thread.daemon = True
        thread.start()

    def update_orders_table(self, orders):
        """更新委托单表格"""
        # 保存当前选中的委托单（用于刷新后恢复选中状态）
        selected_order_id = None
        selected_items = self.okx_orders_tree.selection()
        if selected_items:
            try:
                item = self.okx_orders_tree.item(selected_items[0])
                values = item['values']
                if values and len(values) >= 9:
                    selected_order_id = values[8]  # 订单ID
            except Exception as e:
                print(f"[OKX Orders] Failed to save selection: {e}")

        # 清空表格
        for item in self.okx_orders_tree.get_children():
            self.okx_orders_tree.delete(item)

        if not orders:
            if hasattr(self, 'okx_orders_status_label'):
                self.okx_orders_status_label.config(
                    text="当前无委托",
                    fg=COLORS['text_muted']
                )
            return

        # 添加委托单数据
        for order_info in orders:
            order_type = order_info['type']
            order = order_info['data']

            if order_type == 'normal':
                # 普通委托单
                inst_id = order.get('instId', 'N/A')
                ord_type = order.get('ordType', 'limit')  # limit, market, etc.
                side = order.get('side', 'buy')
                px = order.get('px', '0')
                sz = order.get('sz', '0')
                filled_sz = order.get('accFillSz', '0')
                state = order.get('state', 'live')
                c_time = order.get('cTime', '0')
                ord_id = order.get('ordId', 'N/A')

                # 委托类型映射
                type_map = {
                    'limit': '限价',
                    'market': '市价',
                    'post_only': '只做Maker',
                    'fok': 'FOK',
                    'ioc': 'IOC',
                    'optimal_limit_ioc': '最优限价IOC'
                }
                type_text = type_map.get(ord_type, ord_type)

                # 方向映射
                side_text = '买入' if side == 'buy' else '卖出'

                # 状态映射
                state_map = {
                    'live': '未成交',
                    'partially_filled': '部分成交',
                    'filled': '完全成交',
                    'canceled': '已撤销'
                }
                state_text = state_map.get(state, state)

                # 格式化时间
                try:
                    timestamp = int(c_time) / 1000
                    time_str = datetime.fromtimestamp(timestamp).strftime('%m-%d %H:%M:%S')
                except:
                    time_str = 'N/A'

                # 格式化价格
                if px and px != '0' and px != '-1':
                    price_text = f"${float(px):.4f}"
                else:
                    price_text = '市价'

                values = (
                    type_text,
                    inst_id,
                    side_text,
                    price_text,
                    sz,
                    filled_sz,
                    state_text,
                    time_str,
                    ord_id
                )

            elif order_type == 'algo':
                # 策略委托单（止盈止损等）
                inst_id = order.get('instId', 'N/A')
                ord_type = order.get('ordType', 'conditional')
                side = order.get('side', 'buy')
                sz = order.get('sz', '0')
                state = order.get('state', 'live')
                c_time = order.get('cTime', '0')
                algo_id = order.get('algoId', 'N/A')

                # 获取触发价格
                tp_trigger = order.get('tpTriggerPx', '')
                sl_trigger = order.get('slTriggerPx', '')

                # 委托类型映射
                type_map = {
                    'conditional': '止盈止损',
                    'oco': '双向止盈止损',
                    'trigger': '计划委托',
                    'move_order_stop': '移动止盈止损',
                    'iceberg': '冰山委托',
                    'twap': 'TWAP'
                }
                type_text = type_map.get(ord_type, ord_type)

                # 方向映射
                side_text = '买入' if side == 'buy' else '卖出'

                # 状态映射
                state_map = {
                    'live': '等待触发',
                    'effective': '已生效',
                    'canceled': '已撤销',
                    'order_failed': '委托失败'
                }
                state_text = state_map.get(state, state)

                # 格式化时间
                try:
                    timestamp = int(c_time) / 1000
                    time_str = datetime.fromtimestamp(timestamp).strftime('%m-%d %H:%M:%S')
                except:
                    time_str = 'N/A'

                # 格式化触发价格
                if tp_trigger and sl_trigger:
                    price_text = f"TP:{float(tp_trigger):.2f}/SL:{float(sl_trigger):.2f}"
                elif tp_trigger:
                    price_text = f"TP: ${float(tp_trigger):.4f}"
                elif sl_trigger:
                    price_text = f"SL: ${float(sl_trigger):.4f}"
                else:
                    price_text = 'N/A'

                values = (
                    type_text,
                    inst_id,
                    side_text,
                    price_text,
                    sz,
                    'N/A',  # 策略单没有已成交量
                    state_text,
                    time_str,
                    algo_id
                )

            # 插入行
            item_id = self.okx_orders_tree.insert('', tk.END, values=values)

            # 根据方向设置行颜色
            if side == 'buy':
                self.okx_orders_tree.item(item_id, tags=('buy',))
            else:
                self.okx_orders_tree.item(item_id, tags=('sell',))

        # 配置标签颜色
        self.okx_orders_tree.tag_configure('buy', foreground=COLORS['profit'])
        self.okx_orders_tree.tag_configure('sell', foreground=COLORS['loss'])

        # 恢复之前的选中状态
        if selected_order_id:
            try:
                for item in self.okx_orders_tree.get_children():
                    values = self.okx_orders_tree.item(item)['values']
                    if values and len(values) >= 9:
                        item_order_id = values[8]
                        if item_order_id == selected_order_id:
                            self.okx_orders_tree.selection_set(item)
                            self.okx_orders_tree.see(item)
                            break
            except Exception as e:
                print(f"[OKX Orders] Failed to restore selection: {e}")

        # 更新状态
        if hasattr(self, 'okx_orders_status_label'):
            self.okx_orders_status_label.config(
                text=f"✓ 共 {len(orders)} 个委托 | 更新时间: {datetime.now().strftime('%H:%M:%S')}",
                fg=COLORS['success']
            )

    def cancel_selected_order(self):
        """撤销选中的委托单"""
        if not self.okx_trader:
            messagebox.showerror("错误", "OKX交易未配置！")
            return

        selection = self.okx_orders_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要撤销的委托单！")
            return

        try:
            item = self.okx_orders_tree.item(selection[0])
            values = item['values']

            order_type = values[0]  # 委托类型
            inst_id = values[1]  # 交易品种
            order_id = values[8]  # 订单ID

            # 确认撤单
            confirm = messagebox.askyesno(
                "确认撤单",
                f"确定要撤销以下委托吗？\n\n"
                f"类型: {order_type}\n"
                f"品种: {inst_id}\n"
                f"订单ID: {order_id}"
            )

            if not confirm:
                return

            print(f"[OKX Orders] Canceling order: {order_id}")

            # 判断是普通委托还是策略委托
            if order_type in ['限价', '市价', '只做Maker', 'FOK', 'IOC', '最优限价IOC']:
                # 普通委托
                result = self.okx_trader.cancel_order(inst_id=inst_id, order_id=order_id)
            else:
                # 策略委托
                result = self.okx_trader.cancel_algo_order([{
                    'algoId': order_id,
                    'instId': inst_id
                }])

            if result.get('code') == '0':
                messagebox.showinfo("成功", "委托已撤销！")
                # 刷新委托列表
                self.refresh_okx_orders()
            else:
                error_msg = result.get('msg', '未知错误')
                messagebox.showerror("失败", f"撤单失败: {error_msg}")

        except Exception as e:
            print(f"[OKX Orders] Cancel error: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("异常", f"撤单异常: {str(e)}")

    def cancel_all_orders(self):
        """全部撤单"""
        if not self.okx_trader:
            messagebox.showerror("错误", "OKX交易未配置！")
            return

        # 获取所有委托单
        all_items = self.okx_orders_tree.get_children()
        if not all_items:
            messagebox.showinfo("提示", "当前没有委托单！")
            return

        # 确认全部撤单
        confirm = messagebox.askyesno(
            "确认全部撤单",
            f"确定要撤销所有 {len(all_items)} 个委托吗？\n\n"
            "此操作不可撤销！"
        )

        if not confirm:
            return

        print(f"[OKX Orders] Canceling all {len(all_items)} orders...")

        success_count = 0
        fail_count = 0

        for item in all_items:
            try:
                values = self.okx_orders_tree.item(item)['values']
                order_type = values[0]
                inst_id = values[1]
                order_id = values[8]

                # 判断是普通委托还是策略委托
                if order_type in ['限价', '市价', '只做Maker', 'FOK', 'IOC', '最优限价IOC']:
                    result = self.okx_trader.cancel_order(inst_id=inst_id, order_id=order_id)
                else:
                    result = self.okx_trader.cancel_algo_order([{
                        'algoId': order_id,
                        'instId': inst_id
                    }])

                if result.get('code') == '0':
                    success_count += 1
                else:
                    fail_count += 1

            except Exception as e:
                print(f"[OKX Orders] Failed to cancel {order_id}: {e}")
                fail_count += 1

        # 刷新委托列表
        self.refresh_okx_orders()

        # 显示结果
        messagebox.showinfo(
            "撤单完成",
            f"撤单完成！\n\n"
            f"成功: {success_count} 个\n"
            f"失败: {fail_count} 个"
        )

    def toggle_okx_orders_auto_refresh(self):
        """切换委托单自动刷新"""
        if self.okx_orders_auto_refresh.get():
            print("[OKX Orders] Real-time refresh enabled (2s)")
            self.start_okx_orders_auto_refresh()
        else:
            print("[OKX Orders] Auto-refresh disabled")

    def start_okx_orders_auto_refresh(self):
        """启动委托单自动刷新"""
        if not self.okx_orders_auto_refresh.get():
            return

        # 刷新委托单
        self.refresh_okx_orders()

        # 2秒后继续刷新（实时更新）
        if self.okx_orders_auto_refresh.get():
            self.root.after(2000, self.start_okx_orders_auto_refresh)

    def toggle_okx_auto_refresh(self):
        """切换自动刷新"""
        if self.okx_auto_refresh.get():
            self.start_okx_auto_refresh()
        else:
            # 停止自动刷新（下次调用时不会继续）
            pass

    def start_okx_auto_refresh(self):
        """启动自动刷新"""
        if self.okx_auto_refresh.get():
            self.refresh_okx_data()
            # 递归调用
            self.root.after(self.okx_refresh_interval, self.start_okx_auto_refresh)

    # ==================== 主界面自动刷新功能 ====================

    def toggle_main_auto_refresh(self):
        """切换主界面自动刷新"""
        if self.main_auto_refresh.get():
            print("✓ 启动主界面自动刷新（每15分钟）")
            self.start_main_auto_refresh()
        else:
            print("✓ 停止主界面自动刷新")

    def start_main_auto_refresh(self):
        """启动主界面自动刷新定时器"""
        if not self.main_auto_refresh.get():
            return

        print(f"===== 主界面自动刷新 =====")
        print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 执行刷新（在新线程中）
        if not self.is_loading:
            thread = threading.Thread(target=self.fetch_data)
            thread.daemon = True
            thread.start()
        else:
            print("⚠️ 正在加载数据，跳过本次刷新")

        # 继续下一次刷新（15分钟后）
        if self.main_auto_refresh.get():
            next_refresh_time = datetime.now() + timedelta(milliseconds=self.main_refresh_interval)
            print(f"下次刷新时间: {next_refresh_time.strftime('%Y-%m-%d %H:%M:%S')}")
            self.root.after(self.main_refresh_interval, self.start_main_auto_refresh)

    # ==================== OKX交易配置相关方法 ====================

    def load_okx_config(self):
        """从文件加载OKX配置"""
        try:
            with open(self.okx_config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.okx_config.update(config)
                print("[OKX] Config loaded successfully")

                # 创建交易客户端
                self.okx_trader = OKXTrader(
                    api_key=self.okx_config['api_key'],
                    secret_key=self.okx_config['secret_key'],
                    passphrase=self.okx_config['passphrase'],
                    is_demo=self.okx_config.get('is_demo', True)
                )
        except FileNotFoundError:
            print("[OKX] Config file not found, using default config")
        except Exception as e:
            print(f"[OKX] Failed to load config: {e}")

    def save_okx_config(self):
        """保存OKX配置到文件"""
        try:
            with open(self.okx_config_file, 'w', encoding='utf-8') as f:
                json.dump(self.okx_config, f, indent=2, ensure_ascii=False)
            print("[OKX] Config saved successfully")
            return True
        except Exception as e:
            print(f"[OKX] Failed to save config: {e}")
            return False

    def show_okx_config_window(self):
        """显示OKX API配置窗口"""
        config_window = tk.Toplevel(self.root)
        config_window.title("OKX API 配置")
        config_window.geometry("600x500")
        config_window.configure(bg=COLORS['bg_primary'])

        # 主容器
        main_frame = tk.Frame(config_window, bg=COLORS['bg_primary'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 标题
        title_label = tk.Label(
            main_frame,
            text="⚙️ OKX API 交易配置",
            font=FONTS['title'],
            bg=COLORS['bg_primary'],
            fg=COLORS['text_primary']
        )
        title_label.pack(pady=(0, 20))

        # 配置表单框架
        form_frame = tk.LabelFrame(
            main_frame,
            text="API 凭证",
            font=FONTS['heading'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary'],
            padx=15,
            pady=15
        )
        form_frame.pack(fill=tk.X, pady=(0, 10))

        # API Key
        tk.Label(
            form_frame,
            text="API Key:",
            font=FONTS['body'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_secondary']
        ).grid(row=0, column=0, sticky='w', pady=5)

        api_key_entry = tk.Entry(
            form_frame,
            font=FONTS['body'],
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary'],
            insertbackground=COLORS['text_primary'],
            width=45
        )
        api_key_entry.grid(row=0, column=1, padx=(10, 0), pady=5)
        api_key_entry.insert(0, self.okx_config.get('api_key', ''))

        # Secret Key
        tk.Label(
            form_frame,
            text="Secret Key:",
            font=FONTS['body'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_secondary']
        ).grid(row=1, column=0, sticky='w', pady=5)

        secret_key_entry = tk.Entry(
            form_frame,
            font=FONTS['body'],
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary'],
            insertbackground=COLORS['text_primary'],
            show='*',
            width=45
        )
        secret_key_entry.grid(row=1, column=1, padx=(10, 0), pady=5)
        secret_key_entry.insert(0, self.okx_config.get('secret_key', ''))

        # Passphrase
        tk.Label(
            form_frame,
            text="Passphrase:",
            font=FONTS['body'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_secondary']
        ).grid(row=2, column=0, sticky='w', pady=5)

        passphrase_entry = tk.Entry(
            form_frame,
            font=FONTS['body'],
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary'],
            insertbackground=COLORS['text_primary'],
            show='*',
            width=45
        )
        passphrase_entry.grid(row=2, column=1, padx=(10, 0), pady=5)
        passphrase_entry.insert(0, self.okx_config.get('passphrase', ''))

        # 交易模式选择
        mode_frame = tk.LabelFrame(
            main_frame,
            text="交易模式",
            font=FONTS['heading'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary'],
            padx=15,
            pady=15
        )
        mode_frame.pack(fill=tk.X, pady=(0, 10))

        is_demo_var = tk.BooleanVar(value=self.okx_config.get('is_demo', True))

        demo_rb = tk.Radiobutton(
            mode_frame,
            text="🔧 模拟盘（测试用，不花真钱）",
            variable=is_demo_var,
            value=True,
            font=FONTS['body'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary'],
            selectcolor=COLORS['bg_tertiary'],
            activebackground=COLORS['bg_hover'],
            activeforeground=COLORS['text_primary']
        )
        demo_rb.pack(anchor='w', pady=5)

        real_rb = tk.Radiobutton(
            mode_frame,
            text="💰 实盘（真实交易，请谨慎）",
            variable=is_demo_var,
            value=False,
            font=FONTS['body'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['warning'],
            selectcolor=COLORS['bg_tertiary'],
            activebackground=COLORS['bg_hover'],
            activeforeground=COLORS['warning']
        )
        real_rb.pack(anchor='w', pady=5)

        # 提示信息
        tip_frame = tk.Frame(main_frame, bg=COLORS['bg_tertiary'], relief=tk.FLAT, bd=0)
        tip_frame.pack(fill=tk.X, pady=(0, 15))

        tk.Label(
            tip_frame,
            text="💡 如何获取OKX API密钥：\n" +
                 "1. 登录OKX官网 → 个人中心 → API管理\n" +
                 "2. 创建API密钥（权限：交易）\n" +
                 "3. 建议先使用模拟盘测试功能",
            font=FONTS['small'],
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_secondary'],
            justify=tk.LEFT
        ).pack(padx=10, pady=10)

        # 按钮区域
        button_frame = tk.Frame(main_frame, bg=COLORS['bg_primary'])
        button_frame.pack(fill=tk.X)

        # 测试连接按钮
        def test_connection():
            # 临时创建trader测试
            test_trader = OKXTrader(
                api_key=api_key_entry.get().strip(),
                secret_key=secret_key_entry.get().strip(),
                passphrase=passphrase_entry.get().strip(),
                is_demo=is_demo_var.get()
            )

            success, msg = test_trader.test_connection()

            if success:
                messagebox.showinfo("连接测试", msg)
            else:
                messagebox.showerror("连接测试", msg)

        test_btn = tk.Button(
            button_frame,
            text="🔍 测试连接",
            command=test_connection,
            bg=COLORS['info'],
            fg=COLORS['text_primary'],
            font=FONTS['body_bold'],
            activebackground='#0284c7',
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=10,
            cursor='hand2'
        )
        test_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 保存按钮
        def save_config():
            self.okx_config['api_key'] = api_key_entry.get().strip()
            self.okx_config['secret_key'] = secret_key_entry.get().strip()
            self.okx_config['passphrase'] = passphrase_entry.get().strip()
            self.okx_config['is_demo'] = is_demo_var.get()

            if self.save_okx_config():
                # 重新创建交易客户端
                self.okx_trader = OKXTrader(
                    api_key=self.okx_config['api_key'],
                    secret_key=self.okx_config['secret_key'],
                    passphrase=self.okx_config['passphrase'],
                    is_demo=self.okx_config['is_demo']
                )
                messagebox.showinfo("成功", "OKX配置已保存！")
                config_window.destroy()
            else:
                messagebox.showerror("错误", "保存配置失败")

        save_btn = tk.Button(
            button_frame,
            text="💾 保存配置",
            command=save_config,
            bg=COLORS['success'],
            fg=COLORS['text_primary'],
            font=FONTS['body_bold'],
            activebackground='#059669',
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=10,
            cursor='hand2'
        )
        save_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 取消按钮
        cancel_btn = tk.Button(
            button_frame,
            text="❌ 取消",
            command=config_window.destroy,
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_secondary'],
            font=FONTS['body_bold'],
            activebackground=COLORS['bg_hover'],
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=10,
            cursor='hand2'
        )
        cancel_btn.pack(side=tk.LEFT)

    def toggle_auto_copy_trading(self):
        """切换自动跟单状态"""
        if not self.okx_trader:
            messagebox.showerror("错误", "请先配置OKX API！")
            self.show_okx_config_window()
            return

        if not self.auto_copy_trader:
            try:
                self.auto_copy_trader = AutoCopyTrader(self)
                self.add_message("自动跟单系统已初始化", "success")
            except Exception as e:
                self.add_message(f"初始化自动跟单失败: {str(e)}", "error")
                return

        if self.auto_copy_trader.is_running:
            # 停止跟单
            self.auto_copy_trader.stop()
            self.auto_copy_btn.config(
                text="🤖 启动跟单",
                bg='#6366f1'
            )
            self.add_message("自动跟单已停止", "info")

            # 停止自动刷新
            if hasattr(self, 'okx_positions_auto_refresh'):
                self.okx_positions_auto_refresh.set(False)
            if hasattr(self, 'okx_orders_auto_refresh'):
                self.okx_orders_auto_refresh.set(False)
        else:
            # 启动跟单前检查
            # 1. 检查是否已刷新数据
            if not self.data.get('timestamp'):
                messagebox.showwarning(
                    "提示",
                    "请先按照以下步骤操作：\n\n"
                    "1. 选择币种（BTC/ETH/SOL）\n"
                    "2. 选择时间筛选（7天）\n"
                    "3. 选择金额筛选（>1亿）\n"
                    "4. 点击[刷新数据]按钮\n"
                    "5. 等待数据加载完成\n"
                    "6. 再点击[启动跟单]"
                )
                self.add_message("⚠️ 请先刷新数据", "warning")
                return

            # 2. 检查表格中是否有数据
            if not self.tree.get_children():
                messagebox.showwarning(
                    "提示",
                    "当前表格中没有数据！\n\n"
                    "请检查：\n"
                    "1. 是否已点击[刷新数据]\n"
                    "2. 筛选条件是否过于严格\n"
                    "3. 当前是否有符合条件的大户"
                )
                self.add_message("⚠️ 表格中没有数据", "warning")
                return

            # 3. 确认当前筛选条件
            selected_coin = self.selected_coin.get()
            time_filter = self.time_filter.get()
            amount_filter = self.amount_filter.get()

            time_text = f"{time_filter}天" if time_filter != "all" else "全部"
            amount_text = "全部"
            if amount_filter == "5000w":
                amount_text = ">5000万"
            elif amount_filter == "1y":
                amount_text = ">1亿"

            trader_count = len(self.tree.get_children())

            # 显示确认对话框
            confirm_msg = f"即将对表格中的 {trader_count} 个大户启动自动跟单\n\n"
            confirm_msg += f"当前筛选条件：\n"
            confirm_msg += f"• 币种: {selected_coin}\n"
            confirm_msg += f"• 时间: {time_text}\n"
            confirm_msg += f"• 金额: {amount_text}\n\n"
            confirm_msg += f"确认启动吗？"

            if not messagebox.askyesno("确认启动跟单", confirm_msg):
                return

            # 启动跟单
            self.auto_copy_trader.start()
            self.auto_copy_btn.config(
                text="⏹️ 停止跟单",
                bg=COLORS['loss']
            )
            self.add_message("自动跟单已启动", "success")

            # 自动开启OKX数据自动刷新
            if hasattr(self, 'okx_positions_auto_refresh'):
                self.okx_positions_auto_refresh.set(True)
                self.start_okx_positions_auto_refresh()
            if hasattr(self, 'okx_orders_auto_refresh'):
                self.okx_orders_auto_refresh.set(True)
                self.start_okx_orders_auto_refresh()

    def show_okx_trading_window(self):
        """显示OKX手动交易窗口"""
        if not self.okx_trader or not self.okx_config.get('api_key'):
            messagebox.showwarning("提示", "请先配置OKX API密钥")
            self.show_okx_config_window()
            return

        trading_window = tk.Toplevel(self.root)
        trading_window.title("OKX 手动交易")
        trading_window.geometry("700x800")
        trading_window.configure(bg=COLORS['bg_primary'])

        # 主容器
        main_frame = tk.Frame(trading_window, bg=COLORS['bg_primary'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # 标题
        title_label = tk.Label(
            main_frame,
            text="💹 OKX 手动交易",
            font=FONTS['title'],
            bg=COLORS['bg_primary'],
            fg=COLORS['text_primary']
        )
        title_label.pack(pady=(0, 15))

        # 账户信息框
        account_frame = tk.LabelFrame(
            main_frame,
            text="📊 账户信息",
            font=FONTS['heading'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary'],
            padx=10,
            pady=10
        )
        account_frame.pack(fill=tk.X, pady=(0, 10))

        account_info_label = tk.Label(
            account_frame,
            text="点击刷新按钮查看账户信息",
            font=FONTS['body'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_secondary']
        )
        account_info_label.pack()

        def refresh_account():
            """刷新账户信息"""
            result = self.okx_trader.get_account_balance()
            if result.get('code') == '0' and result.get('data'):
                balance_data = result['data'][0]
                details = balance_data.get('details', [{}])[0]

                equity = details.get('eq', 'N/A')
                available = details.get('availEq', 'N/A')
                currency = details.get('ccy', 'USDT')

                info_text = f"💰 总权益: {equity} {currency}\n"
                info_text += f"📈 可用保证金: {available} {currency}"

                account_info_label.config(text=info_text, fg=COLORS['text_primary'])
            else:
                error_msg = result.get('msg', '获取失败')
                account_info_label.config(text=f"❌ {error_msg}", fg=COLORS['loss'])

        refresh_account_btn = tk.Button(
            account_frame,
            text="🔄 刷新",
            command=refresh_account,
            bg=COLORS['accent'],
            fg=COLORS['text_primary'],
            font=FONTS['body'],
            activebackground=COLORS['accent_hover'],
            relief=tk.FLAT,
            bd=0,
            padx=15,
            pady=5,
            cursor='hand2'
        )
        refresh_account_btn.pack(pady=5)

        # 交易表单框
        trade_frame = tk.LabelFrame(
            main_frame,
            text="📝 交易下单",
            font=FONTS['heading'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary'],
            padx=15,
            pady=15
        )
        trade_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 产品ID
        tk.Label(
            trade_frame,
            text="交易对:",
            font=FONTS['body'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_secondary']
        ).grid(row=0, column=0, sticky='w', pady=8)

        inst_id_entry = tk.Entry(
            trade_frame,
            font=FONTS['body'],
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary'],
            insertbackground=COLORS['text_primary'],
            width=30
        )
        inst_id_entry.grid(row=0, column=1, padx=(10, 0), pady=8)
        inst_id_entry.insert(0, "BTC-USDT-SWAP")

        tk.Label(
            trade_frame,
            text="(例: BTC-USDT-SWAP)",
            font=FONTS['small'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_muted']
        ).grid(row=0, column=2, padx=(5, 0))

        # 交易方向
        tk.Label(
            trade_frame,
            text="方向:",
            font=FONTS['body'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_secondary']
        ).grid(row=1, column=0, sticky='w', pady=8)

        side_var = tk.StringVar(value="buy")
        side_frame = tk.Frame(trade_frame, bg=COLORS['bg_secondary'])
        side_frame.grid(row=1, column=1, sticky='w', pady=8)

        tk.Radiobutton(
            side_frame,
            text="买入 (做多)",
            variable=side_var,
            value="buy",
            font=FONTS['body'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['profit'],
            selectcolor=COLORS['bg_tertiary'],
            activebackground=COLORS['bg_hover'],
            activeforeground=COLORS['profit']
        ).pack(side=tk.LEFT, padx=(0, 10))

        tk.Radiobutton(
            side_frame,
            text="卖出 (做空)",
            variable=side_var,
            value="sell",
            font=FONTS['body'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['loss'],
            selectcolor=COLORS['bg_tertiary'],
            activebackground=COLORS['bg_hover'],
            activeforeground=COLORS['loss']
        ).pack(side=tk.LEFT)

        # 订单类型
        tk.Label(
            trade_frame,
            text="类型:",
            font=FONTS['body'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_secondary']
        ).grid(row=2, column=0, sticky='w', pady=8)

        order_type_var = tk.StringVar(value="market")
        order_type_frame = tk.Frame(trade_frame, bg=COLORS['bg_secondary'])
        order_type_frame.grid(row=2, column=1, sticky='w', pady=8)

        tk.Radiobutton(
            order_type_frame,
            text="市价单",
            variable=order_type_var,
            value="market",
            font=FONTS['body'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary'],
            selectcolor=COLORS['bg_tertiary'],
            activebackground=COLORS['bg_hover'],
            activeforeground=COLORS['text_primary']
        ).pack(side=tk.LEFT, padx=(0, 10))

        tk.Radiobutton(
            order_type_frame,
            text="限价单",
            variable=order_type_var,
            value="limit",
            font=FONTS['body'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary'],
            selectcolor=COLORS['bg_tertiary'],
            activebackground=COLORS['bg_hover'],
            activeforeground=COLORS['text_primary']
        ).pack(side=tk.LEFT)

        # 数量
        tk.Label(
            trade_frame,
            text="数量:",
            font=FONTS['body'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_secondary']
        ).grid(row=3, column=0, sticky='w', pady=8)

        size_entry = tk.Entry(
            trade_frame,
            font=FONTS['body'],
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary'],
            insertbackground=COLORS['text_primary'],
            width=30
        )
        size_entry.grid(row=3, column=1, padx=(10, 0), pady=8)
        size_entry.insert(0, "1")

        tk.Label(
            trade_frame,
            text="(张数)",
            font=FONTS['small'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_muted']
        ).grid(row=3, column=2, padx=(5, 0))

        # 价格（限价单用）
        tk.Label(
            trade_frame,
            text="价格:",
            font=FONTS['body'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_secondary']
        ).grid(row=4, column=0, sticky='w', pady=8)

        price_entry = tk.Entry(
            trade_frame,
            font=FONTS['body'],
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary'],
            insertbackground=COLORS['text_primary'],
            width=30
        )
        price_entry.grid(row=4, column=1, padx=(10, 0), pady=8)

        tk.Label(
            trade_frame,
            text="(限价单必填)",
            font=FONTS['small'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_muted']
        ).grid(row=4, column=2, padx=(5, 0))

        # 交易模式
        tk.Label(
            trade_frame,
            text="保证金模式:",
            font=FONTS['body'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_secondary']
        ).grid(row=5, column=0, sticky='w', pady=8)

        trade_mode_var = tk.StringVar(value="cross")
        trade_mode_frame = tk.Frame(trade_frame, bg=COLORS['bg_secondary'])
        trade_mode_frame.grid(row=5, column=1, sticky='w', pady=8)

        tk.Radiobutton(
            trade_mode_frame,
            text="全仓",
            variable=trade_mode_var,
            value="cross",
            font=FONTS['body'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary'],
            selectcolor=COLORS['bg_tertiary'],
            activebackground=COLORS['bg_hover'],
            activeforeground=COLORS['text_primary']
        ).pack(side=tk.LEFT, padx=(0, 10))

        tk.Radiobutton(
            trade_mode_frame,
            text="逐仓",
            variable=trade_mode_var,
            value="isolated",
            font=FONTS['body'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary'],
            selectcolor=COLORS['bg_tertiary'],
            activebackground=COLORS['bg_hover'],
            activeforeground=COLORS['text_primary']
        ).pack(side=tk.LEFT)

        # 杠杆倍数
        tk.Label(
            trade_frame,
            text="杠杆倍数:",
            font=FONTS['body'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_secondary']
        ).grid(row=6, column=0, sticky='w', pady=8)

        leverage_frame = tk.Frame(trade_frame, bg=COLORS['bg_secondary'])
        leverage_frame.grid(row=6, column=1, columnspan=2, sticky='ew', pady=8, padx=(10, 0))

        # 杠杆倍数变量
        leverage_var = tk.IntVar(value=10)

        # 杠杆倍数输入框
        leverage_entry = tk.Entry(
            leverage_frame,
            font=FONTS['body'],
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary'],
            insertbackground=COLORS['text_primary'],
            textvariable=leverage_var,
            width=8
        )
        leverage_entry.pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(
            leverage_frame,
            text="倍",
            font=FONTS['body'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_secondary']
        ).pack(side=tk.LEFT, padx=(0, 15))

        # 杠杆倍数滑块
        leverage_scale = tk.Scale(
            leverage_frame,
            from_=1,
            to=100,
            orient=tk.HORIZONTAL,
            variable=leverage_var,
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary'],
            activebackground=COLORS['accent'],
            highlightthickness=0,
            troughcolor=COLORS['bg_tertiary'],
            length=200,
            font=FONTS['small']
        )
        leverage_scale.pack(side=tk.LEFT)

        # 快捷倍数按钮
        quick_leverage_frame = tk.Frame(trade_frame, bg=COLORS['bg_secondary'])
        quick_leverage_frame.grid(row=7, column=1, columnspan=2, sticky='w', pady=(0, 8), padx=(10, 0))

        tk.Label(
            quick_leverage_frame,
            text="快捷:",
            font=FONTS['small'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_muted']
        ).pack(side=tk.LEFT, padx=(0, 5))

        for lev in [1, 5, 10, 20, 50, 75, 100]:
            tk.Button(
                quick_leverage_frame,
                text=f"{lev}x",
                command=lambda l=lev: leverage_var.set(l),
                bg=COLORS['bg_tertiary'],
                fg=COLORS['text_primary'],
                font=FONTS['small'],
                activebackground=COLORS['accent'],
                relief=tk.FLAT,
                bd=0,
                padx=8,
                pady=2,
                cursor='hand2'
            ).pack(side=tk.LEFT, padx=2)

        # 下单按钮（放在快捷按钮下面）
        order_btn_frame = tk.Frame(trade_frame, bg=COLORS['bg_secondary'])
        order_btn_frame.grid(row=8, column=0, columnspan=3, pady=15)

        order_btn = tk.Button(
            order_btn_frame,
            text="📤 立即下单",
            command=lambda: None,  # 临时占位，后面会修改
            bg=COLORS['accent'],
            fg=COLORS['text_primary'],
            font=FONTS['body_bold'],
            activebackground=COLORS['accent_hover'],
            relief=tk.FLAT,
            bd=0,
            padx=40,
            pady=12,
            cursor='hand2'
        )
        order_btn.pack()

        # 结果显示
        result_text = scrolledtext.ScrolledText(
            trade_frame,
            wrap=tk.WORD,
            font=FONTS['body'],
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary'],
            insertbackground=COLORS['text_primary'],
            height=8
        )
        result_text.grid(row=9, column=0, columnspan=3, pady=10, sticky='ew')

        # 下单按钮
        def place_order():
            """执行下单"""
            inst_id = inst_id_entry.get().strip()
            side = side_var.get()
            order_type = order_type_var.get()
            size = size_entry.get().strip()
            price = price_entry.get().strip()
            trade_mode = trade_mode_var.get()
            leverage = leverage_var.get()

            if not inst_id or not size:
                messagebox.showwarning("提示", "请填写交易对和数量")
                return

            if order_type == "limit" and not price:
                messagebox.showwarning("提示", "限价单必须填写价格")
                return

            # 验证杠杆倍数
            if leverage < 1 or leverage > 100:
                messagebox.showwarning("提示", "杠杆倍数必须在1-100之间")
                return

            # 确认下单
            confirm_msg = f"确认下单：\n"
            confirm_msg += f"交易对: {inst_id}\n"
            confirm_msg += f"方向: {'买入' if side == 'buy' else '卖出'}\n"
            confirm_msg += f"类型: {'市价单' if order_type == 'market' else '限价单'}\n"
            confirm_msg += f"数量: {size}张\n"
            if order_type == "limit":
                confirm_msg += f"价格: {price}\n"
            confirm_msg += f"模式: {'全仓' if trade_mode == 'cross' else '逐仓'}\n"
            confirm_msg += f"杠杆: {leverage}x\n"
            confirm_msg += f"\n{'[模拟盘]' if self.okx_config.get('is_demo') else '[实盘]'}"

            if not messagebox.askyesno("确认下单", confirm_msg):
                return

            # 执行下单
            result_text.delete(1.0, tk.END)
            result_text.insert(tk.END, "正在设置杠杆倍数...\n")

            try:
                # 先设置杠杆倍数
                leverage_result = self.okx_trader.set_leverage(
                    inst_id=inst_id,
                    lever=str(leverage),
                    mgn_mode=trade_mode
                )

                if leverage_result.get('code') != '0':
                    error_msg = leverage_result.get('msg', '设置杠杆失败')
                    result_text.insert(tk.END, f"⚠️ 设置杠杆失败: {error_msg}\n")
                    result_text.insert(tk.END, "继续下单...\n")
                else:
                    result_text.insert(tk.END, f"✓ 杠杆已设置为 {leverage}x\n")

                result_text.insert(tk.END, "正在下单...\n")
                result_text.update()

                # 执行下单
                if order_type == "market":
                    result = self.okx_trader.place_market_order(
                        inst_id=inst_id,
                        side=side,
                        size=size,
                        trade_mode=trade_mode
                    )
                else:
                    result = self.okx_trader.place_limit_order(
                        inst_id=inst_id,
                        side=side,
                        size=size,
                        price=price,
                        trade_mode=trade_mode
                    )

                result_text.delete(1.0, tk.END)

                if result.get('code') == '0':
                    result_text.insert(tk.END, "✓ 下单成功！\n\n", 'success')
                    order_data = result.get('data', [{}])[0]
                    result_text.insert(tk.END, f"订单ID: {order_data.get('ordId', 'N/A')}\n")
                    result_text.insert(tk.END, f"客户单号: {order_data.get('clOrdId', 'N/A')}\n")
                    result_text.insert(tk.END, f"状态: {order_data.get('sCode', 'N/A')}\n")
                    result_text.insert(tk.END, f"消息: {order_data.get('sMsg', 'N/A')}\n")
                else:
                    result_text.insert(tk.END, f"✗ 下单失败\n\n", 'error')
                    result_text.insert(tk.END, f"错误代码: {result.get('code')}\n")
                    result_text.insert(tk.END, f"错误信息: {result.get('msg')}\n")

                # 配置tag颜色
                result_text.tag_config('success', foreground=COLORS['profit'])
                result_text.tag_config('error', foreground=COLORS['loss'])

            except Exception as e:
                result_text.delete(1.0, tk.END)
                result_text.insert(tk.END, f"✗ 异常: {str(e)}\n", 'error')
                result_text.tag_config('error', foreground=COLORS['loss'])

        # 设置下单按钮的command
        order_btn.config(command=place_order)

        # 配置网格列权重
        trade_frame.grid_columnconfigure(1, weight=1)

    def toggle_language(self):
        """切换语言"""
        self.lang.switch_language()

    def on_language_changed(self):
        """当语言改变时更新界面文本"""
        try:
            # 更新窗口标题
            self.root.title(self.lang.get_text('window_title'))

            # 更新主标题
            if hasattr(self, 'title_label'):
                self.title_label.config(text=self.lang.get_text('window_title'))

            # 更新语言切换按钮文本
            if hasattr(self, 'lang_btn'):
                btn_text = f"🌐 {self.lang.get_text('btn_language')}"
                self.lang_btn.config(text=btn_text)

            # 更新按钮文本
            if hasattr(self, 'refresh_btn'):
                self.refresh_btn.config(text=f"🔄 {self.lang.get_text('btn_refresh')}")

            if hasattr(self, 'export_btn'):
                self.export_btn.config(text=f"💾 {self.lang.get_text('btn_export')}")

            if hasattr(self, 'okx_config_btn'):
                self.okx_config_btn.config(text=f"⚙️ {self.lang.get_text('btn_okx_config')}")

            if hasattr(self, 'okx_trade_btn'):
                self.okx_trade_btn.config(text=f"💹 {self.lang.get_text('btn_manual_trade')}")

            if hasattr(self, 'auto_copy_btn'):
                # 根据当前状态决定文本
                current_text = self.auto_copy_btn.cget('text')
                if '启动' in current_text or 'Start' in current_text:
                    self.auto_copy_btn.config(text=f"🤖 {self.lang.get_text('btn_auto_copy')}")
                else:
                    self.auto_copy_btn.config(text=f"🛑 {self.lang.get_text('btn_stop_copy')}")

            # 更新筛选面板
            if hasattr(self, 'filter_coin_label'):
                self.filter_coin_label.config(text=f"📊 {self.lang.get_text('filter_coin')}")

            if hasattr(self, 'filter_time_label'):
                self.filter_time_label.config(text=f"⏰ {self.lang.get_text('filter_time')}")

            if hasattr(self, 'filter_amount_label'):
                self.filter_amount_label.config(text=f"💰 {self.lang.get_text('filter_amount')}")

            # 更新时间筛选选项
            if hasattr(self, 'time_filter_radios'):
                for rb, key in self.time_filter_radios:
                    rb.config(text=self.lang.get_text(key))

            # 更新金额筛选选项
            if hasattr(self, 'amount_filter_radios'):
                for rb, key in self.amount_filter_radios:
                    rb.config(text=self.lang.get_text(key))

            # 更新持仓表格列标题
            if hasattr(self, 'tree') and hasattr(self, 'position_table_column_keys'):
                try:
                    for i, col_key in enumerate(self.position_table_column_keys):
                        col_text = self.lang.get_text(col_key)
                        # Treeview的列是从0开始的，但我们需要用列标识符
                        col_id = f'#{i+1}'
                        self.tree.heading(col_id, text=col_text)
                except Exception as e:
                    print(f"更新表格列标题失败: {e}")

            # 如果有notebook（标签页），更新标签页名称
            if hasattr(self, 'notebook'):
                try:
                    # 获取所有标签页
                    tabs = self.notebook.tabs()
                    # 更新每个标签页的名称
                    # 注意：标签页的顺序是固定的，根据创建顺序
                    # 0: 原始数据, 1: 持仓数据, 2: OKX数据表格, 3: OKX市值热力图,
                    # 4: OKX当前持仓, 5: OKX当前委托, 6: 自动跟单监控, 7: 收藏地址
                    if len(tabs) >= 1:
                        self.notebook.tab(tabs[0], text=self.lang.get_text('tab_raw_data'))
                    if len(tabs) >= 2:
                        self.notebook.tab(tabs[1], text=self.lang.get_text('tab_position_data'))
                    if len(tabs) >= 3:
                        self.notebook.tab(tabs[2], text=self.lang.get_text('tab_okx_table'))
                    if len(tabs) >= 4:
                        self.notebook.tab(tabs[3], text=self.lang.get_text('tab_okx_heatmap'))
                    if len(tabs) >= 5:
                        self.notebook.tab(tabs[4], text=self.lang.get_text('tab_okx_analysis'))
                    if len(tabs) >= 8:
                        # 第8个标签页是收藏地址
                        self.notebook.tab(tabs[7], text=self.lang.get_text('tab_favorites'))
                except Exception as e:
                    print(f"更新标签页名称失败: {e}")

            # 更新用户详情窗口（如果存在）
            if hasattr(self, 'user_detail_window') and self.user_detail_window and self.user_detail_window.winfo_exists():
                try:
                    # 更新窗口标题
                    if hasattr(self, 'user_detail_address'):
                        self.user_detail_window.title(f"{self.lang.get_text('detail_window_title')} - {self.user_detail_address}")

                    # 更新用户地址标签
                    if hasattr(self, 'detail_ui_refs') and 'address_label' in self.detail_ui_refs:
                        label = self.detail_ui_refs['address_label']
                        current_text = label.cget('text')
                        # 提取地址部分（地址以0x开头）
                        if '0x' in current_text:
                            address = current_text[current_text.index('0x'):]
                            label.config(text=f"{self.lang.get_text('detail_user_address')} {address}")

                    # 更新控制栏
                    if 'session_tip' in self.detail_ui_refs:
                        self.detail_ui_refs['session_tip'].config(text=self.lang.get_text('detail_session_tip'))

                    if 'refresh_btn' in self.detail_ui_refs:
                        self.detail_ui_refs['refresh_btn'].config(text=f"🔄 {self.lang.get_text('detail_manual_refresh')}")

                    if 'auto_refresh_cb' in self.detail_ui_refs:
                        self.detail_ui_refs['auto_refresh_cb'].config(text=self.lang.get_text('detail_auto_refresh'))

                    if 'update_time_label' in self.detail_ui_refs:
                        if hasattr(self, 'detail_last_update_text'):
                            self.detail_ui_refs['update_time_label'].config(
                                text=f"{self.lang.get_text('detail_last_update')} {self.detail_last_update_text}"
                            )

                    # 更新盈亏统计框架标题
                    if 'pnl_frame' in self.detail_ui_refs:
                        self.detail_ui_refs['pnl_frame'].config(text=self.lang.get_text('detail_pnl_stats'))

                    # 更新盈亏统计标签
                    if 'pnl_text_labels' in self.detail_ui_refs:
                        for data_key, (label, label_key) in self.detail_ui_refs['pnl_text_labels'].items():
                            label.config(text=self.lang.get_text(label_key))

                    # 更新图表框架标题
                    if 'chart_frame' in self.detail_ui_refs:
                        self.detail_ui_refs['chart_frame'].config(text=self.lang.get_text('detail_pnl_chart'))

                    # 更新持仓框架标题
                    if 'position_frame' in self.detail_ui_refs and hasattr(self, 'detail_position_count'):
                        self.detail_ui_refs['position_frame'].config(
                            text=f"{self.lang.get_text('detail_positions')} ({self.detail_position_count})"
                        )

                    # 更新委托框架标题
                    if 'order_frame' in self.detail_ui_refs and hasattr(self, 'detail_order_count'):
                        self.detail_ui_refs['order_frame'].config(
                            text=f"{self.lang.get_text('detail_orders')} ({self.detail_order_count})"
                        )

                    # 更新交易框架标题
                    if 'trade_frame' in self.detail_ui_refs and hasattr(self, 'detail_trade_count'):
                        self.detail_ui_refs['trade_frame'].config(
                            text=f"{self.lang.get_text('detail_trades')} ({self.detail_trade_count})"
                        )

                    # 更新充提框架标题
                    if 'transfer_frame' in self.detail_ui_refs:
                        if hasattr(self, 'detail_deposit_count') and hasattr(self, 'detail_withdrawal_count'):
                            total = self.detail_deposit_count + self.detail_withdrawal_count
                            self.detail_ui_refs['transfer_frame'].config(
                                text=f"{self.lang.get_text('detail_transfers')} ({total})"
                            )

                    # 更新充提统计标签
                    if 'transfer_stats_label' in self.detail_ui_refs:
                        if hasattr(self, 'detail_deposit_count') and hasattr(self, 'detail_withdrawal_count'):
                            self.detail_ui_refs['transfer_stats_label'].config(
                                text=self.lang.get_text('detail_transfer_stats',
                                    deposit=self.detail_deposit_count,
                                    withdrawal=self.detail_withdrawal_count)
                            )

                except Exception as e:
                    print(f"更新详情窗口失败: {e}")

            # 显示切换成功的消息
            lang_name = "中文" if self.lang.get_current_language() == 'zh' else "English"
            if hasattr(self, 'add_message'):
                self.add_message(f"语言已切换到 {lang_name} / Language switched to {lang_name}", "success")

        except Exception as e:
            print(f"语言切换更新UI失败: {e}")
            import traceback
            traceback.print_exc()


# ==================== 自动跟单管理类 ====================

class AutoCopyTrader:
    """
    自动跟单交易管理类

    功能：
    1. 筛选大户地址（7天、1亿美元）
    2. 记录跟单开始时间戳
    3. 获取OKX账户可用保证金
    4. 按张数等比例计算跟单数量
    5. 自动下单（最多50%保证金）
    6. 监控交易历史（只处理时间戳之后）
    7. 检测平仓/加仓并同步
    8. 检测止盈止损并跟随
    9. 支持多账户跟单（50%+50%）
    """

    def __init__(self, app):
        """
        初始化自动跟单管理器

        Args:
            app: HyperliquidMonitor主应用实例
        """
        self.app = app
        self.okx_trader = app.okx_trader

        # 跟单状态
        self.is_running = False
        self.followed_traders = {}  # {trader_address: TraderInfo}

        # 最小交易数量
        self.MIN_BTC_SIZE = 0.0001

        # 保证金使用限制
        self.MAX_MARGIN_RATIO = 0.5  # 单个订单最多50%

        # 刷新间隔
        self.MONITOR_INTERVAL = 10 * 1000  # 10秒（毫秒）
        self.DATA_CACHE_INTERVAL = 60  # 数据缓存时间：60秒
        self.REFRESH_INTERVAL = 15 * 60 * 1000  # 15分钟（毫秒）

        # 是否已完成初始化（首次跟单大户）
        self.initialized = False

        # 上次刷新数据的时间
        self.last_refresh_time = None

        # 数据缓存：避免频繁启动浏览器
        # {trader_address: {'data': trader_data, 'timestamp': datetime}}
        self.trader_data_cache = {}

        # 状态持久化文件
        self.state_file = 'auto_copy_state.json'

        # 已处理的订单ID（防止重复下单）
        self.processed_orders = set()  # {order_id}

        # 跟单成功计数
        self.successful_copies = 0

        # 启动时加载上次的状态
        self.load_state()

        print("[AutoCopyTrader] 初始化完成")

    def load_state(self):
        """从文件加载上次的跟单状态"""
        try:
            if not os.path.exists(self.state_file):
                print("[AutoCopyTrader] 未找到状态文件，这是首次启动")
                return

            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)

            # 加载上次会话时间
            last_session = state.get('last_session_time')
            if last_session:
                print(f"[AutoCopyTrader] 检测到上次会话: {last_session}")

            # 加载已处理的订单ID
            self.processed_orders = set(state.get('processed_orders', []))
            print(f"[AutoCopyTrader] 加载了 {len(self.processed_orders)} 个已处理订单")

            # 加载跟单成功计数
            self.successful_copies = state.get('successful_copies', 0)
            print(f"[AutoCopyTrader] 加载了跟单成功计数: {self.successful_copies}")

            # 加载跟随的大户信息
            saved_traders = state.get('followed_traders', {})
            if saved_traders:
                print(f"[AutoCopyTrader] 检测到 {len(saved_traders)} 个上次跟随的大户")

                # 询问用户是否继续还是重新开始
                from tkinter import messagebox
                result = messagebox.askyesnocancel(
                    "检测到上次跟单记录",
                    f"检测到上次会话记录：\n\n"
                    f"• 会话时间: {last_session}\n"
                    f"• 跟随大户: {len(saved_traders)}个\n"
                    f"• 已处理订单: {len(self.processed_orders)}笔\n\n"
                    f"是否继续上次的跟单？\n\n"
                    f"[是] 继续上次的跟单（避免重复下单）\n"
                    f"[否] 清除记录，重新开始\n"
                    f"[取消] 暂不启动"
                )

                if result is True:  # 继续
                    print("[AutoCopyTrader] 用户选择：继续上次跟单")
                    # 恢复跟随大户的信息（但不恢复datetime对象）
                    for addr, info in saved_traders.items():
                        # 转换时间戳字符串为datetime对象
                        start_time_str = info.get('start_time_str')
                        if start_time_str:
                            try:
                                start_timestamp = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
                            except:
                                start_timestamp = datetime.now()
                        else:
                            start_timestamp = datetime.now()

                        self.followed_traders[addr] = {
                            'start_timestamp': start_timestamp,
                            'start_time_str': start_time_str,
                            'positions': info.get('positions', []),
                            'last_trades': info.get('last_trades', []),
                            'margin_used': info.get('margin_used', 0),
                            'active': info.get('active', True)
                        }

                    self.app.add_message(
                        f"✅ 已恢复 {len(self.followed_traders)} 个大户的跟单状态",
                        "success"
                    )

                elif result is False:  # 重新开始
                    print("[AutoCopyTrader] 用户选择：清除记录，重新开始")
                    self.clear_state()
                    self.app.add_message("🔄 已清除上次记录，将重新开始", "info")

                else:  # 取消
                    print("[AutoCopyTrader] 用户选择：暂不启动")
                    # 不做任何操作

        except Exception as e:
            print(f"[AutoCopyTrader] 加载状态失败: {e}")
            import traceback
            traceback.print_exc()

    def save_state(self):
        """保存当前跟单状态到文件"""
        try:
            # 准备要保存的数据
            state = {
                'last_session_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'processed_orders': list(self.processed_orders),
                'successful_copies': self.successful_copies,
                'followed_traders': {}
            }

            # 保存跟随大户的信息（转换datetime为字符串）
            for addr, info in self.followed_traders.items():
                state['followed_traders'][addr] = {
                    'start_time_str': info.get('start_time_str', ''),
                    'positions': info.get('positions', []),
                    'last_trades': info.get('last_trades', [])[:10],  # 只保存最近10笔
                    'margin_used': info.get('margin_used', 0),
                    'active': info.get('active', True)
                }

            # 写入文件
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)

            print(f"[AutoCopyTrader] 状态已保存: {len(self.followed_traders)}个大户, "
                  f"{len(self.processed_orders)}个已处理订单")

        except Exception as e:
            print(f"[AutoCopyTrader] 保存状态失败: {e}")

    def clear_state(self):
        """清除状态文件和内存中的状态"""
        try:
            # 清除内存
            self.processed_orders.clear()
            self.followed_traders.clear()
            self.successful_copies = 0

            # 删除文件
            if os.path.exists(self.state_file):
                os.remove(self.state_file)
                print("[AutoCopyTrader] 状态文件已删除")

        except Exception as e:
            print(f"[AutoCopyTrader] 清除状态失败: {e}")

    def start(self):
        """启动自动跟单"""
        if self.is_running:
            self.app.add_message("自动跟单已在运行中", "warning")
            return

        self.is_running = True
        self.last_refresh_time = datetime.now()  # 记录启动时间
        self.app.add_message("🚀 自动跟单已启动", "success")
        print("[AutoCopyTrader] 启动自动跟单")
        print(f"[AutoCopyTrader] 将每15分钟自动刷新数据，寻找新的大单")

        # 开始主循环（仅在首次运行时筛选大户）
        self.main_loop()

    def stop(self):
        """停止自动跟单"""
        self.is_running = False
        self.initialized = False  # 重置初始化标志，下次启动时重新筛选

        # 停止前保存状态
        self.save_state()

        self.app.add_message("⏹️ 自动跟单已停止", "info")
        print("[AutoCopyTrader] 停止自动跟单")

    def main_loop(self):
        """主循环：首次筛选大户并开始跟单，之后每15分钟刷新寻找新大单"""
        if not self.is_running:
            return

        try:
            # 首次运行：筛选表格中的大户并开始跟单
            if not self.initialized:
                # 1. 从当前表格中获取大户列表
                traders = self.filter_big_traders()

                if not traders:
                    self.app.add_message("表格中没有找到大户", "warning")
                else:
                    self.app.add_message(f"找到 {len(traders)} 个符合条件的大户", "info")

                    # 2. 为每个大户创建跟单任务
                    for trader_address in traders:
                        if trader_address not in self.followed_traders:
                            self.start_following_trader(trader_address)

                # 标记为已初始化
                self.initialized = True

            # 检查是否需要15分钟刷新
            now = datetime.now()
            elapsed = (now - self.last_refresh_time).total_seconds()

            if elapsed >= 900:  # 15分钟 = 900秒
                print(f"[AutoCopyTrader] ⏰ 已过15分钟，自动刷新数据寻找新大单...")
                self.app.add_message("🔄 15分钟定时刷新：正在寻找新的大单...", "info")

                # 刷新Hyperliquid数据
                self.app.refresh_data()

                # 更新刷新时间
                self.last_refresh_time = now

                # 等待3秒让数据加载完成，然后检查新大户
                self.app.root.after(3000, self.check_new_traders)

            # 监控已跟随的大户（每次循环都执行）
            self.monitor_all_traders()

        except Exception as e:
            self.app.add_message(f"跟单系统异常: {str(e)}", "error")
            print(f"[AutoCopyTrader] 主循环异常: {e}")
            import traceback
            traceback.print_exc()

        # 10秒后继续监控和检查
        if self.is_running:
            self.app.root.after(self.MONITOR_INTERVAL, self.main_loop)

    def filter_big_traders(self):
        """
        从当前表格中获取符合条件的大户

        注意：这个方法直接读取Treeview中已经过筛选的数据
        用户需要先：
        1. 在界面上选择币种（BTC/ETH/SOL）
        2. 选择时间筛选（7天）
        3. 选择金额筛选（>1亿）
        4. 点击"刷新数据"
        5. 然后点击"启动跟单"

        Returns:
            list: 符合条件的大户地址列表
        """
        try:
            # 获取当前Treeview中显示的所有行
            traders = []

            # 遍历Treeview中的所有项
            for item in self.app.tree.get_children():
                try:
                    # 获取行的值
                    values = self.app.tree.item(item)['values']

                    # Treeview的列（参考update_display中的结构）:
                    # 0: 排名 (#)
                    # 1: 用户地址
                    # 2: 币种
                    # 3: 方向（多/空）
                    # 4: 仓位
                    # 5: 未实现盈亏(%)
                    # 6: 开仓价格
                    # 7: 爆仓价格
                    # 8: 保证金
                    # 9: 资金费
                    # 10: 当前价格
                    # 11: 开仓时间

                    if len(values) < 12:
                        continue

                    address = str(values[1]).strip()  # 用户地址

                    # 避免重复
                    if address and address not in traders:
                        traders.append(address)

                except Exception as e:
                    print(f"[AutoCopyTrader] 读取表格行失败: {e}")
                    continue

            return traders

        except Exception as e:
            print(f"[AutoCopyTrader] 获取大户列表失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    def check_new_traders(self):
        """
        检查是否有新的大户出现，并自动开始跟单
        """
        try:
            if not self.is_running:
                return

            # 获取当前表格中的所有大户
            current_traders = self.filter_big_traders()

            # 找出新出现的大户（不在已跟随列表中）
            new_traders = [addr for addr in current_traders if addr not in self.followed_traders]

            if new_traders:
                print(f"[AutoCopyTrader] 🆕 发现 {len(new_traders)} 个新大户!")
                self.app.add_message(f"🆕 发现 {len(new_traders)} 个新大户，开始跟单...", "success")

                # 为每个新大户创建跟单任务
                for trader_address in new_traders:
                    self.start_following_trader(trader_address)
            else:
                print(f"[AutoCopyTrader] ✓ 没有发现新的大户")
                self.app.add_message("✓ 15分钟刷新完成，暂无新大户", "info")

        except Exception as e:
            print(f"[AutoCopyTrader] 检查新大户失败: {e}")
            import traceback
            traceback.print_exc()

    def is_within_days(self, time_str, days):
        """
        判断时间是否在指定天数内

        Args:
            time_str: 时间字符串，如 "03:12 10-16"
            days: 天数

        Returns:
            bool: 是否在指定天数内
        """
        try:
            from datetime import datetime, timedelta

            # 解析时间字符串 "03:12 10-16"
            # 假设格式为 "HH:MM MM-DD"
            parts = time_str.strip().split()
            if len(parts) < 2:
                return False

            time_part = parts[0]  # "03:12"
            date_part = parts[1]  # "10-16"

            # 当前年份
            current_year = datetime.now().year

            # 解析月-日
            month_day = date_part.split('-')
            if len(month_day) != 2:
                return False

            month = int(month_day[0])
            day = int(month_day[1])

            # 解析时-分
            hour_min = time_part.split(':')
            if len(hour_min) != 2:
                return False

            hour = int(hour_min[0])
            minute = int(hour_min[1])

            # 构建完整时间
            trade_time = datetime(current_year, month, day, hour, minute)

            # 计算时间差
            now = datetime.now()
            delta = now - trade_time

            return delta.days <= days

        except Exception as e:
            print(f"[AutoCopyTrader] 解析时间失败: {time_str}, 错误: {e}")
            return False

    def parse_amount(self, amount_str):
        """
        解析仓位金额字符串

        Args:
            amount_str: 如 "$1.75亿 1610.93 BTC"

        Returns:
            float: 美元金额
        """
        return self.app.parse_amount(amount_str)

    def start_following_trader(self, trader_address):
        """
        开始跟随一个大户

        Args:
            trader_address: 大户地址
        """
        try:
            self.app.add_message(f"📌 开始跟随大户: {trader_address[:8]}...", "info")
            print(f"[AutoCopyTrader] 开始跟随: {trader_address}")

            # 1. 记录开始时间戳（非常重要！）
            start_timestamp = datetime.now()

            # 2. 获取OKX账户可用保证金
            available_margin = self.get_available_margin()
            if not available_margin:
                self.app.add_message("⚠️ 无法获取OKX账户余额", "error")
                return

            self.app.add_message(f"💰 可用保证金: ${available_margin:.2f}", "info")

            # 3. 获取大户当前持仓
            trader_data = self.get_trader_data(trader_address)
            if not trader_data:
                self.app.add_message("⚠️ 无法获取大户数据", "error")
                return

            # 4. 计算并执行跟单
            self.copy_trader_positions(trader_address, trader_data, available_margin)

            # 5. 保存跟单信息
            self.followed_traders[trader_address] = {
                'start_timestamp': start_timestamp,
                'start_time_str': start_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'positions': trader_data.get('positions', []),
                'last_trades': trader_data.get('trades', []),
                'margin_used': 0,  # 已使用的保证金
                'active': True
            }

            # 6. 保存状态到文件
            self.save_state()

            self.app.add_message(f"✅ 跟单任务已创建: {trader_address[:8]}...", "success")

        except Exception as e:
            self.app.add_message(f"创建跟单任务失败: {str(e)}", "error")
            print(f"[AutoCopyTrader] 开始跟随失败: {e}")
            import traceback
            traceback.print_exc()

    def get_available_margin(self):
        """
        获取OKX账户可用保证金

        Returns:
            float: 可用保证金（美元）
        """
        try:
            result = self.okx_trader.get_account_balance()
            if result.get('code') == '0' and result.get('data'):
                balance_data = result['data'][0]
                details = balance_data.get('details', [{}])[0]
                available = details.get('availEq', '0')
                return float(available)
            return None
        except Exception as e:
            print(f"[AutoCopyTrader] 获取账户余额失败: {e}")
            return None

    def get_trader_data(self, trader_address):
        """
        获取大户的详细数据（持仓、委托、交易历史）
        使用缓存机制，避免频繁启动浏览器

        Args:
            trader_address: 大户地址（简写）

        Returns:
            dict: 包含positions, open_orders, trades的字典
        """
        try:
            # 1. 检查缓存
            now = datetime.now()
            cache = self.trader_data_cache.get(trader_address)

            if cache:
                cached_time = cache['timestamp']
                elapsed = (now - cached_time).total_seconds()

                # 如果缓存还在有效期内（60秒），直接返回缓存数据
                if elapsed < self.DATA_CACHE_INTERVAL:
                    print(f"[AutoCopyTrader] 使用缓存数据: {trader_address[:8]}... (缓存时间: {elapsed:.0f}秒前)")
                    return cache['data']
                else:
                    print(f"[AutoCopyTrader] 缓存已过期: {trader_address[:8]}... ({elapsed:.0f}秒前), 重新获取数据")

            # 2. 缓存不存在或已过期，需要重新获取
            # 从user_links中获取完整URL
            user_links = self.app.data.get('user_links', {})
            url = user_links.get(trader_address)

            if not url:
                print(f"[AutoCopyTrader] 未找到用户链接: {trader_address}")
                # 尝试构建URL
                # 如果是完整地址（40位）
                if len(trader_address.replace('0x', '')) == 40:
                    url = f"https://www.coinglass.com/zh/hyperliquid/{trader_address}"
                else:
                    return None

            print(f"[AutoCopyTrader] 启动浏览器获取用户详情: {trader_address[:8]}...")
            print(f"[AutoCopyTrader] URL: {url}")

            # 3. 使用fetch_user_details_sync方法获取数据
            user_data = self.fetch_user_details_sync(url, trader_address)

            # 4. 更新缓存
            if user_data:
                self.trader_data_cache[trader_address] = {
                    'data': user_data,
                    'timestamp': now
                }
                print(f"[AutoCopyTrader] 数据已缓存: {trader_address[:8]}...")

            return user_data

        except Exception as e:
            print(f"[AutoCopyTrader] 获取用户数据失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def fetch_user_details_sync(self, url, user_address):
        """
        同步获取用户详情（不使用线程，用于跟单系统）

        Args:
            url: 用户详情页URL
            user_address: 用户地址

        Returns:
            dict: 用户详情数据
        """
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from webdriver_manager.chrome import ChromeDriverManager
        import time
        import re

        driver = None
        try:
            # 配置浏览器（无头模式 + 静默日志）
            chrome_options = Options()
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            # 抑制Chrome日志输出
            chrome_options.add_argument('--log-level=3')
            chrome_options.add_argument('--silent')

            # 将ChromeDriver日志重定向到null（抑制DevTools日志）
            import os
            service = Service(
                ChromeDriverManager().install(),
                log_path=os.devnull if os.name != 'nt' else 'NUL'
            )
            driver = webdriver.Chrome(service=service, options=chrome_options)

            # 隐藏webdriver属性
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                '''
            })

            # 访问页面
            driver.get(url)
            time.sleep(5)  # 等待页面加载

            # 初始化返回数据
            user_details = {
                'positions': [],
                'open_orders': [],
                'trades': []
            }

            # 点击标签页并提取数据的辅助函数
            def click_tab_and_extract(tab_name, data_key):
                try:
                    # 查找并点击标签
                    tab_buttons = driver.find_elements(By.CSS_SELECTOR, "button[role='tab'].MuiTab-root")
                    for tab_btn in tab_buttons:
                        btn_text = tab_btn.text.strip()
                        clean_text = re.sub(r'\([0-9]+\)', '', btn_text).strip().replace(' ', '').replace('&', '')
                        if tab_name.replace(' ', '').replace('&', '') in clean_text:
                            driver.execute_script("arguments[0].click();", tab_btn)
                            time.sleep(1.5)
                            break

                    # 提取表格数据
                    all_rows = driver.find_elements(By.CLASS_NAME, "ant-table-row")
                    visible_rows = [row for row in all_rows if row.get_attribute('aria-hidden') != 'true']

                    for row in visible_rows:
                        cells = row.find_elements(By.TAG_NAME, 'td')
                        if len(cells) == 0:
                            continue

                        if data_key == 'positions':
                            if len(cells) >= 7:
                                position = {
                                    '代币': cells[0].text.strip(),
                                    '方向': cells[1].text.strip(),
                                    '杠杆': cells[2].text.strip(),
                                    '价值': cells[3].text.strip(),
                                    '数量': cells[4].text.strip(),
                                    '开仓价格': cells[5].text.strip(),
                                    '盈亏(PnL)': cells[6].text.strip(),
                                    '资金费': cells[7].text.strip() if len(cells) > 7 else '',
                                    '爆仓价格': cells[8].text.strip() if len(cells) > 8 else ''
                                }
                                if position['代币'] and position['方向']:
                                    user_details[data_key].append(position)

                        elif data_key == 'trades':
                            if len(cells) >= 4:
                                trade = {}
                                column_names = ['交易哈希', '方向', '时间', '盈亏', '代币', '价格', '数量']
                                for i, cell in enumerate(cells):
                                    col_name = column_names[i] if i < len(column_names) else f'列{i+1}'
                                    trade[col_name] = cell.text.strip()
                                if trade.get('交易哈希') or trade.get('时间'):
                                    user_details[data_key].append(trade)

                        elif data_key == 'open_orders':
                            if len(cells) >= 4:
                                order = {}
                                column_names = ['时间', '代币', '类型', '方向', '数量', '价格', '已成交', '订单ID']
                                for i, cell in enumerate(cells):
                                    col_name = column_names[i] if i < len(column_names) else f'列{i+1}'
                                    order[col_name] = cell.text.strip()
                                if order.get('代币'):
                                    user_details[data_key].append(order)

                except Exception as e:
                    print(f"[AutoCopyTrader] 提取{tab_name}数据失败: {e}")

            # 提取各个标签页的数据
            click_tab_and_extract('仓位', 'positions')
            click_tab_and_extract('交易', 'trades')
            click_tab_and_extract('当前委托', 'open_orders')

            return user_details

        except Exception as e:
            print(f"[AutoCopyTrader] fetch_user_details_sync异常: {e}")
            import traceback
            traceback.print_exc()
            return None

        finally:
            if driver:
                driver.quit()

    def copy_trader_positions(self, trader_address, trader_data, available_margin):
        """
        复制大户的持仓

        Args:
            trader_address: 大户地址
            trader_data: 大户数据
            available_margin: 可用保证金
        """
        positions = trader_data.get('positions', [])
        if not positions:
            self.app.add_message("大户当前无持仓", "info")
            return

        # 获取当前选中的币种
        selected_coin = self.app.selected_coin.get()

        for pos in positions:
            try:
                token = pos.get('代币', '')
                if token != selected_coin:
                    continue

                # 解析持仓信息
                direction = pos.get('方向', '')  # 多/空
                size_str = pos.get('数量', '')  # "1610.93 BTC"
                entry_price_str = pos.get('开仓价格', '')  # "$108043.9"
                liq_price_str = pos.get('爆仓价格', '')  # "$88,061.07"

                # 解析数量
                size = self.parse_size(size_str)
                if not size:
                    continue

                # 计算我应该下单的数量
                my_size = self.calculate_copy_size(
                    size,
                    available_margin,
                    trader_address,
                    trader_data  # 传入trader_data
                )

                if my_size < self.MIN_BTC_SIZE:
                    self.app.add_message(f"⚠️ 计算的数量({my_size:.4f})低于最小值({self.MIN_BTC_SIZE})", "warning")
                    my_size = self.MIN_BTC_SIZE

                # 执行下单
                self.place_copy_order(
                    coin=token,
                    direction=direction,
                    size=my_size
                )

            except Exception as e:
                self.app.add_message(f"复制持仓失败: {str(e)}", "error")
                print(f"[AutoCopyTrader] 复制持仓失败: {e}")
                continue

    def parse_size(self, size_str):
        """
        解析数量字符串

        Args:
            size_str: 如 "1610.93 BTC"

        Returns:
            float: 数量
        """
        try:
            # 提取数字部分
            parts = size_str.split()
            if parts:
                return float(parts[0].replace(',', ''))
            return None
        except:
            return None

    def calculate_copy_size(self, trader_size, available_margin, trader_address, trader_data=None):
        """
        计算跟单数量（按张数等比例缩放）

        Args:
            trader_size: 大户的仓位大小（BTC数量）
            available_margin: 我的可用保证金（美元）
            trader_address: 大户地址
            trader_data: 大户数据（可选，如果没有则从followed_traders获取）

        Returns:
            float: 我应该下单的数量
        """
        try:
            # 获取大户的持仓信息，计算总价值
            if trader_data:
                # 使用传入的trader_data
                positions = trader_data.get('positions', [])
            else:
                # 从followed_traders获取
                trader_info = self.followed_traders.get(trader_address, {})
                positions = trader_info.get('positions', [])

            if not positions:
                # 如果没有持仓信息，使用简化计算
                # 假设使用50%保证金
                max_margin = available_margin * self.MAX_MARGIN_RATIO
                # 简化：假设当前价格约10万美元，使用10倍杠杆
                # 可买入数量 = (可用保证金 * 杠杆) / 价格
                # 这里我们简化为：可用保证金的50%等价于多少BTC
                estimated_price = 100000  # 假设BTC价格10万美元
                estimated_leverage = 10
                my_size = (max_margin * estimated_leverage) / estimated_price
                return max(my_size, self.MIN_BTC_SIZE)

            # 计算大户持仓总价值
            trader_total_value = 0
            selected_coin = self.app.selected_coin.get()

            for pos in positions:
                coin = pos.get('代币', '')
                if selected_coin in coin:
                    value_str = pos.get('价值', '')
                    # 解析价值，如 "$17.46万"
                    value = self.parse_position_value(value_str)
                    trader_total_value += value

            if trader_total_value <= 0:
                print(f"[AutoCopyTrader] 无法获取大户持仓价值")
                return self.MIN_BTC_SIZE

            # 计算比例：(我的可用保证金 * 50%) / 大户持仓价值
            my_max_margin = available_margin * self.MAX_MARGIN_RATIO
            ratio = my_max_margin / trader_total_value

            # 计算我应该下单的数量
            my_size = trader_size * ratio

            print(f"[AutoCopyTrader] 比例计算:")
            print(f"  大户持仓价值: ${trader_total_value:,.2f}")
            print(f"  大户数量: {trader_size}")
            print(f"  我的可用保证金: ${available_margin:,.2f}")
            print(f"  最大使用保证金(50%): ${my_max_margin:,.2f}")
            print(f"  计算比例: {ratio:.6f}")
            print(f"  计算数量: {my_size:.6f}")

            # 确保不低于最小值
            if my_size < self.MIN_BTC_SIZE:
                print(f"[AutoCopyTrader] 计算数量({my_size:.6f})低于最小值({self.MIN_BTC_SIZE})，使用最小值")
                return self.MIN_BTC_SIZE

            return my_size

        except Exception as e:
            print(f"[AutoCopyTrader] 计算跟单数量失败: {e}")
            import traceback
            traceback.print_exc()
            return self.MIN_BTC_SIZE

    def parse_position_value(self, value_str):
        """
        解析持仓价值字符串

        Args:
            value_str: 如 "$17.46万" 或 "$1.75亿"

        Returns:
            float: 美元价值
        """
        try:
            value_str = value_str.strip().replace('$', '').replace(',', '')

            if '万' in value_str:
                # 提取数字部分
                num_str = value_str.replace('万', '')
                return float(num_str) * 10000
            elif '亿' in value_str:
                num_str = value_str.replace('亿', '')
                return float(num_str) * 100000000
            else:
                # 纯数字
                return float(value_str)

        except Exception as e:
            print(f"[AutoCopyTrader] 解析价值失败: {value_str}, 错误: {e}")
            return 0

    def place_copy_order(self, coin, direction, size):
        """
        执行跟单下单

        Args:
            coin: 币种（BTC/ETH/SOL）
            direction: 方向（多/空）
            size: 数量（BTC/ETH/SOL数量，需要转换为张数）
        """
        try:
            # 构建交易对
            inst_id = f"{coin}-USDT-SWAP"

            # 方向转换
            side = "buy" if direction == "多" else "sell"

            # 转换为张数
            # BTC-USDT-SWAP: 1张 = 0.01 BTC
            # ETH-USDT-SWAP: 1张 = 0.1 ETH
            # SOL-USDT-SWAP: 1张 = 1 SOL
            contract_size_map = {
                'BTC': 0.01,   # 1张 = 0.01 BTC
                'ETH': 0.1,    # 1张 = 0.1 ETH
                'SOL': 1.0,    # 1张 = 1 SOL
            }

            contract_size = contract_size_map.get(coin, 0.01)
            size_in_contracts = int(size / contract_size)  # 转换为张数并取整

            # 确保至少1张
            if size_in_contracts < 1:
                size_in_contracts = 1

            self.app.add_message(f"📤 下单: {side.upper()} {size:.6f} {coin} ({size_in_contracts}张)", "info")
            print(f"[AutoCopyTrader] 下单: {inst_id} {side} {size:.6f} {coin} = {size_in_contracts}张")

            # 先设置杠杆倍数（默认10倍）
            try:
                leverage = 10
                leverage_result = self.okx_trader.set_leverage(
                    inst_id=inst_id,
                    lever=str(leverage),
                    mgn_mode="cross"
                )
                if leverage_result.get('code') == '0':
                    print(f"[AutoCopyTrader] 杠杆已设置为 {leverage}x")
                else:
                    # 设置杠杆失败不影响下单，继续
                    print(f"[AutoCopyTrader] 设置杠杆失败: {leverage_result.get('msg', '未知错误')}")
            except Exception as e:
                print(f"[AutoCopyTrader] 设置杠杆异常: {e}")

            # 调用OKX API下单
            result = self.okx_trader.place_market_order(
                inst_id=inst_id,
                side=side,
                size=str(size_in_contracts),  # 使用张数
                trade_mode="cross"
            )

            if result.get('code') == '0':
                order_data = result.get('data', [{}])[0]
                order_id = order_data.get('ordId', 'N/A')
                self.app.add_message(f"✅ 下单成功! 订单ID: {order_id}", "success")
                print(f"[AutoCopyTrader] 下单成功: {order_id}")

                # 记录已处理的订单ID，防止重复下单
                self.processed_orders.add(order_id)

                # 增加成功计数
                self.successful_copies += 1
                print(f"[AutoCopyTrader] 跟单成功计数: {self.successful_copies}")

                # 保存状态
                self.save_state()

                return True
            else:
                error_code = result.get('code', 'N/A')
                error_msg = result.get('msg', '未知错误')
                self.app.add_message(f"❌ 下单失败: {error_msg}", "error")
                print(f"[AutoCopyTrader] 下单失败 - Code: {error_code}, Msg: {error_msg}")
                print(f"[AutoCopyTrader] 完整响应: {result}")
                return False

        except Exception as e:
            self.app.add_message(f"下单异常: {str(e)}", "error")
            print(f"[AutoCopyTrader] 下单异常: {e}")
            import traceback
            traceback.print_exc()
            return False

    def place_limit_order(self, coin, direction, size, price, is_limit=True):
        """
        执行限价单下单

        Args:
            coin: 币种（BTC/ETH/SOL）
            direction: 方向（多/空）
            size: 数量（BTC/ETH/SOL数量，需要转换为张数）
            price: 限价价格
            is_limit: 是否是限价单，False则使用市价单
        """
        try:
            # 构建交易对
            inst_id = f"{coin}-USDT-SWAP"

            # 方向转换
            side = "buy" if direction == "多" else "sell"

            # 转换为张数
            contract_size_map = {
                'BTC': 0.01,   # 1张 = 0.01 BTC
                'ETH': 0.1,    # 1张 = 0.1 ETH
                'SOL': 1.0,    # 1张 = 1 SOL
            }

            contract_size = contract_size_map.get(coin, 0.01)
            size_in_contracts = int(size / contract_size)  # 转换为张数并取整

            # 确保至少1张
            if size_in_contracts < 1:
                size_in_contracts = 1

            order_type_str = "限价单" if is_limit else "市价单"
            self.app.add_message(
                f"📤 下{order_type_str}: {side.upper()} {size:.6f} {coin} ({size_in_contracts}张) @ {price}",
                "info"
            )
            print(f"[AutoCopyTrader] 下{order_type_str}: {inst_id} {side} {size:.6f} {coin} = {size_in_contracts}张 @ {price}")

            # 先设置杠杆倍数（默认10倍）
            try:
                leverage = 10
                leverage_result = self.okx_trader.set_leverage(
                    inst_id=inst_id,
                    lever=str(leverage),
                    mgn_mode="cross"
                )
                if leverage_result.get('code') == '0':
                    print(f"[AutoCopyTrader] 杠杆已设置为 {leverage}x")
                else:
                    print(f"[AutoCopyTrader] 设置杠杆失败: {leverage_result.get('msg', '未知错误')}")
            except Exception as e:
                print(f"[AutoCopyTrader] 设置杠杆异常: {e}")

            # 根据类型调用不同的下单方法
            if is_limit:
                # 调用OKX API下限价单
                result = self.okx_trader.place_limit_order(
                    inst_id=inst_id,
                    side=side,
                    size=str(size_in_contracts),  # 使用张数
                    price=str(price),
                    trade_mode="cross"
                )
            else:
                # 调用OKX API下市价单
                result = self.okx_trader.place_market_order(
                    inst_id=inst_id,
                    side=side,
                    size=str(size_in_contracts),
                    trade_mode="cross"
                )

            if result.get('code') == '0':
                order_data = result.get('data', [{}])[0]
                order_id = order_data.get('ordId', 'N/A')
                self.app.add_message(f"✅ 下单成功! 订单ID: {order_id}", "success")
                print(f"[AutoCopyTrader] 下单成功: {order_id}")

                # 记录已处理的订单ID，防止重复下单
                self.processed_orders.add(order_id)

                # 增加成功计数
                self.successful_copies += 1
                print(f"[AutoCopyTrader] 跟单成功计数: {self.successful_copies}")

                # 保存状态
                self.save_state()

                return True
            else:
                error_code = result.get('code', 'N/A')
                error_msg = result.get('msg', '未知错误')
                self.app.add_message(f"❌ 下单失败: {error_msg}", "error")
                print(f"[AutoCopyTrader] 下单失败 - Code: {error_code}, Msg: {error_msg}")
                print(f"[AutoCopyTrader] 完整响应: {result}")
                return False

        except Exception as e:
            self.app.add_message(f"下单异常: {str(e)}", "error")
            print(f"[AutoCopyTrader] 下单异常: {e}")
            import traceback
            traceback.print_exc()
            return False

    def monitor_all_traders(self):
        """监控所有已跟随的大户"""
        if not self.is_running:
            return

        for trader_address, info in self.followed_traders.items():
            if info.get('active'):
                self.monitor_trader(trader_address, info)

        # 注意：不再在这里调用after，由main_loop统一控制循环

    def monitor_trader(self, trader_address, trader_info):
        """
        监控单个大户的交易活动

        Args:
            trader_address: 大户地址
            trader_info: 大户跟单信息
        """
        try:
            # 获取大户最新数据
            trader_data = self.get_trader_data(trader_address)
            if not trader_data:
                print(f"[AutoCopyTrader] ⚠️ 无法获取大户数据: {trader_address[:8]}...")
                return

            # 输出读取到的数据统计
            positions = trader_data.get('positions', [])
            trades = trader_data.get('trades', [])
            open_orders = trader_data.get('open_orders', [])
            deposits = trader_data.get('deposits', [])
            withdrawals = trader_data.get('withdrawals', [])

            print(f"[AutoCopyTrader] 📊 监控数据 {trader_address[:8]}...: "
                  f"{len(positions)}个持仓, {len(trades)}条交易, "
                  f"{len(open_orders)}个委托, {len(deposits)}条充值, {len(withdrawals)}条提现")

            # 显示持仓详情
            if positions:
                print(f"[AutoCopyTrader] 📈 当前持仓:")
                for idx, pos in enumerate(positions, 1):
                    print(f"  [{idx}] {pos.get('代币', 'N/A')} {pos.get('方向', 'N/A')} "
                          f"{pos.get('杠杆', 'N/A')} | 价值: {pos.get('价值', 'N/A')} | "
                          f"数量: {pos.get('数量', 'N/A')} | 盈亏: {pos.get('盈亏(PnL)', 'N/A')}")

            # 获取时间戳
            start_timestamp = trader_info['start_timestamp']

            # 1. 检查委托变化（优先处理，更快跟单）
            new_orders = self.filter_new_orders(
                trader_data.get('open_orders', []),
                trader_info.get('last_orders', []),
                start_timestamp
            )

            if new_orders:
                print(f"[AutoCopyTrader] 🆕 检测到 {len(new_orders)} 个新委托!")
                self.process_new_orders(trader_address, new_orders)
                trader_info['last_orders'] = trader_data.get('open_orders', [])
            else:
                print(f"[AutoCopyTrader] ✓ 暂无新委托")

            # 2. 检查交易历史（只处理时间戳之后的）
            new_trades = self.filter_new_trades(
                trader_data.get('trades', []),
                trader_info.get('last_trades', []),
                start_timestamp
            )

            if new_trades:
                print(f"[AutoCopyTrader] 🆕 检测到 {len(new_trades)} 笔新交易!")
                self.process_new_trades(trader_address, new_trades)
                trader_info['last_trades'] = trader_data.get('trades', [])
            else:
                print(f"[AutoCopyTrader] ✓ 暂无新交易（跟单开始时间: {trader_info['start_time_str']}）")

            # 3. 检查止盈止损设置
            self.check_and_copy_tpsl(trader_address, trader_data)

        except Exception as e:
            print(f"[AutoCopyTrader] 监控大户失败: {e}")
            import traceback
            traceback.print_exc()

    def filter_new_trades(self, current_trades, last_trades, start_timestamp):
        """
        过滤出新的交易（在时间戳之后的）

        Args:
            current_trades: 当前交易历史
            last_trades: 上次的交易历史
            start_timestamp: 跟单开始时间戳

        Returns:
            list: 新交易列表
        """
        new_trades = []

        for trade in current_trades:
            try:
                # 解析交易时间
                time_str = trade.get('时间', '')
                trade_time = self.parse_trade_time(time_str)

                if not trade_time:
                    continue

                # 只处理时间戳之后的交易
                if trade_time <= start_timestamp:
                    continue

                # 检查是否是新交易（不在上次的列表中）
                trade_hash = trade.get('交易哈希', '')
                is_new = True
                for last_trade in last_trades:
                    if last_trade.get('交易哈希', '') == trade_hash:
                        is_new = False
                        break

                if is_new:
                    new_trades.append(trade)

            except Exception as e:
                print(f"[AutoCopyTrader] 过滤交易失败: {e}")
                continue

        return new_trades

    def parse_trade_time(self, time_str):
        """
        解析交易时间字符串

        Args:
            time_str: 如 "10-18 08:22:53"

        Returns:
            datetime: 时间对象
        """
        try:
            # 格式: "10-18 08:22:53"
            current_year = datetime.now().year
            parts = time_str.strip().split()

            if len(parts) < 2:
                return None

            date_part = parts[0]  # "10-18"
            time_part = parts[1]  # "08:22:53"

            month_day = date_part.split('-')
            hour_min_sec = time_part.split(':')

            if len(month_day) != 2 or len(hour_min_sec) != 3:
                return None

            month = int(month_day[0])
            day = int(month_day[1])
            hour = int(hour_min_sec[0])
            minute = int(hour_min_sec[1])
            second = int(hour_min_sec[2])

            return datetime(current_year, month, day, hour, minute, second)

        except Exception as e:
            print(f"[AutoCopyTrader] 解析交易时间失败: {time_str}, 错误: {e}")
            return None

    def filter_new_orders(self, current_orders, last_orders, start_timestamp):
        """
        过滤出新的委托（在时间戳之后的，且不在上次列表中）

        Args:
            current_orders: 当前委托列表
            last_orders: 上次的委托列表
            start_timestamp: 跟单开始时间戳

        Returns:
            list: 新委托列表
        """
        new_orders = []

        for order in current_orders:
            try:
                # 解析委托时间
                time_str = order.get('时间', '')
                order_time = self.parse_trade_time(time_str)

                if not order_time:
                    # 如果没有时间字段或解析失败，跳过时间检查
                    # 但仍然检查是否是新委托
                    pass
                else:
                    # 只处理时间戳之后的委托
                    if order_time <= start_timestamp:
                        continue

                # 检查是否是新委托（不在上次的列表中）
                # 使用多个字段组合作为唯一标识
                order_key = f"{order.get('代币', '')}_{order.get('类型', '')}_{order.get('方向', '')}_{order.get('数量', '')}_{order.get('价格', '')}_{order.get('时间', '')}"

                is_new = True
                for last_order in last_orders:
                    last_order_key = f"{last_order.get('代币', '')}_{last_order.get('类型', '')}_{last_order.get('方向', '')}_{last_order.get('数量', '')}_{last_order.get('价格', '')}_{last_order.get('时间', '')}"
                    if last_order_key == order_key:
                        is_new = False
                        break

                if is_new:
                    new_orders.append(order)

            except Exception as e:
                print(f"[AutoCopyTrader] 过滤委托失败: {e}")
                continue

        return new_orders

    def process_new_trades(self, trader_address, new_trades):
        """
        处理新的交易（检测买入/卖出并同步）

        Args:
            trader_address: 大户地址
            new_trades: 新交易列表
        """
        selected_coin = self.app.selected_coin.get()

        for trade in new_trades:
            try:
                direction = trade.get('方向', '')  # Buy/Sell
                token = trade.get('代币', '')
                size_str = trade.get('数量', '')
                price_str = trade.get('价格', '')

                # 检查是否是当前跟踪的币种
                if selected_coin not in token:
                    continue

                # 解析数量
                trader_size = self.parse_trade_size(size_str)
                if not trader_size or trader_size <= 0:
                    print(f"[AutoCopyTrader] 无法解析交易数量: {size_str}")
                    continue

                # 获取可用保证金
                available_margin = self.get_available_margin()
                if not available_margin:
                    self.app.add_message("⚠️ 无法获取账户余额", "error")
                    continue

                # 计算我应该交易的数量
                my_size = self.calculate_copy_size(
                    trader_size,
                    available_margin,
                    trader_address
                )

                # 确保不低于最小值
                if my_size < self.MIN_BTC_SIZE:
                    self.app.add_message(
                        f"⚠️ 计算数量({my_size:.6f})低于最小值，使用最小值{self.MIN_BTC_SIZE}",
                        "warning"
                    )
                    my_size = self.MIN_BTC_SIZE

                # 执行交易
                if direction.lower() in ['buy', '买入', '开多']:
                    self.app.add_message(
                        f"🔔 检测到{direction}: {trader_size} {selected_coin}",
                        "info"
                    )
                    # 同步买入
                    self.place_copy_order(
                        coin=selected_coin,
                        direction="多",
                        size=my_size
                    )

                elif direction.lower() in ['sell', '卖出', '开空', '平多', '平仓']:
                    self.app.add_message(
                        f"🔔 检测到{direction}: {trader_size} {selected_coin}",
                        "warning"
                    )
                    # 同步卖出
                    self.place_copy_order(
                        coin=selected_coin,
                        direction="空",
                        size=my_size
                    )

            except Exception as e:
                print(f"[AutoCopyTrader] 处理交易失败: {e}")
                import traceback
                traceback.print_exc()
                continue

    def parse_trade_size(self, size_str):
        """
        解析交易数量字符串

        Args:
            size_str: 如 "10.5", "10.5 BTC" 等

        Returns:
            float: 数量
        """
        try:
            # 移除币种名称，只保留数字
            size_str = size_str.strip()
            # 提取第一个数字部分
            parts = size_str.split()
            if parts:
                num_str = parts[0].replace(',', '')
                return float(num_str)
            return None
        except Exception as e:
            print(f"[AutoCopyTrader] 解析交易数量失败: {size_str}, 错误: {e}")
            return None

    def process_new_orders(self, trader_address, new_orders):
        """
        处理新的委托（检测开仓/平仓委托并同步下单）

        Args:
            trader_address: 大户地址
            new_orders: 新委托列表
        """
        selected_coin = self.app.selected_coin.get()

        for order in new_orders:
            try:
                token = order.get('代币', '')
                order_type = order.get('类型', '')  # 限价、市价、止盈、止损等
                direction = order.get('方向', '')  # Buy/Sell/开多/开空/平多/平空
                size_str = order.get('数量', '')
                price_str = order.get('价格', '')

                # 检查是否是当前跟踪的币种
                if selected_coin not in token:
                    continue

                # 跳过止盈止损订单（由check_and_copy_tpsl处理）
                is_tpsl = any(keyword in order_type for keyword in ['止盈', '止损', 'TP', 'SL', 'Take Profit', 'Stop Loss'])
                if is_tpsl:
                    continue

                # 解析数量
                trader_size = self.parse_trade_size(size_str)
                if not trader_size or trader_size <= 0:
                    print(f"[AutoCopyTrader] 无法解析委托数量: {size_str}")
                    continue

                # 解析价格
                price = self.parse_price(price_str)
                if not price or price <= 0:
                    print(f"[AutoCopyTrader] 无法解析委托价格: {price_str}")
                    continue

                # 获取可用保证金
                available_margin = self.get_available_margin()
                if not available_margin:
                    self.app.add_message("⚠️ 无法获取账户余额", "error")
                    continue

                # 计算我应该交易的数量
                my_size = self.calculate_copy_size(
                    trader_size,
                    available_margin,
                    trader_address
                )

                # 确保不低于最小值
                if my_size < self.MIN_BTC_SIZE:
                    self.app.add_message(
                        f"⚠️ 计算数量({my_size:.6f})低于最小值，使用最小值{self.MIN_BTC_SIZE}",
                        "warning"
                    )
                    my_size = self.MIN_BTC_SIZE

                # 判断委托方向
                is_buy = any(keyword in direction.lower() for keyword in ['buy', '买', '开多', 'long'])
                is_sell = any(keyword in direction.lower() for keyword in ['sell', '卖', '开空', '平', 'short', 'close'])

                # 确定下单类型（限价单/市价单）
                is_limit = '限价' in order_type or 'Limit' in order_type
                is_market = '市价' in order_type or 'Market' in order_type

                if is_buy:
                    self.app.add_message(
                        f"🔔 检测到新委托({order_type}): 买入 {trader_size} {selected_coin} @ {price}",
                        "info"
                    )
                    # 同步下限价买单
                    self.place_limit_order(
                        coin=selected_coin,
                        direction="多",
                        size=my_size,
                        price=price,
                        is_limit=is_limit
                    )

                elif is_sell:
                    self.app.add_message(
                        f"🔔 检测到新委托({order_type}): 卖出 {trader_size} {selected_coin} @ {price}",
                        "warning"
                    )
                    # 同步下限价卖单
                    self.place_limit_order(
                        coin=selected_coin,
                        direction="空",
                        size=my_size,
                        price=price,
                        is_limit=is_limit
                    )

            except Exception as e:
                print(f"[AutoCopyTrader] 处理委托失败: {e}")
                import traceback
                traceback.print_exc()
                continue

    def check_and_copy_tpsl(self, trader_address, trader_data):
        """
        检查并复制止盈止损设置

        Args:
            trader_address: 大户地址
            trader_data: 大户数据
        """
        open_orders = trader_data.get('open_orders', [])
        selected_coin = self.app.selected_coin.get()

        for order in open_orders:
            try:
                token = order.get('代币', '')
                order_type = order.get('类型', '')
                trigger_price_str = order.get('价格', '')
                direction = order.get('方向', '')
                size_str = order.get('数量', '')

                # 检查币种
                if selected_coin not in token:
                    continue

                # 检测止盈止损订单
                is_tp = '止盈' in order_type or 'TP' in order_type.upper() or 'Take Profit' in order_type
                is_sl = '止损' in order_type or 'SL' in order_type.upper() or 'Stop Loss' in order_type

                if not (is_tp or is_sl):
                    continue

                # 解析触发价格
                trigger_price = self.parse_price(trigger_price_str)
                if not trigger_price or trigger_price <= 0:
                    print(f"[AutoCopyTrader] 无法解析触发价格: {trigger_price_str}")
                    continue

                # 解析数量
                trader_size = self.parse_trade_size(size_str)
                if not trader_size or trader_size <= 0:
                    print(f"[AutoCopyTrader] 无法解析订单数量: {size_str}")
                    continue

                # 获取可用保证金
                available_margin = self.get_available_margin()
                if not available_margin:
                    continue

                # 计算我的数量
                my_size = self.calculate_copy_size(
                    trader_size,
                    available_margin,
                    trader_address
                )

                if my_size < self.MIN_BTC_SIZE:
                    my_size = self.MIN_BTC_SIZE

                # 显示消息
                order_type_name = "止盈" if is_tp else "止损"
                self.app.add_message(
                    f"🎯 检测到{order_type_name}设置: 触发价${trigger_price:,.2f}",
                    "info"
                )

                # 构建交易对
                inst_id = f"{selected_coin}-USDT-SWAP"

                # 方向转换（止盈止损的方向与持仓方向相反）
                # 如果大户是多单，止盈/止损应该是卖出（sell）
                # 如果大户是空单，止盈/止损应该是买入（buy）
                side = "sell" if direction in ["多", "买入", "Buy"] else "buy"

                # 使用OKX API设置止盈止损
                # 注意：OKX的止盈止损API比较复杂，这里使用简化版本
                try:
                    # 使用条件单（algo order）
                    result = self.okx_trader.place_algo_order(
                        inst_id=inst_id,
                        side=side,
                        size=str(my_size),
                        trigger_price=str(trigger_price),
                        order_type='conditional',  # 条件单
                        trade_mode='cross'
                    )

                    if result and result.get('code') == '0':
                        self.app.add_message(
                            f"✅ {order_type_name}设置成功! 触发价: ${trigger_price:,.2f}",
                            "success"
                        )
                    else:
                        error_msg = result.get('msg', '未知错误') if result else '请求失败'
                        self.app.add_message(
                            f"❌ {order_type_name}设置失败: {error_msg}",
                            "error"
                        )

                except Exception as e:
                    print(f"[AutoCopyTrader] 设置止盈止损异常: {e}")
                    self.app.add_message(
                        f"❌ {order_type_name}设置异常: {str(e)}",
                        "error"
                    )

            except Exception as e:
                print(f"[AutoCopyTrader] 检查止盈止损失败: {e}")
                import traceback
                traceback.print_exc()
                continue

    def parse_price(self, price_str):
        """
        解析价格字符串

        Args:
            price_str: 如 "$108043.9" 或 "108043.9"

        Returns:
            float: 价格
        """
        try:
            price_str = price_str.strip().replace('$', '').replace(',', '')
            return float(price_str)
        except Exception as e:
            print(f"[AutoCopyTrader] 解析价格失败: {price_str}, 错误: {e}")
            return None


def main():
    """主函数"""
    root = tk.Tk()
    app = HyperliquidMonitor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
