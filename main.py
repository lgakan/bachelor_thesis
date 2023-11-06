from datetime import timedelta

import pandas as pd

from lib.logger import logger
from scripts.system import BareSystem, PvSystem, RawFullSystem, SmartSystem


def main():
    date_start = pd.to_datetime("05.05.2020 05:00:00", format="%d.%m.%Y %H:%M:%S")
    date_stop = pd.to_datetime("05.05.2020 10:00:00", format="%d.%m.%Y %H:%M:%S")
    bare_system = BareSystem()
    pv_system = PvSystem()
    raw_full_system = RawFullSystem()
    smart_system = SmartSystem()

    for current_date in pd.date_range(start=date_start, end=date_stop, freq=timedelta(hours=1)):
        logger.info(f"CURRENT DATE: {current_date}")
        bare_system.feed_consumption(current_date)
        pv_system.feed_consumption(current_date)
        raw_full_system.feed_consumption(current_date)
        smart_system.feed_consumption(current_date)

    bare_system.plot_charts()
    pv_system.plot_charts()
    raw_full_system.plot_charts()
    smart_system.plot_charts()

    logger.info(f"BareSystem cost: {bare_system.summed_cost}")
    logger.info(f"PvSystem cost: {pv_system.summed_cost}")
    logger.info(f"RawFullSystem cost: {raw_full_system.summed_cost}")
    logger.info(f"SmartSystem cost: {smart_system.summed_cost}")


if __name__ == "__main__":
    main()
