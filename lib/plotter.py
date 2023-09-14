import matplotlib.pyplot as plt
import pandas as pd


class Plotter:
    def __init__(self, columns_names: list[str]):
        self.df = pd.DataFrame({k: [] for k in ["Date"] + columns_names})

    def add_data_row(self, data_row: list):
        self.df.loc[len(self.df)] = data_row

    def plot_charts(self, title: str = "System Data"):
        axes = self.df.plot(kind='line', x='Date', subplots=True, figsize=(10, 10), sharex=True, title=title)
        for idx, column_name in enumerate(self.df.columns[1:]):
            axes[idx].set_ylabel(column_name)
        plt.show()


if __name__ == "__main__":
    plotter = Plotter(["y1", 'y2', 'y3'])
    for i in range(10):
        plotter.add_data_row([f'data{i}', i*1.0, i*2.0, i*3.0])
    plotter.plot_charts()
