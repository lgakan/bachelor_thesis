from datetime import timedelta

import pandas as pd

from scripts.load import Load
from scripts.system import RawSystem, PvSystem, SemiSmartSystem, SmartSystem


def main():
    date_start = "01.01.2015 00:00:00"
    date_stop = "01.01.2015 23:00:00"
    consumer = Load(date_column="Date")

    raw_system = RawSystem()
    pv_system = PvSystem()
    semi_smart_system = SemiSmartSystem()
    smart_system = SmartSystem()

    for current_date in pd.date_range(start=date_start, end=date_stop, freq=timedelta(hours=1)):
        current_consumption = consumer.get_consumption_by_date(current_date)

        raw_system.feed_consumption(current_date, current_consumption)
        raw_system.plotter.add_data_row([current_date,
                                         raw_system.energy_pricer.get_rce_by_date(current_date),
                                         current_consumption,
                                         raw_system.summed_price])

        pv_system.feed_consumption(current_date, current_consumption)
        pv_system.plotter.add_data_row([current_date,
                                        pv_system.energy_pricer.get_rce_by_date(current_date),
                                        current_consumption,
                                        pv_system.producer.get_production_by_date(current_date),
                                        pv_system.summed_price])

        semi_smart_system.feed_consumption(current_date, current_consumption)
        semi_smart_system.plotter.add_data_row([current_date,
                                                semi_smart_system.energy_pricer.get_rce_by_date(current_date),
                                                current_consumption,
                                                semi_smart_system.producer.get_production_by_date(current_date),
                                                semi_smart_system.energy_bank.get_lvl(),
                                                semi_smart_system.summed_price])

        smart_system.feed_consumption(current_date, current_consumption)
        smart_system.plotter.add_data_row([current_date,
                                           smart_system.energy_pricer.get_rce_by_date(current_date),
                                           current_consumption,
                                           smart_system.producer.get_production_by_date(current_date),
                                           smart_system.energy_bank.get_lvl(),
                                           smart_system.summed_price])

    raw_system.plotter.plot_charts("System Data - Raw")
    pv_system.plotter.plot_charts("System Data - Pv Smart")
    semi_smart_system.plotter.plot_charts("System Data - Semi-Smart")
    smart_system.plotter.plot_charts("System Data - Smart")


if __name__ == "__main__":
    main()
