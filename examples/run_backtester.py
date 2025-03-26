from src.event import EventEngine
from src.trader.engine import MainEngine
from src.trader.ui import MainWindow, create_qapp

from src.gateway.xt import XtGateway
from src.app.datamanager import DataManagerApp
from src.app.cta_backtester import CtaBacktesterApp
from src.app.vp_backtester import VPBacktesterApp


def main():
    """主入口函数"""
    qapp = create_qapp()

    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)
    main_engine.add_gateway(XtGateway)
    main_engine.add_app(CtaBacktesterApp)
    main_engine.add_app(VPBacktesterApp)
    main_engine.add_app(DataManagerApp)

    main_window = MainWindow(main_engine, event_engine)
    main_window.showMaximized()

    qapp.exec()


if __name__ == "__main__":
    main()
