from datetime import datetime, timedelta, time
from typing import Optional, Callable

from pandas import DataFrame
from xtquant import (
    xtdata,
    xtdatacenter as xtdc
)
from filelock import FileLock, Timeout

from src.trader.setting import SETTINGS
from src.trader.constant import Exchange, Interval
from src.trader.object import BarData, TickData, HistoryRequest
from src.trader.utility import ZoneInfo, get_file_path
from src.trader.datafeed import BaseDatafeed
from src.util.utility import insert_tick_history, insert_bar_history

INTERVAL_VT2XT: dict[Interval, str] = {
    Interval.MINUTE: "1m",
    Interval.DAILY: "1d",
    Interval.TICK: "tick"
}

INTERVAL_ADJUSTMENT_MAP: dict[Interval, timedelta] = {
    Interval.MINUTE: timedelta(minutes=1),
    Interval.DAILY: timedelta()         # 日线无需进行调整
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


class XtDatafeed(BaseDatafeed):
    """迅投研数据服务接口"""

    lock_filename = "xt_lock"
    lock_filepath = get_file_path(lock_filename)

    def __init__(self):
        """"""
        self.username: str = SETTINGS["datafeed.username"]
        self.password: str = SETTINGS["datafeed.password"]
        self.inited: bool = False

        self.lock: FileLock = None

        xtdata.enable_hello = False

    def init(self, output: Callable = print) -> bool:
        """初始化"""
        if self.inited:
            return True

        try:
            # 使用Token连接，无需启动客户端
            if self.username != "client":
                self.init_xtdc()

            # 尝试查询合约信息，确认连接成功
            xtdata.get_instrument_detail("000001.SZ")
        except Exception as ex:
            output(f"迅投研数据服务初始化失败，发生异常：{ex}")
            return False

        self.inited = True
        return True

    def get_lock(self) -> bool:
        """获取文件锁，确保单例运行"""
        self.lock = FileLock(self.lock_filepath)

        try:
            self.lock.acquire(timeout=1)
            return True
        except Timeout:
            return False

    def init_xtdc(self) -> None:
        """初始化xtdc服务进程"""
        if not self.get_lock():
            return

        # 设置token
        xtdc.set_token(self.password)

        # 设置连接池
        xtdc.set_allow_optmize_address(["115.231.218.73:55310", "115.231.218.79:55310"])

        # 开启使用期货真实夜盘时间
        xtdc.set_future_realtime_mode(True)

        # 执行初始化，但不启动默认58609端口监听
        xtdc.init(False)

        # 设置监听端口58620
        xtdc.listen(port=58620)

    def query_bar_history(self, req: HistoryRequest, output: Callable = print) -> Optional[list[BarData]]:
        """查询K线数据"""
        history: list[BarData] = []

        if not self.inited:
            n: bool = self.init(output)
            if not n:
                return history

        df: DataFrame = get_history_df(req, output)
        if df.empty:
            return history

        adjustment: timedelta = INTERVAL_ADJUSTMENT_MAP[req.interval]
        insert_bar_history(req.symbol, req.exchange, req.interval, history, df)

        return history

    def query_tick_history(self, req: HistoryRequest, output: Callable = print) -> Optional[list[TickData]]:
        """查询Tick数据"""
        history: list[TickData] = []

        if not self.inited:
            n: bool = self.init(output)
            if not n:
                return history

        df: DataFrame = get_history_df(req, output)
        if df.empty:
            return history
        insert_tick_history(req.symbol, req.exchange, history, df)
        return history


def get_history_df(req: HistoryRequest, output: Callable = print) -> DataFrame:
    """获取历史数据DataFrame"""
    symbol: str = req.symbol
    exchange: Exchange = req.exchange
    start: datetime = req.start
    end: datetime = req.end
    interval: Interval = req.interval

    if not interval:
        interval = Interval.TICK

    xt_interval: str = INTERVAL_VT2XT.get(interval, None)
    if not xt_interval:
        output(f"迅投研查询历史数据失败：不支持的时间周期{interval.value}")
        return DataFrame()

    # 为了查询夜盘数据
    end += timedelta(1)

    # 从服务器下载获取
    xt_symbol: str = symbol + "." + EXCHANGE_VT2XT[exchange]
    start: str = start.strftime("%Y%m%d%H%M%S")
    end: str = end.strftime("%Y%m%d%H%M%S")

    if exchange in (Exchange.SSE, Exchange.SZSE) and len(symbol) > 6:
        xt_symbol += "O"

    xtdata.download_history_data(xt_symbol, xt_interval, start, end)
    data: dict = xtdata.get_local_data([], [xt_symbol], xt_interval, start, end, -1, "front_ratio", False)      # 默认等比前复权

    df: DataFrame = data[xt_symbol]
    return df
