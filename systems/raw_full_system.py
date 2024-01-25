from typing import Union

import pandas as pd

from scripts.energy_bank import EnergyBank
from scripts.pv import Pv
from systems.system_base import SystemBase


class RawFullSystem(SystemBase):
    def __init__(self, energy_bank: EnergyBank, pv_producer: Pv, load_multiplier: Union[None, int] = None, **kwargs):
        super().__init__(load_multiplier=load_multiplier)
        self.producer = pv_producer
        self.energy_bank = energy_bank

    def calculate_cost(self, price: float, balance: float) -> float:
        bank_lvl = self.energy_bank.lvl
        balance_after_bank = self.energy_bank.manage_energy(balance)
        if balance >= 0.0:
            cost = -balance_after_bank * price + self.energy_bank.operation_cost(balance - balance_after_bank)
        else:
            cost = -balance_after_bank * price + self.energy_bank.operation_cost(min(bank_lvl, abs(balance)))
        return cost

    def feed_consumption(self, date_in: pd.Timestamp) -> None:
        consumption = self.consumer.get_consumption_by_date(date_in)
        rce_price = self.energy_pricer.get_rce_by_date(date_in)
        production = self.producer.get_production_by_date(date_in)
        current_balance = round(production - consumption, 2)
        cost = self.calculate_cost(rce_price, current_balance)
        self.log_data(cost, current_balance, self.energy_bank.lvl)
        self.summed_cost += round(cost, 2)
        self.plotter.add_data_row([date_in, rce_price, consumption, production, self.energy_bank.lvl, self.summed_cost])
