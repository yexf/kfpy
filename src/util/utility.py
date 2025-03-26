"""
General utility functions.
"""

import json
import os
from collections import namedtuple
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Union

from xtquant import xtdata

from src.trader.object import ContractData
from src.trader.utility import load_json, save_json


def get_util_file_path(filename: str) -> Path:
    current_script_path = Path(__file__).resolve()

    # 获取当前脚本所在的文件夹路径
    current_script_folder = current_script_path.parent
    temp_path: Path = current_script_folder.joinpath(filename)
    return temp_path


def save_util_json(filename: str, data: dict) -> None:
    """
    Save data into json file in temp path.
    """
    filepath: Path = get_util_file_path(filename)
    with open(filepath, mode="w+", encoding="UTF-8") as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


def load_util_json(filename: str) -> [object, dict]:
    """
    Load data from json file in temp path.
    """
    filepath: Path = get_util_file_path(filename)

    if filepath.exists():
        with open(filepath, mode="r", encoding="UTF-8") as f:
            datastr = f.read()
            data: object = json.loads(datastr, object_hook=lambda dic: namedtuple("X", dic.keys())(*dic.values()))
        return data, json.loads(datastr)
    else:
        save_util_json(filename, {})
        return {}, {}


def is_need_update(filename: str):
    current_date = str(datetime.now().date())
    contract = load_json(filename)
    if "date" in contract and contract["date"] == current_date:
        return False
    else:
        return True


def update_data(filename: str, data: Union[dict, list]) -> None:
    current_date = str(datetime.now().date())
    json_dict = {"data": data, "date": current_date}
    save_json(filename, json_dict)


def get_data(filename: str) -> Union[dict, list]:
    json_dict = load_json(filename)
    if "data" in json_dict:
        return json_dict["data"]
    else:
        return {}


def get_data_path():
    client = xtdata.get_client()
    client_data_dir = client.get_data_dir()
    data_path = os.path.abspath(os.path.dirname(client_data_dir))
    return data_path


def get_qmt_config() -> dict:
    data_path = get_data_path()
    test_config_path = "test_qmt_account.json"
    test_config = load_json(test_config_path)
    if test_config["mini路径"] == data_path:
        return test_config

    config_path = "qmt_account.json"
    config = load_json(config_path)
    if config["mini路径"] == data_path:
        return config
    return {}


def thread_hold():
    import threading
    import time

    def slp():
        while True:
            time.sleep(0.1)

    t = threading.Thread(target=slp)
    t.start()
    t.join()


def dict_conv_contract(contract_dict: dict) -> ContractData:
    def dict_to_dataclass(cls, data):
        return cls(**data)

    contract: ContractData = dict_to_dataclass(ContractData, contract_dict)
    return contract


def contract_to_dict(contract: ContractData) -> dict:
    contract_dict = asdict(contract)
    del contract_dict['extra']
    exchange = contract_dict["exchange"]
    product = contract_dict["product"]
    contract_dict["exchange"] = exchange.value
    contract_dict["product"] = product.value
    return contract_dict
