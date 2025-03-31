from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Optional, List, Callable, Dict, Union
from src.gateway.qmt.utils import to_vn_contract
from src.trader.constant import Interval, Exchange
from src.trader.database import TickOverview, BarOverview, BaseDatabase, get_database
from src.trader.datafeed import BaseDatafeed
from src.trader.object import SubscribeRequest, SectorHistoryRequest, SectorData, HistoryRequest, BarData, TickData, \
    SectorDataItem
from src.trader.utility import TEMP_DIR
from src.util.save_tick_data import conv_bond_infos


def get_bond_info(dt: datetime) -> List[List[SubscribeRequest]]:
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


def get_live_bond_info(dt) -> List[List[SubscribeRequest]]:
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
