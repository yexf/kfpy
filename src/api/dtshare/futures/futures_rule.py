# -*- coding:utf-8 -*-
# /usr/bin/env python
"""
Author: Tong Du
Data:2019/10/30 21:51
contact: dtshare@126.com
desc: 国泰君安期货-交易日历数据表
http://www.gtjaqh.com/jyrl.html
"""
import pandas as pd

from ...dtshare.futures.cons import futures_rule_url


def futures_rule():
    """
    国泰君安期货-交易日历数据表, 必须在交易日运行
    http://www.gtjaqh.com/jyrl.html
    :return: 交易日历数据
    :rtype: pandas.DataFrame
    """
    temp_df = pd.read_html(futures_rule_url, header=0)[0]
    temp_df.dropna(subset=["品种"], inplace=True)
    return temp_df


if __name__ == '__main__':
    futures_rule_df = futures_rule()
    print(futures_rule_df)
