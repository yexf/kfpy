# -*- coding:utf-8 -*-
"""
@FileName  :qmt_gateway.py
@Time      :2022/11/8 16:49
@Author    :fsksf
"""
from collections import defaultdict
from typing import Dict, List
from src.event import Event, EventEngine
from src.trader.event import (
    EVENT_TIMER,
    EVENT_TICK,
    EVENT_LOG,
)
from src.trader.constant import (
    Product, Direction, OrderType, Exchange

)
from src.trader.gateway import BaseGateway
from src.trader.object import (
    OrderRequest,
    CancelRequest,
    SubscribeRequest,
    ContractData,
    TradeData, LogData,
)

from src.api.qmt.md import MD
from src.api.qmt.td import TD
from src.trader.utility import load_json


class QmtGateway(BaseGateway):
    default_setting: Dict[str, str] = {
        "交易账号": "",
        "mini路径": ""
    }

    TRADE_TYPE = (Product.ETF, Product.EQUITY, Product.BOND, Product.INDEX)
    exchanges = (Exchange.SSE, Exchange.SZSE)

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
        self.td.connect(setting)

    def close(self) -> None:
        self.md.close()

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


if __name__ == '__main__':
    event_engine = EventEngine()
    qmt = QmtGateway(event_engine)
    qmt.subscribe(SubscribeRequest(symbol='000001', exchange=Exchange.SZSE))
    # qmt.md.get_contract()
    test_config_path = "test_qmt_account.json"
    test_config = load_json(test_config_path)
    config_path = "qmt_account.json"
    config = load_json(test_config_path)
    qmt.td.connect(test_config)
    event_engine.register(EVENT_LOG, lambda event: print(event.data.level, event.data.msg))
    event_engine.register(EVENT_TICK, lambda event: print(event.data))
    event_engine.start()
    import threading
    import time


    def slp():
        while True:
            time.sleep(0.1)


    t = threading.Thread(target=slp)
    t.start()
    t.join()
