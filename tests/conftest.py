import pytest

from lib.config import CustomEnum
from scripts.energy_bank import EnergyBank
from scripts.prediction_strategy import NightPredictionStrategy, DayPredictionStrategy


class EbProps(CustomEnum):
    CAPACITY = 5.0
    LVL = 2.0
    MIN_LVL = 0.5
    COST = 1000.0
    CYCLES = 1000


@pytest.fixture()
def energy_bank() -> EnergyBank:
    return EnergyBank(capacity=EbProps.CAPACITY,
                      min_lvl=EbProps.MIN_LVL,
                      lvl=EbProps.LVL,
                      purchase_cost=EbProps.COST,
                      cycles_num=EbProps.CYCLES)


@pytest.fixture()
def night_strategy() -> NightPredictionStrategy:
    return NightPredictionStrategy(min_energy=EbProps.MIN_LVL, max_energy=EbProps.CAPACITY)


@pytest.fixture()
def day_strategy() -> DayPredictionStrategy:
    return DayPredictionStrategy(min_energy=EbProps.MIN_LVL, max_energy=EbProps.CAPACITY)
