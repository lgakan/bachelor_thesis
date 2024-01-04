from typing import Union, List

import pytest

from scripts.energy_bank import EnergyBank
from scripts.prediction_strategy import DayPredictionStrategy, NightPredictionStrategy, simulate_eb_operation
from tests.conftest import EbProps


@pytest.mark.parametrize("balance, start_lvl, expected_lvl", [(0.0, None, EbProps.LVL),
                                                              (-1.0, EbProps.CAPACITY, EbProps.CAPACITY - 1.0),
                                                              (1.0, EbProps.MIN_LVL, EbProps.MIN_LVL + 1.0),
                                                              ([2*EbProps.CAPACITY, -4*EbProps.CAPACITY, EbProps.LVL, 1], None, EbProps.MIN_LVL + EbProps.LVL + 1)])
def test_simulate_eb_operations(balance: Union[float, List[float]], start_lvl: Union[float, None], expected_lvl: float, energy_bank: EnergyBank) -> None:
    assert simulate_eb_operation(energy_bank, balance, start_lvl) == expected_lvl


class TestDayAlgorithm:
    def test_basic_optimize_mixed_balances(self, energy_bank: EnergyBank, day_strategy: DayPredictionStrategy) -> None:
        balances = [-0.08, -0.89, 0.45, 0.15, 0.18, 1.05]
        need = 0.5
        output_balances, _ = day_strategy.optimize_mixed_balances(energy_bank, need, balances)
        assert output_balances == [0.0, 0.0, 0.45, 0.15, 0.18, 1.05]

    def test_basic_optimize_positive_balances(self, energy_bank: EnergyBank, day_strategy: DayPredictionStrategy) -> None:
        prices = [127.69, -129.71, 40.53, 50.14, -150.79, 14.88]
        balances = [0.08, 0.89, 0.45, 0.15, 0.18, 1.05]
        output_balances = day_strategy.optimize_positive_balances(energy_bank, energy_bank.lvl, balances, prices)
        assert output_balances == [0.08, 0.89, 0.45, 0.15, 0.18, 1.05]

    def test_basic_mixed_prices_handler(self, energy_bank: EnergyBank, day_strategy: DayPredictionStrategy) -> None:
        prices = [127.69, -129.71, 40.53, 50.14, -150.79, 14.88]
        balances = [-0.08, -0.89, 0.45, 0.15, 0.18, 1.05]
        output_balances = day_strategy.mixed_prices_handler(energy_bank, energy_bank.lvl, prices, balances)
        assert output_balances == [0.0, 3.0, 0.45, -0.18, 0.0, 1.05]

    def test_basic_negative_prices_handler(self, energy_bank: EnergyBank, day_strategy: DayPredictionStrategy) -> None:
        prices = [-127.69, -129.71, -40.53, -150.79, -14.88]
        balances = [-1.2, -0.4, 3.45, 1.68, -0.05]
        output_balances = day_strategy.mixed_prices_handler(energy_bank, energy_bank.lvl, prices, balances)
        assert output_balances == [0.0, 0.0, 3.45, 1.68, 0.0]

    def test_basic_positive_prices_handler(self, energy_bank: EnergyBank, day_strategy: DayPredictionStrategy) -> None:
        prices = [127.69, 129.71, 40.53, 150.79, 14.88]
        balances = [-1.2, -0.4, 3.45, 1.68, -0.05]
        output_balances = day_strategy.positive_prices_handler(energy_bank, energy_bank.lvl, prices, balances)
        assert output_balances == [-1.2, -0.4, 3.45, 1.68, 0.0]

    @pytest.mark.parametrize("start_en ,prices, balances, expected_balances", [(EbProps.MIN_LVL, [48.77, 174.3, 122.19, 22.72, -36.07], [-0.4, -0.49, -0.9, -0.73, -0.12], [0.0, 0.0, 0.0, 0.0, 4.5]),
                                                                               (EbProps.LVL, [66.54, 26.91, 128.15, 187.33, 152.03], [0.0, -0.31, -0.81, -0.61, 0.21], [0.0, 0.0, 0.0, 0.0, 0.21]),
                                                                               (EbProps.CAPACITY, [-9.63, 135.89, 146.28, -14.27, 109.78], [-0.07, -0.49, -0.46, -0.51, -0.71], [0.0, 0.0, 0.0, 0.0, 0.0])])
    def test_get_plan(self, start_en: float, prices: List[float], balances: List[float], expected_balances: List[float],
                      energy_bank: EnergyBank, day_strategy: DayPredictionStrategy) -> None:
        output_balances = day_strategy.get_plan(start_en, prices, balances)
        assert output_balances == expected_balances


class TestNightAlgorithm:
    def test_basic_calculate_hourly_balances(self, energy_bank: EnergyBank, night_strategy: NightPredictionStrategy) -> None:
        balances = [1.0, 0.4, -2.9, -0.5]
        idx_order = [0, 3, 2, 1]
        output_balances = night_strategy.calculate_hourly_balances(energy_bank, idx_order, balances, energy_bank.lvl)
        assert output_balances == [1.0, 0.4, -2.9, 0.0]

    @pytest.mark.parametrize("idx_order, balances", [([0, 1, 1], [6.7, -20.1, -30.5]),
                                                     ([0, 2], [6.7, -20.1]),
                                                     ([0, 2, 1], [6.7, -20.1])])
    def test_invalid_calculate_hourly_balances(self, idx_order: List[int], balances: List[float],
                                               energy_bank: EnergyBank, night_strategy: NightPredictionStrategy) -> None:
        with pytest.raises(Exception):
            night_strategy.calculate_hourly_balances(energy_bank, idx_order, balances, energy_bank.lvl)

    def test_basic_mixed_prices_handler(self, energy_bank: EnergyBank, night_strategy: NightPredictionStrategy) -> None:
        prices = [127.69, -129.71, 40.53, 50.14, -150.79, 14.88]
        balances = [-0.08, -0.89, 0.45, 0.15, 0.18, 1.05]
        output_balances = night_strategy.mixed_prices_handler(energy_bank, prices, balances)
        assert output_balances == [-0.08, 0.0, 0.45, 0.15, 0.0, 1.05]

    def test_basic_positive_prices_handler(self, energy_bank: EnergyBank, night_strategy: NightPredictionStrategy) -> None:
        prices = [127.69, 129.71, 40.53, 150.79, 14.88]
        balances = [-1.08, -0.89, 0.45, -1.68, 1.05]
        output_balances = night_strategy.positive_prices_handler(energy_bank, prices, balances)
        assert output_balances == [0.0, -0.27, 0.45, -1.68, 1.05]

    @pytest.mark.parametrize("start_en ,prices, balances, expected_balances", [(EbProps.MIN_LVL, [48.77, 174.3, 122.19, 22.72, -36.07], [-0.4, -0.49, -0.9, -0.73, -0.12], [-0.4, -0.49, -0.9, -0.73, 0]),
                                                                               (EbProps.LVL, [66.54, 26.91, 128.15, 187.33, 152.03], [0.0, -0.31, -0.81, -0.61, 0.21], [0.0, -0.08, -0.81, -0.61, 0.21]),
                                                                               (EbProps.CAPACITY, [-9.63, 135.89, 146.28, -14.27, 109.78], [-0.07, -0.49, -0.46, -0.51, -0.71], [0.0, -0.49, -0.46, 0.0, -0.71])])
    def test_get_plan(self, start_en: float, prices: List[float], balances: List[float], expected_balances: List[float],
                      energy_bank: EnergyBank, night_strategy: NightPredictionStrategy) -> None:
        output_balances = night_strategy.get_plan(start_en, prices, balances)
        assert output_balances == expected_balances
