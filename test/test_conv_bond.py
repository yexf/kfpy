from src.util.data_tool.eastmoney_bond import get_eastmoney_bond, get_eastmoney_bond_all
from src.util.utility import is_need_update, update_data, get_data

if __name__ == '__main__':
    if is_need_update("conv_bond.json"):
        data_df = get_eastmoney_bond()
        dict_obj = data_df.T.to_dict()
        list_bond = []
        for i in dict_obj:
            list_bond.append(dict_obj[i])
        update_data("conv_bond.json", list_bond)
    if is_need_update("conv_bond_all.json"):
        data_df = get_eastmoney_bond_all()
        dict_obj = data_df.T.to_dict()
        list_bond = []
        for i in dict_obj:
            list_bond.append(dict_obj[i])
        update_data("conv_bond_all.json", list_bond)
