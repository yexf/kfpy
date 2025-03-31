import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from time import sleep
from tqdm import tqdm
from xtquant import xtdata

from src.event import EventEngine
from src.gateway.qmt import QmtGateway
from src.gateway.qmt.utils import TO_VN_Exchange_map, timestamp_to_datetime
from src.trader.constant import Interval
from src.trader.database import get_database
from src.trader.object import TickData
from src.util import timer
from src.util.data_tool.eastmoney_bond import get_bond_info
from src.util.timer import get_datatime
from src.trader.utility import load_json, save_json
from src.util.utility import get_data_path

pbar = None
last_finished = 0
conv_bond_infos = get_bond_info("conv_bond_all.json")


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


def next_day(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%Y%m%d")
    dt += timedelta(days=1)
    return dt.strftime("%Y%m%d")


def pre_day(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%Y%m%d")
    dt -= timedelta(days=1)
    return dt.strftime("%Y%m%d")


INTERVAL_Sec2VT: dict[str, str] = {
    "0": Interval.TICK.value,
    "60": Interval.MINUTE.value,
    "86400": Interval.DAILY.value,
}


def build_donwload_file_info() -> dict[str, set]:
    data_path = get_data_path()
    download_file_info = {}
    files_info = {}
    for files in os.listdir(data_path):
        if files == "SH" or files == "SZ":
            path: str = os.path.join(data_path, files)
            for root, dirs, files in os.walk(path):
                if len(dirs) == 0:
                    files_info[root] = files
    for key in files_info:
        path: Path = Path(key)
        if path.parent.name in INTERVAL_Sec2VT:
            exchange = path.parent.parent.name
            symbol = path.name
            date_list = files_info[key]
            date_info = set()
            for date_dat in date_list:
                date, suffix = date_dat.rsplit('.')
                date_info.add(date)
            xt_symbol = f"{symbol}.{exchange}"
            download_file_info[xt_symbol] = date_info
    return download_file_info


def build_download_plan(start_time: str = '20250101'):
    """  创建下载计划
    :param start_time: 开始时间 ，格式YYYYMMDD e.g. "20250101"
    :param end_time: 结束时间 ，格式YYYYMMDD e.g. "20250325"
    :return: dict 下载计划   {
        '123099.SH': ['20250101', '20250325'],
        '123089.SH': ['20250101', '20250325'],
    }
    """
    end_time = datetime.now().strftime("%Y%m%d")
    if datetime.now().hour < 17:
        end_time = pre_day(end_time)
    start_time = datetime.strptime(start_time, "%Y%m%d")
    end_time = datetime.strptime(end_time, "%Y%m%d")

    format_str = "%Y-%m-%d %H:%M:%S"
    download_plan = {}
    for bi in conv_bond_infos:
        exchange = bi["交易市场"]
        if exchange != "CNSESZ" and exchange != "CNSESH":
            continue
        code = bi["交易代码"]
        dedate = bi["退市日期"]
        indate = bi["上市日期"]
        stock_code = bi['正股代码'] + code[6:]
        if indate is None:
            continue
        indate_dt = datetime.strptime(indate, format_str)
        if indate_dt > end_time:
            continue

        if indate_dt < start_time:
            cstart_time = start_time
        else:
            cstart_time = indate_dt

        if dedate is None:
            cend_time = end_time
        else:
            dedate_dt = datetime.strptime(indate, format_str)
            if dedate_dt < start_time:
                continue
            elif dedate_dt > end_time:
                cend_time = end_time
            else:
                cend_time = dedate_dt

        download_plan[code] = [cstart_time.strftime("%Y%m%d"), cend_time.strftime("%Y%m%d")]
        download_plan[stock_code] = [cstart_time.strftime("%Y%m%d"), cend_time.strftime("%Y%m%d")]
    return download_plan


def do_download(code, start_time, end_time):
    jdt_clean()
    xtdata.download_history_data2([code], "tick", start_time=start_time, end_time=end_time, callback=on_process)
    sleep(0.5)


def do_download_plan(download_config_file: str, download_plan: dict) -> None:
    """  执行下载计划
    :param download_config_file: 下载配置文件 e.g. "download_config.json"
    :param download_plan: 下载计划
    """
    download_config = load_json(download_config_file)
    for code in download_plan:
        start_time = download_plan[code][0]
        cstart_time = start_time
        end_time = download_plan[code][1]
        print("download", code, cstart_time, end_time)
        if code in download_config:
            has_end_time = download_config[code][1]
            if has_end_time > start_time:
                cstart_time = next_day(has_end_time)
            if has_end_time >= end_time:
                continue
        do_download(code, cstart_time, end_time)
        download_config[code] = [start_time, end_time]
        save_json(download_config_file, download_config)


def conv_tick(qmt_gateway, datas):
    tick_list = []
    for code, data_list in datas.items():
        symbol, suffix = code.rsplit('.')
        exchange = TO_VN_Exchange_map[suffix]
        for data in data_list:
            ask_price = data['askPrice']
            ask_vol = data['askVol']
            bid_price = data['bidPrice']
            bid_vol = data['bidVol']

            tick = TickData(
                gateway_name=qmt_gateway.gateway_name,
                symbol=symbol,
                exchange=exchange,
                datetime=timestamp_to_datetime(data['time']),
                last_price=data['lastPrice'],
                volume=data['volume'],
                open_price=data['open'],
                high_price=data['high'],
                low_price=data['low'],
                pre_close=data['lastClose'],
                limit_down=0,
                limit_up=0,
                ask_price_1=ask_price[0],
                ask_price_2=ask_price[1],
                ask_price_3=ask_price[2],
                ask_price_4=ask_price[3],
                ask_price_5=ask_price[4],

                ask_volume_1=ask_vol[0],
                ask_volume_2=ask_vol[1],
                ask_volume_3=ask_vol[2],
                ask_volume_4=ask_vol[3],
                ask_volume_5=ask_vol[4],

                bid_price_1=bid_price[0],
                bid_price_2=bid_price[1],
                bid_price_3=bid_price[2],
                bid_price_4=bid_price[3],
                bid_price_5=bid_price[4],

                bid_volume_1=bid_vol[0],
                bid_volume_2=bid_vol[1],
                bid_volume_3=bid_vol[2],
                bid_volume_4=bid_vol[3],
                bid_volume_5=bid_vol[4],
            )
            contract = qmt_gateway.get_contract(tick.symbol)
            if contract:
                tick.name = contract.name
            tick.limit_up = data['lastPrice'] * 1.2
            tick.limit_down = data['lastPrice'] * 0.8
            tick_list.append(tick)
    return tick_list


def do_dumpdb(qmt_gateway, database_engine, code, start_date, end_date):
    start_time_dt = datetime.strptime(start_date, "%Y%m%d")
    end_time_dt = datetime.strptime(end_date, "%Y%m%d")
    start_time = get_datatime(start_time_dt, "start")
    end_time = get_datatime(end_time_dt, "end")
    data = xtdata.get_market_data([], [code], "tick",
                                  timer.to_tick_market_str(start_time), timer.to_tick_market_str(end_time))
    tick_list = conv_tick(qmt_gateway, data)
    print("保存tick数据到数据库", code, start_date, end_date)
    database_engine.save_tick_data(tick_list, True)


def do_dumpdb_plan(qmt_gateway, database_engine, download_config_file: str) -> None:
    """  执行dump tick数据到db计划
    :param database_engine:数据库引擎
    :param download_config_file: 下载配置文件 e.g. "download_config.json"
    :param download_plan: dump配置文件 e.g. "dump_config.json"
    """
    download_plan = load_json(download_config_file)
    tick_overviews = database_engine.get_tick_overview()
    tick_overview_dict = {}
    for tick_overview in tick_overviews:
        tick_overview_dict[tick_overview.symbol] = tick_overview
    for code in download_plan:
        start_time = download_plan[code][0]
        cstart_time = start_time
        end_time = download_plan[code][1]
        symbol = code[:6]
        print("dump", code, cstart_time, end_time)
        if symbol in tick_overview_dict:
            tick_overview = tick_overview_dict[symbol]
            to_end_time = tick_overview.end.strftime("%Y%m%d")
            if to_end_time > start_time:
                cstart_time = next_day(to_end_time)
            if to_end_time >= end_time:
                continue
        do_dumpdb(qmt_gateway, database_engine, code, cstart_time, end_time)


def save_tick_data():
    event_engine = EventEngine()
    qmt_gateway = QmtGateway(event_engine)
    database_engine = get_database()
    download_config_file = "download_config.json"
    download_plan = build_download_plan()
    do_download_plan(download_config_file, download_plan)
    do_dumpdb_plan(qmt_gateway, database_engine, download_config_file)


if __name__ == '__main__':
    save_tick_data()
