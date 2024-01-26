from datetime import timedelta
from typing import Union, List

import pandas as pd

from lib.config import Config
from scripts.file_management import DfManager


class Load:
    """
    Class simulating electricity consumption of a single-family home.
    """

    def __init__(self, date_column: Union[str, None] = None, multiplier: Union[None, int] = None):
        self.date_column = date_column
        self._multiplier = multiplier
        self.df_manager = DfManager(Config.DATA_ENERGY_CONSUMPTION, date_column)

    @property
    def multiplier_val(self):
        return self._multiplier

    def simulate_load_multiplier(self, load: Union[float, List[float]]) -> Union[float, List[float]]:
        if self._multiplier is None:
            return load
        if isinstance(load, list):
            return [self._multiplier * i for i in load]
        elif isinstance(load, float):
            return self._multiplier * load
        else:
            raise Exception("The load must be a floating-point number or a list of floating-point numbers")

    def get_consumption_by_date(self, date_start: pd.Timestamp, date_end: Union[pd.Timestamp, None] = None) -> Union[List[float], float]:
        if date_end is None:
            if not self.df_manager.is_date_in_file(self.date_column, date_start):
                raise Exception(f"Date: {date_start} is not valid")
            load_value = self.df_manager.get_cell_by_date(self.date_column, date_start, "Load (kW)")
        else:
            if not (self.df_manager.is_date_in_file(self.date_column, date_start) or
                    self.df_manager.is_date_in_file(self.date_column, date_end)):
                raise Exception(f"Date column {date_start} or {date_end} is not valid")
            dates = pd.date_range(start=date_start, end=date_end, freq=timedelta(hours=1))
            load_value = [self.df_manager.get_cell_by_date(self.date_column, x, "Load (kW)") for x in dates]
        return self.simulate_load_multiplier(load_value)


if __name__ == "__main__":
    load_in = Load(date_column="Date")
    print(load_in.get_consumption_by_date(pd.to_datetime("01.01.2015 06:00:00")))
