"""
OKX API 交易模块
支持永续合约交易
"""

import hmac
import base64
import json
import time
from datetime import datetime
import requests
from typing import Optional, Dict, List


class OKXTrader:
    """OKX交易类"""

    def __init__(self, api_key: str = "", secret_key: str = "", passphrase: str = "", is_demo: bool = True):
        """
        初始化OKX交易客户端

        Args:
            api_key: API Key
            secret_key: Secret Key
            passphrase: Passphrase
            is_demo: 是否使用模拟盘（True=模拟盘, False=实盘）
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase
        self.is_demo = is_demo

        # API基础URL
        if is_demo:
            self.base_url = "https://www.okx.com"  # 模拟盘也使用同一个URL，通过header区分
        else:
            self.base_url = "https://www.okx.com"

        self.timeout = 10

    def _get_timestamp(self) -> str:
        """获取ISO 8601格式的时间戳"""
        return datetime.utcnow().isoformat(timespec='milliseconds') + 'Z'

    def _sign(self, timestamp: str, method: str, request_path: str, body: str = "") -> str:
        """
        生成签名

        Args:
            timestamp: 时间戳
            method: HTTP方法
            request_path: 请求路径
            body: 请求体

        Returns:
            签名字符串
        """
        if not self.secret_key:
            return ""

        message = timestamp + method.upper() + request_path + body
        mac = hmac.new(
            bytes(self.secret_key, encoding='utf8'),
            bytes(message, encoding='utf-8'),
            digestmod='sha256'
        )
        return base64.b64encode(mac.digest()).decode()

    def _get_headers(self, method: str, request_path: str, body: str = "") -> Dict:
        """
        生成请求头

        Args:
            method: HTTP方法
            request_path: 请求路径
            body: 请求体

        Returns:
            请求头字典
        """
        timestamp = self._get_timestamp()
        sign = self._sign(timestamp, method, request_path, body)

        headers = {
            'OK-ACCESS-KEY': self.api_key,
            'OK-ACCESS-SIGN': sign,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        }

        # 模拟盘需要添加特殊header
        if self.is_demo:
            headers['x-simulated-trading'] = '1'

        return headers

    def _request(self, method: str, endpoint: str, params: Optional[Dict] = None, data: Optional[Dict] = None) -> Dict:
        """
        发送HTTP请求

        Args:
            method: HTTP方法
            endpoint: API端点
            params: URL参数
            data: 请求体数据

        Returns:
            响应JSON
        """
        url = self.base_url + endpoint

        # 构建请求路径（用于签名）
        request_path = endpoint
        if params:
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            request_path += '?' + query_string

        # 构建请求体
        body = ""
        if data:
            body = json.dumps(data)

        # 生成请求头
        headers = self._get_headers(method, request_path, body)

        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=self.timeout)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")

            response.raise_for_status()
            result = response.json()

            return result

        except requests.exceptions.RequestException as e:
            return {
                'code': '-1',
                'msg': f'请求失败: {str(e)}',
                'data': []
            }
        except Exception as e:
            return {
                'code': '-1',
                'msg': f'未知错误: {str(e)}',
                'data': []
            }

    # ==================== 账户相关API ====================

    def get_account_balance(self) -> Dict:
        """
        获取账户余额

        Returns:
            账户余额信息
        """
        endpoint = '/api/v5/account/balance'
        return self._request('GET', endpoint)

    def get_positions(self, inst_type: str = "SWAP", inst_id: str = "") -> Dict:
        """
        获取持仓信息

        Args:
            inst_type: 产品类型 SPOT:币币, SWAP:永续合约, FUTURES:交割合约
            inst_id: 产品ID，如 BTC-USDT-SWAP

        Returns:
            持仓信息
        """
        endpoint = '/api/v5/account/positions'
        params = {'instType': inst_type}
        if inst_id:
            params['instId'] = inst_id
        return self._request('GET', endpoint, params=params)

    def set_leverage(self, inst_id: str, lever: str, mgn_mode: str = "cross", pos_side: str = "") -> Dict:
        """
        设置杠杆倍数

        Args:
            inst_id: 产品ID，如 BTC-USDT-SWAP
            lever: 杠杆倍数，1-100
            mgn_mode: 保证金模式 cross:全仓, isolated:逐仓
            pos_side: 持仓方向 long:多头, short:空头, 空字符串:单向持仓

        Returns:
            设置结果
        """
        endpoint = '/api/v5/account/set-leverage'
        data = {
            'instId': inst_id,
            'lever': str(lever),
            'mgnMode': mgn_mode
        }
        if pos_side:
            data['posSide'] = pos_side

        return self._request('POST', endpoint, data=data)

    # ==================== 交易相关API ====================

    def place_order(
        self,
        inst_id: str,
        trade_mode: str,
        side: str,
        order_type: str,
        size: str,
        price: str = "",
        pos_side: str = "",
        reduce_only: bool = False,
        **kwargs
    ) -> Dict:
        """
        下单

        Args:
            inst_id: 产品ID，如 BTC-USDT-SWAP
            trade_mode: 交易模式 cross:全仓, isolated:逐仓, cash:非保证金
            side: 订单方向 buy:买入, sell:卖出
            order_type: 订单类型 market:市价单, limit:限价单, post_only:只做maker单
            size: 委托数量
            price: 委托价格（限价单必填）
            pos_side: 持仓方向 long:开多, short:开空, net:非双向持仓（默认）
            reduce_only: 是否只减仓
            **kwargs: 其他参数

        Returns:
            下单结果
        """
        endpoint = '/api/v5/trade/order'

        data = {
            'instId': inst_id,
            'tdMode': trade_mode,
            'side': side,
            'ordType': order_type,
            'sz': size,
        }

        if price:
            data['px'] = price

        if pos_side:
            data['posSide'] = pos_side

        if reduce_only:
            data['reduceOnly'] = 'true'

        # 添加其他参数
        data.update(kwargs)

        return self._request('POST', endpoint, data=data)

    def place_market_order(
        self,
        inst_id: str,
        side: str,
        size: str,
        trade_mode: str = "cross",
        pos_side: str = "",
        reduce_only: bool = False
    ) -> Dict:
        """
        市价单（快捷下单）

        Args:
            inst_id: 产品ID，如 BTC-USDT-SWAP
            side: 订单方向 buy:买入, sell:卖出
            size: 委托数量
            trade_mode: 交易模式 cross:全仓, isolated:逐仓
            pos_side: 持仓方向 long:开多, short:开空, net:非双向持仓
            reduce_only: 是否只减仓

        Returns:
            下单结果
        """
        return self.place_order(
            inst_id=inst_id,
            trade_mode=trade_mode,
            side=side,
            order_type='market',
            size=size,
            pos_side=pos_side,
            reduce_only=reduce_only
        )

    def place_limit_order(
        self,
        inst_id: str,
        side: str,
        size: str,
        price: str,
        trade_mode: str = "cross",
        pos_side: str = "",
        reduce_only: bool = False
    ) -> Dict:
        """
        限价单（快捷下单）

        Args:
            inst_id: 产品ID，如 BTC-USDT-SWAP
            side: 订单方向 buy:买入, sell:卖出
            size: 委托数量
            price: 委托价格
            trade_mode: 交易模式 cross:全仓, isolated:逐仓
            pos_side: 持仓方向 long:开多, short:开空, net:非双向持仓
            reduce_only: 是否只减仓

        Returns:
            下单结果
        """
        return self.place_order(
            inst_id=inst_id,
            trade_mode=trade_mode,
            side=side,
            order_type='limit',
            size=size,
            price=price,
            pos_side=pos_side,
            reduce_only=reduce_only
        )

    def cancel_order(self, inst_id: str, order_id: str = "", client_order_id: str = "") -> Dict:
        """
        撤销订单

        Args:
            inst_id: 产品ID
            order_id: 订单ID
            client_order_id: 客户自定义订单ID

        Returns:
            撤销结果
        """
        endpoint = '/api/v5/trade/cancel-order'
        data = {'instId': inst_id}

        if order_id:
            data['ordId'] = order_id
        elif client_order_id:
            data['clOrdId'] = client_order_id
        else:
            return {'code': '-1', 'msg': '必须提供orderId或clOrdId', 'data': []}

        return self._request('POST', endpoint, data=data)

    def get_order(self, inst_id: str, order_id: str = "", client_order_id: str = "") -> Dict:
        """
        查询订单

        Args:
            inst_id: 产品ID
            order_id: 订单ID
            client_order_id: 客户自定义订单ID

        Returns:
            订单信息
        """
        endpoint = '/api/v5/trade/order'
        params = {'instId': inst_id}

        if order_id:
            params['ordId'] = order_id
        elif client_order_id:
            params['clOrdId'] = client_order_id
        else:
            return {'code': '-1', 'msg': '必须提供orderId或clOrdId', 'data': []}

        return self._request('GET', endpoint, params=params)

    def get_pending_orders(self, inst_type: str = "SWAP", inst_id: str = "") -> Dict:
        """
        获取未成交订单

        Args:
            inst_type: 产品类型
            inst_id: 产品ID

        Returns:
            未成交订单列表
        """
        endpoint = '/api/v5/trade/orders-pending'
        params = {'instType': inst_type}
        if inst_id:
            params['instId'] = inst_id
        return self._request('GET', endpoint, params=params)

    # ==================== 止盈止损API ====================

    def place_algo_order(
        self,
        inst_id: str,
        trade_mode: str,
        side: str,
        order_type: str,
        size: str,
        tp_trigger_px: str = "",
        tp_ord_px: str = "",
        sl_trigger_px: str = "",
        sl_ord_px: str = "",
        pos_side: str = "",
        **kwargs
    ) -> Dict:
        """
        下策略委托单（止盈止损）

        Args:
            inst_id: 产品ID
            trade_mode: 交易模式 cross:全仓, isolated:逐仓
            side: 订单方向 buy:买入, sell:卖出
            order_type: 订单类型 conditional:单向止盈止损, oco:双向止盈止损
            size: 委托数量
            tp_trigger_px: 止盈触发价
            tp_ord_px: 止盈委托价（-1=市价）
            sl_trigger_px: 止损触发价
            sl_ord_px: 止损委托价（-1=市价）
            pos_side: 持仓方向 long:开多, short:开空
            **kwargs: 其他参数

        Returns:
            下单结果
        """
        endpoint = '/api/v5/trade/order-algo'

        data = {
            'instId': inst_id,
            'tdMode': trade_mode,
            'side': side,
            'ordType': order_type,
            'sz': size,
        }

        if tp_trigger_px:
            data['tpTriggerPx'] = tp_trigger_px
            data['tpOrdPx'] = tp_ord_px if tp_ord_px else '-1'

        if sl_trigger_px:
            data['slTriggerPx'] = sl_trigger_px
            data['slOrdPx'] = sl_ord_px if sl_ord_px else '-1'

        if pos_side:
            data['posSide'] = pos_side

        data.update(kwargs)

        return self._request('POST', endpoint, data=data)

    def place_tp_sl_order(
        self,
        inst_id: str,
        side: str,
        size: str,
        tp_price: str = "",
        sl_price: str = "",
        trade_mode: str = "cross",
        pos_side: str = ""
    ) -> Dict:
        """
        快捷设置止盈止损（市价单）

        Args:
            inst_id: 产品ID
            side: 平仓方向（与持仓相反）
            size: 委托数量
            tp_price: 止盈价格
            sl_price: 止损价格
            trade_mode: 交易模式
            pos_side: 持仓方向

        Returns:
            下单结果
        """
        order_type = "oco" if (tp_price and sl_price) else "conditional"

        return self.place_algo_order(
            inst_id=inst_id,
            trade_mode=trade_mode,
            side=side,
            order_type=order_type,
            size=size,
            tp_trigger_px=tp_price,
            tp_ord_px="-1" if tp_price else "",
            sl_trigger_px=sl_price,
            sl_ord_px="-1" if sl_price else "",
            pos_side=pos_side
        )

    def get_algo_orders(self, inst_type: str = "SWAP", inst_id: str = "", order_type: str = "") -> Dict:
        """
        获取策略委托单列表

        Args:
            inst_type: 产品类型
            inst_id: 产品ID
            order_type: 订单类型 conditional, oco, trigger, etc.

        Returns:
            策略委托单列表
        """
        endpoint = '/api/v5/trade/orders-algo-pending'

        # 如果没有指定order_type，则查询所有类型
        if not order_type:
            # 查询所有策略委托类型
            all_orders = []
            order_types = ['conditional', 'oco', 'trigger', 'move_order_stop', 'iceberg', 'twap']

            for ot in order_types:
                params = {'instType': inst_type, 'ordType': ot}
                if inst_id:
                    params['instId'] = inst_id

                result = self._request('GET', endpoint, params=params)
                print(f"[OKX API] Query {ot}: code={result.get('code')}, count={len(result.get('data', []))}")
                if result.get('code') == '0':
                    orders = result.get('data', [])
                    all_orders.extend(orders)
                else:
                    print(f"[OKX API] {ot} failed: {result.get('msg', 'Unknown')}")

            return {
                'code': '0',
                'msg': '',
                'data': all_orders
            }
        else:
            # 查询指定类型
            params = {'instType': inst_type, 'ordType': order_type}
            if inst_id:
                params['instId'] = inst_id
            return self._request('GET', endpoint, params=params)

    def cancel_algo_order(self, algo_ids: List[Dict]) -> Dict:
        """
        撤销策略委托单

        Args:
            algo_ids: 算法订单ID列表，格式: [{'algoId': 'xxx', 'instId': 'BTC-USDT-SWAP'}]

        Returns:
            撤销结果
        """
        endpoint = '/api/v5/trade/cancel-algos'
        data = algo_ids
        return self._request('POST', endpoint, data=data)

    # ==================== 行情相关API ====================

    def get_ticker(self, inst_id: str) -> Dict:
        """
        获取单个产品行情

        Args:
            inst_id: 产品ID，如 BTC-USDT-SWAP

        Returns:
            行情信息
        """
        endpoint = '/api/v5/market/ticker'
        params = {'instId': inst_id}
        return self._request('GET', endpoint, params=params)

    def get_instruments(self, inst_type: str = "SWAP") -> Dict:
        """
        获取交易产品列表

        Args:
            inst_type: 产品类型

        Returns:
            产品列表
        """
        endpoint = '/api/v5/public/instruments'
        params = {'instType': inst_type}
        return self._request('GET', endpoint, params=params)

    # ==================== 工具方法 ====================

    def test_connection(self) -> tuple:
        """
        测试API连接

        Returns:
            (是否成功, 消息)
        """
        try:
            result = self.get_account_balance()

            if result.get('code') == '0':
                return (True, "✓ API连接成功")
            else:
                error_msg = result.get('msg', '未知错误')
                return (False, f"✗ API连接失败: {error_msg}")

        except Exception as e:
            return (False, f"✗ 连接异常: {str(e)}")

    def format_position(self, position: Dict) -> str:
        """
        格式化持仓信息

        Args:
            position: 持仓数据

        Returns:
            格式化的字符串
        """
        inst_id = position.get('instId', 'N/A')
        pos = position.get('pos', '0')
        avg_px = position.get('avgPx', '0')
        upl = position.get('upl', '0')
        upl_ratio = position.get('uplRatio', '0')

        # 转换为百分比
        try:
            upl_ratio_pct = float(upl_ratio) * 100
            upl_ratio_str = f"{upl_ratio_pct:.2f}%"
        except:
            upl_ratio_str = upl_ratio

        return f"{inst_id}: {pos}张 @ {avg_px} | 盈亏: {upl} ({upl_ratio_str})"


if __name__ == "__main__":
    # 测试代码
    print("OKX交易模块")
    print("请在主程序中配置API Key使用")
