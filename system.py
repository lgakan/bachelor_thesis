from lib.plotter import Plotter
from scripts.energy_manager import EnergyManager


class System:
    def __init__(self):
        self.energy_manager = EnergyManager()


def main():
    system = System()
    plotter = Plotter(["price", "consumption", "production", "energy_bank"])
    # system.energy_manager.log_energy_status_by_date("01.01.2015 06:00:00")
    for i in range(9):
        current_date = f"01.01.2015 0{i}:00:00"
        current_demand = system.energy_manager.get_demand_by_date(current_date)
        if current_demand >= 0:
            system.energy_manager.energy_bank.release_energy(current_demand)
        else:
            system.energy_manager.energy_bank.store_energy(current_demand)
        logged_values = system.energy_manager.log_energy_status_by_date(current_date)
        plotter.add_data_row([f"{i}"] + logged_values)

    plotter.plot_charts()


if __name__ == "__main__":
    main()
