"""
语言配置文件 / Language Configuration
支持中英文切换 / Support Chinese-English Switching
"""

LANGUAGES = {
    'zh': {
        # 主窗口标题
        'window_title': '加密货币监控系统',
        'author': '作者',

        # 标签页
        'tab_raw_data': '原始数据',
        'tab_position_data': '持仓数据',
        'tab_okx_table': 'OKX 数据表格',
        'tab_okx_heatmap': 'OKX 市值热力图',
        'tab_okx_analysis': 'OKX 市场分析',

        # 按钮
        'btn_refresh': '刷新数据',
        'btn_export': '导出数据',
        'btn_clear': '清空日志',
        'btn_language': 'English',  # 显示切换到的目标语言
        'btn_okx_refresh': '刷新',
        'btn_auto_refresh': '自动刷新',
        'btn_okx_config': 'OKX配置',
        'btn_manual_trade': '手动交易',
        'btn_auto_copy': '启动跟单',
        'btn_stop_copy': '停止跟单',

        # 筛选面板
        'filter_title': '数据筛选',
        'filter_coin': '币种筛选（单选）',
        'filter_coin_placeholder': '输入币种（如BTC）',
        'filter_time': '开仓时间',
        'filter_time_all': '全部时间',
        'filter_time_1d': '最近1天',
        'filter_time_3d': '最近3天',
        'filter_time_7d': '最近7天',
        'filter_time_31d': '最近31天',
        'filter_amount': '仓位金额',
        'filter_amount_all': '全部金额',
        'filter_amount_50m': '>5000万',
        'filter_amount_100m': '>1亿',
        'filter_amount_placeholder': '最小金额',
        'btn_apply_filter': '应用筛选',
        'btn_reset_filter': '重置筛选',

        # 状态栏
        'status_ready': '就绪',
        'status_loading': '加载中...',
        'status_refreshing': '刷新中...',
        'status_success': '数据加载成功',
        'status_error': '加载失败',
        'status_export_success': '数据导出成功',
        'status_filter_applied': '筛选已应用',

        # 表格列标题 - Hyperliquid持仓表
        'col_rank': '排名',
        'col_user_address': '用户地址(双击查看详情)',
        'col_symbol': '币种',
        'col_direction': '方向',
        'col_position': '仓位',
        'col_unrealized_pnl': '未实现盈亏(%)',
        'col_entry_price': '开仓价格',
        'col_liquidation_price': '爆仓价格',
        'col_margin': '保证金',
        'col_funding': '资金费',
        'col_current_price': '当前价格',
        'col_open_time': '开仓时间',

        # OKX表格列标题
        'col_price': '价格',
        'col_change_24h': '24h涨跌',
        'col_volume': '24h成交量',
        'col_market_cap': '市值',
        'col_time': '时间',
        'col_amount': '金额',
        'col_type': '类型',

        # OKX 分析
        'okx_market_overview': '市场概览',
        'okx_total_coins': '总币种数',
        'okx_gainers': '上涨',
        'okx_losers': '下跌',
        'okx_neutral': '持平',
        'okx_top_gainers': '涨幅榜 TOP 10',
        'okx_top_losers': '跌幅榜 TOP 10',
        'okx_market_sentiment': '市场情绪',
        'okx_bullish': '看涨',
        'okx_bearish': '看跌',

        # 消息提示
        'msg_loading': '正在加载数据，请稍候...',
        'msg_no_data': '暂无数据',
        'msg_export_success': '数据已导出到：',
        'msg_export_failed': '导出失败：',
        'msg_refresh_success': '刷新成功！',
        'msg_refresh_failed': '刷新失败：',
        'msg_confirm_export': '确认导出',
        'msg_confirm_export_text': '是否导出当前数据到Excel？',

        # 用户详情窗口
        'detail_window_title': '用户详情',
        'detail_user_address': '👤 用户地址:',
        'detail_session_tip': '💡 数据已保持浏览器会话,可实时刷新数据(无需重新加载页面)',
        'detail_manual_refresh': '手动刷新',
        'detail_auto_refresh': '自动刷新 (10秒)',
        'detail_last_update': '最后更新:',
        'detail_first_load': '首次加载',
        'detail_error_title': '⚠️ 错误信息',
        'detail_debug_log': '🔧 调试日志',
        'detail_pnl_stats': '📊 盈亏统计',
        'detail_total_pnl': '💰 总盈亏',
        'detail_pnl_24h': '📈 24小时盈亏',
        'detail_pnl_48h': '📉 48小时盈亏',
        'detail_pnl_7d': '📅 7天盈亏',
        'detail_pnl_30d': '🗓️ 30天盈亏',
        'detail_position_value': '💼 仓位价值',
        'detail_pnl_chart': '📈 盈亏趋势图',
        'detail_pnl_unit': '盈亏(万美元)',
        'detail_chart_title': '盈亏趋势对比',
        'detail_period_24h': '24小时',
        'detail_period_48h': '48小时',
        'detail_period_7d': '7天',
        'detail_period_30d': '30天',
        'detail_positions': '📦 当前持仓',
        'detail_no_positions': '暂无持仓数据',
        'detail_orders': '📝 当前委托',
        'detail_no_orders': '暂无委托数据',
        'detail_trades': '🔄 交易历史',
        'detail_no_trades': '暂无交易记录',
        'detail_transfers': '💰 充值 & 提现',
        'detail_no_transfers': '暂无充提记录',
        'detail_deposit': '充值',
        'detail_withdrawal': '提现',
        'detail_transfer_stats': '充值: {deposit} 条 | 提现: {withdrawal} 条',

        # 持仓表格列
        'detail_col_token': '代币',
        'detail_col_direction': '方向',
        'detail_col_leverage': '杠杆',
        'detail_col_value': '价值',
        'detail_col_size': '数量',
        'detail_col_entry_price': '开仓价格',
        'detail_col_pnl': '盈亏(PnL)',
        'detail_col_funding': '资金费',
        'detail_col_liq_price': '爆仓价格',

        # 提示框
        'msg_browser_closed': '浏览器会话已关闭,无法刷新数据',
        'msg_refresh_title': '提示',
        'msg_update_success': '数据已更新!',
        'msg_update_title': '成功',
        'msg_update_failed': '刷新数据失败',
        'msg_update_failed_title': '失败',

        # 其他
        'loading_text': '加载中',
        'no_data_text': '暂无数据',
        'total_records': '共 {count} 条记录',
        'filtered_records': '筛选后 {count} 条记录',
    },

    'en': {
        # Main window title
        'window_title': 'Crypto Market Monitor',
        'author': 'Author',

        # Tabs
        'tab_raw_data': 'Raw Data',
        'tab_position_data': 'Position Data',
        'tab_okx_table': 'OKX Data Table',
        'tab_okx_heatmap': 'OKX Market Heatmap',
        'tab_okx_analysis': 'OKX Market Analysis',

        # Buttons
        'btn_refresh': 'Refresh',
        'btn_export': 'Export',
        'btn_clear': 'Clear Log',
        'btn_language': '中文',  # Show target language
        'btn_okx_refresh': 'Refresh',
        'btn_auto_refresh': 'Auto Refresh',
        'btn_okx_config': 'OKX Config',
        'btn_manual_trade': 'Manual Trade',
        'btn_auto_copy': 'Start Copy',
        'btn_stop_copy': 'Stop Copy',

        # Filter panel
        'filter_title': 'Data Filter',
        'filter_coin': 'Symbol Filter (Single)',
        'filter_coin_placeholder': 'Enter symbol (e.g. BTC)',
        'filter_time': 'Opening Time',
        'filter_time_all': 'All Time',
        'filter_time_1d': 'Last 1 Day',
        'filter_time_3d': 'Last 3 Days',
        'filter_time_7d': 'Last 7 Days',
        'filter_time_31d': 'Last 31 Days',
        'filter_amount': 'Position Amount',
        'filter_amount_all': 'All Amounts',
        'filter_amount_50m': '>$50M',
        'filter_amount_100m': '>$100M',
        'filter_amount_placeholder': 'Min Amount',
        'btn_apply_filter': 'Apply Filter',
        'btn_reset_filter': 'Reset Filter',

        # Status bar
        'status_ready': 'Ready',
        'status_loading': 'Loading...',
        'status_refreshing': 'Refreshing...',
        'status_success': 'Data loaded successfully',
        'status_error': 'Loading failed',
        'status_export_success': 'Data exported successfully',
        'status_filter_applied': 'Filter applied',

        # Table columns - Hyperliquid Position Table
        'col_rank': 'Rank',
        'col_user_address': 'User Address (Dbl-Click for Details)',
        'col_symbol': 'Symbol',
        'col_direction': 'Direction',
        'col_position': 'Position',
        'col_unrealized_pnl': 'Unrealized PnL(%)',
        'col_entry_price': 'Entry Price',
        'col_liquidation_price': 'Liq. Price',
        'col_margin': 'Margin',
        'col_funding': 'Funding',
        'col_current_price': 'Current Price',
        'col_open_time': 'Open Time',

        # OKX Table columns
        'col_price': 'Price',
        'col_change_24h': '24h Change',
        'col_volume': '24h Volume',
        'col_market_cap': 'Market Cap',
        'col_time': 'Time',
        'col_amount': 'Amount',
        'col_type': 'Type',

        # OKX Analysis
        'okx_market_overview': 'Market Overview',
        'okx_total_coins': 'Total Coins',
        'okx_gainers': 'Gainers',
        'okx_losers': 'Losers',
        'okx_neutral': 'Neutral',
        'okx_top_gainers': 'Top 10 Gainers',
        'okx_top_losers': 'Top 10 Losers',
        'okx_market_sentiment': 'Market Sentiment',
        'okx_bullish': 'Bullish',
        'okx_bearish': 'Bearish',

        # Messages
        'msg_loading': 'Loading data, please wait...',
        'msg_no_data': 'No data available',
        'msg_export_success': 'Data exported to: ',
        'msg_export_failed': 'Export failed: ',
        'msg_refresh_success': 'Refresh successful!',
        'msg_refresh_failed': 'Refresh failed: ',
        'msg_confirm_export': 'Confirm Export',
        'msg_confirm_export_text': 'Export current data to Excel?',

        # User Detail Window
        'detail_window_title': 'Trader Details',
        'detail_user_address': '👤 User Address:',
        'detail_session_tip': '💡 Browser session active, data can be refreshed in real-time (no page reload)',
        'detail_manual_refresh': 'Manual Refresh',
        'detail_auto_refresh': 'Auto Refresh (10s)',
        'detail_last_update': 'Last Update:',
        'detail_first_load': 'First Load',
        'detail_error_title': '⚠️ Error Info',
        'detail_debug_log': '🔧 Debug Log',
        'detail_pnl_stats': '📊 PnL Statistics',
        'detail_total_pnl': '💰 Total PnL',
        'detail_pnl_24h': '📈 24h PnL',
        'detail_pnl_48h': '📉 48h PnL',
        'detail_pnl_7d': '📅 7d PnL',
        'detail_pnl_30d': '🗓️ 30d PnL',
        'detail_position_value': '💼 Position Value',
        'detail_pnl_chart': '📈 PnL Trend Chart',
        'detail_pnl_unit': 'PnL ($10k USD)',
        'detail_chart_title': 'PnL Trend Comparison',
        'detail_period_24h': '24 Hours',
        'detail_period_48h': '48 Hours',
        'detail_period_7d': '7 Days',
        'detail_period_30d': '30 Days',
        'detail_positions': '📦 Current Positions',
        'detail_no_positions': 'No position data',
        'detail_orders': '📝 Open Orders',
        'detail_no_orders': 'No order data',
        'detail_trades': '🔄 Trade History',
        'detail_no_trades': 'No trade records',
        'detail_transfers': '💰 Deposits & Withdrawals',
        'detail_no_transfers': 'No transfer records',
        'detail_deposit': 'Deposit',
        'detail_withdrawal': 'Withdrawal',
        'detail_transfer_stats': 'Deposits: {deposit} | Withdrawals: {withdrawal}',

        # Position Table Columns
        'detail_col_token': 'Token',
        'detail_col_direction': 'Direction',
        'detail_col_leverage': 'Leverage',
        'detail_col_value': 'Value',
        'detail_col_size': 'Size',
        'detail_col_entry_price': 'Entry Price',
        'detail_col_pnl': 'PnL',
        'detail_col_funding': 'Funding',
        'detail_col_liq_price': 'Liq. Price',

        # Message Boxes
        'msg_browser_closed': 'Browser session closed, cannot refresh data',
        'msg_refresh_title': 'Notice',
        'msg_update_success': 'Data updated!',
        'msg_update_title': 'Success',
        'msg_update_failed': 'Data refresh failed',
        'msg_update_failed_title': 'Failed',

        # Others
        'loading_text': 'Loading',
        'no_data_text': 'No Data',
        'total_records': 'Total: {count} records',
        'filtered_records': 'Filtered: {count} records',
    }
}


class LanguageManager:
    """语言管理器 / Language Manager"""

    def __init__(self, default_language='zh'):
        """
        初始化语言管理器

        Args:
            default_language: 默认语言 ('zh' 或 'en')
        """
        self.current_language = default_language
        self.observers = []  # 观察者列表，用于语言切换时通知更新UI

    def get_text(self, key, **kwargs):
        """
        获取当前语言的文本

        Args:
            key: 文本键
            **kwargs: 格式化参数

        Returns:
            str: 对应语言的文本
        """
        text = LANGUAGES.get(self.current_language, LANGUAGES['zh']).get(key, key)

        # 支持格式化
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError:
                pass

        return text

    def switch_language(self):
        """切换语言"""
        self.current_language = 'en' if self.current_language == 'zh' else 'zh'
        self.notify_observers()

    def get_current_language(self):
        """获取当前语言"""
        return self.current_language

    def add_observer(self, callback):
        """
        添加观察者（当语言切换时会被通知）

        Args:
            callback: 回调函数
        """
        if callback not in self.observers:
            self.observers.append(callback)

    def remove_observer(self, callback):
        """移除观察者"""
        if callback in self.observers:
            self.observers.remove(callback)

    def notify_observers(self):
        """通知所有观察者"""
        for callback in self.observers:
            try:
                callback()
            except Exception as e:
                print(f"Error notifying observer: {e}")


# 全局语言管理器实例
_language_manager = None

def get_language_manager():
    """获取全局语言管理器实例"""
    global _language_manager
    if _language_manager is None:
        _language_manager = LanguageManager()
    return _language_manager


# 便捷函数
def get_text(key, **kwargs):
    """获取文本的便捷函数"""
    return get_language_manager().get_text(key, **kwargs)


def switch_language():
    """切换语言的便捷函数"""
    get_language_manager().switch_language()


if __name__ == '__main__':
    # 测试代码
    lm = LanguageManager('zh')

    print("中文测试:")
    print(f"窗口标题: {lm.get_text('window_title')}")
    print(f"刷新按钮: {lm.get_text('btn_refresh')}")
    print(f"记录统计: {lm.get_text('total_records', count=100)}")

    print("\n切换到英文:")
    lm.switch_language()
    print(f"Window Title: {lm.get_text('window_title')}")
    print(f"Refresh Button: {lm.get_text('btn_refresh')}")
    print(f"Record Count: {lm.get_text('total_records', count=100)}")
