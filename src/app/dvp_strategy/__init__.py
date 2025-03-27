from pathlib import Path

from src.trader.app import BaseApp
from src.trader.constant import Direction
from src.trader.object import TickData, BarData, TradeData, OrderData
from src.trader.utility import BarGenerator, ArrayManager

from .base import APP_NAME, StopOrder

from .engine import DVPEngine
from .template import DVPTemplate

class DVPStrategyApp(BaseApp):
    """"""

    app_name = APP_NAME
    app_module = __name__
    app_path = Path(__file__).parent
    display_name = "日内量价策略"
    engine_class = DVPEngine
    widget_name = "DVPManager"
    icon_name = str(app_path.joinpath("ui", "dvp.ico"))
