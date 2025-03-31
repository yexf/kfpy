from datetime import datetime, timedelta
from functools import lru_cache
from typing import Optional, List, Callable, Dict, Union
from src.gateway.qmt.utils import to_vn_contract
from src.trader.constant import Interval, Exchange
from src.trader.database import TickOverview, BarOverview, BaseDatabase, get_database
from src.trader.datafeed import BaseDatafeed
from src.trader.object import SubscribeRequest, SectorHistoryRequest, SectorData, HistoryRequest, BarData, TickData, \
    SectorDataItem
from src.util.save_tick_data import conv_bond_info


def get_live_bond_info(dt):
    bond_infos: list[SubscribeRequest] = []
    stock_infos: list[SubscribeRequest] = []
    format_str = "%Y-%m-%d %H:%M:%S"
    for bi in conv_bond_info:
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
    return bond_infos, stock_infos


def build_sector_data(req: SectorHistoryRequest) -> Union[SectorData, None]:
    if req.sector == "沪深转债":
        bond_infos, stock_infos = get_live_bond_info(req.date)
        contract_list = bond_infos + stock_infos
        return SectorData(sector=req.sector,
                          gateway_name="XT",
                          contract_list=contract_list,
                          date=req.date,
                          data={})
    else:
        return None


def download_bond_data(database: BaseDatabase, datafeed: BaseDatafeed, sd: SectorData, output: Callable):
    tick_overview: list[TickOverview] = database.get_tick_overview()
    bar_overview: list[BarOverview] = database.get_bar_overview()
    tick_overview_dict: dict[str, TickOverview] = {}
    bar_overview_dict: dict[str, bar_overview] = {}
    for tick in tick_overview:
        vt_symbol: str = f"{tick.symbol}.{tick.exchange.value}"
        tick_overview_dict[vt_symbol] = tick
    for bar in bar_overview:
        vt_symbol: str = f"{bar.symbol}.{bar.exchange.value}"
        bar_overview_dict[vt_symbol] = bar
    progress = 0
    for code in sd.contract_list:
        vt_symbol: str = code.vt_symbol
        progress_bar: str = "#" * int(progress * 10 + 1)
        tick_req: HistoryRequest = HistoryRequest(
            symbol=code.symbol,
            exchange=code.exchange,
            start=sd.date + timedelta(hours=9, minutes=30),
            end=sd.date + timedelta(hours=15),
            interval=Interval.TICK
        )
        daily_req: HistoryRequest = HistoryRequest(
            symbol=code.symbol,
            exchange=code.exchange,
            start=sd.date - timedelta(days=30 * 6),
            end=sd.date,
            interval=Interval.DAILY
        )
        sdi = SectorDataItem(tick_data=[], daily_data=[])
        if vt_symbol not in tick_overview_dict:
            download_flag = True
        else:
            tick_ov: TickOverview = tick_overview_dict[vt_symbol]
            if tick_req.start < tick_ov.start or tick_req.end > tick_ov.end:
                download_flag = True
            else:
                download_flag = False
        if download_flag:
            sdi.tick_data = datafeed.query_tick_history(tick_req, output)
            if len(sdi.tick_data) > 0:
                database.save_tick_data(sdi.tick_data, True)

            output("下载进度：{} [{:.0%}]".format(progress_bar, progress))
        if vt_symbol not in bar_overview_dict:
            download_flag = True
        else:
            bar_ov: BarOverview = bar_overview_dict[vt_symbol]
            if daily_req.end <= bar_ov.end:
                download_flag = False
            else:
                download_flag = True
        if download_flag:
            sdi.bar_data = datafeed.query_bar_history(daily_req, output)
            if len(sdi.bar_data) > 0:
                database.save_bar_data(sdi.bar_data)
            output("下载进度：{} [{:.0%}]".format(progress_bar, progress))
        progress += 1 / len(sd.contract_list)
        progress = min(progress, 1)


@lru_cache(maxsize=999, typed=True)
def load_sector_data_item(
        symbol: str,
        exchange: Exchange,
        date: datetime,
) -> SectorDataItem:
    """"""
    database: BaseDatabase = get_database()
    daily_data: List[BarData] = database.load_bar_data(
        symbol=symbol,
        exchange=exchange,
        interval=Interval.DAILY,
        start=date - timedelta(days=30 * 6),
        end=date,
    )
    tick_data: List[TickData] = database.load_tick_data(
        symbol=symbol,
        exchange=exchange,
        start=date + timedelta(hours=9, minutes=30),
        end=date + timedelta(hours=15),
    )
    return SectorDataItem(tick_data=tick_data, daily_data=daily_data)


def load_bond_data(sector_data: SectorData, output: Callable):
    progress = 0
    for code in sector_data.contract_list:
        progress_bar: str = "#" * int(progress * 10 + 1)
        output("加载进度：{} [{:.0%}]".format(progress_bar, progress))
        sector_data.data[code.vt_symbol] = load_sector_data_item(code.symbol, code.exchange, sector_data.date)

        progress += 1 / len(sector_data.contract_list)
        progress = min(progress, 1)
