from datetime import datetime

from src.trader.constant import Exchange, Interval
from src.trader.database import get_database, BarOverview
from src.trader.ui import create_qapp
from src.chart import ChartWidget, VolumeItem, CandleItem
from src.util.dtshare import get_index_data

if __name__ == "__main__":
    database = get_database()
    bar_overview: list[BarOverview] = database.get_bar_overview()
    code: str = 'sh000001'
    bars = None
    for bar in bar_overview:
        if code == bar.symbol:
            bars = database.load_bar_data(
                code,
                Exchange.SSE,
                interval=Interval.DAILY,
                start=datetime(1970, 1, 1),
                end=datetime.now()
            )
    if bars is None:
        sh001 = get_index_data()
        bars = database.save_bar_data(sh001)
    app = create_qapp()
    widget = ChartWidget()
    widget.add_plot("candle", hide_x_axis=True)
    widget.add_plot("volume", maximum_height=150)
    widget.add_item(CandleItem, "candle", "candle")
    widget.add_item(VolumeItem, "volume", "volume")
    widget.add_cursor()

    n = len(bars)
    history = bars[:n]
    new_data = bars[n:]

    widget.update_history(history)

    # widget.show()
    widget.showMaximized()
    app.exec()
