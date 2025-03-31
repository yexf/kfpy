import os
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from xtquant import (
    xtdata
)

from src.gateway.qmt.utils import to_vn_contract
from src.gateway.xt.xt_datafeed import XtDatafeed
from src.trader.constant import Exchange, Interval
from src.trader.object import BarData, TickData, HistoryRequest, SubscribeRequest
from src.trader.utility import ZoneInfo, load_json, save_json
from src.trader.datafeed import BaseDatafeed
from typing import Callable, Optional, List

from src.util.bond_util import get_bond_info
from src.util.utility import insert_tick_history, insert_bar_history, get_data_path

INTERVAL_VT2XT: dict[Interval, str] = {
    Interval.MINUTE: "1m",
    Interval.DAILY: "1d",
    Interval.TICK: "tick"
}

INTERVAL_ADJUSTMENT_MAP: dict[Interval, timedelta] = {
    Interval.MINUTE: timedelta(minutes=1),
    Interval.DAILY: timedelta()  # 日线无需进行调整
}

EXCHANGE_VT2XT: dict[Exchange, str] = {
    Exchange.SSE: "SH",
    Exchange.SZSE: "SZ",
    Exchange.BSE: "BJ",
    Exchange.SHFE: "SF",
    Exchange.CFFEX: "IF",
    Exchange.INE: "INE",
    Exchange.DCE: "DF",
    Exchange.CZCE: "ZF",
    Exchange.GFEX: "GF",
}

CHINA_TZ = ZoneInfo("Asia/Shanghai")

INTERVAL_Sec2VT: dict[str, str] = {
    "0": Interval.TICK.value,
    "60": Interval.MINUTE.value,
    "86400": Interval.DAILY.value,
}


def tick_donwload_file_info() -> dict[str, set]:
    data_path = get_data_path()
    download_file_info = {}
    files_info = {}
    for files in os.listdir(data_path):
        if files == "SH" or files == "SZ":
            path: str = os.path.join(data_path, files)
            for root, dirs, files in os.walk(path):
                if len(dirs) == 0:
                    files_info[root] = files
    for key in files_info:
        path: Path = Path(key)
        if path.parent.name in INTERVAL_Sec2VT:
            exchange = path.parent.parent.name
            symbol = path.name
            date_list = files_info[key]
            date_info = set()
            for date_dat in date_list:
                date, suffix = date_dat.rsplit('.')
                date_info.add(date)
            xt_symbol = f"{symbol}.{exchange}"
            download_file_info[xt_symbol] = date_info
    return download_file_info


@lru_cache(typed=True)
def get_daily_data(start: datetime, end: datetime, interval: Interval, output: Callable = print, step=10) -> Optional[
    List[BarData]]:
    history: list[BarData] = []
    xt_interval: str = INTERVAL_VT2XT.get(interval, None)
    if not xt_interval:
        output(f"迅投研查询历史数据失败：不支持的时间周期{interval.value}")
        return []

    code_infos: List[List[SubscribeRequest]] = get_bond_info(end)
    [bond_infos, stock_infos] = code_infos

    xt_code_list = []
    for code in bond_infos + stock_infos:
        # 从服务器下载获取
        xt_symbol: str = code.symbol + "." + EXCHANGE_VT2XT[code.exchange]
        xt_code_list.append(xt_symbol)
    if len(xt_code_list) > 0:
        start: str = start.strftime("%Y%m%d")
        end: str = end.strftime("%Y%m%d")
        data = xtdata.get_local_data([], xt_code_list, xt_interval, start, end, -1, "front_ratio",
                                     False)  # 默认等比前复权

        index = 0
        count = 0
        while index < len(xt_code_list):
            last = min(index + step, len(xt_code_list))
            codes = xt_code_list[index:last]
            for code in codes:
                symbol, exchange = to_vn_contract(code)
                insert_bar_history(symbol, exchange, interval, history, data[code])
                count += 1
            progress = count / len(xt_code_list)
            progress_bar: str = "#" * int(progress * 10 + 1)
            output("bar加载: {} [{:.0%}]".format(progress_bar, progress))
            index = last
    return history


@lru_cache(typed=True)
def get_tick_data(start: datetime, end: datetime, output: Callable = print, step=10) -> Optional[List[TickData]]:
    history: list[TickData] = []
    interval = Interval.TICK
    xt_interval: str = INTERVAL_VT2XT.get(interval, None)
    if not xt_interval:
        output(f"迅投研查询历史数据失败：不支持的时间周期{interval.value}")
        return []

    code_infos: List[List[SubscribeRequest]] = get_bond_info(end)
    [bond_infos, stock_infos] = code_infos

    xt_code_list = []
    for code in bond_infos + stock_infos:
        # 从服务器下载获取
        xt_symbol: str = code.symbol + "." + EXCHANGE_VT2XT[code.exchange]
        xt_code_list.append(xt_symbol)

    if len(xt_code_list) > 0:
        start: str = start.strftime("%Y%m%d")
        end: str = end.strftime("%Y%m%d")

        index = 0
        count = 0
        while index < len(xt_code_list):
            last = min(index + step, len(xt_code_list))
            codes = xt_code_list[index:last]
            data = xtdata.get_local_data([], codes, xt_interval, start, end, -1, "front_ratio",
                                         False)  # 默认等比前复权
            for code in data:
                symbol, exchange = to_vn_contract(code)
                insert_tick_history(symbol, exchange, history, data[code])
                count += 1
            progress = count / len(xt_code_list)
            progress_bar: str = "#" * int(progress * 10 + 1)
            output("tick加载：{} [{:.0%}]".format(progress_bar, progress))
            index = last
    return history


def download_daily_data(start: datetime, end: datetime, interval: Interval, output: Callable = print):
    xt_interval: str = INTERVAL_VT2XT.get(interval, None)
    if not xt_interval:
        output(f"迅投研查询历史数据失败：不支持的时间周期{interval.value}")
        return {}

    code_infos: List[List[SubscribeRequest]] = get_bond_info(end)
    [bond_infos, stock_infos] = code_infos

    daily_list = []
    start: str = start.strftime("%Y%m%d")
    end: str = end.strftime("%Y%m%d")
    for bond in bond_infos:
        # 从服务器下载获取
        xt_symbol: str = bond.symbol + "." + EXCHANGE_VT2XT[bond.exchange]
        daily_list.append(xt_symbol)
    for stock in stock_infos:
        # 从服务器下载获取
        xt_symbol: str = stock.symbol + "." + EXCHANGE_VT2XT[stock.exchange]
        daily_list.append(xt_symbol)

    def out_process(data):
        finished = data["finished"]
        total = data["total"]
        message = data["message"]
        progress = finished / total
        progress_bar: str = "#" * int(progress * 10 + 1)

        output("bar下载：{} {} [{:.0%}]".format(message, progress_bar, progress))

    if len(daily_list) > 0:
        xtdata.download_history_data2(daily_list, xt_interval, start, end, out_process)


def download_tick_data(tick_donwload_info: dict[str, set], start: datetime, output: Callable = print):
    interval = Interval.TICK
    xt_interval: str = INTERVAL_VT2XT.get(interval, None)
    if not xt_interval:
        output(f"迅投研查询历史数据失败：不支持的时间周期{interval.value}")
        return {}

    code_infos: List[List[SubscribeRequest]] = get_bond_info(start)
    [bond_infos, stock_infos] = code_infos

    tick_list = []
    start: str = start.strftime("%Y%m%d")
    end: str = start
    for bond in bond_infos:
        # 从服务器下载获取
        xt_symbol: str = bond.symbol + "." + EXCHANGE_VT2XT[bond.exchange]
        if start not in tick_donwload_info[xt_symbol]:
            tick_list.append(xt_symbol)

    for stock in stock_infos:
        # 从服务器下载获取
        xt_symbol: str = stock.symbol + "." + EXCHANGE_VT2XT[stock.exchange]
        if start not in tick_donwload_info[xt_symbol]:
            tick_list.append(xt_symbol)

    def out_process(data):
        finished = data["finished"]
        total = data["total"]
        message = data["message"]
        progress = finished / total
        progress_bar: str = "#" * int(progress * 10 + 1)

        output("tick下载：{} {} [{:.0%}]".format(message, progress_bar, progress))

    if len(tick_list) > 0:
        xtdata.download_history_data2(tick_list, xt_interval, start, end, out_process)


class QmtDatafeed(BaseDatafeed):
    def __init__(self):
        """"""
        self.xt_datafeed = XtDatafeed()
        self.xt_datafeed.username = "client"
        self.tick_donwload_info: dict[str, set] = tick_donwload_file_info()
        self.daily_download_info_file = "daily_download_info.json"
        self.daily_download_info: dict = load_json(self.daily_download_info_file)
        self.daily_timedelta = timedelta(days=6 * 31)

    def query_bar_history(self, req: HistoryRequest, output: Callable = print) -> Optional[List[BarData]]:
        if req.symbol == "沪深转债" and req.interval == Interval.DAILY:
            end: str = req.start.strftime("%Y%m%d")
            start = req.start - self.daily_timedelta
            daily_download_info = self.daily_download_info.get(req.symbol, {})
            # 只下载数据
            if req.exchange == Exchange.DOWNLOAD:
                if end not in daily_download_info:
                    download_daily_data(req.start - self.daily_timedelta, req.start, Interval.DAILY, output)
                    daily_download_info[end] = self.daily_timedelta.days
                    self.daily_download_info[req.symbol] = daily_download_info
                    save_json(self.daily_download_info_file, self.daily_download_info)
                return None
            # 只获取数据
            elif req.exchange == Exchange.GET:
                history: list[BarData] = []
                if end not in daily_download_info:
                    return history
                else:
                    history = get_daily_data(start, req.start, Interval.DAILY, output)
                return history
            else:
                return None
        return self.xt_datafeed.query_bar_history(req, output)

    def query_tick_history(self, req: HistoryRequest, output: Callable = print) -> Optional[List[TickData]]:
        if req.symbol == "沪深转债":
            history: list[TickData] = []
            if req.exchange == Exchange.DOWNLOAD:
                download_tick_data(self.tick_donwload_info, req.start, output)
                self.tick_donwload_info = tick_donwload_file_info()
                return history
            elif req.exchange == Exchange.GET:
                return get_tick_data(req.start, req.start, output)
            else:
                return None
        return self.xt_datafeed.query_bar_history(req, output)


if __name__ == '__main__':
    qmt_datafeed = QmtDatafeed()
    qmt_datafeed.query_tick_history(
        req=HistoryRequest(symbol="沪深转债", exchange=Exchange.DOWNLOAD, start=datetime.now() - timedelta(days=8)),
        output=print)
    history = qmt_datafeed.query_tick_history(
        req=HistoryRequest(symbol="沪深转债", exchange=Exchange.GET, start=datetime.now() - timedelta(days=8)),
        output=print)
    print(len(history))
    qmt_datafeed.query_bar_history(
        req=HistoryRequest(symbol="沪深转债", exchange=Exchange.DOWNLOAD, interval=Interval.DAILY,
                           start=datetime.now()),
        output=print)
    history = qmt_datafeed.query_bar_history(
        req=HistoryRequest(symbol="沪深转债", exchange=Exchange.GET, interval=Interval.DAILY,
                           start=datetime.now()),
        output=print)
    print(len(history))
