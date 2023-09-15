from datetime import timedelta

import pandas as pd

from lib.plotter import Plotter
from scripts.energy_manager import EnergyManager


class System:
    def __init__(self):
        self.energy_manager = EnergyManager()


def main():
    system = System()
    plotter = Plotter(["price [zl]", "consumption [kWh]", "production [kWh]", "energy_bank [kWh]"])
    for current_date in pd.date_range(start='01.01.2015 00:00:00', end='01.01.2015 23:00:00', freq=timedelta(hours=1)):
        print(type(current_date))
        current_demand = system.energy_manager.get_demand_by_date(current_date)
        if current_demand >= 0:
            system.energy_manager.energy_bank.release_energy(current_demand)
        else:
            system.energy_manager.energy_bank.store_energy(current_demand)
        logged_values = system.energy_manager.log_energy_status_by_date(current_date)
        plotter.add_data_row([current_date] + logged_values)
    plotter.plot_charts()


if __name__ == "__main__":
    main()
