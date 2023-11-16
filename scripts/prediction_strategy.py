import random
from abc import ABC, abstractmethod
from typing import List, Union
import copy

import numpy as np

from lib.logger import logger
from scripts.energy_bank import EnergyBank


def sort_list_idxes_ascending(list_in: List[float]) -> List[int]:
    return np.argsort(list_in)[:].tolist()


def simulate_eb_operation(eb: EnergyBank, balance_in: Union[float, List[float]], start_lvl: Union[None, float]) -> float:
    fake_eb = copy.deepcopy(eb)
    if start_lvl is not None:
        fake_eb.lvl = start_lvl
    if isinstance(balance_in, float):
        fake_eb.manage_energy(balance_in)
    elif isinstance(balance_in, list):
        for balance_value in balance_in:
            fake_eb.manage_energy(balance_value)
    return fake_eb.lvl


def separate_negative_prices(prices: List[float], balances: List[float]) -> List[List[float]]:
    # [1, 2, -3, -4, 5, -6, 7] -> [[1, 2], [-3, -4], [5], [-6], [7]]
    if all([i > 0 for i in prices]):
        raise Exception("At least 1 price needs to be negative!")
    balances_lists = [[balances[0]]]
    for i in range(1, len(balances)):
        if (prices[i - 1] > 0 and prices[i] > 0) or (prices[i - 1] < 0 and prices[i] < 0):
            balances_lists[-1].append(balances[i])
        else:
            balances_lists.append([balances[i]])
    return balances_lists


class PredictionStrategy(ABC):
    @abstractmethod
    def get_plan(self, start_energy: float, prices: List[float], hourly_balances: List[float]) -> None:
        pass


class DayPredictionStrategy(PredictionStrategy):
    def __init__(self, min_energy, max_energy):
        self.min_energy = min_energy
        self.max_energy = max_energy

    def _optimize_balances(self, eb: EnergyBank, need: float, balances: List[float]) -> (List[float], float):
        positive_balances = [i for i in balances if i > 0]
        if eb.lvl + sum(positive_balances) <= self.max_energy:
            for i in range(len(balances)):
                if balances[i] < 0.0:
                    need -= abs(balances[i])
                    balances[i] = 0.0
            return balances, need
        predicted_en = simulate_eb_operation(eb, balances)
        new_predicted_en = simulate_eb_operation(eb, balances[1:])
        if new_predicted_en == predicted_en:
            if eb.lvl + balances[0] < 0:
                balances[0] = 0.0
            return balances, need
        current_need = abs(balances[0])
        if need <= current_need:
            current_need = need
        balances[0] += current_need
        return balances, need - current_need

    def _optimize_positive_balances(self, start_energy: float, balances: List[float], prices_order: List[int], prices: List[float]) -> List[float]:
        if prices_order[-1] == len(balances) - 1:
            return balances
        for idx in range(len(balances)-1, 0, -1):
            current_energy_lvl = forecast_final_energy_lvl(self.min_energy, self.max_energy, start_energy, balances[:idx])
            if current_energy_lvl + balances[idx] > self.max_energy and prices[idx] > prices[idx-1]:
                i_need = balances[idx] + current_energy_lvl - self.max_energy
                new_balance = max(0.0, balances[idx] - i_need)
                balances[idx-1] = new_balance
        return balances

    def mixed_prices_handler(self, eb: EnergyBank, start_energy: float, prices: List[float], hourly_balances: List[float]):
        balances_groups = separate_negative_prices(prices, hourly_balances)
        for idx_list in range(len(balances_groups)):
            idx_group_start = len([element for sublist in balances_groups[:idx_list] for element in sublist])
            idx_group_end = idx_group_start + len(balances_groups[idx_list])
            group_first_price = prices[idx_group_start]
            if group_first_price > 0:
                self.positive_prices_handler(eb, start_energy, prices[idx_group_start:idx_group_end], hourly_balances[idx_group_start:idx_group_end])
                # predicted_final_lvl = simulate_eb_operation(eb, balances_groups[idx_list], start_energy)
                # negative_index_list = [idx for idx, value in enumerate(balances_groups[idx_list]) if value < 0.0]
                # need = round(self.max_energy - predicted_final_lvl, 2)
                # positive_balances = [i for i in balances_groups[idx_list] if i > 0]
                # is_full_eb_possible = eb.lvl + sum(positive_balances) > self.max_energy
                # if is_full_eb_possible:
                #     idx_order = sort_list_idxes_ascending(prices[idx_group_start:idx_group_end])
                #     for idx in idx_order:
                #         if idx in negative_index_list:
                #             eb.lvl = simulate_eb_operation(eb, hourly_balances[idx_group_start:idx_group_end+idx], start_energy)
                #             hourly_balances[idx_group_start+idx:idx_group_end], need = self._optimize_balances(eb, need, hourly_balances[idx_group_start+idx:idx_group_end])
            else:
                for idx in range(1, len(balances_groups[idx_list])):
                    eb.lvl = simulate_eb_operation(eb, hourly_balances[idx_group_start:idx_group_end + idx], start_energy)
                    is_full_eb_possible = eb.lvl + hourly_balances[idx_group_start + idx] > self.max_energy
                    if is_full_eb_possible:
                        idx_order = sort_list_idxes_ascending(prices[idx_group_start: idx_group_end + idx])
                        balances_to_optimize = hourly_balances[idx_group_start:idx_group_end + idx]
                        prices_to_optimize = prices[idx_group_start: idx_group_end + idx]
                        balances_to_optimize = self._optimize_positive_balances(eb, balances_to_optimize, idx_order, prices_to_optimize)
                    elif hourly_balances[idx_group_start + idx] < 0.0:
                        hourly_balances[idx_group_start + idx] = 0.0
                    else:
                        eb.lvl += hourly_balances[idx_group_start + idx] # TODO

    def positive_prices_handler(self, eb: EnergyBank, start_energy: float, prices: List[float], hourly_balances: List[float]):
        predicted_final_lvl = simulate_eb_operation(eb, hourly_balances)
        negative_index_list = [idx for idx, value in enumerate(hourly_balances) if value < 0.0]
        need = round(self.max_energy - predicted_final_lvl, 2)
        positive_balances = [i for i in hourly_balances if i > 0]
        is_full_eb_possible = eb.lvl + sum(positive_balances) > self.max_energy
        if is_full_eb_possible:
            idx_order = sort_list_idxes_ascending(prices)
            for idx in idx_order:
                if idx in negative_index_list:
                    eb.lvl = simulate_eb_operation(eb, hourly_balances[:idx], start_energy)
                    hourly_balances[idx:], need = self._optimize_balances(eb, need, hourly_balances[idx:])
                    if need <= 0.0:
                        break
                    pass
        else:
            positive_hourly_balances = [0 if i < 0 else i for i in hourly_balances]
            return positive_hourly_balances
        return hourly_balances

    def get_plan(self, start_energy: float, prices: List[float], hourly_balances: List[float]) -> List[float]:
        eb = EnergyBank(min_lvl=self.min_energy, capacity=self.max_energy, lvl=start_energy)
        if any([price < 0.0 for price in prices]):
            hourly_balances = self.mixed_prices_handler(eb, prices, hourly_balances)
        else:
            hourly_balances = self.positive_prices_handler(eb, start_energy, prices, hourly_balances)
        return [round(x, 2) for x in hourly_balances]


class NightPredictionStrategy(PredictionStrategy):
    def __init__(self, min_energy, max_energy):
        self.min_energy = min_energy
        self.max_energy = max_energy

    @staticmethod
    def calculate_hourly_balances(eb: EnergyBank, idx_order: List[int], hourly_balances_in: List[float]) -> List[float]:
        extra = simulate_eb_operation(eb, hourly_balances_in[:-1]) + hourly_balances_in[-1]
        for idx in idx_order:
            idx_last = len(hourly_balances_in) - 1
            is_extra_higher_than_balance = hourly_balances_in[idx] <= extra
            are_negative = hourly_balances_in[idx] <= 0.0 and extra <= 0.0
            if idx == idx_last or (is_extra_higher_than_balance and are_negative):
                hourly_balances_in[idx] -= extra
                break
            elif hourly_balances_in[idx] >= 0.0 > extra:
                extra -= hourly_balances_in[idx]
                hourly_balances_in[idx] = 0.0
        return [round(x, 2) for x in hourly_balances_in]

    def mixed_prices_handler(self, eb: EnergyBank, prices: List[float], hourly_balances: List[float]):
        balances_groups = separate_negative_prices(prices, hourly_balances)
        for idx_list in range(len(balances_groups)):
            idx_group_start = len([element for sublist in balances_groups[:idx_list] for element in sublist])
            idx_group_end = idx_group_start + len(balances_groups[idx_list])
            group_first_price = prices[idx_group_start]
            if group_first_price > 0:
                group_prices = prices[idx_group_start:idx_group_end]
                group_balances = hourly_balances[idx_group_start:idx_group_end]
                self.positive_prices_handler(eb, group_prices, group_balances)
            else:
                eb.lvl = eb.capacity
                idle_length = len(balances_groups[idx_list])
                idx_group_end = idx_group_start + idle_length
                idle_hours = [0] * idle_length
                hourly_balances[idx_group_start: idx_group_end] = idle_hours
        return hourly_balances

    def positive_prices_handler(self, eb: EnergyBank, prices: List[float], hourly_balances: List[float]):
        for idx in range(len(hourly_balances)):
            eb.manage_energy(hourly_balances[idx])
            if eb.lvl == self.min_energy:
                idx_desc_order = sort_list_idxes_ascending(prices[:idx + 1])[::-1]
                hourly_balances[:idx + 1] = self.calculate_hourly_balances(eb, idx_desc_order, hourly_balances[:idx + 1])
        return hourly_balances

    def get_plan(self, start_energy: float, prices: List[float], hourly_balances: List[float]) -> List[float]:
        eb = EnergyBank(min_lvl=self.min_energy, capacity=self.max_energy, lvl=start_energy)
        if any([price < 0.0 for price in prices]):
            hourly_balances = self.mixed_prices_handler(eb, prices, hourly_balances)
        else:
            hourly_balances = self.positive_prices_handler(eb, prices, hourly_balances)
        return [round(x, 2) for x in hourly_balances]


if __name__ == "__main__":
    my_min_energy = 0.0
    my_start_energy = round(random.uniform(1.0, 2.5), 2)
    my_max_energy = 3.0
    random_prices = [round(random.uniform(-50.0, 200.0), 2) for _ in range(5)]
    day_random_hourly_balances = [round(random.uniform(-1.0, 1.5), 2) for _ in range(5)]
    night_random_hourly_balances = [round(random.uniform(-1.0, 0.3), 2) for _ in range(5)]
    logger.info(f"Start energy lvl: {my_start_energy}")
    logger.info(f"random_prices: {random_prices}")
    logger.info(f"day_random_hourly_balances: {day_random_hourly_balances}")
    day_algo = DayPredictionStrategy(my_min_energy, my_max_energy)
    day_plan = day_algo.get_plan(my_start_energy, random_prices, day_random_hourly_balances)
    logger.info(f"Finished day plan: {day_plan}")
    logger.info(f"Final energy lvl: {forecast_final_energy_lvl(my_min_energy, my_max_energy, my_start_energy, day_plan)}")
    logger.info(f"night_random_hourly_balances: {night_random_hourly_balances}")
    night_algo = NightPredictionStrategy(my_min_energy, my_max_energy)
    night_plan = night_algo.get_plan(my_start_energy, random_prices, night_random_hourly_balances)
    logger.info(f"Finished night plan: {night_plan}")
