from datetime import datetime, timedelta, time

import pandas as pd
from pandas import DataFrame
from xtquant import (
    xtdata
)

from src.gateway.qmt.utils import to_vn_contract
from src.gateway.xt.xt_datafeed import XtDatafeed
from src.trader.constant import Exchange, Interval
from src.trader.object import BarData, TickData, HistoryRequest, SubscribeRequest
from src.trader.utility import ZoneInfo
from src.trader.datafeed import BaseDatafeed
from typing import Callable, Optional, List, Dict

from src.util.bond_util import get_bond_info
from src.util.save_tick_data import on_process, build_donwload_file_info
from src.util.utility import insert_tick_history, insert_bar_history

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


class QmtDatafeed(BaseDatafeed):
    def __init__(self):
        """"""
        self.xt_datafeed = XtDatafeed()
        self.xt_datafeed.username = "client"
        self.donwload_file_info: dict[str, set] = build_donwload_file_info()

    def query_bar_history(self, req: HistoryRequest, output: Callable = print) -> Optional[List[BarData]]:
        if req.exchange != Exchange.LOCAL:
            return self.xt_datafeed.query_bar_history(req, output)
        else:
            history: list[BarData] = []
            if req.symbol == "沪深转债":
                bond_infos: List[List[SubscribeRequest]] = get_bond_info(req.start)
                code_df: dict[str, pd.DataFrame] = get_history_df(self.donwload_file_info, bond_infos, req, output)
                if len(code_df) == 0:
                    return history
                for code in code_df:
                    symbol, exchange = to_vn_contract(code)
                    insert_bar_history(symbol, exchange, req.interval, history, code_df[code])
            return history

    def query_tick_history(self, req: HistoryRequest, output: Callable = print) -> Optional[List[TickData]]:
        req.interval = Interval.TICK
        if req.exchange != Exchange.LOCAL:
            return self.xt_datafeed.query_bar_history(req, output)
        else:
            history: list[TickData] = []
            if req.symbol == "沪深转债":
                bond_infos: List[List[SubscribeRequest]] = get_bond_info(req.start)
                code_df: dict[str, pd.DataFrame] = get_history_df(self.donwload_file_info, bond_infos, req, output)
                if len(code_df) == 0:
                    return history
                progress = 0
                for code in code_df:
                    symbol, exchange = to_vn_contract(code)
                    progress_bar: str = "#" * int(progress * 10 + 1)
                    insert_tick_history(symbol, exchange, history, code_df[code])
                    output("查询进度：{} [{:.0%}]".format(progress_bar, progress))
                    progress += 1 / len(code_df)
            return history


def get_history_df(donwload_file_info: dict[str, set], bond_infos: List[List[SubscribeRequest]], req: HistoryRequest,
                   output: Callable = print) -> Dict[str, pd.DataFrame]:
    """获取历史数据DataFrame"""
    start: datetime = req.start
    end: datetime = req.end
    interval: Interval = req.interval

    if not interval:
        interval = Interval.TICK
    if interval == Interval.TICK:
        end = start.replace(hour=0, minute=0, second=0, microsecond=0)
    xt_interval: str = INTERVAL_VT2XT.get(interval, None)
    if not xt_interval:
        output(f"迅投研查询历史数据失败：不支持的时间周期{interval.value}")
        return {}
    [bond_infos, stock_infos] = bond_infos

    daily_list = []
    tick_list = []
    start: str = start.strftime("%Y%m%d")
    end: str = end.strftime("%Y%m%d")
    for bond in bond_infos:
        # 从服务器下载获取
        xt_symbol: str = bond.symbol + "." + EXCHANGE_VT2XT[bond.exchange]
        daily_list.append(xt_symbol)
        if interval == Interval.TICK:
            if start not in donwload_file_info[xt_symbol]:
                tick_list.append(xt_symbol)
    for stock in stock_infos:
        # 从服务器下载获取
        xt_symbol: str = stock.symbol + "." + EXCHANGE_VT2XT[stock.exchange]
        daily_list.append(xt_symbol)
        if interval == Interval.TICK:
            if start not in donwload_file_info[xt_symbol]:
                tick_list.append(xt_symbol)

    if interval == Interval.TICK:
        if len(tick_list) > 0:
            xtdata.download_history_data2(tick_list, xt_interval, start, end, on_process)
    else:
        if len(daily_list) > 0:
            xtdata.download_history_data2(daily_list, xt_interval, start, end, on_process)
    data: dict[str, pd.DataFrame] = {}
    if len(daily_list) > 0:
        data = xtdata.get_local_data([], daily_list, xt_interval, start, end, -1, "front_ratio",
                                     False)  # 默认等比前复权
    return data


if __name__ == '__main__':
    qmt_datafeed = QmtDatafeed()
    history = qmt_datafeed.query_tick_history(
        req=HistoryRequest(symbol="沪深转债", exchange=Exchange.LOCAL, start=datetime.now() - timedelta(days=7)),
        output=print)
    print(len(history))
    history = qmt_datafeed.query_bar_history(
        req=HistoryRequest(symbol="沪深转债", exchange=Exchange.LOCAL, interval=Interval.DAILY, start=datetime.now() - timedelta(days=6 * 31), end=datetime.now()),
        output=print)
    print(len(history))
