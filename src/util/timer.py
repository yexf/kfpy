import time
from typing import Union

from datetime import datetime


def timestamp_us(dt):
    """将 utc 时间 (datetime 格式) 转为 utc 时间戳
    :param dt: {datetime}2016-02-25 20:21:04.242000
    :return: 13位 的毫秒时间戳 1456431664242
    """
    ts = float(time.mktime(dt.timetuple())) * 1000 + dt.microsecond / 1000.0
    return ts


def timestamp_s(dt):
    return int(time.mktime(dt.timetuple())) * 1000


def timestamp(dt=None):
    if dt is None:
        dt = now()
        return timestamp_us(dt)
    return timestamp_s(dt)


def from_timestamp(ts: Union[float, int]):
    """将 13 位整数的毫秒时间戳转化成 utc 时间 (字符串格式，含毫秒)
    :param ts: 13 位整数的毫秒时间戳 (1456402864242)
    :return: 返回字符串格式 {str}'2016-02-25 12:21:04.242000'
    """
    return datetime.fromtimestamp(ts / 1000.0)


def from_strtime(timestr):
    local_datetime = datetime.strptime(timestr, "%Y-%m-%d %H:%M:%S.%f")
    return local_datetime


def now():
    now_time = datetime.now()
    return now_time


def to_tick_market_str(dt: datetime) -> str:
    return dt.strftime("%Y%m%d%H%M%S")


def to_date_str(dt: datetime) -> str:
    return dt.strftime("%Y%m%d")


def to_time_str(dt: datetime) -> str:
    return dt.strftime("%H%M%S.%f")


def to_timetag(dt: datetime) -> str:
    return dt.strftime("%Y%m%d %H:%M:%S")


def from_date(timestr) -> datetime:
    return datetime.strptime(timestr, "%Y%m%d")


def from_timetag(timestr):
    local_datetime = datetime.strptime(timestr, "%Y%m%d %H:%M:%S")
    return timestamp_s(local_datetime)
