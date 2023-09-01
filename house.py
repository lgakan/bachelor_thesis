from lib.config import Config


class House:
    """
    A class representing household power consumption.

    Attributes:
        consumption (float): Household power consumption expressed in kWh.
    """
    def __init__(self, consumption: float = 0.0):
        self.consumption = consumption

    def get_current_consumption(self):
        with open(Config.DATA_ENERGY_USAGE, 'r') as f:
            self.consumption = f.readline()
            return self.consumption
