import os
from datetime import timedelta
from io import StringIO
from typing import List, Union

import pandas as pd
import requests

from lib.config import Config, PhotovoltaicDirection
from scripts.file_management import DfManager


class Pv:
    """
    A class representing household photovoltaic system.

    Attributes:
        size (float): The size of photovoltaic installation expressed in kW.
        direction (PhotovoltaicDirection): The photovoltaic installation: east-west or south.
    """

    def __init__(self,
                 date_column: Union[None, str] = None,
                 size: int = 5,
                 direction: PhotovoltaicDirection = PhotovoltaicDirection.SOUTH):
        self.date_column = date_column
        self.size = size
        self._direction = direction
        self.df_manager = DfManager(Config.DATA_ENERGY_PRODUCTION, date_column)
        if not os.path.exists(Config.DATA_ENERGY_PRODUCTION):
            self.update_pv_file()

    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, new_direction: PhotovoltaicDirection):
        if new_direction != PhotovoltaicDirection.EAST or new_direction != PhotovoltaicDirection.SOUTH:
            raise Exception("This direction is not supported!")
        self._direction = new_direction

    def calculate_azimuth(self) -> int:
        if self._direction == PhotovoltaicDirection.EAST:
            if Config.LATITUDE >= 0.0:
                return 90
            else:
                return -90
        elif self._direction == PhotovoltaicDirection.SOUTH:
            if Config.LATITUDE >= 0.0:
                return 180
            else:
                return -180

    def update_pv_file(self):
        s = requests.Session()
        url = Config.PV_API_LINK + "data/pv"
        args = {
            'lat': Config.LATITUDE,
            'lon': Config.LONGITUDE,
            'date_from': '2019-01-01',
            'date_to': '2019-12-31',
            'dataset': 'merra2',
            'capacity': self.size,
            'system_loss': 0.1,
            'tracking': 0,
            'tilt': 35,
            'azim': self.calculate_azimuth(),
            'format': 'csv'
        }
        response = s.get(url, params=args)
        df = pd.read_csv(StringIO(response.text), skiprows=3)
        df["time"] = pd.to_datetime(df['time'], format='%Y-%m-%d %H:%M')
        df["time"] = df["time"].apply(lambda x: x.replace(year=2020))
        df["time"] = df['time'].dt.strftime('%d.%m.%Y %H:%M:%S')
        df.columns = ["Date", "PV gen (kW)"]
        self.df_manager.save_to_file(df)

    def get_production_by_date(self, date_start: pd.Timestamp, date_end: Union[pd.Timestamp, None] = None) -> Union[List[float], float]:
        if date_end is None:
            if not self.df_manager.is_date_in_file(self.date_column, date_start):
                raise Exception(f"Date: {date_start} is not valid")
            return self.df_manager.get_cell_by_date(self.date_column, date_start, "PV gen (kW)")
        else:
            if not (self.df_manager.is_date_in_file(self.date_column, date_start) or
                    self.df_manager.is_date_in_file(self.date_column, date_end)):
                raise Exception(f"Date column {date_start} or {date_end} is not valid")
            dates = pd.date_range(start=date_start, end=date_end, freq=timedelta(hours=1))
            return [self.df_manager.get_cell_by_date(self.date_column, x, "PV gen (kW)") for x in dates]


# if __name__ == "__main__":
#     pv = Pv(date_column="Date")
#     print(pv.get_production_by_date(pd.to_datetime("01.01.2015 06:00:00")))
