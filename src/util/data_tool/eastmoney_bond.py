import json
from typing import Union

import pandas as pd
import requests

from src.util.data_tool import demjson
from src.util.utility import load_util_json, is_need_update, update_data, get_data


def reload_columns(data_df: pd.DataFrame) -> pd.DataFrame:
    columns_list = [
        "序号",
        "_",
        "转债最新价",
        "转债涨跌幅",
        "转债代码",
        "_",
        "转债名称",
        "上市日期",
        "_",
        "纯债价值",
        "_",
        "正股最新价",
        "正股涨跌幅",
        "_",
        "正股代码",
        "_",
        "正股名称",
        "转股价",
        "转股价值",
        "转股溢价率",
        "纯债溢价率",
        "回售触发价",
        "强赎触发价",
        "到期赎回价",
        "开始转股日",
        "申购日期",
    ]
    data_df.columns = columns_list
    data_df = data_df[
        [
            "序号",
            "转债代码",
            "转债名称",
            "转债最新价",
            "转债涨跌幅",
            "正股代码",
            "正股名称",
            "正股最新价",
            "正股涨跌幅",
            "转股价",
            "转股价值",
            "转股溢价率",
            "纯债溢价率",
            "回售触发价",
            "强赎触发价",
            "到期赎回价",
            "纯债价值",
            "开始转股日",
            "上市日期",
            "申购日期",
        ]
    ]
    return data_df


def get_eastmoney_bond() -> pd.DataFrame:
    """
    东方财富网-行情中心-债券市场-可转债
    https://quote.eastmoney.com/center/fullscreenlist.html#convertible_comparison
    :return: 可转债比价表数据
    :rtype: pandas.DataFrame
    """
    url = "https://16.push2.eastmoney.com/api/qt/clist/get"
    params = {
        "pn": "1",
        "pz": "100",
        "po": "1",
        "np": "1",
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": "2",
        "invt": "2",
        "fid": "f243",
        "fs": "b:MK0354",
        "fields": "f1,f152,f2,f3,f12,f13,f14,f227,f228,f229,f230,f231,f232,f233,f234,f235,f236,f237,f238,f239,f240,"
                  "f241,f242,f26,f243",
        "_": "1590386857527",
    }
    r = requests.get(url, params=params)
    temp_list = []
    text_data = r.text
    json_data = demjson.decode(text_data)  # 解压json数据
    temp_df = pd.DataFrame(json_data["data"]["diff"])
    temp_list.append(temp_df)
    pages = json_data["rt"]
    for i in range(2, pages):
        params["pn"] = i
        r = requests.get(url, params=params)
        text_data = r.text
        json_data = demjson.decode(text_data)  # 解压json数据
        temp_df = pd.DataFrame(json_data["data"]["diff"])
        temp_list.append(temp_df)
    temp_df = pd.concat(temp_list)
    temp_df.reset_index(inplace=True)
    temp_df["index"] = range(1, len(temp_df) + 1)
    return reload_columns(temp_df)


def get_eastmoney_url_param():
    url_obj, url_json = load_util_json("data_tool/eastmoney_url.json")
    host = url_obj.host
    dataview = url_obj.dataview
    url = "https:" + getattr(host.production, dataview.dataurl.hostname) + dataview.dataurl.url
    param = url_json["dataview"]["dataurl"]["params"]
    return url, dataview, param.copy()


def get_eastmoney_bond_data(url, dataview, param, cb_name: str, page_num: int, page_size: int) -> str:
    param["callback"] = cb_name
    urlkeyvalues = dataview.urlkeyvalues
    param[urlkeyvalues.sortname] = dataview.sortname
    param[urlkeyvalues.sortorder] = dataview.sortorder
    param[urlkeyvalues.pagesize] = page_size
    param[urlkeyvalues.pagenumber] = page_num
    r = requests.get(url, params=param)
    return r.text


def reload_columns_all(data_df: pd.DataFrame) -> pd.DataFrame:
    columns_list = ['转债代码', '交易代码', '交易市场', '转债名称',
                    '退市日期', '上市日期', '正股代码', '债券期限',
                    '评级', '-', '-', '-', '-',
                    '付息日', '-', '-',
                    '发行规模', '-', '-', '-',
                    '-', '-', '-', '-',
                    '-', '-', '-',
                    '-', '-', '-',
                    '-', '-', '-',
                    '申购日期', '申购代码', '申购名称',
                    '中签日', '-', '正股名称',
                    '每股配售额', '-', '中签率',
                    '-', '转股结束日', '转股开始日',
                    '-', '-', '-', '正股价',
                    '转股价', '转股价值', '债现价',
                    '转股溢价率', '-', '-',
                    '-', '-', '-', '-',
                    '-', '-', '-', '-',
                    '-', '-', '-', '-',
                    '-', '每中一签获利']
    data_df.columns = columns_list
    data_df = data_df[['转债代码', '交易代码', '交易市场', '转债名称',
                       '退市日期', '上市日期', '债券期限',
                       '评级', '付息日', '发行规模', '正股代码', '正股名称',
                       '申购日期', '申购代码', '申购名称',
                       '中签日', '每股配售额', '中签率',
                       '转股结束日', '转股开始日', '正股价',
                       '转股价', '转股价值', '债现价',
                       '转股溢价率', '每中一签获利']]
    return data_df


def get_eastmoney_bond_all(page_size=100) -> pd.DataFrame:
    temp_list = []
    url, dataview, param = get_eastmoney_url_param()
    data_text = get_eastmoney_bond_data(url, dataview, param, "", 1, page_size)
    resultdata_obj = json.loads(data_text)
    pages = resultdata_obj["result"]["pages"]
    data = resultdata_obj["result"]["data"]
    temp_df = pd.DataFrame(data)
    temp_df = temp_df.dropna(axis=1, how='all')
    temp_list.append(temp_df)
    for i in range(2, pages + 1):
        data_text = get_eastmoney_bond_data(url, dataview, param, "", i, page_size)
        resultdata_obj = json.loads(data_text)
        data = resultdata_obj["result"]["data"]
        temp_df = pd.DataFrame(data)
        temp_df = temp_df.dropna(axis=1, how='all')
        temp_list.append(temp_df)
    ret_df = pd.concat(temp_list)
    ret_df.reset_index(drop=True, inplace=True)
    return reload_columns_all(ret_df)


def update_eastmoney_bond(file_name: str) -> bool:
    if is_need_update(file_name):
        if file_name == "conv_bond_all.json":
            data_df = get_eastmoney_bond_all()
        elif file_name == "conv_bond.json":
            data_df = get_eastmoney_bond()
        else:
            return False
        dict_obj = data_df.T.to_dict()
        list_bond = []
        for i in dict_obj:
            list_bond.append(dict_obj[i])
        update_data(file_name, list_bond)
    return True


def get_bond_info(file_name: str) -> Union[dict, list]:
    if update_eastmoney_bond(file_name):
        return get_data(file_name)
    else:
        return {}
