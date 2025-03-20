from pathlib import Path

from src.trader.app import BaseApp
from src.trader.constant import Direction
from src.trader.object import TickData, BarData, TradeData, OrderData
from src.trader.utility import BarGenerator, ArrayManager

from .base import APP_NAME, StopOrder

from .engine import SmartMoneyEngine


# from .template import CtaTemplate, CtaSignal, TargetPosTemplate
#

class SmartMoneyStrategyApp(BaseApp):
    """"""

    app_name = APP_NAME
    app_module = __name__
    app_path = Path(__file__).parent
    display_name = "SmartMoney策略"
    engine_class = SmartMoneyEngine
    widget_name = "SmartMoneyManager"
    icon_name = "SM.ico"
