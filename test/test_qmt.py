import pandas as pd
from tqdm import tqdm
from xtquant import xtdata

from src.util.timer import from_timestamp, to_date_str


pbar = None
last_finished = 0


def jdt_clean():
    global pbar
    global last_finished
    pbar = None
    last_finished = 0


def jdt(finished, totol, message):
    global pbar
    global last_finished
    if not pbar:
        pbar = tqdm(total=totol)
    need_update = finished - last_finished
    last_finished = finished
    pbar.update(need_update)
    pbar.set_description(message)


def on_process(data):
    jdt(data["finished"], data["total"], data["message"])
def get_daa():
    xtdata.download_history_data2(["000001.SH"], "1d", start_time="19910101", end_time="20240823", callback=on_process)
    data = xtdata.get_market_data(stock_list=["000001.SH"], period="1d", start_time="19910101", end_time="20240823")

    # datas= pd.DataFrame(data)
    all_ticks = pd.concat(data, axis=0)
    all_ticks = all_ticks.transpose()
    all_ticks.to_csv("shh000001.csv")
    print(all_ticks)


if __name__ == '__main__':
    sector_list = xtdata.get_sector_list()
    print(sector_list)
    dates = xtdata.get_trading_dates("SH")
    for date in dates:
        dt = from_timestamp(date)
        print(to_date_str(dt))
    get_daa()
