from enum import Enum
from typing import Union


class CustomEnum(Enum):
    def __get__(self, instance, owner):
        return self.value


class Config(CustomEnum):
    # The data to fill in
    LATITUDE = 50.07
    LONGITUDE = 19.92

    # local paths
    LOG_FILE_PATH = "lib/program_log.log"
    DATA_PRICES = "lib/data/prices.csv"
    DATA_ENERGY_PRODUCTION = "lib/data/energy_production.csv"
    DATA_ENERGY_CONSUMPTION = "lib/data/energy_consumption2.csv"

    # http_links
    PV_API_LINK = "https://www.renewables.ninja/api/"
    CSV_DOWNLOAD_LINK = f"https://www.pse.pl/getcsv/-/export/csv/PL_CENY_RYN_EN/"


class PhotovoltaicDirection(CustomEnum):
    SOUTH = "south"
    EAST = "east"


class DataTypes(CustomEnum):
    DF_VALUES = Union[str, int, float]