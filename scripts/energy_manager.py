from typing import List

from lib.config import DataTypes
from lib.logger import logger
from scripts.energy_bank import EnergyBank
from scripts.energy_pricing import EnergyWebScraper
from scripts.load import Load
from scripts.pv import Pv


class EnergyManager:
    def __init__(self, date_column: None | str = None):
        self.consumer = Load(date_column=date_column)
        self.producer = Pv(date_column=date_column)
        self.energy_bank = EnergyBank()
        self.energy_pricer = EnergyWebScraper(date_column=date_column)

    def log_energy_status_by_date(self, date_in: DataTypes.TIMESTAMP) -> List:
        logger.info(f"Current date: {date_in}")
        logger.info(f"Current energy price: {self.energy_pricer.get_rce_by_date(date_in)} zl")
        logger.info(f"Current consumption: {self.consumer.get_consumption_by_date(date_in)} kWh")
        logger.info(f"Current production: {self.producer.get_production_by_date(date_in):.2} kWh")
        logger.info(f"Current energy bank lvl: {self.energy_bank.get_lvl():.2} kWh \n")
        return [self.energy_pricer.get_rce_by_date(date_in),
                self.consumer.get_consumption_by_date(date_in),
                self.producer.get_production_by_date(date_in),
                self.energy_bank.get_lvl()]

    def get_demand_by_date(self, date_in: DataTypes.TIMESTAMP) -> float:
        return self.consumer.get_consumption_by_date(date_in) - self.producer.get_production_by_date(date_in)
