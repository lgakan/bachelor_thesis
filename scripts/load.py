from datetime import timedelta
from typing import Union, List

import pandas as pd

from lib.config import Config
from scripts.file_management import DfManager


class Load:
    """
    A class representing household power consumption.
    """

    def __init__(self, date_column: Union[str, None] = None, consumption: float = 0.0):
        self.consumption = consumption
        self.df_manager = DfManager(Config.DATA_ENERGY_USAGE, date_column)
        self.date_column = date_column

    def get_consumption_by_date(self, date_start: pd.Timestamp, date_end: Union[pd.Timestamp, None] = None) -> Union[List[float], float]:
        if date_end is None:
            if not self.df_manager.is_date_in_file(self.date_column, date_start):
                raise Exception(f"Date: {date_start} is not valid")
            return self.df_manager.get_cell_by_date(self.date_column, date_start, "Load (kW)")
        else:
            if not (self.df_manager.is_date_in_file(self.date_column, date_start) or self.df_manager.is_date_in_file(self.date_column, date_end)):
                raise Exception(f"Date column {date_start} or {date_end} is not valid")
            dates = pd.date_range(start=date_start, end=date_end, freq=timedelta(hours=1))
            return [self.df_manager.get_cell_by_date(self.date_column, x, "Load (kW)") for x in dates]

# Example
# if __name__ == "__main__":
#     load = Load(column_name="Date")
#     print(load.get_consumption_by_date(pd.to_datetime("01.01.2015 06:00:00")))
