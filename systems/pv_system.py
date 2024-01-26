from typing import Union

import pandas as pd

from scripts.pv import Pv
from systems.system_base import SystemBase


class PvSystem(SystemBase):
    def __init__(self, pv_size: int = 5, load_multiplier: Union[None, int] = None, **kwargs):
        super().__init__(load_multiplier=load_multiplier)
        self.producer = Pv(date_column="Date", size=pv_size)

    @staticmethod
    def calculate_cost(price: float, consumption: float) -> float:
        return consumption * price

    def feed_consumption(self, date_in: pd.Timestamp) -> None:
        consumption = self.consumer.get_consumption_by_date(date_in)
        rce_price = self.energy_pricer.get_rce_by_date(date_in)
        production = self.producer.get_production_by_date(date_in)
        reduced_consumption = round(consumption - production, 2)
        cost = self.calculate_cost(rce_price, reduced_consumption)
        self.log_data(cost)
        self.summed_cost += round(cost, 2)
        self.plotter.add_data_row([date_in, rce_price, consumption, production, 0, self.summed_cost])
