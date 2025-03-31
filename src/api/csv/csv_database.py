from datetime import datetime
from typing import List

from src.trader.constant import Exchange, Interval
from src.trader.database import BaseDatabase, TickOverview, BarOverview
from src.trader.object import TickData, BarData


class CsvDatabase(BaseDatabase):
    def save_bar_data(self, bars: List[BarData], stream: bool = False) -> bool:
        pass

    def save_tick_data(self, ticks: List[TickData], stream: bool = False) -> bool:
        pass

    def load_bar_data(self, symbol: str, exchange: Exchange, interval: Interval, start: datetime, end: datetime) -> List[BarData]:
        pass

    def load_tick_data(self, symbol: str, exchange: Exchange, start: datetime, end: datetime) -> List[TickData]:
        pass

    def delete_bar_data(self, symbol: str, exchange: Exchange, interval: Interval) -> int:
        pass

    def delete_tick_data(self, symbol: str, exchange: Exchange) -> int:
        pass

    def get_bar_overview(self) -> List[BarOverview]:
        pass

    def get_tick_overview(self) -> List[TickOverview]:
        pass