from src.trader.utility import *

test_config_path = "test_qmt_account.json"
config_path = "qmt_account.json"

test_account_config = {"交易账号": "55008900", "mini路径": r'D:\Program Files\gj_qmt_mn\userdata_mini'}
account_config = {"交易账号": "86895069", "mini路径": r'D:\Program Files\gjzq_qmt\userdata_mini'}

save_json(test_config_path, test_account_config)
save_json(config_path, account_config)
