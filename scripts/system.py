from datetime import timedelta
from typing import List, Union

import pandas as pd
from numpy import argsort

from lib.plotter import Plotter
from scripts.energy_bank import EnergyBank
from scripts.energy_manager import EnergyManager
from scripts.energy_pricing import EnergyWebScraper
from scripts.load import Load
from scripts.pv import Pv
from abc import abstractmethod


def is_ascending(arr: List[Union[int, float]]):
    n = len(arr)
    for i in range(1, n):
        if arr[i - 1] > arr[i]:
            return False
    return True


class System:
    def __init__(self):
        self.producer = Pv(date_column="Date")
        self.energy_bank = EnergyBank()
        self.energy_manager = EnergyManager(date_column="Date")
        self.summed_cost = 0
        self.energy_pricer = EnergyWebScraper(date_column="Date")
        self.plotter = Plotter(["price [zl]", "consumption [kWh]", "production [kWh]", "energy_bank [kWh]", "Total price"])
        self.consumer = Load(date_column="Date")
        self.x_list = None

    @abstractmethod
    def feed_consumption(self, date_in: pd.Timestamp) -> None:
        pass

    def plot_charts(self):
        self.plotter.plot_charts(f"System Data - {self.__class__.__name__}")


class RawSystem(System):
    def feed_consumption(self, date_in: pd.Timestamp) -> None:
        consumption = self.consumer.get_consumption_by_date(date_in)
        rce_price = self.energy_pricer.get_rce_by_date(date_in)
        cost = consumption * rce_price
        self.summed_cost += cost
        self.plotter.add_data_row([date_in, rce_price, consumption, 0, 0, self.summed_cost])


class PvSystem(System):
    def feed_consumption(self, date_in: pd.Timestamp):
        consumption = self.consumer.get_consumption_by_date(date_in)
        rce_price = self.energy_pricer.get_rce_by_date(date_in)
        pv_prod = self.producer.get_production_by_date(date_in)
        reduced_consumption = consumption - pv_prod
        if reduced_consumption > 0:
            cost = reduced_consumption * rce_price
        else:
            cost = 0
        self.summed_cost += cost
        self.plotter.add_data_row([date_in, rce_price, consumption, pv_prod, 0, self.summed_cost])


class SemiSmartSystem(System):
    def feed_consumption(self, date_in: pd.Timestamp) -> None:
        consumption = self.consumer.get_consumption_by_date(date_in)
        rce_price = self.energy_pricer.get_rce_by_date(date_in)
        pv_prod = self.producer.get_production_by_date(date_in)
        reduced_consumption_by_pv = consumption - pv_prod
        if reduced_consumption_by_pv > 0:
            reduced_consumption_by_bank = reduced_consumption_by_pv - self.energy_bank.get_lvl()
            if reduced_consumption_by_bank > 0:
                self.energy_bank.release_energy(self.energy_bank.get_lvl())
                cost = reduced_consumption_by_bank * rce_price
            else:
                self.energy_bank.release_energy(reduced_consumption_by_pv)
                cost = 0
        else:
            self.energy_bank.store_energy(reduced_consumption_by_pv)
            cost = 0
        self.summed_cost += cost
        self.plotter.add_data_row([date_in, rce_price, consumption, pv_prod, self.energy_bank.get_lvl(), self.summed_cost])


class SmartSystem(System):
    def feed_consumption(self, date_in: pd.Timestamp) -> None:
        con1 = True  # self.energy_pricer.check_next_day_availability(date_in)
        con2 = date_in.hour > 14
        last_3_prods = [self.producer.get_production_by_date(date_in - timedelta(hours=i)) for i in range(3)]
        con3 = is_ascending(last_3_prods) or sum(last_3_prods) / len(last_3_prods) <= 0.5
        con4 = self.x_list is None
        if con1 and con2 and con3 and con4:
            energy_bank_lvl = self.energy_bank.get_lvl()
            self.energy_pricer.get_prices_file_by_date(date_in, date_in + timedelta(days=1))
            start = date_in
            end = start.replace(day=date_in.day + 1, hour=7)
            rce_prices = self.energy_pricer.get_rce_by_date(start, end)
            consumptions = self.consumer.get_consumption_by_date(start, end)
            dates = pd.date_range(start=start, end=end, freq=timedelta(hours=1))
            sorted_prices_idx = argsort(rce_prices)[::-1].tolist()
            x_list = [{'Date': dates[i], 'Value': 0.0} for i in range(len(sorted_prices_idx))]
            for price_idx in sorted_prices_idx:
                c_consumption = consumptions[price_idx]
                energy = energy_bank_lvl - c_consumption
                if energy >= 0.0:
                    x_list[price_idx]["Value"] = c_consumption
                    energy_bank_lvl -= c_consumption
                else:
                    x_list[price_idx]["Value"] = energy_bank_lvl
                    break
            self.x_list = pd.DataFrame(x_list)
        if self.x_list is not None:
            consumption = self.consumer.get_consumption_by_date(date_in)
            rce_price = self.energy_pricer.get_rce_by_date(date_in)
            pv_prod = self.producer.get_production_by_date(date_in)
            predicted_energy_from_bank = self.x_list.loc[self.x_list["Date"] == date_in, "Value"].values[0]
            reduced_consumption_by_pv = consumption - pv_prod
            if reduced_consumption_by_pv > 0:
                reduced_consumption_by_bank = reduced_consumption_by_pv - predicted_energy_from_bank
                if reduced_consumption_by_bank > 0:
                    self.energy_bank.release_energy(predicted_energy_from_bank)
                    cost = reduced_consumption_by_bank * rce_price
                else:
                    self.energy_bank.release_energy(reduced_consumption_by_pv)
                    try:
                        self.x_list.loc[self.x_list["Date"] == date_in + timedelta(
                            hours=1), "Value"] += -reduced_consumption_by_bank
                    except:
                        pass
                    cost = 0
            else:
                self.energy_bank.store_energy(reduced_consumption_by_pv)
                cost = 0
            self.summed_cost += cost
            self.plotter.add_data_row([date_in, rce_price, consumption, pv_prod, self.energy_bank.get_lvl(), self.summed_cost])
            if date_in == self.x_list["Date"].iloc[-1]:
                self.x_list = None
        else:
            consumption = self.consumer.get_consumption_by_date(date_in)
            rce_price = self.energy_pricer.get_rce_by_date(date_in)
            pv_prod = self.producer.get_production_by_date(date_in)
            reduced_consumption_by_pv = consumption - pv_prod
            if reduced_consumption_by_pv > 0:
                reduced_consumption_by_bank = reduced_consumption_by_pv - self.energy_bank.get_lvl()
                if reduced_consumption_by_bank > 0:
                    self.energy_bank.release_energy(self.energy_bank.get_lvl())
                    cost = reduced_consumption_by_bank * rce_price
                else:
                    self.energy_bank.release_energy(reduced_consumption_by_pv)
                    cost = 0
            else:
                self.energy_bank.store_energy(reduced_consumption_by_pv)
                cost = 0
            self.summed_cost += cost
            self.plotter.add_data_row([date_in, rce_price, consumption, pv_prod, self.energy_bank.get_lvl(), self.summed_cost])
