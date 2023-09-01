from energy_bank import EnergyBank
from energy_pricing import EnergyPricing
from house import House
from lib.logger import logger
from pv import Pv


class Algorithm:
    def __init__(self):
        self.house = House()
        self.pv = Pv()
        self.energy_bank = EnergyBank()
        # self.energy_pricing = EnergyPricing("https://www.pse.pl/dane-systemowe/funkcjonowanie-rb/raporty-dobowe-z"
        #                                     "-funkcjonowania-rb/podstawowe-wskazniki-cenowe-i-kosztowe/rynkowa-cena"
        #                                     "-energii-elektrycznej-rce")
        self.energy_pricing = EnergyPricing()


def main():
    hours = int(input("From 1 to 24, for how many hours do you want to run algorithm: "))

    algo = Algorithm()
    logger.info(f"Current consumption: {algo.house.get_current_consumption()}")
    logger.info(f"Current production: {algo.pv.get_current_production()}")
    logger.info(f"Current energy bank level: {algo.energy_bank.lvl}")
    logger.info(f"Current energy price for 4am: {algo.energy_pricing.get_current_rce(hours)}")


if __name__ == "__main__":
    main()
