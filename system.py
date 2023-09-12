from scripts.energy_management import EnergyManagement


class System:
    def __init__(self):
        self.energy_manager = EnergyManagement()


def main():
    system = System()
    system.energy_manager.get_energy_status_by_date("01.01.2015 06:00:00")


if __name__ == "__main__":
    main()
