import pytest

from scripts.energy_bank import EnergyBank
from tests.conftest import EbProps


class TestEnergyBank:
    def test_min_border(self, energy_bank: EnergyBank) -> None:
        energy_bank.lvl = energy_bank.min_lvl
        energy_bank.manage_energy(-1.0)
        assert energy_bank.lvl == energy_bank.min_lvl

    def test_max_border(self, energy_bank: EnergyBank) -> None:
        energy_bank.lvl = energy_bank.capacity
        energy_bank.manage_energy(1.0)
        assert energy_bank.lvl == energy_bank.capacity

    @pytest.mark.parametrize("balance_in, expected_lvl", [(-1.0, EbProps.LVL-1.0),
                                                          (-EbProps.LVL, EbProps.MIN_LVL),
                                                          (-(EbProps.CAPACITY+1.0), EbProps.MIN_LVL)])
    def test_negative_balances(self, balance_in: float, expected_lvl: float, energy_bank: EnergyBank) -> None:
        energy_bank.manage_energy(balance_in)
        assert energy_bank.lvl == expected_lvl

    @pytest.mark.parametrize("balance_in, expected_lvl", [(1.0, EbProps.LVL+1.0),
                                                          ((EbProps.CAPACITY-EbProps.LVL), EbProps.CAPACITY),
                                                          (EbProps.CAPACITY+1.0, EbProps.CAPACITY)])
    def test_positive_balances(self, balance_in: float, expected_lvl: float, energy_bank: EnergyBank) -> None:
        energy_bank.manage_energy(balance_in)
        assert energy_bank.lvl == expected_lvl

    @pytest.mark.parametrize("cost_in, cycles_in, balance_input,expected_cost", [(1.0, 1, 5, 2.5),
                                                                                 (400.0, 5.0, 5, 200),
                                                                                 (20.0, 40, 10, 2.5)])
    def test_operation_cost_calculating(self, cost_in: float, cycles_in: int, balance_input: float, expected_cost: float):
        energy_bank = EnergyBank(purchase_cost=cost_in, cycles_num=cycles_in)
        assert energy_bank.operation_cost(balance_input) == expected_cost
        assert energy_bank.operation_cost(-balance_input) == expected_cost

    def test_idle_input(self, energy_bank: EnergyBank):
        previous_energy_lvl = energy_bank.lvl
        energy_bank.manage_energy(0)
        assert previous_energy_lvl == energy_bank.lvl

    @pytest.mark.parametrize("invalid_new_lvl", [-2 * EbProps.CAPACITY, 2 * EbProps.CAPACITY, 'LVL', '11'])
    def test_invalid_lvl(self, invalid_new_lvl, energy_bank: EnergyBank):
        with pytest.raises(Exception):
            energy_bank.lvl = invalid_new_lvl

    def test_same_operation_cost(self, energy_bank: EnergyBank):
        balance_in = 5.0
        operation_cost = energy_bank.operation_cost(balance_in)
        for _ in range(10):
            energy_bank.operation_cost(balance_in)
        assert operation_cost == energy_bank.operation_cost(balance_in)
