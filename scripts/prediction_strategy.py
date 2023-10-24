import random
from abc import ABC, abstractmethod
from typing import List
from scripts.energy_bank import EnergyBank

import numpy as np


class PredictionStrategy(ABC):
    @abstractmethod
    def get_plan(self, start_energy: float, prices: List[float], hourly_balances: List[float]) -> None:
        pass


class DayPredictionStrategy(PredictionStrategy):
    def __init__(self, min_energy, max_energy):
        self.min_energy = min_energy
        self.max_energy = max_energy
        self.energy_bank = EnergyBank(capacity=max_energy, min_lvl=min_energy)

    @staticmethod
    def sort_list_idxes_ascending(prices) -> List[int]:
        return np.argsort(prices)[:].tolist()

    def forecast_final_energy_lvl(self, energy_lvl, balances: List[float]) -> float:
        current_energy_lvl = energy_lvl
        for energy_idx in range(len(balances)):
            potential_energy_lvl = current_energy_lvl + balances[energy_idx]
            if potential_energy_lvl >= self.max_energy:
                current_energy_lvl = self.max_energy
            elif potential_energy_lvl < self.min_energy:
                current_energy_lvl = 0.0
            else:
                current_energy_lvl += balances[energy_idx]
        return round(current_energy_lvl, 2)

    def _optimize_balance(self, energy_lvl: float, need: float, balances: List[float]) -> (List[float], float):
        positive_balances = [i for i in balances if i > 0]
        if energy_lvl + sum(positive_balances) <= self.max_energy:
            for i in range(len(balances)):
                if balances[i] < 0.0:
                    need -= abs(balances[i])
                    balances[i] = 0.0
            return balances, need
        predicted_en = self.forecast_final_energy_lvl(energy_lvl, balances)
        new_predicted_en = self.forecast_final_energy_lvl(energy_lvl, balances[1:])
        if new_predicted_en == predicted_en:
            if energy_lvl + balances[0] < 0:
                balances[0] = 0.0
            return balances, need
        current_need = abs(balances[0])
        if need <= current_need:
            current_need = need
        balances[0] += current_need
        return balances, need - current_need

    def get_plan(self, start_energy: float, prices: List[float], hourly_balances: List[float]) -> List[float]:
        predicted_final_lvl = self.forecast_final_energy_lvl(start_energy, hourly_balances)
        negative_index_list = [idx for idx, value in enumerate(hourly_balances) if value < 0.0]
        # if predicted_final_lvl >= self.max_energy:
        #     return [round(x, 2) for x in hourly_balances]
        need = round(self.max_energy - predicted_final_lvl, 2)
        positive_balances = [i for i in hourly_balances if i > 0]
        print(f"predicted_bank_lvl: {predicted_final_lvl}")
        print(f"need: {need}")
        print(f"Algo will work: {start_energy + sum(positive_balances) > self.max_energy}")
        if start_energy + sum(positive_balances) > self.max_energy:
            idx_order = self.sort_list_idxes_ascending(prices)
            for idx in idx_order:
                if idx in negative_index_list:
                    new_start_energy = self.forecast_final_energy_lvl(start_energy, hourly_balances[:idx])
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

    @staticmethod
    def sort_list_idxes_ascending(prices) -> List[int]:
        return np.argsort(prices)[:].tolist()

    def forecast_final_energy_lvl(self, energy_lvl, balances: List[float]) -> float:
        current_energy_lvl = energy_lvl
        for energy_value in balances:
            potential_energy_lvl = current_energy_lvl + energy_value
            if potential_energy_lvl >= self.max_energy:
                current_energy_lvl = self.max_energy
            elif potential_energy_lvl <= self.min_energy:
                current_energy_lvl = 0.0
            else:
                current_energy_lvl += energy_value
        return round(current_energy_lvl, 2)

    def get_plan(self, start_energy: float, prices: List[float], hourly_balances: List[float]) -> List[float]:
        current_energy_lvl = start_energy
        for i in range(len(hourly_balances)):
            potential_energy_lvl = current_energy_lvl + hourly_balances[i]
            if potential_energy_lvl >= self.max_energy:
                current_energy_lvl = self.max_energy
            elif potential_energy_lvl >= self.min_energy:
                current_energy_lvl = potential_energy_lvl
            else:
                current_energy_lvl = 0.0
                inner_balances = hourly_balances[:i + 1]
                extra = self.forecast_final_energy_lvl(start_energy, inner_balances[:-1]) + inner_balances[-1]  
                idx_order = self.sort_list_idxes_ascending(prices[:i + 1])
                for idx in idx_order:
                    if idx == len(inner_balances) - 1:
                        inner_balances[idx] -= extra
                        hourly_balances[:i + 1] = inner_balances[:i + 1]
                        break
                    else:
                        if inner_balances[idx] < 0.0:
                            if inner_balances[idx] <= extra:
                                inner_balances[idx] -= extra
                                hourly_balances[:i + 1] = inner_balances[:i + 1]
                                hourly_balances = [round(x, 2) for x in hourly_balances]
                                break
                            else:
                                extra -= inner_balances[idx]
                                inner_balances[idx] = 0.0
                                hourly_balances[:i + 1] = inner_balances[:i + 1]
                                hourly_balances = [round(x, 2) for x in hourly_balances]
                        else:
                            continue
        return [round(x, 2) for x in hourly_balances]


if __name__ == "__main__":
    my_min_energy = 0.0
    my_start_energy = round(random.uniform(1.0, 2.5), 2)
    my_max_energy = 3.0
    random_prices = [round(random.uniform(100.0, 300.0), 2) for _ in range(5)]
    day_random_hourly_balances = [round(random.uniform(-1.0, 1.5), 2) for _ in range(5)]
    night_random_hourly_balances = [round(random.uniform(-1.0, 0.3), 2) for _ in range(5)]
    print(f"Start energy lvl: {my_start_energy}")
    print(f"random_prices: {random_prices}")
    print()
    print(f"day_random_hourly_balances: {day_random_hourly_balances}")
    day_algo = DayPredictionStrategy(my_min_energy, my_max_energy)
    day_plan = day_algo.get_plan(my_start_energy, random_prices, day_random_hourly_balances)
    print(f"Finished day plan: {day_plan}")
    print(f"Final energy lvl: {day_algo.forecast_final_energy_lvl(my_start_energy, day_plan)}")
    print()
    print(f"night_random_hourly_balances: {night_random_hourly_balances}")
    night_algo = NightPredictionStrategy(my_min_energy, my_max_energy)
    night_plan = night_algo.get_plan(my_start_energy, random_prices, night_random_hourly_balances)
    print(f"Finished night plan: {night_plan}")
    print(f"Final energy lvl: {night_algo.forecast_final_energy_lvl(my_start_energy, night_plan)}")
