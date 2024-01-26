import pytest

from lib.config import CustomEnum
from scripts.energy_bank import EnergyBank
from scripts.prediction_strategy import NightPredictionStrategy, DayPredictionStrategy
from scripts.pv import Pv


class EbProps(CustomEnum):
    CAPACITY = 5.0
    LVL = 2.0
    MIN_LVL = 0.5
    COST = 1000.0
    CYCLES = 1000


class PvProps(CustomEnum):
    SIZE = 5.0


@pytest.fixture()
def energy_bank(**kwargs):
    def _energy_bank(capacity=EbProps.CAPACITY,
                     min_lvl=EbProps.MIN_LVL,
                     lvl=EbProps.LVL,
                     purchase_cost=EbProps.COST,
                     cycles_num=EbProps.CYCLES,
                     **kwargs) -> EnergyBank:
        return EnergyBank(capacity=capacity,
                          min_lvl=min_lvl,
                          lvl=lvl,
                          purchase_cost=purchase_cost,
                          cycles_num=cycles_num)
    return _energy_bank


@pytest.fixture()
def pv_producer(**kwargs):
    def _pv_producer(size=PvProps.SIZE) -> Pv:
        return Pv(size=size)

    return _pv_producer


@pytest.fixture()
def night_strategy() -> NightPredictionStrategy:
    return NightPredictionStrategy(min_energy=EbProps.MIN_LVL, max_energy=EbProps.CAPACITY)


@pytest.fixture()
def day_strategy() -> DayPredictionStrategy:
    return DayPredictionStrategy(min_energy=EbProps.MIN_LVL, max_energy=EbProps.CAPACITY)
