import time

import pandas
from selenium import webdriver
from selenium.webdriver.common.by import By
import csv
from lib.config import Config
import shutil
from lib.file_manager import CSVFile
from lib.config import DataTypes


class EnergyPricing:
    # TODO: NEEDS TO BE IMPLEMENTED
    # def __init__(self):
    #     self.prices = []
    #
    # @staticmethod
    # def update_prices_file():
    #     driver = webdriver.Chrome()
    #     driver.get(Config.LINK_ENERGY_PRICES)
    #     time.sleep(3)
    #     download_button = driver.find_element(By.XPATH, f"//a[@href='{Config.LINK_CSV_DOWNLOAD}']")
    #     download_button.click()
    #     time.sleep(5)
    #     shutil.move(Config.PATH_DOWNLOAD_DIR, Config.DATA_PRICES)

    def __init__(self):
        self.csv_file = CSVFile(Config.DATA_PRICES)

    def get_rce_by_date(self, date: DataTypes.TIMESTAMP):
        return self.csv_file.get_colum_value_by_date("RCE", date)

