from datetime import timedelta
from io import StringIO
from typing import Union, List

import pandas as pd
import requests
import os
from lib.config import Config
from scripts.file_management import DfManager
from lib.logger import logger


class EnergyWebScraper:
    """
    Class fetching Polish market prices of electricity. Hereafter referred to as RCE
    """

    def __init__(self, prices_path: str = Config.DATA_PRICES, date_column: Union[str, None] = None):
        self.df_manager = DfManager(prices_path, date_column)
        self.date_column = date_column

    @staticmethod
    def download_prices_by_date(date_start: pd.Timestamp, date_end: Union[pd.Timestamp, None] = None) -> pd.DataFrame:
        if date_end is None or date_start.strftime('%Y%m%d') == date_end.strftime('%Y%m%d'):
            url = Config.CSV_DOWNLOAD_LINK + "data/" + date_start.strftime('%Y%m%d')
        else:
            url = Config.CSV_DOWNLOAD_LINK + "data_od/" + date_start.strftime("%Y%m%d") + "/data_do/" + date_end.strftime("%Y%m%d")
        response = requests.get(url)
        return pd.read_csv(StringIO(response.content.decode('utf-8')), sep=';', decimal=',')

    @staticmethod
    def simulate_negative_prices(prices: List[float], start_idx: int = 20, negative_amount: int = 7) -> List[float]:
        if start_idx + negative_amount < len(prices):
            prices[start_idx:start_idx + negative_amount] = [-x for x in prices[start_idx:start_idx + negative_amount]]
        return prices

    def get_prices_file_by_date(self, date_start: pd.Timestamp, date_end: Union[pd.Timestamp, None] = None, simulate_negative: bool = False) -> None:
        df = self.download_prices_by_date(date_start, date_end)
        df[self.date_column] = df["Data"].astype(str) + df["Godzina"].apply(lambda x: x - 1).astype(str) + "00"
        df[self.date_column] = pd.to_datetime(df["Date"], format="%Y%m%d%H%M%S")
        df[self.date_column] = df[self.date_column].dt.strftime('%d.%m.%Y %H:%M:%S')
        df.drop(["Data", "Godzina"], axis=1, inplace=True)
        if simulate_negative:
            df.update({"RCE": self.simulate_negative_prices(df["RCE"].tolist())})
        self.df_manager.save_to_file(df)

    def get_rce_by_date(self, date_start: pd.Timestamp, date_end: Union[pd.Timestamp, None] = None) -> Union[List[float], float]:
        if not os.path.isfile(self.df_manager.path):
            self.get_prices_file_by_date(date_start)
        if date_end is None:
            if not self.df_manager.is_date_in_file(self.date_column, date_start):
                self.get_prices_file_by_date(date_start)
            return self.df_manager.get_cell_by_date(self.date_column, date_start, "RCE")
        else:
            if not (self.df_manager.is_date_in_file(self.date_column, date_start) and self.df_manager.is_date_in_file(self.date_column, date_end)):
                self.get_prices_file_by_date(date_start, date_end)
            dates = pd.date_range(start=date_start, end=date_end, freq=timedelta(hours=1))
            return [self.df_manager.get_cell_by_date(self.date_column, x, "RCE") for x in dates]

    def check_next_day_availability(self, date_in: pd.Timestamp) -> bool:
        try:
            self.download_prices_by_date(date_in)
        except pd.errors.ParserError as e:
            logger.fatal(e)
            return False
        else:
            return True


if __name__ == "__main__":
    scaper = EnergyWebScraper("test_file.csv", date_column="Date")
    scaper.get_prices_file_by_date(date_start=pd.Timestamp("21.09.2023 02:00:00"))
    scaper.check_next_day_availability(pd.Timestamp("21.09.2011 02:00:00"))
    print(scaper.get_rce_by_date(pd.Timestamp("21.09.2023 02:00:00")))
