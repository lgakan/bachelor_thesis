from scripts.energy_bank import EnergyBank
from lib.logger import logger
from scripts.load import Load
from scripts.pv import Pv


class EnergyManagement:
    def __init__(self):
        self.consumer = Load()
        self.producer = Pv()
        self.energy_bank = EnergyBank()

    def get_energy_status_by_date(self, date: str):
        logger.info(f"Current date: {date}")
        logger.info(f"Current consumption: {self.consumer.get_current_consumption(date)}")
        logger.info(f"Current production: {self.producer.get_current_production(date)}")
        logger.info(f"Current bank lvl: {self.energy_bank.get_lvl()} \n")
