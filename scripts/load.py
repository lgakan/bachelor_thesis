from lib.config import Config
from lib.config import DataTypes
from lib.file_management import DfManager


class Load:
    """
    A class representing household power consumption.

    Attributes:
        consumption (float): Household power consumption expressed in kWh.
        df_manager (DfManager): The CSVFile class object for csv files management.
    """

    def __init__(self, date_column: None | str = None, consumption: float = 0.0, ):
        self.consumption = consumption
        self.df_manager = DfManager(Config.DATA_ENERGY_USAGE, date_column)
        self.date_column = date_column

    def get_consumption_by_date(self, date_in: DataTypes.TIMESTAMP) -> float:
        return self.df_manager.get_cell_by_date(self.date_column, date_in, "Load (kW)")


# Example
# if __name__ == "__main__":
#     load = Load(column_name="Date")
#     print(load.get_consumption_by_date(pd.to_datetime("01.01.2015 06:00:00")))
