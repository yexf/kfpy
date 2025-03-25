from datetime import datetime
from typing import List

from src.api.dtshare import bond_zh_hs_cov_daily
from src.trader.constant import Exchange, Interval
from src.trader.object import BarData


def get_index_data(code: str = 'sh000001') -> List[BarData]:
    df = bond_zh_hs_cov_daily(code)
    bar_list = []
    dict_obj = df.T.to_dict()
    # 定义字符串的格式
    format_str = "%Y-%m-%d %H:%M:%S"
    for key in dict_obj:
        item = dict_obj[key]
        # 使用 strptime 方法转换
        dt = datetime.strptime(str(key), format_str)
        bar_list.append(BarData(symbol=code, exchange=Exchange.SSE, datetime=dt,
                                interval=Interval.DAILY,
                                volume=item['volume'] / 100 / 1e8,
                                turnover=0,
                                open_interest=0,
                                open_price=item['open'],
                                high_price=item['high'],
                                low_price=item['low'],
                                close_price=item['close'], gateway_name="DTShare"))
    return bar_list
