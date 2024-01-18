from typing import Union

import pandas as pd

from lib.sun_manager import SunManager
from scripts.energy_bank import EnergyBank
from scripts.pv import Pv
from systems.system_base import SystemBase


class SmartSaveSystem(SystemBase):
    def __init__(self, eb_capacity: float = 3.0,
                 eb_min_lvl: float = 0.0,
                 eb_start_lvl: float = 1.0,
                 eb_purchase_cost: float = 10000.0,
                 eb_cycles: int = 5000,
                 pv_size: int = 5,
                 load_multiplier: Union[None, int] = None,
                 **kwargs):
        super().__init__(load_multiplier=load_multiplier)
        self.producer = Pv(date_column="Date", size=pv_size)
        self.energy_bank = EnergyBank(capacity=eb_capacity, min_lvl=eb_min_lvl, lvl=eb_start_lvl,
                                      purchase_cost=eb_purchase_cost, cycles_num=eb_cycles)
        self.sun_manager = SunManager()
        self.average_energy_cost = None

    def calculate_average_energy_cost(self, date_in: pd.Timestamp, sunrise: int, sunset: int) -> None:
        if date_in.hour >= sunset:
            end_date = date_in.replace(day=date_in.day + 1, hour=sunrise)
        elif sunrise <= date_in.hour < sunset:
            end_date = date_in.replace(hour=sunset)
        else:
            end_date = date_in.replace(hour=sunrise)
        rce_prices = self.energy_pricer.get_rce_by_date(date_in, end_date)
        self.average_energy_cost = sum(rce_prices) / len(rce_prices)

    def _calculate_cost_positive_price(self, price: float, balance: float) -> float:
        bank_operation_cost = self.energy_bank.operation_cost(balance)
        if balance >= 0.0:
            if price >= self.average_energy_cost + bank_operation_cost:
                cost = -balance * price
            else:
                rest_energy = self.energy_bank.manage_energy(balance)
                cost = -rest_energy * price + self.energy_bank.operation_cost(balance - rest_energy)
        else:
            if price >= self.average_energy_cost + bank_operation_cost:
                rest_energy = self.energy_bank.manage_energy(balance)
                cost = -rest_energy * price + self.energy_bank.operation_cost(balance - rest_energy)
            else:
                cost = -balance * price
        return cost

    def _calculate_cost_negative_price(self, price: float, balance: float) -> float:
        if balance >= 0.0:
            rest_energy = self.energy_bank.manage_energy(balance)
            cost = -rest_energy * price + self.energy_bank.operation_cost(balance - rest_energy)
        else:
            charged_energy = self.energy_bank.capacity - self.energy_bank.lvl
            self.energy_bank.manage_energy(charged_energy)
            cost = -price * charged_energy + self.energy_bank.operation_cost(charged_energy)
        return cost

    def calculate_cost(self, price: float, balance: float) -> float:
        if price >= 0.0:
            return self._calculate_cost_positive_price(price, balance)
        else:
            return self._calculate_cost_negative_price(price, balance)

    def feed_consumption(self, date_in: pd.Timestamp) -> None:
        sunrise, sunset = self.sun_manager.get_sun_data(date_in)
        if date_in.hour == sunset or date_in.hour == sunrise or self.average_energy_cost is None:
            self.calculate_average_energy_cost(date_in, sunrise, sunset)
        rce_price = self.energy_pricer.get_rce_by_date(date_in)
        consumption = self.consumer.get_consumption_by_date(date_in)
        production = self.producer.get_production_by_date(date_in)
        current_balance = round(production - consumption, 2)
        cost = self.calculate_cost(rce_price, current_balance)
        self.log_data(cost, current_balance, self.energy_bank.lvl)
        self.summed_cost += round(cost, 2)
        self.plotter.add_data_row([date_in, rce_price, consumption, production, self.energy_bank.lvl, self.summed_cost])
