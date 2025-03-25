from src.trader.database import get_database
from src.util.dtshare import get_index_data

if __name__ == "__main__":
    database = get_database()
    sh001 = get_index_data()
    bars = database.save_bar_data(sh001)