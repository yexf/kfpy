# -*- coding:utf-8 -*-
"""
@FileName  :qmt_gateway.py
@Time      :2022/11/8 16:49
@Author    :fsksf
"""
from collections import defaultdict
from typing import Dict, List
from src.event import EventEngine
from src.trader.event import (
    EVENT_TIMER,
)
from src.trader.constant import (
    Product, Exchange

)
from src.trader.gateway import BaseGateway
from src.trader.object import (
    OrderRequest,
    CancelRequest,
    SubscribeRequest,
    ContractData,
    TradeData, )

from src.gateway.qmt.md import MD
from src.util.utility import get_qmt_config
from src.gateway.qmt.td import TD

class QmtGateway(BaseGateway):
    default_setting: Dict[str, str] = {
        "交易账号": "",
        "mini路径": ""
    }

    TRADE_TYPE = (Product.ETF, Product.EQUITY, Product.BOND, Product.INDEX)
    exchanges = (Exchange.SSE, Exchange.SZSE)
    default_name = "QMT"
    def __init__(self, event_engine: EventEngine, gateway_name: str = 'QMT'):
        super(QmtGateway, self).__init__(event_engine, gateway_name)
        self.contracts: Dict[str, ContractData] = {}
        self.md = MD(self)
        self.td = TD(self)
        self.components: Dict[str, List[TradeData]] = defaultdict(list)
        self.count = -1
        self.event_engine.register(EVENT_TIMER, self.process_timer_event)

    def connect(self, setting: dict) -> None:
        self.md.connect(setting)
        if setting is None or setting == {} or setting["交易账号"] == '':
            self.td.connect(get_qmt_config())
        else:
            self.td.connect(setting)

    def close(self) -> None:
        self.md.close()
        self.td.close()

    def subscribe(self, req: SubscribeRequest) -> None:
        return self.md.subscribe(req)

    def send_order(self, req: OrderRequest) -> str:
        return self.td.send_order(req)

    def cancel_order(self, req: CancelRequest) -> None:
        return self.td.cancel_order(req.orderid)

    def query_account(self) -> None:
        self.td.query_account()

    def query_position(self) -> None:
        self.td.query_position()

    def query_order(self):
        self.td.query_order()

    def query_trade(self):
        self.td.query_trade()

    def on_contract(self, contract):
        self.contracts[contract.vt_symbol] = contract
        super(QmtGateway, self).on_contract(contract)

    def get_contract(self, vt_symbol):
        return self.contracts.get(vt_symbol)

    def process_timer_event(self, event) -> None:
        if not self.td.inited:
            return
        if self.count == -1:
            self.query_trade()
        self.count += 1
        if self.count < 21:
            return
        self.query_account()
        self.query_position()
        self.query_order()
        self.count = 0

    def write_log(self, msg):
        super(QmtGateway, self).write_log(f"[QMT] {msg}")
