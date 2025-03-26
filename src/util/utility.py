"""
General utility functions.
"""

import json
from collections import namedtuple
from datetime import datetime
from pathlib import Path
from typing import Union

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
