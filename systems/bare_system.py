from typing import Union

import pandas as pd

from systems.system_base import SystemBase


class BareSystem(SystemBase):
    def __init__(self, load_multiplier: Union[None, int] = None, **kwargs):
        super().__init__(load_multiplier=load_multiplier)

    @staticmethod
    def calculate_cost(price: float, consumption: float) -> float:
        return consumption * price

    def feed_consumption(self, date_in: pd.Timestamp) -> None:
        consumption = self.consumer.get_consumption_by_date(date_in)
        rce_price = self.energy_pricer.get_rce_by_date(date_in)
        cost = self.calculate_cost(consumption, rce_price)
        self.log_data(cost)
        self.summed_cost += round(cost, 2)
        self.plotter.add_data_row([date_in, rce_price, consumption, 0, 0, self.summed_cost])
