import os
import time
from typing import List

import numpy as np
import pandas as pd
import pytest

from scripts.energy_pricing import EnergyWebScraper


def create_random_date() -> pd.Timestamp:
    date_start = pd.Timestamp("01.01.2020 00:00:00")
    date_end = pd.Timestamp("31.12.2020 23:00:00")
    start_u = date_start.value // 10 ** 9
    end_u = date_end.value // 10 ** 9
    return pd.to_datetime(np.random.randint(start_u, end_u, 1), unit='s')[0]


class TestEnergyWebScaper:
    TEST_PATH = "test_energy_pricing.csv"

    @pytest.fixture(scope="function")
    def web_scraper(self) -> EnergyWebScraper:
        time.sleep(3)
        yield EnergyWebScraper(prices_path=self.TEST_PATH, date_column="Date")
        if os.path.exists(self.TEST_PATH):
            os.remove(self.TEST_PATH)

    def test_download_single_day_prices(self, web_scraper: EnergyWebScraper) -> None:
        date_start = create_random_date()
        df = web_scraper.download_prices_by_date(date_start)
        assert df.columns.tolist() == ["Data", "Godzina", "RCE"]
        assert df.size == 24 * 3

        first_date = pd.to_datetime(df["Data"].astype(str)[0], format="%Y%m%d")
        last_date = pd.to_datetime(df["Data"].astype(str).iloc[-1], format="%Y%m%d")
        assert first_date.floor('D') == date_start.floor('D')
        assert last_date.floor('D') == date_start.floor('D')

    def test_download_multi_day_prices(self, web_scraper: EnergyWebScraper) -> None:
        day_amount = np.random.randint(1, 4)
        date_start = create_random_date()
        date_end = date_start + pd.Timedelta(days=day_amount)
        df = web_scraper.download_prices_by_date(date_start, date_end)
        assert df.size == 24 * 3 * (day_amount + 1)

        first_date = pd.to_datetime(df["Data"].astype(str)[0], format="%Y%m%d")
        last_date = pd.to_datetime(df["Data"].astype(str).iloc[-1], format="%Y%m%d")
        assert first_date.floor('D') == date_start.floor('D')
        assert last_date.floor('D') == date_end.floor('D')

    def test_get_prices_file_single_date(self, web_scraper: EnergyWebScraper) -> None:
        date_start = create_random_date()
        web_scraper.get_prices_file_by_date(date_start)
        assert os.path.exists(self.TEST_PATH)

    def test_get_prices_file_multi_date(self, web_scraper: EnergyWebScraper) -> None:
        day_amount = np.random.randint(1, 4)
        date_start = create_random_date()
        date_end = date_start + pd.Timedelta(days=day_amount)
        web_scraper.get_prices_file_by_date(date_start, date_end)
        assert os.path.exists(self.TEST_PATH)

    @pytest.mark.parametrize("str_date_in, expected_rce", [("10.01.2023 03:00:00", 0.61),
                                                           ("03.04.2023 09:00:00", 0.58),
                                                           ("31.10.2023 00:00:00", 0.38)])
    def test_get_single_rce_by_date(self, str_date_in: str, expected_rce: float, web_scraper: EnergyWebScraper) -> None:
        date_in = pd.to_datetime(str_date_in, format="%d.%m.%Y %H:%M:%S")
        rce_val = web_scraper.get_rce_by_date(date_in)
        assert rce_val == expected_rce

    @pytest.mark.parametrize("date_start, date_end, expected_list_rce", [
        ("10.01.2023 01:00:00", "10.01.2023 05:00:00", [0.60, 0.60, 0.61, 0.62, 0.70]),
        ("03.04.2023 21:00:00", "03.04.2023 02:00:00", []),
        ("31.10.2023 23:00:00", "01.11.2023 01:00:00", [0.41, 0.25, 0.23])])
    def test_get_multi_rce_by_dates(self, date_start: str, date_end: str, expected_list_rce: List[float], web_scraper: EnergyWebScraper) -> None:
        date_s, date_e = pd.to_datetime(date_start, format="%d.%m.%Y %H:%M:%S"), pd.to_datetime(date_end, format="%d.%m.%Y %H:%M:%S")
        list_rce = web_scraper.get_rce_by_date(date_s, date_e)
        assert list_rce == expected_list_rce

    @pytest.mark.parametrize("date_in, answer", [("10.01.2023 01:00:00", True),
                                                 ((pd.Timestamp.now() + pd.Timedelta(days=2)).strftime("%d.%m.%Y %H:%M:%S"), False)])
    def test_check_next_day_availability(self, date_in: str, answer: bool, web_scraper: EnergyWebScraper) -> None:
        date_in = pd.to_datetime(date_in, format="%d.%m.%Y %H:%M:%S")
        assert web_scraper.check_next_day_availability(date_in) == answer
