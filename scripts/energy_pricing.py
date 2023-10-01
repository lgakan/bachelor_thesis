from datetime import date
from datetime import timedelta
from io import StringIO

import pandas as pd
import requests

from lib.config import Config
from lib.config import DataTypes
from lib.file_management import DfManager


class EnergyWebScraper:
    """
    A class for web scrapping polish RCE from a web.
    """

    def __init__(self, prices_path: str = Config.DATA_PRICES, date_column: None | str = None):
        self.df_manager = DfManager(prices_path, date_column)
        self.date_column = date_column

    def download_prices_by_date(self, date_in: DataTypes.TIMESTAMP = date.today()):
        url = Config.LINK_CSV_DOWNLOAD + date_in.strftime('%Y%m%d')
        response = requests.get(url)
        df = pd.read_csv(StringIO(response.content.decode('utf-8')), sep=';', decimal=',')

        df[self.date_column] = df["Data"].astype(str) + df["Godzina"].apply(lambda x: x - 1).astype(str) + "00"
        df[self.date_column] = pd.to_datetime(df["Date"], format="%Y%m%d%H%M%S")
        df[self.date_column] = df[self.date_column].dt.strftime('%d.%m.%Y %H:%M:%S')
        df.drop(["Data", "Godzina"], axis=1, inplace=True)
        self.df_manager.save_to_file(df)

    def get_rce_by_date(self, date_in: DataTypes.TIMESTAMP):
        date_compare = pd.Timestamp(self.df_manager.get_from_file()[self.date_column].iloc[0]).strftime("%d.%m.%Y")
        if date_in.strftime("%d.%m.%Y") != date_compare:
            self.download_prices_by_date(date_in)
        return self.df_manager.get_cell_by_date(self.date_column, date_in, "RCE")

    def check_next_day_availability(self, date_in: pd.Timestamp):
        pass


if __name__ == "__main__":
    scaper = EnergyWebScraper(date_column="Date")
    scaper.download_prices_by_date(date_in=pd.Timestamp("21.09.2023 02:00:00"))
    print(scaper.get_rce_by_date(pd.Timestamp("21.09.2023 02:00:00")))
