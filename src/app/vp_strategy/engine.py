""""""

from src.event import EventEngine
from src.trader.engine import BaseEngine, MainEngine
from src.trader.constant import (
    Status
)

from .base import (
    EngineType,
    StopOrderStatus
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


class VolPriceEngine(BaseEngine):
    """"""

    engine_type = EngineType.LIVE  # live trading engine

    setting_filename = "cta_strategy_setting.json"
    data_filename = "cta_strategy_data.json"

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine) -> None:
        super(VolPriceEngine, self).__init__(
            main_engine, event_engine, "SmartMoneyStrategy")

    def init_engine(self):
        pass

    def close(self) -> None:
        pass

