from datetime import datetime

from src.trader.constant import Interval
from src.trader.optimize import OptimizationSetting
from src.app.cta_strategy.backtesting import BacktestingEngine
from src.app.cta_strategy.strategies.atr_rsi_strategy import AtrRsiStrategy

engine = BacktestingEngine()
engine.set_parameters(
    vt_symbol="IF888.CFFEX",
    interval=Interval.MINUTE,
    start=datetime(2019, 1, 1),
    end=datetime(2019, 4, 30),
    rate=0.3/10000,
    slippage=0.2,
    size=300,
    pricetick=0.2,
    capital=1_000_000,
)
engine.add_strategy(AtrRsiStrategy, {})


engine.load_data()
engine.run_backtesting()
df = engine.calculate_result()
engine.calculate_statistics()
engine.show_chart()

setting = OptimizationSetting()
setting.set_target("sharpe_ratio")
setting.add_parameter("atr_length", 25, 27, 1)
setting.add_parameter("atr_ma_length", 10, 30, 10)

engine.run_ga_optimization(setting)

engine.run_bf_optimization(setting)