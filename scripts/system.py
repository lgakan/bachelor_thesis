import pandas as pd

from lib.plotter import Plotter
from scripts.energy_bank import EnergyBank
from scripts.energy_manager import EnergyManager
from scripts.energy_pricing import EnergyWebScraper
from scripts.pv import Pv


class RawSystem:
    def __init__(self):
        self.summed_price = 0
        self.energy_pricer = EnergyWebScraper(date_column="Date")
        self.plotter = Plotter(["price [zl]", "consumption [kWh]", "Total price"])

    def feed_consumption(self, date: pd.Timestamp, consumption: float):
        price = consumption * self.energy_pricer.get_rce_by_date(date)
        self.summed_price += price


class PvSystem:
    def __init__(self):
        self.producer = Pv(date_column="Date")
        self.summed_price = 0
        self.energy_pricer = EnergyWebScraper(date_column="Date")
        self.plotter = Plotter(["price [zl]", "consumption [kWh]", "production [kWh]", "Total price"])

    def feed_consumption(self, date: pd.Timestamp, consumption: float):
        pv_prod = self.producer.get_production_by_date(date)
        reduced_consumption = consumption - pv_prod
        if reduced_consumption > 0:
            price = reduced_consumption * self.energy_pricer.get_rce_by_date(date)
        else:
            price = 0
        self.summed_price += price


class SemiSmartSystem:
    def __init__(self):
        self.producer = Pv(date_column="Date")
        self.energy_bank = EnergyBank()
        self.summed_price = 0
        self.energy_pricer = EnergyWebScraper(date_column="Date")
        self.plotter = Plotter(["price [zl]", "consumption [kWh]", "production [kWh]", "energy_bank [kWh]", "Total price"])

    def feed_consumption(self, date: pd.Timestamp, consumption: float):
        pv_prod = self.producer.get_production_by_date(date)
        reduced_consumption_by_pv = consumption - pv_prod
        if reduced_consumption_by_pv > 0:
            reduced_consumption_by_bank = reduced_consumption_by_pv - self.energy_bank.get_lvl()
            if reduced_consumption_by_bank > 0:
                self.energy_bank.release_energy(self.energy_bank.get_lvl())
                price = reduced_consumption_by_bank * self.energy_pricer.get_rce_by_date(date)
            else:
                self.energy_bank.release_energy(reduced_consumption_by_pv)
                price = 0
        else:
            self.energy_bank.store_energy(reduced_consumption_by_pv)
            price = 0
        self.summed_price += price


class SmartSystem:
    def __init__(self):
        self.producer = Pv(date_column="Date")
        self.energy_bank = EnergyBank()
        self.energy_manager = EnergyManager(date_column="Date")
        self.summed_price = 0
        self.energy_pricer = EnergyWebScraper(date_column="Date")
        self.plotter = Plotter(["price [zl]", "consumption [kWh]", "production [kWh]", "energy_bank [kWh]", "Total price"])

    def feed_consumption(self, date: pd.Timestamp, consumption: float):
        pv_prod = self.producer.get_production_by_date(date)
