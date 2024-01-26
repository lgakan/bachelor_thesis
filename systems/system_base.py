from abc import abstractmethod
from typing import Union

import pandas as pd

from lib.logger import logger
from scripts.energy_pricing import EnergyWebScraper
from scripts.load import Load
from scripts.plotter import Plotter


class SystemBase:
    def __init__(self, load_multiplier: Union[None, int] = None):
        self.summed_cost = 0
        self.energy_pricer = EnergyWebScraper(date_column="Date")
        self.plotter = Plotter(["price [zl/kWh]", "consumption [kWh]", "production [kWh]", "energy_bank [kWh]", "Total price [zl]"])
        self.consumer = Load(date_column="Date", multiplier=load_multiplier)

    @abstractmethod
    def feed_consumption(self, date_in: pd.Timestamp) -> None:
        pass

    def plot_charts(self):
        return self.plotter.plot_charts(f"System Data - {self.__class__.__name__}")

    def log_data(self, cost: float, balance: Union[None, float] = None, bank_lvl: Union[None, float] = None) -> None:
        logger.info(f"{self.__class__.__name__} current cost: {cost:.3}")
        if balance is not None:
            logger.info(f"{self.__class__.__name__} current balance: {balance:.3}")
        if bank_lvl is not None:
            logger.info(f"{self.__class__.__name__} current energy_bank_lvl: {bank_lvl:.3}")
