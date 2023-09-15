from datetime import timedelta
from typing import List

import matplotlib.pyplot as plt
import pandas as pd

from lib.config import DataTypes


class Plotter:
    """
    A class created for plotting data from pandas dataframe.

    Attributes:
        df (pandas.DataFrame): A dataframe that stores data for plotting.
    """

    def __init__(self, columns_names: List[str]):
        self.df = pd.DataFrame({k: [] for k in ["Date"] + columns_names})

    def add_data_row(self, data_row: List[DataTypes.DF_VALUES]) -> None:
        self.df.loc[len(self.df)] = data_row

    def plot_charts(self, title: str = "System Data") -> None:
        axes = self.df.plot(kind='line', x='Date', subplots=True, figsize=(10, 10), sharex=True, title=title)
        for idx, column_name in enumerate(self.df.columns[1:]):
            axes[idx].set_ylabel(column_name)
        plt.show()


if __name__ == "__main__":
    plotter = Plotter(["y1", 'y2', 'y3'])
    start_date = pd.to_datetime("01.01.2015 00:00:00")
    for i in range(10):
        plotter.add_data_row([start_date, i * 1.0, i * 2.0, i * 3.0])
        start_date += timedelta(hours=1)
    plotter.plot_charts()
