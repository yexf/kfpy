from pathlib import Path

from src.trader.app import BaseApp

from .base import APP_NAME, StopOrder

from .engine import VolPriceEngine


# from .template import CtaTemplate, CtaSignal, TargetPosTemplate
#

class VolPriceStrategyApp(BaseApp):
    """"""

    app_name = APP_NAME
    app_module = __name__
    app_path = Path(__file__).parent
    display_name = "量价策略"
    engine_class = VolPriceEngine
    widget_name = "VolPriceManager"
    icon_name = "SM.ico"
