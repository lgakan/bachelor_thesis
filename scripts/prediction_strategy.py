import random
from abc import ABC, abstractmethod
from typing import List

import numpy as np

from lib.logger import logger
from scripts.energy_bank import EnergyBank


def sort_list_idxes_ascending(list_in: List[float]) -> List[int]:
    return np.argsort(list_in)[:].tolist()


def simulate_eb(min_energy, max_energy, energy_lvl, balance: float) -> float:
    potential_energy_lvl = energy_lvl + balance
    if potential_energy_lvl >= max_energy:
        return max_energy
    elif min_energy < potential_energy_lvl < max_energy:
        return round(potential_energy_lvl, 2)
    else:
        return min_energy


def forecast_final_energy_lvl(min_energy, max_energy, energy_lvl, balances: List[float]) -> float:
    current_energy_lvl = energy_lvl
    for balance_value in balances:
        current_energy_lvl = simulate_eb(min_energy, max_energy, current_energy_lvl, balance_value)
    return round(current_energy_lvl, 2)


def negative_prices_process(prices: List[float], balances: List[float]) -> List[List[float]]:
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
        self.energy_bank = EnergyBank(capacity=max_energy, min_lvl=min_energy)

    def _optimize_balance(self, energy_lvl: float, need: float, balances: List[float]) -> (List[float], float):
        positive_balances = [i for i in balances if i > 0]
        if energy_lvl + sum(positive_balances) <= self.max_energy:
            for i in range(len(balances)):
                if balances[i] < 0.0:
                    need -= abs(balances[i])
                    balances[i] = 0.0
            return balances, need
        predicted_en = forecast_final_energy_lvl(self.min_energy, self.max_energy, energy_lvl, balances)
        new_predicted_en = forecast_final_energy_lvl(self.min_energy, self.max_energy, energy_lvl, balances[1:])
        if new_predicted_en == predicted_en:
            if energy_lvl + balances[0] < 0:
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

    def get_plan(self, start_energy: float, prices: List[float], hourly_balances: List[float]) -> List[float]:
        if any([price < 0.0 for price in prices]):
            balances_groups = negative_prices_process(prices, hourly_balances)
            for idx_list in range(len(balances_groups)):
                group_start_idx = len([element for sublist in balances_groups[:idx_list] for element in sublist])
                group_last_idx = group_start_idx + len(balances_groups[idx_list])
                group_first_price = prices[group_start_idx]
                if group_first_price > 0:
                    predicted_final_lvl = forecast_final_energy_lvl(self.min_energy, self.max_energy, start_energy, balances_groups[idx_list])
                    negative_index_list = [idx for idx, value in enumerate(balances_groups[idx_list]) if value < 0.0]
                    need = round(self.max_energy - predicted_final_lvl, 2)
                    positive_balances = [i for i in balances_groups[idx_list] if i > 0]
                    if start_energy + sum(positive_balances) > self.max_energy:
                        idx_order = sort_list_idxes_ascending(prices[group_start_idx:group_last_idx])
                        for idx in idx_order:
                            if idx in negative_index_list:
                                current_energy_lvl = forecast_final_energy_lvl(self.min_energy, self.max_energy, start_energy, hourly_balances[group_start_idx:group_start_idx+idx])
                                hourly_balances[group_start_idx+idx: len(balances_groups[idx_list])], need = self._optimize_balance(current_energy_lvl, need, hourly_balances[group_start_idx+idx: len(balances_groups[idx_list])])
                                if need <= 0.0:
                                    break
                    else:
                        positive_hourly_balances = [0 if i < 0 else i for i in hourly_balances[group_start_idx: len(balances_groups[idx_list])]]
                        hourly_balances[group_start_idx: len(balances_groups[idx_list])] = positive_hourly_balances
                else:
                    for idx in range(1, len(balances_groups[idx_list])):
                        current_energy_lvl = forecast_final_energy_lvl(self.min_energy, self.max_energy, start_energy, hourly_balances[group_start_idx:group_start_idx + idx])
                        if current_energy_lvl + hourly_balances[group_start_idx + idx] > self.max_energy:
                            idx_order = sort_list_idxes_ascending(prices[group_start_idx: group_start_idx + idx])
                            hourly_balances[group_start_idx: group_start_idx + idx] = self._optimize_positive_balances(start_energy, hourly_balances[group_start_idx: group_start_idx + idx], idx_order, prices[group_start_idx: group_start_idx + idx])
                        elif hourly_balances[group_start_idx + idx] < 0.0:
                            hourly_balances[group_start_idx + idx] = 0.0
                        else:
                            current_energy_lvl += hourly_balances[group_start_idx + idx]
        else:
            predicted_final_lvl = forecast_final_energy_lvl(self.min_energy, self.max_energy, start_energy, hourly_balances)
            negative_index_list = [idx for idx, value in enumerate(hourly_balances) if value < 0.0]
            need = round(self.max_energy - predicted_final_lvl, 2)
            positive_balances = [i for i in hourly_balances if i > 0]
            if start_energy + sum(positive_balances) > self.max_energy:
                idx_order = sort_list_idxes_ascending(prices)
                for idx in idx_order:
                    if idx in negative_index_list:
                        new_start_energy = forecast_final_energy_lvl(self.min_energy, self.max_energy, start_energy, hourly_balances[:idx])
                        hourly_balances[idx:], need = self._optimize_balance(new_start_energy, need, hourly_balances[idx:])
                        if need <= 0.0:
                            break
            else:
                positive_hourly_balances = [0 if i < 0 else i for i in hourly_balances]
                return positive_hourly_balances
        return [round(x, 2) for x in hourly_balances]


class NightPredictionStrategy(PredictionStrategy):
    def __init__(self, min_energy, max_energy):
        self.min_energy = min_energy
        self.max_energy = max_energy

    def calculate_hourly_balance(self, start_energy_in, idx_order, hourly_balances_in, i_balance) -> List[float]:
        extra = forecast_final_energy_lvl(self.min_energy, self.max_energy, start_energy_in, hourly_balances_in[:-1]) + hourly_balances_in[-1]
        for idx in idx_order:
            if idx == len(hourly_balances_in) - 1:
                hourly_balances_in[idx] -= extra
                hourly_balances_in[:i_balance + 1] = hourly_balances_in[:i_balance + 1]
                break
            else:
                if hourly_balances_in[idx] < 0.0:
                    if hourly_balances_in[idx] <= extra:
                        hourly_balances_in[idx] -= extra
                        hourly_balances_in[:i_balance + 1] = hourly_balances_in[:i_balance + 1]
                        hourly_balances_in = [round(x, 2) for x in hourly_balances_in]
                        break
                    else:
                        extra -= hourly_balances_in[idx]
                        hourly_balances_in[idx] = 0.0
                        hourly_balances_in[:i_balance + 1] = hourly_balances_in[:i_balance + 1]
                        hourly_balances_in = [round(x, 2) for x in hourly_balances_in]
                else:
                    continue
        return [round(x, 2) for x in hourly_balances_in]

    def get_plan(self, start_energy: float, prices: List[float], hourly_balances: List[float]) -> List[float]:
        current_energy_lvl = start_energy
        if any([price < 0.0 for price in prices]):
            balance_groups = negative_prices_process(prices, hourly_balances)
            for idx_list in range(len(balance_groups)):
                group_start_idx = len([element for sublist in balance_groups[:idx_list] for element in sublist])
                group_last_idx = group_start_idx + len(balance_groups[idx_list])
                group_first_price = prices[group_start_idx]
                if group_first_price > 0:
                    for i in range(group_start_idx, group_last_idx):
                        current_energy_lvl = simulate_eb(self.min_energy, self.max_energy, current_energy_lvl, hourly_balances[i])
                        if current_energy_lvl == self.min_energy:
                            idx_order = sort_list_idxes_ascending(prices[group_start_idx:i + 1])
                            hourly_balances[group_start_idx:i + 1] = self.calculate_hourly_balance(start_energy, idx_order, hourly_balances[group_start_idx:i + 1], i + group_start_idx)
                else:
                    current_energy_lvl = start_energy = 3.0
                    hourly_balances[group_start_idx: group_start_idx + len(balance_groups[idx_list])] = [0] * len(balance_groups[idx_list])
        else:
            for i in range(len(hourly_balances)):
                current_energy_lvl = simulate_eb(self.min_energy, self.max_energy, current_energy_lvl, hourly_balances[i])
                if current_energy_lvl == self.min_energy:
                    idx_order = sort_list_idxes_ascending(prices[:i + 1])
                    hourly_balances = self.calculate_hourly_balance(start_energy, idx_order, hourly_balances, i)
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
