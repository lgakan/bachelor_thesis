from scripts.energy_bank import EnergyBank
from lib.logger import logger
from scripts.load import Load
from scripts.pv import Pv
from scripts.energy_pricing import EnergyPricing


class EnergyManager:
    def __init__(self):
        self.consumer = Load()
        self.producer = Pv()
        self.energy_bank = EnergyBank()
        self.energy_pricer = EnergyPricing()

    def log_energy_status_by_date(self, date: str):
        logger.info(f"Current date: {date}")
        logger.info(f"Current energy price: {self.energy_pricer.get_rce_by_date(date)} zl")
        logger.info(f"Current consumption: {self.consumer.get_consumption_by_date(date)} kWh")
        logger.info(f"Current production: {self.producer.get_production_by_date(date):.2} kWh")
        logger.info(f"Current energy bank lvl: {self.energy_bank.get_lvl():.2} kWh \n")
        return self.energy_pricer.get_rce_by_date(date), \
               self.consumer.get_consumption_by_date(date), \
               self.producer.get_production_by_date(date), \
               self.energy_bank.get_lvl()

    def get_demand_by_date(self, date: str) -> float:
        """
        date (str): Date for which the demand will be calculated
        :return (float): Demand for the date (production-consumption).
        """
        return self.consumer.get_consumption_by_date(date) - self.producer.get_production_by_date(date)
