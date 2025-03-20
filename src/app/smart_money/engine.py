""""""

import importlib
import os
import traceback
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable
from datetime import datetime, timedelta
from threading import Thread
from queue import Queue
from copy import copy

from src.event import Event, EventEngine
from src.trader.engine import BaseEngine, MainEngine
from src.trader.object import (
    OrderRequest,
    SubscribeRequest,
    LogData,
    TickData,
    BarData,
    ContractData
)
from src.trader.event import (
    EVENT_TICK,
    EVENT_ORDER,
    EVENT_TRADE,
    EVENT_POSITION
)
from src.trader.constant import (
    Direction,
    OrderType,
    Interval,
    Exchange,
    Offset,
    Status
)
from src.trader.utility import load_json, save_json
from src.trader.database import DbTickData, DbBarData
from src.trader.setting import SETTINGS

from .base import (
    EVENT_SM_LOG,
    EVENT_SM_STRATEGY,
    EVENT_SM_STOPORDER,
    EngineType,
    StopOrder,
    StopOrderStatus,
    STOPORDER_PREFIX
)

# from .template import CtaTemplate
# from .converter import OffsetConverter


STOP_STATUS_MAP = {
    Status.SUBMITTING: StopOrderStatus.WAITING,
    Status.NOTTRADED: StopOrderStatus.WAITING,
    Status.PARTTRADED: StopOrderStatus.TRIGGERED,
    Status.ALLTRADED: StopOrderStatus.TRIGGERED,
    Status.CANCELLED: StopOrderStatus.CANCELLED,
    Status.REJECTED: StopOrderStatus.CANCELLED
}


class SmartMoneyEngine(BaseEngine):
    """"""

    engine_type = EngineType.LIVE  # live trading engine

    setting_filename = "cta_strategy_setting.json"
    data_filename = "cta_strategy_data.json"

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine) -> None:
        super(SmartMoneyEngine, self).__init__(
            main_engine, event_engine, "SmartMoneyStrategy")

    def init_engine(self):
        pass

    def close(self) -> None:
        pass


def to_rq_symbol(vt_symbol: str):
    """
    CZCE product of RQData has symbol like "TA1905" while
    vt symbol is "TA905.CZCE" so need to add "1" in symbol.
    """
    symbol, exchange_str = vt_symbol.split(".")
    if exchange_str != "CZCE":
        return symbol.upper()

    for count, word in enumerate(symbol):
        if word.isdigit():
            break

    product = symbol[:count]
    year = symbol[count]
    month = symbol[count + 1:]

    if year == "9":
        year = "1" + year
    else:
        year = "2" + year

    rq_symbol = f"{product}{year}{month}".upper()
    return rq_symbol
