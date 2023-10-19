from abc import abstractmethod
from datetime import timedelta
from typing import List, Union

import pandas as pd

from scripts.plotter import Plotter
from scripts.energy_bank import EnergyBank
from scripts.energy_pricing import EnergyWebScraper
from scripts.load import Load
from scripts.prediction_strategy import PredictionStrategy, DayPredictionStrategy, NightPredictionStrategy
from scripts.pv import Pv


class SystemBase:
    def __init__(self):
        self.summed_cost = 0
        self.energy_pricer = EnergyWebScraper(date_column="Date")
        self.plotter = Plotter(["price [zl]", "consumption [kWh]", "production [kWh]", "energy_bank [kWh]", "Total price"])
        self.consumer = Load(date_column="Date")

    @abstractmethod
    def feed_consumption(self, date_in: pd.Timestamp) -> None:
        pass

    def plot_charts(self):
        self.plotter.plot_charts(f"System Data - {self.__class__.__name__}")


class BareSystem(SystemBase):
    def __init__(self):
        super().__init__()

    def feed_consumption(self, date_in: pd.Timestamp) -> None:
        consumption = self.consumer.get_consumption_by_date(date_in)
        rce_price = self.energy_pricer.get_rce_by_date(date_in)
        cost = consumption * rce_price
        self.summed_cost += cost
        self.plotter.add_data_row([date_in, rce_price, consumption, 0, 0, self.summed_cost])


class PvSystem(SystemBase):
    def __init__(self):
        super().__init__()
        self.producer = Pv(date_column="Date")

    def feed_consumption(self, date_in: pd.Timestamp) -> None:
        consumption = self.consumer.get_consumption_by_date(date_in)
        rce_price = self.energy_pricer.get_rce_by_date(date_in)
        pv_prod = self.producer.get_production_by_date(date_in)
        reduced_consumption_by_pv = consumption - pv_prod
        cost = reduced_consumption_by_pv * rce_price
        self.summed_cost += cost
        self.plotter.add_data_row([date_in, rce_price, consumption, pv_prod, 0, self.summed_cost])


class RawFullSystem(SystemBase):
    def __init__(self):
        super().__init__()
        self.producer = Pv(date_column="Date")
        self.energy_bank = EnergyBank()

    def feed_consumption(self, date_in: pd.Timestamp) -> None:
        consumption = self.consumer.get_consumption_by_date(date_in)
        rce_price = self.energy_pricer.get_rce_by_date(date_in)
        pv_prod = self.producer.get_production_by_date(date_in)
        reduced_consumption_by_pv = consumption - pv_prod
        if reduced_consumption_by_pv > 0:
            reduced_consumption_by_bank = reduced_consumption_by_pv - self.energy_bank.get_lvl()
            if reduced_consumption_by_bank > 0:
                self.energy_bank.release_energy(self.energy_bank.get_lvl())
                cost = reduced_consumption_by_bank * rce_price
            else:
                self.energy_bank.release_energy(reduced_consumption_by_pv)
                cost = 0
        else:
            energy_surplus = self.energy_bank.store_energy(-reduced_consumption_by_pv)
            cost = -energy_surplus * rce_price
        self.summed_cost += cost
        self.plotter.add_data_row([date_in, rce_price, consumption, pv_prod, self.energy_bank.get_lvl(), self.summed_cost])


class SmartSystem(SystemBase):
    def __init__(self):
        super().__init__()
        self.producer = Pv(date_column="Date")
        self.energy_bank = EnergyBank()
        self._prediction_strategy = None
        self.energy_plan = None

    @property
    def prediction_strategy(self) -> PredictionStrategy:
        return self._prediction_strategy

    @prediction_strategy.setter
    def prediction_strategy(self, strategy: Union[PredictionStrategy | None]) -> None:
        self._prediction_strategy = strategy

    @staticmethod
    def is_ascending(arr: List[Union[int, float]]):
        n = len(arr)
        for i in range(1, n):
            if arr[i - 1] > arr[i]:
                return False
        return True

    def feed_consumption(self, date_in: pd.Timestamp) -> None:
        morning_hour = 7
        afternoon_hour = 14
        start = date_in
        if self.prediction_strategy is None or self.energy_plan is None:
            if date_in.hour >= afternoon_hour:
                self.prediction_strategy = NightPredictionStrategy(self.energy_bank.min_lvl, self.energy_bank.capacity)
                end = start.replace(day=date_in.day + 1, hour=morning_hour)
            elif morning_hour <= date_in.hour < afternoon_hour:
                self.prediction_strategy = DayPredictionStrategy(self.energy_bank.min_lvl, self.energy_bank.capacity)
                end = start.replace(hour=afternoon_hour)
            else:
                self.prediction_strategy = NightPredictionStrategy(self.energy_bank.min_lvl, self.energy_bank.capacity)
                end = start.replace(hour=morning_hour)
            rce_prices = self.energy_pricer.get_rce_by_date(start, end)
            consumptions = self.consumer.get_consumption_by_date(start, end)
            productions = self.producer.get_production_by_date(start, end)
            balances = [round(prod - cons, 2) for (prod, cons) in zip(productions, consumptions)]
            dates = pd.date_range(start=start, end=end, freq=timedelta(hours=1))
            energy_plan = self.prediction_strategy.get_plan(self.energy_bank.get_lvl(), rce_prices, balances)
            self.energy_plan = {k: v for k, v in zip(dates, energy_plan)}

        rce_price = self.energy_pricer.get_rce_by_date(date_in)
        consumption = self.consumer.get_consumption_by_date(date_in)
        production = self.producer.get_production_by_date(date_in)
        balance = round(production - consumption, 2)
        if self.energy_plan[date_in] == balance:
            if balance >= 0.0:
                self.energy_bank.store_energy(balance)
            else:
                self.energy_bank.release_energy(abs(balance))
        else:
            if self.energy_plan[date_in] > 0.0:
                raise Exception(f"{self.energy_plan[date_in]} and {balance}")
            else:
                self.energy_bank.release_energy(abs(self.energy_plan[date_in]))
                buy_energy = self.energy_plan[date_in] - balance
                cost = buy_energy * rce_price
                self.summed_cost += cost
        if self.energy_plan.get(date_in + timedelta(hours=1)) is None:
            self.energy_plan = None
        self.plotter.add_data_row([date_in, rce_price, consumption, production, self.energy_bank.get_lvl(), self.summed_cost])
