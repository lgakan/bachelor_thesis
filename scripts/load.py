from lib.config import Config
from lib.file_manager import CSVFile


class Load:
    """
    A class representing household power consumption.

    Attributes:
        consumption (float): Household power consumption expressed in kWh.
        csv_file (CSVFile): The CSVFile class object for csv files management.
    """
    def __init__(self, consumption: float = 0.0):
        self.consumption = consumption
        self.csv_file = CSVFile(Config.DATA_ENERGY_USAGE)

    def get_consumption_by_date(self, date: str) -> float:
        return self.csv_file.get_colum_value_by_date("Load (kW)", date)

# if __name__ == "__main__":
#     load = Load()
#     print(load.get_consumption_by_date("01.01.2015 06:00:00"))
