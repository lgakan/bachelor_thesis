from datetime import timedelta
from typing import Union

import pandas as pd

from lib.logger import logger
from lib.sun_manager import SunManager
from scripts.energy_bank import EnergyBank
from scripts.prediction_strategy import PredictionStrategy, DayPredictionStrategy, NightPredictionStrategy
from scripts.pv import Pv
from systems.system_base import SystemBase


class SmartSystem(SystemBase):
    def __init__(self, energy_bank: EnergyBank, pv_producer: Pv, load_multiplier: Union[None, int] = None, **kwargs):
        super().__init__(load_multiplier=load_multiplier)
        self.producer = pv_producer
        self.energy_bank = energy_bank
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

    def calculate_average_energy_cost(self, start: pd.Timestamp, end: pd.Timestamp) -> None:
        prices = self.energy_pricer.get_rce_by_date(start, end)
        self.average_energy_cost = sum(prices) / len(prices)

    def calculate_cost(self, price: float, predicted_bal: float, real_bal: float) -> float:
        if price >= 0.0:
            return self._calculate_cost_positive_price(price, predicted_bal, real_bal)
        else:
            return self._calculate_cost_negative_price(price, predicted_bal, real_bal)

    def _calculate_cost_positive_price(self, price: float, predicted_bal: float, real_bal: float) -> float:
        if price >= self.average_energy_cost or real_bal >= 0.0:
            if predicted_bal >= 0.0 and real_bal >= 0.0:
                return self._calculate_cost_positive_balance(price, predicted_bal, real_bal)
            elif predicted_bal <= 0.0 and real_bal <= 0.0:
                return self._calculate_cost_negative_balance(price, predicted_bal, real_bal)
            elif predicted_bal <= 0 and real_bal >= 0.0:
                rest_predicted = self.energy_bank.manage_energy(predicted_bal)
                bank_operation_cost = self.energy_bank.operation_cost(predicted_bal - rest_predicted)
                current_energy_profit = -price * real_bal
                bank_energy_profit = -price * (predicted_bal - rest_predicted)
                return bank_energy_profit + current_energy_profit + bank_operation_cost
            raise Exception(f"Unexpected predicted_bal: {predicted_bal} and real_bal: {real_bal} values!")
        elif real_bal < 0.0 < price < self.average_energy_cost:
            return -real_bal * price

    def _calculate_cost_negative_price(self, price: float, predicted_bal: float, real_bal: float, last_hour: bool = False) -> float:
        bank_free_space = self.energy_bank.capacity - self.energy_bank.lvl
        if isinstance(self._prediction_strategy, NightPredictionStrategy):
            self.energy_bank.manage_energy(bank_free_space)
            bank_filling_cost = self.energy_bank.operation_cost(bank_free_space)
            if predicted_bal >= 0.0 and real_bal >= 0.0:
                return self._calculate_cost_positive_balance(price, predicted_bal, real_bal) + bank_filling_cost
            elif predicted_bal <= 0.0 and real_bal <= 0.0:
                return self._calculate_cost_negative_balance(price, predicted_bal, real_bal) + bank_filling_cost
            raise Exception(f"predicted_bal: {predicted_bal} and real_bal: {real_bal} must be of the same sign!")
        else:
            rest_real = self.energy_bank.manage_energy(real_bal)
            bank_operation_cost = self.energy_bank.operation_cost(real_bal - rest_real)
            if last_hour:
                bank_operation_cost += self.energy_bank.operation_cost(self.energy_bank.capacity - self.energy_bank.lvl)
                self.energy_bank.lvl = self.energy_bank.capacity
            return -(real_bal - rest_real) * price + bank_operation_cost

    def _calculate_cost_positive_balance(self, price: float, predicted_bal: float, real_bal: float) -> float:
        if real_bal < 0.0 or predicted_bal < 0.0:
            raise Exception(f"predicted_bal: {predicted_bal} and real_bal: {real_bal} must be positive!")
        bank_free_space = self.energy_bank.capacity - self.energy_bank.lvl
        if real_bal <= bank_free_space:
            if real_bal >= predicted_bal:
                self.energy_bank.manage_energy(predicted_bal)
                return -round(real_bal - predicted_bal, 2) * price + self.energy_bank.operation_cost(predicted_bal)
            else:
                self.energy_bank.manage_energy(real_bal)
                return self.energy_bank.operation_cost(real_bal)
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
            prediction_diff = predicted_bal - reduced_predicted_bal
            return -round(real_bal - prediction_diff, 2) * price + self.energy_bank.operation_cost(prediction_diff)
        elif real_bal >= predicted_bal and abs_real <= bank_lvl:
            reduced_real_bal = self.energy_bank.manage_energy(real_bal)
            real_diff = real_bal - reduced_real_bal
            return self.energy_bank.operation_cost(real_diff)
        raise Exception("Error!")

    def _choose_prediction_strategy(self, date_in: pd.Timestamp) -> pd.Timestamp:
        sunrise, sunset = self.sun_manager.get_sun_data(date_in)
        if date_in.hour >= sunset:
            self.prediction_strategy = NightPredictionStrategy(self.energy_bank.min_lvl, self.energy_bank.capacity)
            strategy_end_date = date_in.replace(day=date_in.day + 1, hour=sunrise)
        elif sunrise <= date_in.hour < sunset:
            self.prediction_strategy = DayPredictionStrategy(self.energy_bank.min_lvl, self.energy_bank.capacity)
            strategy_end_date = date_in.replace(hour=sunset)
        else:
            self.prediction_strategy = NightPredictionStrategy(self.energy_bank.min_lvl, self.energy_bank.capacity)
            strategy_end_date = date_in.replace(hour=sunrise)
        if self.average_energy_cost is None or date_in.hour == sunset or date_in.hour == sunrise:
            self.calculate_average_energy_cost(date_in, strategy_end_date)
        return strategy_end_date

    def create_energy_plan(self, start_date: pd.Timestamp) -> None:
        strategy_end_date = self._choose_prediction_strategy(start_date)
        rce_prices = self.energy_pricer.get_rce_by_date(start_date, strategy_end_date)
        consumptions = self.consumer.get_consumption_by_date(start_date, strategy_end_date)
        productions = self.producer.get_production_by_date(start_date, strategy_end_date)
        balances = [round(prod - cons, 2) for (prod, cons) in zip(productions, consumptions)]
        dates = pd.date_range(start=start_date, end=strategy_end_date, freq=timedelta(hours=1))
        energy_plan = self.prediction_strategy.get_plan(self.energy_bank.lvl, rce_prices, balances)
        logger.info(f"SmartSystem EP input rce_prices: {rce_prices}")
        logger.info(f"SmartSystem EP input balances: {balances}")
        logger.info(f"SmartSystem EP: {energy_plan}")
        self.energy_plan = {k: v for k, v in zip(dates, energy_plan)}

    def feed_consumption(self, date_in: pd.Timestamp) -> None:
        self.create_energy_plan(date_in)
        rce_price = self.energy_pricer.get_rce_by_date(date_in)
        consumption = self.consumer.get_consumption_by_date(date_in)
        production = self.producer.get_production_by_date(date_in)
        current_balance = round(production - consumption, 2)
        predicted_balance = self.energy_plan[date_in]
        cost = self.calculate_cost(rce_price, predicted_balance, current_balance)
        self.log_data(cost, current_balance, self.energy_bank.lvl)
        self.summed_cost += round(cost, 2)
        self.plotter.add_data_row([date_in, rce_price, consumption, production, self.energy_bank.lvl, self.summed_cost])
