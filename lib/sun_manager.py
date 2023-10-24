import pandas as pd
from suntime import Sun


class SunManager:
    def __init__(self, latitude: float = 50.07, longitude: float = 19.92):
        self.latitude = latitude
        self.longitude = longitude

    def get_sun_data(self, date_in: pd.Timestamp) -> (int, int):
        sun = Sun(self.latitude, self.longitude)
        sunrise = sun.get_local_sunrise_time(date_in.date())
        sunset = sun.get_local_sunset_time(date_in.date())
        return int(sunrise.strftime('%H')), int(sunset.strftime('%H'))


if __name__ == "__main__":
    sun_manager = SunManager()
    time_s = pd.to_datetime("24.10.2023 05:00:00", format="%d.%m.%Y %H:%M:%S")
    print(sun_manager.get_sun_data(time_s))
