from datetime import datetime
from typing import List

from src.api.dtshare import bond_zh_hs_cov_daily
from src.trader.constant import Exchange, Interval
from src.trader.object import BarData
from src.trader.ui import create_qapp, QtCore
from src.chart import ChartWidget, VolumeItem, CandleItem


def get_index_data(code: str = 'sh000001') -> List[BarData]:
    df = bond_zh_hs_cov_daily(code)
    bar_list = []
    dict_obj = df.T.to_dict()
    for key in dict_obj:
        item = dict_obj[key]
        bar_list.append(BarData(symbol=code, exchange=Exchange.SSE, datetime=key,
                                interval=Interval.DAILY,
                                volume=item['volume'] / 100 / 1e8,
                                turnover=0,
                                open_interest=0,
                                open_price=item['open'],
                                high_price=item['high'],
                                low_price=item['low'],
                                close_price=item['close'], gateway_name="DTShare"))
    return bar_list


if __name__ == "__main__":
    app = create_qapp()

    bars = get_index_data()

    widget = ChartWidget()
    widget.add_plot("candle", hide_x_axis=True)
    widget.add_plot("volume", maximum_height=200)
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
