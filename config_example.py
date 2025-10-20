"""
OKX 监控系统配置示例
复制此文件为 config.py 并根据需要修改配置
"""

# ==================== API 配置 ====================
# OKX API 配置（公开接口，不需要 API Key）
OKX_API_CONFIG = {
    'base_url': 'https://www.okx.com/api/v5',
    'timeout': 10,  # 请求超时时间（秒）
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# ==================== 监控配置 ====================
# 监控的产品类型
INST_TYPE = "SWAP"  # SPOT-币币, SWAP-永续合约, FUTURES-交割合约

# 只显示 USDT 永续合约
FILTER_USDT_ONLY = True

# 显示的币种数量
TOP_N_COINS = 50  # 数据表格显示前50个

# 热力图显示数量
HEATMAP_TOP_N = 20  # 热力图显示前20个

# ==================== 刷新设置 ====================
# 自动刷新间隔（毫秒）
AUTO_REFRESH_INTERVAL = 10000  # 10秒

# 最小刷新间隔（毫秒）- 防止触发频率限制
MIN_REFRESH_INTERVAL = 5000  # 5秒

# ==================== 监控币种列表 ====================
# 重点监控的币种（可选，用于高亮显示）
FOCUS_COINS = [
    'BTC', 'ETH', 'SOL', 'BNB', 'XRP',
    'ADA', 'DOGE', 'MATIC', 'DOT', 'AVAX',
    'LINK', 'UNI', 'ATOM', 'LTC', 'ARB',
    'OP', 'APT', 'SUI', 'INJ', 'TRX'
]

# ==================== 界面主题配置 ====================
# 深色主题配色方案
DARK_THEME = {
    'bg_primary': '#0a0e27',      # 主背景色（深蓝）
    'bg_secondary': '#1a1f3a',    # 次要背景色
    'accent': '#00d4ff',          # 强调色（青色）
    'text_primary': '#ffffff',    # 主要文字色
    'text_secondary': '#888888',  # 次要文字色
    'up_color': '#00ff88',        # 上涨颜色（绿色）
    'down_color': '#ff4444',      # 下跌颜色（红色）
    'neutral': '#cccccc'          # 中性颜色
}

# 浅色主题配色方案（可选）
LIGHT_THEME = {
    'bg_primary': '#ffffff',
    'bg_secondary': '#f5f5f5',
    'accent': '#1890ff',
    'text_primary': '#333333',
    'text_secondary': '#666666',
    'up_color': '#52c41a',
    'down_color': '#ff4d4f',
    'neutral': '#888888'
}

# 当前使用的主题
CURRENT_THEME = DARK_THEME  # 或 LIGHT_THEME

# ==================== 市场情绪阈值 ====================
# 市场情绪判断标准（基于平均涨跌幅）
SENTIMENT_THRESHOLDS = {
    'extreme_greed': 2.0,     # > 2% 极度贪婪
    'greed': 0.5,             # > 0.5% 贪婪
    'neutral_high': 0.5,      # -0.5% ~ 0.5% 中性
    'neutral_low': -0.5,
    'fear': -2.0,             # -2% ~ -0.5% 恐惧
    # < -2% 极度恐惧
}

# ==================== 数据格式化 ====================
# 价格显示小数位数
PRICE_DECIMALS = {
    'threshold': 100,         # 阈值
    'high': 2,                # >= 100 显示2位小数
    'low': 4                  # < 100 显示4位小数
}

# 成交量格式化
VOLUME_FORMAT = {
    'thousand': 'K',          # 千
    'million': 'M',           # 百万
    'billion': 'B'            # 十亿
}

# ==================== 窗口设置 ====================
# 窗口大小
WINDOW_SIZE = {
    'width': 1850,
    'height': 900
}

# 窗口标题
WINDOW_TITLE = "加密货币监控系统 - Hyperliquid & OKX"

# ==================== 导出设置 ====================
# 导出文件格式
EXPORT_FORMATS = ['txt', 'json', 'csv']  # 支持的导出格式

# 导出文件名前缀
EXPORT_PREFIX = {
    'hyperliquid': 'hyperliquid_data',
    'okx': 'okx_data'
}

# ==================== 日志设置 ====================
# 是否启用日志
ENABLE_LOGGING = True

# 日志级别
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR

# 日志文件
LOG_FILE = 'monitor.log'

# ==================== 高级设置 ====================
# 数据缓存时间（秒）
DATA_CACHE_TIME = 60

# 错误重试次数
MAX_RETRY_ATTEMPTS = 3

# 重试延迟（秒）
RETRY_DELAY = 2

# 是否显示调试信息
DEBUG_MODE = False

# ==================== 通知设置（扩展功能）====================
# 价格预警（可选功能）
PRICE_ALERTS = {
    'enabled': False,
    'alerts': [
        # {'symbol': 'BTC', 'price': 100000, 'condition': 'above'},
        # {'symbol': 'ETH', 'price': 3000, 'condition': 'below'},
    ]
}

# 涨跌幅预警
CHANGE_ALERTS = {
    'enabled': False,
    'threshold': 10.0  # 涨跌幅超过10%时提醒
}

# ==================== 使用说明 ====================
"""
配置文件使用说明：

1. 基础配置：
   - 修改 TOP_N_COINS 调整显示的币种数量
   - 修改 AUTO_REFRESH_INTERVAL 调整自动刷新间隔

2. 主题配置：
   - 修改 CURRENT_THEME 切换深色/浅色主题
   - 可以自定义 DARK_THEME 或 LIGHT_THEME 中的颜色

3. 监控币种：
   - 修改 FOCUS_COINS 列表添加重点关注的币种

4. 高级功能：
   - 启用 PRICE_ALERTS 设置价格预警
   - 启用 CHANGE_ALERTS 设置涨跌幅预警

5. 导入配置：
   在主程序中：
   ```python
   try:
       import config
       # 使用 config.OKX_API_CONFIG 等
   except ImportError:
       import config_example as config
       # 使用示例配置
   ```
"""
