from datetime import datetime
import pandas as pd
from xtquant import xtdata
from src.util import timer
from src.util.save_tick_data import conv_bond_info, jdt_clean, on_process
from src.util.timer import get_datatime


def get_live_bond_info(datestr):
    bond_infos = {}
    format_str = "%Y-%m-%d %H:%M:%S"
    dt = datetime.strptime(datestr, "%Y%m%d")
    for bi in conv_bond_info:
        code = bi["交易代码"]
        dedate = bi["退市日期"]
        indate = bi["上市日期"]
        if dedate is not None:
            dedate = datetime.strptime(dedate, format_str)
        if indate is not None:
            indate = datetime.strptime(indate, format_str)
        if indate is not None and indate < dt:
            if dedate is None:
                bond_infos[code] = bi
    return bond_infos


def get_daily_data(datestr, stock_list) -> pd.DataFrame:
    dt = datetime.strptime(datestr, "%Y%m%d")
    jdt_clean()
    xtdata.download_history_data2(stock_list, "1d", start_time=datestr, end_time=datestr, callback=on_process)
    data = xtdata.get_market_data(stock_list=stock_list, period="1d", start_time=datestr, end_time=datestr)
    data_dict = {}
    for i in data:
        data_dict[i] = data[i][datestr].T
    all_ticks = pd.DataFrame(data_dict)
    all_ticks.index.name = 'code'
    all_ticks.reset_index(drop=False, inplace=True)
    return all_ticks


def get_tick_data(datestr, stock_list) -> pd.DataFrame:
    dt = datetime.strptime(datestr, "%Y%m%d")
    jdt_clean()
    xtdata.download_history_data2(stock_list, "tick", start_time=datestr, end_time=datestr, callback=on_process)

    start_time = get_datatime(dt, "start")
    end_time = get_datatime(dt, "open1")
    data = xtdata.get_market_data([], stock_list, "tick",
                                  timer.to_tick_market_str(start_time), timer.to_tick_market_str(end_time))
    return data


def get_sort_list(df, col_name, num):
    df = df.sort_values(by=col_name, ascending=False)
    df.reset_index(drop=True, inplace=True)
    return df[:num].code.to_list()


def get_relate_code(bond_infos, bond_list):
    relate_code_list = []
    for item in bond_list:
        stock_code = bond_infos[item]['正股代码'] + item[6:]
        relate_code_list.append(stock_code)
    return relate_code_list


def conv_bond_calc(bond_infos):
    for code in bond_infos:
        item = bond_infos[code]
        stock_price = item['正股价']
        bond_price = item['债现价']
        conv_price = item['转股价']
        if type(bond_price) == float:
            cs_price_new = 100.0 * stock_price / conv_price
            cs_price = item['转股价值']
            zgyjl = item['转股溢价率']
            cp_ratio = ((bond_price / cs_price_new) - 1) * 100
            print(code, zgyjl, round(cp_ratio, 2))


if __name__ == '__main__':
    datestr = "20250303"
    bis = get_live_bond_info(datestr)
    daily_df = get_daily_data(datestr, list(bis.keys()))
    a50_list = get_sort_list(daily_df, "amount", 50)
    s50_list = get_relate_code(bis, a50_list)
    code_list = a50_list + s50_list
    get_tick_data(datestr, code_list)
    # sector_list = xtdata.get_sector_list()
    # print(sector_list)
    # dates = xtdata.get_trading_dates("SH", start_time="20250301")
    # for date in dates:
    #     dt = from_timestamp(date)
    #     print(to_date_str(dt))
