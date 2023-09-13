from scripts.energy_manager import EnergyManager
import matplotlib.pyplot as plt
import numpy as np
from lib.logger import logger


class System:
    def __init__(self):
        self.energy_manager = EnergyManager()


def main():
    system = System()
    # system.energy_manager.log_energy_status_by_date("01.01.2015 06:00:00")
    plot_list = []
    for i in range(3):
        current_date = f"01.01.2015 0{i}:00:00"
        current_demand = system.energy_manager.get_demand_by_date(current_date)
        if current_demand >= 0:
            system.energy_manager.energy_bank.release_energy(current_demand)
        else:
            system.energy_manager.energy_bank.store_energy(current_demand)
        logged_values = system.energy_manager.log_energy_status_by_date(current_date)
        plot_list.append(logged_values)

    print(plot_list)
    plt.plot(np.array([0, 1, 2]), np.array([i[3] for i in plot_list]))
    plt.show()


if __name__ == "__main__":
    main()
