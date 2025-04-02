# -*- coding:utf-8 -*-
"""
@FileName  :utils.py
@Time      :2022/11/8 17:07
@Author    :fsksf
"""
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

from src.trader.object import OrderRequest, SubscribeRequest, HistoryRequest
from src.trader.constant import Exchange, Product, OrderType, Direction, Status, Interval
from xtquant import xtconstant, xtdata

from src.trader.utility import TEMP_DIR

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
    if 'index' in dic and dic['index']:
        return Product.INDEX
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
        tint = tint / 10 ** p
    return datetime.fromtimestamp(tint)


def get_bond_info(conv_bond_infos, dt: datetime) -> List[List[SubscribeRequest]]:
    bond_infos: list[SubscribeRequest] = []
    stock_infos: list[SubscribeRequest] = []
    format_str = "%Y-%m-%d %H:%M:%S"
    dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    for bi in conv_bond_infos:
        exchange = bi["交易市场"]
        if exchange != "CNSESZ" and exchange != "CNSESH":
            continue
        code = bi["交易代码"]
        code, exchange = to_vn_contract(code)
        stock_code = bi['正股代码']
        dedate = bi["退市日期"]
        indate = bi["上市日期"]
        if dedate is not None:
            dedate = datetime.strptime(dedate, format_str)
        if indate is None:
            continue
        indate = datetime.strptime(indate, format_str)
        if indate <= dt:
            if dedate is None or dedate > dt:
                bond_infos.append(SubscribeRequest(symbol=code, exchange=exchange))
                stock_infos.append(SubscribeRequest(symbol=stock_code, exchange=exchange))
    return [bond_infos, stock_infos]


def get_live_bond_info(conv_bond_infos, dt) -> List[List[SubscribeRequest]]:
    bond_infos: list[SubscribeRequest] = []
    stock_infos: list[SubscribeRequest] = []
    format_str = "%Y-%m-%d %H:%M:%S"
    for bi in conv_bond_infos:
        exchange = bi["交易市场"]
        if exchange != "CNSESZ" and exchange != "CNSESH":
            continue
        code = bi["交易代码"]
        code, exchange = to_vn_contract(code)
        stock_code = bi['正股代码']
        dedate = bi["退市日期"]
        indate = bi["上市日期"]
        if dedate is not None:
            dedate = datetime.strptime(dedate, format_str)
        if indate is None:
            continue
        indate = datetime.strptime(indate, format_str)
        if indate + timedelta(days=30 * 6) < dt:
            if dedate is None or dedate > dt:
                bond_infos.append(SubscribeRequest(symbol=code, exchange=exchange))
                stock_infos.append(SubscribeRequest(symbol=stock_code, exchange=exchange))
    return [bond_infos, stock_infos]


class CsvFileSystem:
    def __init__(self):
        self.root = TEMP_DIR.joinpath("csv_database")
        if not self.root.exists():
            self.root.mkdir()
        self.tick_overview_path = self.root.joinpath("tick_overview.csv")
        self.bar_overview_path = self.root.joinpath("bar_overview.csv")

    def get_csv_path(self, req: HistoryRequest) -> Path:
        return self.get_folder_path(req.symbol, req.exchange, req.interval, req.start)

    def get_folder_path(self, symbol: str, exchange: Exchange, interval: Interval, start=None) -> Path:
        """
        Get path for temp folder with folder name.
        """
        interval_path: Path = self.root.joinpath(interval.value)
        if not interval_path.exists():
            interval_path.mkdir()

        folder_path = interval_path
        if interval == Interval.TICK:
            vn_symbol = f"{symbol}.{exchange.value}"
            folder_path = interval_path.joinpath(vn_symbol)
            if not folder_path.exists():
                folder_path.mkdir()
            if start:
                start_str = start.strftime("%Y%m%d")
                folder_path = folder_path.joinpath(start_str + ".csv")
        else:
            vn_symbol = f"{symbol}.{exchange.value}.csv"
            folder_path = folder_path.joinpath(vn_symbol)
        return folder_path
