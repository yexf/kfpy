
from src.util.data_tool.eastmoney_bond import get_eastmoney_bond, get_eastmoney_bond_all
from src.util.utility import update_data

if __name__ == '__main__':
    data_df = get_eastmoney_bond()
    dict_obj = data_df.T.to_dict()
    print(len(data_df))
    list_bond = []
    for i in dict_obj:
        list_bond.append(dict_obj[i])
    update_data("conv_bond.json", list_bond)
    # data_df = get_eastmoney_bond_all()
    # print(len(data_df))
    # data_df.to_csv("可转债.csv")
