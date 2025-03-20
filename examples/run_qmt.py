import multiprocessing
import sys
from time import sleep
from datetime import datetime, time
from logging import INFO
from typing import Union

from src.event import EventEngine
from src.trader.setting import SETTINGS
from src.trader.engine import MainEngine, LogEngine, BaseEngine

from src.api.qmt import QmtGateway
from src.app.smart_money import SmartMoneyStrategyApp, SmartMoneyEngine
from src.app.smart_money.base import EVENT_SM_LOG

SETTINGS["log.active"] = True
SETTINGS["log.level"] = INFO
SETTINGS["log.console"] = True

ctp_setting = {
    "用户名": "",
    "密码": "",
    "经纪商代码": "",
    "交易服务器": "",
    "行情服务器": "",
    "产品名称": "",
    "授权编码": "",
    "产品信息": ""
}

# Chinese futures market trading period (day/night)
DAY_START = time(9, 30)
DAY_END = time(15, 0)

NIGHT_START = time(20, 45)
NIGHT_END = time(2, 45)


def check_trading_period():
    """"""
    current_time = datetime.now().time()

    trading = False
    if ((current_time >= DAY_START and current_time <= DAY_END)):
        trading = True

    return trading


def run_child():
    """
    Running in the child process.
    """
    SETTINGS["log.file"] = True

    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)
    main_engine.add_gateway(QmtGateway)
    sm_engine: Union[SmartMoneyEngine, BaseEngine] = main_engine.add_app(SmartMoneyStrategyApp)
    main_engine.write_log("主引擎创建成功")

    log_engine: Union[LogEngine, BaseEngine] = main_engine.get_engine("log")
    event_engine.register(EVENT_SM_LOG, log_engine.process_log_event)
    main_engine.write_log("注册日志事件监听")

    main_engine.connect(None, "QMT")
    main_engine.write_log("连接QMT接口")

    sleep(10)

    sm_engine.init_engine()
    main_engine.write_log("SM策略初始化完成")

    while True:
        sleep(10)

        trading = check_trading_period()
        if not trading:
            print("关闭子进程")
            main_engine.close()
            sys.exit(0)


def run_parent():
    """
    Running in the parent process.
    """
    print("启动SmartMoney策略守护父进程")

    child_process = None

    while True:
        trading = check_trading_period()

        # Start child process in trading period
        if trading and child_process is None:
            print("启动子进程")
            child_process = multiprocessing.Process(target=run_child)
            child_process.start()
            print("子进程启动成功")

        # 非记录时间则退出子进程
        if not trading and child_process is not None:
            if not child_process.is_alive():
                child_process = None
                print("子进程关闭成功")

        sleep(5)


if __name__ == "__main__":
    run_parent()
