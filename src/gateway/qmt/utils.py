# -*- coding:utf-8 -*-
"""
@FileName  :utils.py
@Time      :2022/11/8 17:07
@Author    :fsksf
"""
import datetime
import os

from src.trader.object import OrderRequest
from src.trader.constant import Exchange, Product, OrderType, Direction, Status
from xtquant import xtconstant, xtdata

from src.trader.utility import load_json
xtdata.enable_hello = False
From_VN_Exchange_map = {
    Exchange.CFFEX: 'CFF',
    Exchange.SSE: 'SH',
    Exchange.SZSE: 'SZ',
    Exchange.SHFE: 'SHF',
    Exchange.CZCE: 'CZC',
    Exchange.DCE: 'DCE',
}

TO_VN_Exchange_map = {v: k for k, v in From_VN_Exchange_map.items()}


From_VN_Trade_Type = {
    Direction.LONG: xtconstant.STOCK_BUY,
    Direction.SHORT: xtconstant.STOCK_SELL,
}


TO_VN_Trade_Type = {v: k for k, v in From_VN_Trade_Type.items()}


TO_VN_ORDER_STATUS = {
    xtconstant.ORDER_UNREPORTED: Status.SUBMITTING,
    xtconstant.ORDER_WAIT_REPORTING: Status.SUBMITTING,
    xtconstant.ORDER_REPORTED: Status.NOTTRADED,
    xtconstant.ORDER_REPORTED_CANCEL: Status.NOTTRADED,
    xtconstant.ORDER_PARTSUCC_CANCEL: Status.PARTTRADED,
    xtconstant.ORDER_PART_CANCEL: Status.CANCELLED,
    xtconstant.ORDER_CANCELED: Status.CANCELLED,
    xtconstant.ORDER_PART_SUCC: Status.PARTTRADED,
    xtconstant.ORDER_SUCCEEDED: Status.ALLTRADED,
    xtconstant.ORDER_JUNK: Status.REJECTED,
    xtconstant.ORDER_UNKNOWN: Status.REJECTED
}


def from_vn_price_type(req: OrderRequest):
    if req.type == OrderType.LIMIT:
        return xtconstant.FIX_PRICE
    elif req.type == OrderType.MARKET:
        return xtconstant.LATEST_PRICE


def to_vn_contract(symbol):
    code, suffix = symbol.rsplit('.')
    exchange = TO_VN_Exchange_map[suffix]
    return code, exchange


TO_VN_Product = {
    'index': Product.INDEX,
    'stock': Product.EQUITY,
    'fund': Product.FUND,
    'etf': Product.ETF
}


def to_vn_product(dic: dict):
    if 'etf' in dic and dic['etf']:
        return Product.ETF
    if 'stock' in dic and dic['stock']:
        return Product.EQUITY
    for k, v in dic.items():
        if v:
            break
    return TO_VN_Product[k]


def to_qmt_code(symbol, exchange):
    suffix = From_VN_Exchange_map[exchange]
    return f'{symbol}.{suffix}'


def timestamp_to_datetime(tint):
    st = len(str(tint))
    if st != 10:
        p = st - 10
        tint = tint / 10**p
    return datetime.datetime.fromtimestamp(tint)


def get_data_path():
    client = xtdata.get_client()
    client_data_dir = client.get_data_dir()
    data_path = os.path.abspath(os.path.dirname(client_data_dir))
    return data_path


def get_config() -> dict:
    data_path = get_data_path()
    test_config_path = "test_qmt_account.json"
    test_config = load_json(test_config_path)
    if test_config["mini路径"] == data_path:
        return test_config

    config_path = "qmt_account.json"
    config = load_json(config_path)
    if config["mini路径"] == data_path:
        return config
    return {}


def thread_hold():
    import threading
    import time

    def slp():
        while True:
            time.sleep(0.1)

    t = threading.Thread(target=slp)
    t.start()
    t.join()
