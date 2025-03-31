"""
General utility functions.
"""
import datetime
import json
import os
from collections import namedtuple
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Union
from zoneinfo import ZoneInfo

from pandas import DataFrame
from xtquant import xtdata

from src.trader.constant import Exchange, Interval
from src.trader.object import TickData, BarData
from src.trader.utility import load_json, save_json


def locate(word):
    return word


def get_util_file_path(filename: str) -> Path:
    current_script_path = Path(__file__).resolve()

    # 获取当前脚本所在的文件夹路径
    current_script_folder = current_script_path.parent
    temp_path: Path = current_script_folder.joinpath(filename)
    return temp_path


def save_util_json(filename: str, data: dict) -> None:
    """
    Save data into json file in temp path.
    """
    filepath: Path = get_util_file_path(filename)
    with open(filepath, mode="w+", encoding="UTF-8") as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


def load_util_json(filename: str) -> [object, dict]:
    """
    Load data from json file in temp path.
    """
    filepath: Path = get_util_file_path(filename)

    if filepath.exists():
        with open(filepath, mode="r", encoding="UTF-8") as f:
            datastr = f.read()
            data: object = json.loads(datastr, object_hook=lambda dic: namedtuple("X", dic.keys())(*dic.values()))
        return data, json.loads(datastr)
    else:
        save_util_json(filename, {})
        return {}, {}


def is_need_update(filename: str):
    current_date = str(datetime.now().date())
    contract = load_json(filename)
    if "date" in contract and contract["date"] == current_date:
        return False
    else:
        return True


def update_data(filename: str, data: Union[dict, list]) -> None:
    current_date = str(datetime.now().date())
    json_dict = {"data": data, "date": current_date}
    save_json(filename, json_dict)


def get_data(filename: str) -> Union[dict, list]:
    json_dict = load_json(filename)
    if "data" in json_dict:
        return json_dict["data"]
    else:
        return {}


def get_data_path():
    client = xtdata.get_client()
    client_data_dir = client.get_data_dir()
    data_path = os.path.abspath(client_data_dir)
    return data_path


def get_qmt_config() -> dict:
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

INTERVAL_ADJUSTMENT_MAP: dict[Interval, timedelta] = {
    Interval.MINUTE: timedelta(minutes=1),
    Interval.DAILY: timedelta()         # 日线无需进行调整
}
CHINA_TZ = ZoneInfo("Asia/Shanghai")
def insert_bar_history(symbol: str, exchange: Exchange, interval: Interval, history: list[BarData], df: DataFrame):
    # 遍历解析
    auction_bar: BarData = None
    adjustment: datetime.timedelta = INTERVAL_ADJUSTMENT_MAP[interval]
    for tp in df.itertuples():
        # 将迅投研时间戳（K线结束时点）转换为VeighNa时间戳（K线开始时点）
        dt: datetime = datetime.fromtimestamp(tp.time / 1000)
        dt = dt.replace(tzinfo=CHINA_TZ)
        dt = dt - adjustment

        # 日线，过滤尚未走完的当日数据
        if interval == Interval.DAILY:
            incomplete_bar: bool = (dt.date() == datetime.now().date()
                                    and datetime.now().time() < time(hour=15))
            if incomplete_bar:
                continue
        # 分钟线，过滤盘前集合竞价数据（合并到开盘后第1根K线中）
        else:
            if ((exchange in (Exchange.SSE, Exchange.SZSE, Exchange.BSE, Exchange.CFFEX)
                 and dt.time() == time(hour=9, minute=29))
                    or (exchange in (Exchange.SHFE, Exchange.INE, Exchange.DCE, Exchange.CZCE, Exchange.GFEX)
                        and dt.time() in (time(hour=8, minute=59), time(hour=20, minute=59)))):
                auction_bar = BarData(
                    symbol=symbol,
                    exchange=exchange,
                    datetime=dt,
                    open_price=float(tp.open),
                    volume=float(tp.volume),
                    turnover=float(tp.amount),
                    gateway_name="XT"
                )
                continue

        # 生成K线对象
        bar: BarData = BarData(
            symbol=symbol,
            exchange=exchange,
            datetime=dt,
            interval=interval,
            volume=float(tp.volume),
            turnover=float(tp.amount),
            open_interest=float(tp.openInterest),
            open_price=float(tp.open),
            high_price=float(tp.high),
            low_price=float(tp.low),
            close_price=float(tp.close),
            gateway_name="XT"
        )

        # 合并集合竞价数据
        if auction_bar and auction_bar.volume:
            bar.open_price = auction_bar.open_price
            bar.volume += auction_bar.volume
            bar.turnover += auction_bar.turnover
            auction_bar = None

        history.append(bar)


def insert_tick_history(symbol: str, exchange: Exchange, history: list[TickData], df: DataFrame):
    # 遍历解析
    for tp in df.itertuples():
        dt: datetime = datetime.fromtimestamp(tp.time / 1000)
        dt = dt.replace(tzinfo=CHINA_TZ)
        tick: TickData = TickData(
            symbol=symbol,
            exchange=exchange,
            datetime=dt,
            volume=float(tp.volume),
            turnover=float(tp.amount),
            open_interest=float(tp.openInt),
            open_price=float(tp.open),
            high_price=float(tp.high),
            low_price=float(tp.low),
            last_price=float(tp.lastPrice),
            pre_close=float(tp.lastClose),
            bid_price_1=float(tp.bidPrice[0]),
            ask_price_1=float(tp.askPrice[0]),
            bid_volume_1=float(tp.bidVol[0]),
            ask_volume_1=float(tp.askVol[0]),
            gateway_name="XT",
        )

        bid_price_2: float = float(tp.bidPrice[1])
        if bid_price_2:
            tick.bid_price_2 = bid_price_2
            tick.bid_price_3 = float(tp.bidPrice[2])
            tick.bid_price_4 = float(tp.bidPrice[3])
            tick.bid_price_5 = float(tp.bidPrice[4])

            tick.ask_price_2 = float(tp.askPrice[1])
            tick.ask_price_3 = float(tp.askPrice[2])
            tick.ask_price_4 = float(tp.askPrice[3])
            tick.ask_price_5 = float(tp.askPrice[4])

            tick.bid_volume_2 = float(tp.bidVol[1])
            tick.bid_volume_3 = float(tp.bidVol[2])
            tick.bid_volume_4 = float(tp.bidVol[3])
            tick.bid_volume_5 = float(tp.bidVol[4])

            tick.ask_volume_2 = float(tp.askVol[1])
            tick.ask_volume_3 = float(tp.askVol[2])
            tick.ask_volume_4 = float(tp.askVol[3])
            tick.ask_volume_5 = float(tp.askVol[4])

        history.append(tick)
