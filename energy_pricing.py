import requests
from bs4 import BeautifulSoup

from lib.logger import logger


class EnergyPricing:
    def __init__(self, url):
        self.url = url

    def get_page_content(self):
        response = requests.get(self.url)
        if response.status_code == 200:
            return response.content
        else:
            logger.critical("Failed to fetch the page content.")
            return None

    def scrape_data(self):
        content = self.get_page_content()
        if content:
            soup = BeautifulSoup(content, 'html.parser')
            products = soup.find_all('div', class_='product')
            for product in products:
                name = product.find('h2', class_='product-name').text
                price = product.find('span', class_='product-price').text
                print(f"Product: {name}, Price: {price}")


if __name__ == "__main__":
    url_to_scrape = "https://www.pse.pl/dane-systemowe/funkcjonowanie-rb/raporty-dobowe-z-funkcjonowania-rb/podstawowe-wskazniki-cenowe-i-kosztowe/rynkowa-cena-energii-elektrycznej-rce"
    scraper = EnergyPricing(url_to_scrape)
    scraper.scrape_data()
