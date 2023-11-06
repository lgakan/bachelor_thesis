import random
from abc import abstractmethod
from datetime import timedelta
from typing import List, Union

import pandas as pd

from lib.logger import logger
from lib.sun_manager import SunManager
from scripts.energy_bank import EnergyBank
from scripts.energy_pricing import EnergyWebScraper
from scripts.load import Load
from scripts.plotter import Plotter
from scripts.prediction_strategy import PredictionStrategy, DayFullBankPredictionStrategy, NightPredictionStrategy
from scripts.pv import Pv


class SystemBase:
    def __init__(self):
        self.summed_cost = 0
        self.energy_pricer = EnergyWebScraper(date_column="Date")
        self.plotter = Plotter(["price [zl]", "consumption [kWh]", "production [kWh]", "energy_bank [kWh]", "Total price [zl]"])
        self.consumer = Load(date_column="Date")

    @abstractmethod
    def feed_consumption(self, date_in: pd.Timestamp) -> None:
        pass

    def plot_charts(self):
        return self.plotter.plot_charts(f"System Data - {self.__class__.__name__}")


class BareSystem(SystemBase):
    def __init__(self):
        super().__init__()

    def feed_consumption(self, date_in: pd.Timestamp) -> None:
        consumption = self.consumer.get_consumption_by_date(date_in)
        rce_price = self.energy_pricer.get_rce_by_date(date_in)
        cost = consumption * rce_price
        self.summed_cost += cost / 1000
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
        self.summed_cost += cost / 1000
        self.plotter.add_data_row([date_in, rce_price, consumption, pv_prod, 0, self.summed_cost])


class RawFullSystem(SystemBase):
    def __init__(self, energy_bank_capacity: float = 3.0):
        super().__init__()
        self.producer = Pv(date_column="Date")
        self.energy_bank = EnergyBank(capacity=energy_bank_capacity)

    def feed_consumption(self, date_in: pd.Timestamp) -> None:
        consumption = self.consumer.get_consumption_by_date(date_in)
        rce_price = self.energy_pricer.get_rce_by_date(date_in)
        pv_prod = self.producer.get_production_by_date(date_in)
        balance = pv_prod - consumption
        balance_after_bank = self.energy_bank.manage_energy(balance)
        if balance_after_bank > 0:
            cost = -balance_after_bank * rce_price
        else:
            cost = -balance_after_bank * rce_price
        self.summed_cost += cost / 1000
        self.plotter.add_data_row([date_in, rce_price, consumption, pv_prod, self.energy_bank.lvl, self.summed_cost])


class SmartSystem(SystemBase):
    def __init__(self, energy_bank_capacity: float = 3.0):
        super().__init__()
        self.producer = Pv(date_column="Date")
        self.energy_bank = EnergyBank(capacity=energy_bank_capacity)
        self.sun_manager = SunManager()
        self._prediction_strategy = None
        self.energy_plan = None

    @property
    def prediction_strategy(self) -> PredictionStrategy:
        return self._prediction_strategy

    @prediction_strategy.setter
    def prediction_strategy(self, strategy: Union[PredictionStrategy, None]) -> None:
        self._prediction_strategy = strategy

    @staticmethod
    def is_ascending(arr: List[Union[int, float]]) -> bool:
        n = len(arr)
        for i in range(1, n):
            if arr[i - 1] > arr[i]:
                return False
        return True

    def calculate_cost(self, predicted_balance: float, current_balance: float, rce_price: float) -> float:
        if current_balance >= 0:
            energy_surplus = self.energy_bank.manage_energy(current_balance)
            cost = -energy_surplus * rce_price
        else:
            if predicted_balance > 0.0:
                raise Exception("Impossible")
            if predicted_balance == 0.0:
                cost = -current_balance * rce_price
            elif 0 > predicted_balance >= current_balance:
                balance_after_bank = self.energy_bank.manage_energy(predicted_balance)
                balance_diff = round(current_balance + balance_after_bank, 2)
                cost = -balance_diff * rce_price
            elif predicted_balance < 0 and predicted_balance < current_balance:
                balance_after_bank = self.energy_bank.manage_energy(current_balance)
                cost = -balance_after_bank * rce_price
        return cost

    def create_energy_plan(self, date_in: pd.Timestamp) -> None:
        start = date_in
        sunrise, sunset = self.sun_manager.get_sun_data(date_in)
        logger.info(f"sunrise: {sunrise} and sunset: {sunset}")
        if date_in.hour >= sunset:
            self.prediction_strategy = NightPredictionStrategy(self.energy_bank.min_lvl, self.energy_bank.capacity)
            end = start.replace(day=date_in.day + 1, hour=sunrise)
        elif sunrise <= date_in.hour < sunset:
            self.prediction_strategy = DayFullBankPredictionStrategy(self.energy_bank.min_lvl,
                                                                     self.energy_bank.capacity)
            end = start.replace(hour=sunset)
        else:
            self.prediction_strategy = NightPredictionStrategy(self.energy_bank.min_lvl, self.energy_bank.capacity)
            end = start.replace(hour=sunrise)
        logger.info(f"New plan type: {type(self.prediction_strategy)}")
        rce_prices = self.energy_pricer.get_rce_by_date(start, end)
        consumptions = self.consumer.get_consumption_by_date(start, end)
        productions = self.producer.get_production_by_date(start, end)
        balances = [round(prod - cons, 2) for (prod, cons) in zip(productions, consumptions)]
        dates = pd.date_range(start=start, end=end, freq=timedelta(hours=1))
        logger.info(f"Input rce_prices: {rce_prices}")
        logger.info(f"Input productions: {productions}")
        logger.info(f"Input consumptions: {consumptions}")
        logger.info(f"Input balances: {balances}")
        energy_plan = self.prediction_strategy.get_plan(self.energy_bank.lvl, rce_prices, balances)
        logger.info(f"energy_plan: {energy_plan}")
        logger.info("")
        self.energy_plan = {k: v for k, v in zip(dates, energy_plan)}

    def feed_consumption(self, date_in: pd.Timestamp) -> None:
        if self.prediction_strategy is None or self.energy_plan is None:
            self.create_energy_plan(date_in)
        rce_price = self.energy_pricer.get_rce_by_date(date_in)
        consumption = self.consumer.get_consumption_by_date(date_in)
        production = self.producer.get_production_by_date(date_in)
        current_balance = round(production - consumption, 2)
        current_balance = round(current_balance * random.uniform(0.8, 1.2), 2)
        predicted_balance = self.energy_plan[date_in]
        logger.info(f"Current balance: {current_balance}")
        logger.info(f"Predicted balance: {predicted_balance}")
        logger.info(f"Current bank lvl: {self.energy_bank.lvl}")
        cost = self.calculate_cost(predicted_balance, current_balance, rce_price)
        logger.info(f"Current cost: {cost}")
        self.summed_cost += cost / 1000
        if self.energy_plan.get(date_in + timedelta(hours=1)) is None:
            self.energy_plan = None
        logger.info(f"After operations bank lvl: {self.energy_bank.lvl}")
        self.plotter.add_data_row([date_in, rce_price, consumption, production, self.energy_bank.lvl, self.summed_cost])
