from ast import List
import importlib
import traceback
from datetime import datetime, timedelta
from threading import Thread
from pathlib import Path
from inspect import getfile
from glob import glob
from types import ModuleType
from pandas import DataFrame
from typing import Optional

from src.app.dvp_strategy import DVPTemplate
from src.event import Event, EventEngine
from src.gateway.qmt.utils import to_vn_contract, get_live_bond_info
from src.trader.engine import BaseEngine, MainEngine
from src.trader.constant import Interval
from src.trader.utility import extract_vt_symbol
from src.trader.object import HistoryRequest, TickData, ContractData, BarData, SectorHistoryRequest, SectorData
from src.trader.datafeed import BaseDatafeed, get_datafeed
from src.trader.database import BaseDatabase, get_database, TickOverview, BarOverview

import src.app.dvp_strategy
from src.app.dvp_strategy.backtesting import (
    DVPBacktestingEngine,
    OptimizationSetting,
    BacktestingMode
)
from src.util.data_tool.eastmoney_bond import get_bond_info
from src.util.utility import locate as _

APP_NAME = "DVPBacktester"

EVENT_BACKTESTER_LOG = "eBacktesterLog"
EVENT_BACKTESTER_BACKTESTING_FINISHED = "eBacktesterBacktestingFinished"
EVENT_BACKTESTER_OPTIMIZATION_FINISHED = "eBacktesterOptimizationFinished"

conv_bond_info = get_bond_info("conv_bond_all.json")
class BacktesterEngine(BaseEngine):
    """
    For running DVP strategy backtesting.
    """

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine) -> None:
        """"""
        super().__init__(main_engine, event_engine, APP_NAME)

        self.classes: dict = {}
        self.backtesting_engine: DVPBacktestingEngine = None
        self.thread: Thread = None

        self.datafeed: BaseDatafeed = get_datafeed()
        self.database: BaseDatabase = get_database()

        # Backtesting reuslt
        self.result_df: DataFrame = None
        self.result_statistics: dict = None

        # Optimization result
        self.result_values: list = None

    def init_engine(self) -> None:
        """"""
        self.write_log(_("初始化DVP回测引擎"))

        self.backtesting_engine = DVPBacktestingEngine()
        # Redirect log from backtesting engine outside.
        self.backtesting_engine.output = self.write_log

        self.load_strategy_class()
        self.write_log(_("策略文件加载完成"))

        self.init_datafeed()

    def init_datafeed(self) -> None:
        """
        Init datafeed client.
        """
        result: bool = self.datafeed.init(self.write_log)
        if result:
            self.write_log(_("数据服务初始化成功"))

    def write_log(self, msg: str) -> None:
        """"""
        event: Event = Event(EVENT_BACKTESTER_LOG)
        event.data = msg
        self.event_engine.put(event)

    def load_strategy_class(self) -> None:
        """
        Load strategy class from source code.
        """
        app_path: Path = Path(src.app.dvp_strategy.__file__).parent
        path1: Path = app_path.joinpath("strategies")
        self.load_strategy_class_from_folder(path1, "src.app.dvp_strategy.strategies")

        path2: Path = Path.cwd().joinpath("strategies")
        self.load_strategy_class_from_folder(path2, "strategies")

    def load_strategy_class_from_folder(self, path: Path, module_name: str = "") -> None:
        """
        Load strategy class from certain folder.
        """
        for suffix in ["py", "pyd", "so"]:
            pathname: str = str(path.joinpath(f"*.{suffix}"))
            for filepath in glob(pathname):
                filename: str = Path(filepath).stem
                name: str = f"{module_name}.{filename}"
                self.load_strategy_class_from_module(name)

    def load_strategy_class_from_module(self, module_name: str) -> None:
        """
        Load strategy class from module file.
        """
        try:
            module: ModuleType = importlib.import_module(module_name)

            # 重载模块，确保如果策略文件中有任何修改，能够立即生效。
            importlib.reload(module)

            for name in dir(module):
                value = getattr(module, name)
                if (
                        isinstance(value, type)
                        and issubclass(value, DVPTemplate)
                        and value not in {DVPTemplate}
                ):
                    self.classes[value.__name__] = value
        except:  # noqa
            msg: str = _("策略文件{}加载失败，触发异常：\n{}").format(
                module_name, traceback.format_exc()
            )
            self.write_log(msg)

    def reload_strategy_class(self) -> None:
        """"""
        self.classes.clear()
        self.load_strategy_class()
        self.write_log(_("策略文件重载刷新完成"))

    def get_strategy_class_names(self) -> list:
        """"""
        return list(self.classes.keys())

    def run_backtesting(
            self,
            class_name: str,
            section: str,
            choose_strategy: str,
            backtester_date: datetime,
            rate: float,
            slippage: float,
            size: int,
            pricetick: float,
            capital: int,
            setting: dict
    ) -> None:
        """"""
        self.result_df = None
        self.result_statistics = None

        engine: DVPBacktestingEngine = self.backtesting_engine
        engine.clear_data()
        mode: BacktestingMode = BacktestingMode.TICK
        engine.set_parameters(
            section=section,
            choose_strategy=choose_strategy,
            backtester_date=backtester_date,
            rate=rate,
            slippage=slippage,
            size=size,
            pricetick=pricetick,
            capital=capital,
            mode=mode
        )

        strategy_class: type[DVPTemplate] = self.classes[class_name]
        engine.add_strategy(
            strategy_class,
            setting
        )

        engine.load_data()
        if not engine.history_data:
            self.write_log(_("策略回测失败，历史数据为空"))
            self.thread = None
            return

        try:
            engine.run_backtesting()
        except Exception:
            msg: str = _("策略回测失败，触发异常：\n{}").format(traceback.format_exc())
            self.write_log(msg)

            self.thread = None
            return

        self.result_df = engine.calculate_result()
        self.result_statistics = engine.calculate_statistics(output=False)

        # Clear thread object handler.
        self.thread = None

        # Put backtesting done event
        event: Event = Event(EVENT_BACKTESTER_BACKTESTING_FINISHED)
        self.event_engine.put(event)

    def start_backtesting(
            self,
            class_name: str,
            section: str,
            choose_strategy: str,
            backtester_date: datetime,
            rate: float,
            slippage: float,
            size: int,
            pricetick: float,
            capital: int,
            setting: dict
    ) -> bool:
        if self.thread:
            self.write_log(_("已有任务在运行中，请等待完成"))
            return False

        self.write_log("-" * 40)
        self.thread = Thread(
            target=self.run_backtesting,
            args=(
                class_name,
                section,
                choose_strategy,
                backtester_date,
                rate,
                slippage,
                size,
                pricetick,
                capital,
                setting
            )
        )
        self.thread.start()

        return True

    def get_result_df(self) -> DataFrame:
        """"""
        return self.result_df

    def get_result_statistics(self) -> dict:
        """"""
        return self.result_statistics

    def get_result_values(self) -> list:
        """"""
        return self.result_values

    def get_default_setting(self, class_name: str) -> dict:
        """"""
        strategy_class: type = self.classes[class_name]
        return strategy_class.get_class_parameters()

    def run_optimization(
            self,
            class_name: str,
            vt_symbol: str,
            interval: str,
            start: datetime,
            end: datetime,
            rate: float,
            slippage: float,
            size: int,
            pricetick: float,
            capital: int,
            optimization_setting: OptimizationSetting,
            use_ga: bool,
            max_workers: int
    ) -> None:
        """"""
        self.result_values = None

        engine: DVPBacktestingEngine = self.backtesting_engine
        engine.clear_data()

        if interval == Interval.TICK.value:
            mode: BacktestingMode = BacktestingMode.TICK
        else:
            mode: BacktestingMode = BacktestingMode.BAR

        engine.set_parameters(
            vt_symbol=vt_symbol,
            interval=interval,
            start=start,
            end=end,
            rate=rate,
            slippage=slippage,
            size=size,
            pricetick=pricetick,
            capital=capital,
            mode=mode
        )

        strategy_class: type = self.classes[class_name]
        engine.add_strategy(
            strategy_class,
            {}
        )

        # 0则代表不限制
        if max_workers == 0:
            max_workers = None

        if use_ga:
            self.result_values = engine.run_ga_optimization(
                optimization_setting,
                output=False,
                max_workers=max_workers
            )
        else:
            self.result_values = engine.run_bf_optimization(
                optimization_setting,
                output=False,
                max_workers=max_workers
            )

        # Clear thread object handler.
        self.thread = None
        self.write_log(_("多进程参数优化完成"))

        # Put optimization done event
        event: Event = Event(EVENT_BACKTESTER_OPTIMIZATION_FINISHED)
        self.event_engine.put(event)

    def start_optimization(
            self,
            class_name: str,
            vt_symbol: str,
            interval: str,
            start: datetime,
            end: datetime,
            rate: float,
            slippage: float,
            size: int,
            pricetick: float,
            capital: int,
            optimization_setting: OptimizationSetting,
            use_ga: bool,
            max_workers: int
    ) -> bool:
        if self.thread:
            self.write_log(_("已有任务在运行中，请等待完成"))
            return False

        self.write_log("-" * 40)
        self.thread = Thread(
            target=self.run_optimization,
            args=(
                class_name,
                vt_symbol,
                interval,
                start,
                end,
                rate,
                slippage,
                size,
                pricetick,
                capital,
                optimization_setting,
                use_ga,
                max_workers
            )
        )
        self.thread.start()

        return True

    def save_sector_data(self, sector_data: SectorData) -> None:
        for code in sector_data.tick_data:
            tick_data = sector_data.tick_data[code]
            self.database.save_tick_data(tick_data, True)

        for code in sector_data.daily_data:
            bar_data = sector_data.daily_data[code]
            self.database.save_bar_data(bar_data)

    def query_sector_data(self, req: SectorHistoryRequest) -> SectorData:
        bond_infos, stock_infos = get_live_bond_info(req.date, conv_bond_info)
        contract_list = bond_infos + stock_infos
        sd: SectorData = SectorData(sector=req.sector,
                                    gateway_name="XT",
                                    contract_list=contract_list,
                                    date=req.date,
                                    tick_data={},
                                    daily_data={})
        tick_overview: list[TickOverview] = self.database.get_tick_overview()
        bar_overview: list[BarOverview] = self.database.get_bar_overview()
        tick_overview_dict: dict[str, TickOverview] = {}
        bar_overview_dict: dict[str, bar_overview] = {}
        for tick in tick_overview:
            vt_symbol: str = f"{tick.symbol}.{tick.exchange.value}"
            tick_overview_dict[vt_symbol] = tick
        for bar in bar_overview:
            vt_symbol: str = f"{bar.symbol}.{bar.exchange.value}"
            bar_overview_dict[vt_symbol] = bar
        for code in contract_list:
            vt_symbol: str = code.vt_symbol
            tick_req: HistoryRequest = HistoryRequest(
                symbol=code.symbol,
                exchange=code.exchange,
                start=req.date + timedelta(hours=9, minutes=30),
                end=req.date + timedelta(hours=15),
                interval=Interval.TICK
            )
            daily_req: HistoryRequest = HistoryRequest(
                symbol=code.symbol,
                exchange=code.exchange,
                start=req.date - timedelta(days=30*6),
                end=req.date,
                interval=Interval.DAILY
            )
            if vt_symbol not in tick_overview_dict:
                download_flag = True
            else:
                tick_ov: TickOverview = tick_overview_dict[vt_symbol]
                if tick_req.start < tick_ov.start or tick_req.end > tick_ov.end:
                    download_flag = True
                else:
                    download_flag = False
            if download_flag:
                self.write_log(_("Tick-{}历史数据开始下载").format(vt_symbol))
                tick_data = self.datafeed.query_tick_history(tick_req, self.write_log)
                if len(tick_data) > 0:
                    sd.tick_data[vt_symbol] = tick_data

            if vt_symbol not in bar_overview_dict:
                download_flag = True
            else:
                bar_ov: BarOverview = bar_overview_dict[vt_symbol]
                if daily_req.end <= bar_ov.end:
                    download_flag = False
                else:
                    download_flag = True
            if download_flag:
                self.write_log(_("Daily-{}历史数据开始下载").format(vt_symbol))
                bar_data = self.datafeed.query_bar_history(daily_req, self.write_log)
                if len(bar_data) > 0:
                    sd.daily_data[vt_symbol] = bar_data
        return sd

    def run_downloading(
            self,
            section: str,
            backtester_date: datetime
    ) -> None:
        """
        执行下载任务
        """
        self.write_log(_("{}-{}开始下载历史数据").format(section, backtester_date))

        req: SectorHistoryRequest = SectorHistoryRequest(
            sector=section,
            date=backtester_date
        )

        try:
            data: SectorData = self.query_sector_data(req)
            if data:
                self.save_sector_data(data)
                self.write_log(_("{}-{}历史数据下载完成").format(section, backtester_date))
            else:
                self.write_log(_("数据下载失败，无法获取{}的历史数据").format(section))
        except Exception:
            msg: str = _("数据下载失败，触发异常：\n{}").format(traceback.format_exc())
            self.write_log(msg)

        # Clear thread object handler.
        self.thread = None

    def start_downloading(
            self,
            section: str,
            backtester_date: datetime
    ) -> bool:
        if self.thread:
            self.write_log(_("已有任务在运行中，请等待完成"))
            return False

        self.write_log("-" * 40)
        self.thread = Thread(
            target=self.run_downloading,
            args=(
                section,
                backtester_date
            )
        )
        self.thread.start()

        return True

    def get_all_trades(self) -> list:
        """"""
        return self.backtesting_engine.get_all_trades()

    def get_all_orders(self) -> list:
        """"""
        return self.backtesting_engine.get_all_orders()

    def get_all_daily_results(self) -> list:
        """"""
        return self.backtesting_engine.get_all_daily_results()

    def get_history_data(self) -> list:
        """"""
        return self.backtesting_engine.history_data

    def get_strategy_class_file(self, class_name: str) -> str:
        """"""
        strategy_class: type = self.classes[class_name]
        file_path: str = getfile(strategy_class)
        return file_path
