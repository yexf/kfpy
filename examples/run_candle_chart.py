from datetime import datetime

from src.trader.constant import Exchange, Interval
from src.trader.database import get_database
from src.trader.ui import create_qapp
from src.chart import ChartWidget, VolumeItem, CandleItem

if __name__ == "__main__":
    app = create_qapp()

    database = get_database()
    bars = database.load_bar_data(
        "sh000001",
        Exchange.SSE,
        interval=Interval.DAILY,
        start=datetime(1970, 1, 1),
        end=datetime.now()
    )

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
