import time
from selenium import webdriver
from selenium.webdriver.common.by import By
import csv
from lib.config import Config
import shutil
# from lib.logger import logger


class EnergyPricing:
    def __init__(self):
        self.prices = []

    @staticmethod
    def update_prices_file():
        driver = webdriver.Chrome()
        driver.get(Config.LINK_ENERGY_PRICES)
        time.sleep(3)
        download_button = driver.find_element(By.XPATH, f"//a[@href='{Config.LINK_CSV_DOWNLOAD}']")
        download_button.click()
        time.sleep(5)
        shutil.move(Config.PATH_DOWNLOAD_DIR, Config.DATA_PRICES)

    def get_current_rce(self, hour: int) -> float | None:
        # self.update_prices_file()
        with open(Config.DATA_PRICES, 'r') as f:
            csv_reader = csv.DictReader(f, delimiter=';')
            for line in csv_reader:
                if line["Godzina"] == str(hour):
                    return line["RCE"]
            return None
