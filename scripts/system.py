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
from scripts.prediction_strategy import PredictionStrategy, DayPredictionStrategy, NightPredictionStrategy
from scripts.pv import Pv


class SystemBase:
    def __init__(self, load_multiplier: Union[None, int] = None):
        self.summed_cost = 0
        self.energy_pricer = EnergyWebScraper(date_column="Date")
        self.plotter = Plotter(["price [zl]", "consumption [kWh]", "production [kWh]", "energy_bank [kWh]", "Total price [zl]"])
        self.consumer = Load(date_column="Date", multiplier=load_multiplier)

    @abstractmethod
    def feed_consumption(self, date_in: pd.Timestamp) -> None:
        pass

    def plot_charts(self):
        return self.plotter.plot_charts(f"System Data - {self.__class__.__name__}")


class BareSystem(SystemBase):
    def __init__(self, load_multiplier: Union[None, int] = None, **kwargs):
        super().__init__(load_multiplier=load_multiplier)

    @staticmethod
    def calculate_cost(price: float, consumption: float) -> float:
        return consumption * price

    def feed_consumption(self, date_in: pd.Timestamp) -> None:
        fake_consumption = self.consumer.get_consumption_by_date(date_in)
        random.seed(0)
        consumption = round(fake_consumption * random.uniform(0.8, 1.2), 2)
        rce_price = self.energy_pricer.get_rce_by_date(date_in)
        cost = self.calculate_cost(consumption, rce_price)
        self.summed_cost += cost / 1000
        self.plotter.add_data_row([date_in, rce_price, consumption, 0, 0, self.summed_cost])


class PvSystem(SystemBase):
    def __init__(self, pv_size: int = 5, load_multiplier: Union[None, int] = None, **kwargs):
        super().__init__(load_multiplier=load_multiplier)
        self.producer = Pv(date_column="Date", size=pv_size)

    @staticmethod
    def calculate_cost(price: float, consumption: float) -> float:
        if consumption < 0.0:
            raise Exception(f"Consumption: {consumption} must be greater than 0.0")
        if price < 0.0 < consumption:
            return -consumption * price
        return consumption * price

    def feed_consumption(self, date_in: pd.Timestamp) -> None:
        consumption = self.consumer.get_consumption_by_date(date_in)
        rce_price = self.energy_pricer.get_rce_by_date(date_in)
        production = self.producer.get_production_by_date(date_in)
        fake_reduced_consumption = round(consumption - production, 2)
        random.seed(0)
        reduced_consumption = round(fake_reduced_consumption * random.uniform(0.8, 1.2), 2)
        cost = self.calculate_cost(rce_price, reduced_consumption)
        self.summed_cost += cost / 1000
        self.plotter.add_data_row([date_in, rce_price, consumption, production, 0, self.summed_cost])


class RawFullSystem(SystemBase):
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

    def calculate_cost(self, price: float, balance: float) -> float:
        bank_lvl = self.energy_bank.lvl
        balance_after_bank = self.energy_bank.manage_energy(balance)
        if balance >= 0.0:
            cost = - balance_after_bank * price + self.energy_bank.operation_cost(balance - balance_after_bank)
        else:
            cost = - balance_after_bank * price + self.energy_bank.operation_cost(min(bank_lvl, abs(balance)))
        return cost

    def feed_consumption(self, date_in: pd.Timestamp) -> None:
        consumption = self.consumer.get_consumption_by_date(date_in)
        rce_price = self.energy_pricer.get_rce_by_date(date_in)
        production = self.producer.get_production_by_date(date_in)
        fake_current_balance = round(production - consumption, 2)
        random.seed(0)
        current_balance = round(fake_current_balance * random.uniform(0.8, 1.2), 2)
        cost = self.calculate_cost(rce_price, current_balance)
        logger.info(f"RawSystem current cost: {cost}")
        self.summed_cost += cost / 1000
        self.plotter.add_data_row([date_in, rce_price, consumption, production, self.energy_bank.lvl, self.summed_cost])


class SmartSystem(SystemBase):
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
        self._prediction_strategy = None
        self.energy_plan = None
        self.average_energy_cost = None

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

    def calculate_average_energy_cost(self, start: pd.Timestamp, end: pd.Timestamp) -> None:
        prices = self.energy_pricer.get_rce_by_date(start, end)
        self.average_energy_cost = sum(prices) / len(prices)

    def calculate_cost(self, price: float, predicted_bal: float, real_bal: float) -> float:
        # if predicted_bal >= 0.0 and real_bal >= 0.0:
        #     return self._calculate_cost_positive_balance(price, predicted_bal, real_bal)
        # elif predicted_bal <= 0.0 and real_bal <= 0.0:
        #     return self._calculate_cost_negative_balance(price, predicted_bal, real_bal)
        # raise Exception(f"predicted_bal: {predicted_bal} and real_bal: {real_bal} must be of the same sign!")
        if price >= 0.0 and price >= self.average_energy_cost:
            if predicted_bal >= 0.0 and real_bal >= 0.0:
                return self._calculate_cost_positive_balance(price, predicted_bal, real_bal)
            elif predicted_bal <= 0.0 and real_bal <= 0.0:
                return self._calculate_cost_negative_balance(price, predicted_bal, real_bal)
            raise Exception(f"predicted_bal: {predicted_bal} and real_bal: {real_bal} must be of the same sign!")
        elif 0.0 < price < self.average_energy_cost:
            return -real_bal * price

    def _calculate_cost_positive_balance(self, price: float, predicted_bal: float, real_bal: float) -> float:
        if real_bal < 0.0 or predicted_bal < 0.0:
            raise Exception(f"predicted_bal: {predicted_bal} and real_bal: {real_bal} must be positive!")
        bank_free_space = self.energy_bank.capacity - self.energy_bank.lvl
        if real_bal <= bank_free_space:
            if real_bal >= predicted_bal:
                self.energy_bank.manage_energy(predicted_bal)
                return -round(real_bal - predicted_bal, 2) * price + self.energy_bank.operation_cost(predicted_bal)
            else:
                self.energy_bank.manage_energy(min(real_bal, predicted_bal))
                return self.energy_bank.operation_cost(min(real_bal, predicted_bal))
        else:
            if real_bal >= bank_free_space >= predicted_bal:
                self.energy_bank.manage_energy(predicted_bal)
                return -round(real_bal - predicted_bal, 2) * price + self.energy_bank.operation_cost(predicted_bal)
            else:
                self.energy_bank.manage_energy(bank_free_space)
                return -round(real_bal - bank_free_space, 2) * price + self.energy_bank.operation_cost(bank_free_space)

    def _calculate_cost_negative_balance(self, price: float, predicted_bal: float, real_bal: float) -> float:
        if real_bal > 0.0 or predicted_bal > 0.0:
            raise Exception(f"predicted_bal: {predicted_bal} and real_bal: {real_bal} must be negative!")
        bank_lvl = self.energy_bank.lvl
        abs_pred = abs(predicted_bal)
        abs_real = abs(real_bal)
        if abs_pred >= bank_lvl and abs_real >= bank_lvl:
            self.energy_bank.manage_energy(-bank_lvl)
            return -round(real_bal + bank_lvl, 2) * price + self.energy_bank.operation_cost(bank_lvl)
        elif real_bal < predicted_bal and abs_pred <= bank_lvl:
            reduced_predicted_bal = self.energy_bank.manage_energy(predicted_bal)
            prediction_diff = predicted_bal + reduced_predicted_bal
            return -round(real_bal + prediction_diff, 2) * price + self.energy_bank.operation_cost(prediction_diff)
        elif real_bal >= predicted_bal and abs_real <= bank_lvl:
            reduced_real_bal = self.energy_bank.manage_energy(real_bal)
            real_diff = real_bal - reduced_real_bal
            return self.energy_bank.operation_cost(real_diff)
        raise Exception("Error!")

    def create_energy_plan(self, date_in: pd.Timestamp) -> None:
        start = date_in
        sunrise, sunset = self.sun_manager.get_sun_data(date_in)
        logger.info(f"sunrise: {sunrise} and sunset: {sunset}")
        if date_in.hour >= sunset:
            self.prediction_strategy = NightPredictionStrategy(self.energy_bank.min_lvl, self.energy_bank.capacity)
            end = start.replace(day=date_in.day + 1, hour=sunrise)
        elif sunrise <= date_in.hour < sunset:
            self.prediction_strategy = DayPredictionStrategy(self.energy_bank.min_lvl, self.energy_bank.capacity)
            end = start.replace(hour=sunset)
        else:
            self.prediction_strategy = NightPredictionStrategy(self.energy_bank.min_lvl, self.energy_bank.capacity)
            end = start.replace(hour=sunrise)
        if self.average_energy_cost is None or start.hour == 0:
            self.calculate_average_energy_cost(start, start.replace(hour=23))
        rce_prices = self.energy_pricer.get_rce_by_date(start, end)
        consumptions = self.consumer.get_consumption_by_date(start, end)
        productions = self.producer.get_production_by_date(start, end)
        balances = [round(prod - cons, 2) for (prod, cons) in zip(productions, consumptions)]
        dates = pd.date_range(start=start, end=end, freq=timedelta(hours=1))
        # logger.info(f"Input rce_prices: {rce_prices}")
        # logger.info(f"Input productions: {productions}")
        # logger.info(f"Input consumptions: {consumptions}")
        # logger.info(f"Input balances: {balances}")
        energy_plan = self.prediction_strategy.get_plan(self.energy_bank.lvl, rce_prices, balances)
        # logger.info(f"energy_plan: {energy_plan}")
        self.energy_plan = {k: v for k, v in zip(dates, energy_plan)}

    def feed_consumption(self, date_in: pd.Timestamp) -> None:
        self.create_energy_plan(date_in)
        # if self.prediction_strategy is None or self.energy_plan is None:
        #     self.create_energy_plan(date_in)
        rce_price = self.energy_pricer.get_rce_by_date(date_in)
        consumption = self.consumer.get_consumption_by_date(date_in)
        production = self.producer.get_production_by_date(date_in)
        fake_current_balance = round(production - consumption, 2)
        random.seed(0)
        current_balance = round(fake_current_balance * random.uniform(0.8, 1.2), 2)
        predicted_balance = self.energy_plan[date_in]
        cost = self.calculate_cost(rce_price, predicted_balance, current_balance)
        logger.info(f"SmartSystem current cost: {cost}")
        self.summed_cost += cost / 1000
        # if self.energy_plan.get(date_in + timedelta(hours=1)) is None:
        #     self.energy_plan = None
        self.plotter.add_data_row([date_in, rce_price, consumption, production, self.energy_bank.lvl, self.summed_cost])


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

    def calculate_average_energy_cost(self, start: pd.Timestamp, end: pd.Timestamp) -> None:
        rce_prices = self.energy_pricer.get_rce_by_date(start, end)
        self.average_energy_cost = sum(rce_prices) / len(rce_prices)

    def calculate_cost(self, price: float, balance: float) -> float:
        bank_operation_cost = self.energy_bank.operation_cost(balance)
        if price >= 0.0:
            if balance >= 0.0:
                if price >= self.average_energy_cost + bank_operation_cost:
                    cost = - balance * price
                else:
                    rest_energy = self.energy_bank.manage_energy(balance)
                    cost = - rest_energy * price + self.energy_bank.operation_cost(balance-rest_energy)
            else:
                if price >= self.average_energy_cost + bank_operation_cost:
                    rest_energy = self.energy_bank.manage_energy(balance)
                    cost = -rest_energy * price + self.energy_bank.operation_cost(balance-rest_energy)
                else:
                    cost = -balance * price
        else:
            if balance >= 0.0:
                rest_energy = self.energy_bank.manage_energy(balance)
                cost = - rest_energy * price + self.energy_bank.operation_cost(balance - rest_energy)
            else:
                charged_energy = self.energy_bank.capacity - self.energy_bank.lvl
                self.energy_bank.manage_energy(charged_energy)
                cost = - price * charged_energy + self.energy_bank.operation_cost(charged_energy)
        return cost

    def feed_consumption(self, date_in: pd.Timestamp) -> None:
        sunrise, sunset = self.sun_manager.get_sun_data(date_in)
        logger.info(f"sunrise: {sunrise} and sunset: {sunset}")
        if date_in.hour == sunset or date_in.hour == sunrise or self.average_energy_cost is None:
            if date_in.hour >= sunset:
                end = date_in.replace(day=date_in.day + 1, hour=sunrise)
            elif sunrise <= date_in.hour < sunset:
                end = date_in.replace(hour=sunset)
            else:
                end = date_in.replace(hour=sunrise)
            self.calculate_average_energy_cost(date_in, end)
        rce_price = self.energy_pricer.get_rce_by_date(date_in)
        consumption = self.consumer.get_consumption_by_date(date_in)
        production = self.producer.get_production_by_date(date_in)
        fake_current_balance = round(production - consumption, 2)
        random.seed(0)
        current_balance = round(fake_current_balance * random.uniform(0.8, 1.2), 2)
        cost = self.calculate_cost(rce_price, current_balance)
        logger.info(f"SaveSystem current cost: {cost}")
        self.summed_cost += round(cost / 1000, 2)
        self.plotter.add_data_row([date_in, rce_price, consumption, production, self.energy_bank.lvl, self.summed_cost])
