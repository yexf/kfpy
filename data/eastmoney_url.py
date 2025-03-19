import json
from collections import namedtuple
from pathlib import Path


def get_file_path(filename: str) -> Path:
    current_script_path = Path(__file__).resolve()

    # 获取当前脚本所在的文件夹路径
    current_script_folder = current_script_path.parent
    temp_path: Path = current_script_folder.joinpath(filename)
    return temp_path


def save_json(filename: str, data: dict) -> None:
    """
    Save data into json file in temp path.
    """
    filepath: Path = get_file_path(filename)
    with open(filepath, mode="w+", encoding="UTF-8") as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


def load_json(filename: str = "eastmoney_url.json") -> [object, dict]:
    """
    Load data from json file in temp path.
    """
    filepath: Path = get_file_path(filename)

    if filepath.exists():
        with open(filepath, mode="r", encoding="UTF-8") as f:
            datastr = f.read()
            data: object = json.loads(datastr, object_hook=lambda dic: namedtuple("X", dic.keys())(*dic.values()))
        return data, json.loads(datastr)
    else:
        save_json(filename, {})
        return {}, {}
