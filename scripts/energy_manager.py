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
