import random
from typing import List

import numpy as np

from scripts.energy_bank import EnergyBank


class DayEnergy:
    def __init__(self, prices: List[float], hourly_balances: List[float], energy_bank: EnergyBank):
        self.prices = prices
        self.hourly_balance = hourly_balances
        self.max_energy = energy_bank.capacity
        self.min_energy = 0.0
        self.start_energy = energy_bank.get_lvl()

    def _sort_idx_ascending(self) -> List[int]:
        return np.argsort(self.prices)[:].tolist()

    def _predict_bank_lvl(self, energy_lvl, balances: List[float]) -> (float, List[float]):
        current_en_lvl = energy_lvl
        idx_negative_collector = []
        for idx, value in enumerate(balances):
            if value < 0:
                idx_negative_collector.append(idx)
            summed_value = current_en_lvl + value
            if summed_value >= self.max_energy:
                current_en_lvl = self.max_energy
            elif summed_value <= self.min_energy:
                current_en_lvl = 0
            else:
                current_en_lvl += value
        return round(current_en_lvl, 2), idx_negative_collector

    def _optimize_balance(self, energy_lvl: float, need: float, balances: List[float]) -> (List[float], float):
        positive_balances = [i for i in balances if i > 0]
        if energy_lvl + sum(positive_balances) <= self.max_energy:
            for i in range(len(balances)):
                if balances[i] < 0.0:
                    need -= abs(balances[i])
                    balances[i] = 0
            return balances, need
        previous_predicted_en, _ = self._predict_bank_lvl(energy_lvl, balances)
        new_predicted_en, _ = self._predict_bank_lvl(energy_lvl, balances[1:])
        if new_predicted_en == previous_predicted_en:
            return balances, need
        current_need = abs(balances[0])
        if need <= current_need:
            current_need = need
            new_predicted_en, _ = self._predict_bank_lvl(energy_lvl, [balances[0]+current_need] + balances[1:])
        if new_predicted_en == previous_predicted_en:
            return balances, need
        else:
            balances[0] += current_need
            return balances, need - current_need

    def perform_calculation(self) -> (List[float], float):
        predicted_bank_lvl, idx_negative_collector = self._predict_bank_lvl(self.start_energy, self.hourly_balance)
        if predicted_bank_lvl >= self.max_energy:
            return [round(x, 2) for x in self.hourly_balance], 0
        need = round(self.max_energy - predicted_bank_lvl, 2)
        if self.start_energy + sum((i for i in self.hourly_balance if i >= 0)) > self.max_energy:
            idx_order = self._sort_idx_ascending()
            for idx in idx_order:
                if idx in idx_negative_collector:
                    if need <= 0.0:
                        break
                    enz, _ = self._predict_bank_lvl(self.start_energy, self.hourly_balance[:idx])
                    self.hourly_balance[idx:], need = self._optimize_balance(enz, need, self.hourly_balance[idx:])
        else:
            return [round(x, 2) for x in self.hourly_balance], need
        return [round(x, 2) for x in self.hourly_balance], need


if __name__ == "__main__":
    en = round(random.uniform(1.0, 2.5))
    test_hourly_balances = [round(random.uniform(-1.0, 1.5), 2) for _ in range(5)]

    test_prices = [round(random.uniform(100.0, 300.0), 2) for _ in range(5)]
    test_bank = EnergyBank(lvl=en)
    test_algo = DayEnergy(test_prices, test_hourly_balances, test_bank)
    print(f"Start bank lvl: {test_bank.get_lvl()}")
    print(f"test_hourly_balances: {test_hourly_balances}")
    print(f"test_prices: {test_prices}")
    finished_hourly_balances, finished_need = test_algo.perform_calculation()
    print(f"finished_hourly_balances: {finished_hourly_balances}\nfinished_need: {finished_need}")
