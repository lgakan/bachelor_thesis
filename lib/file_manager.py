import pandas as pd


class CSVFile:
    def __init__(self, path: str, sep: str = ',', decimal: str = '.'):
        self.path = path
        self.sep = sep
        self.decimal = decimal

    def get_file_content(self) -> pd:
        df = pd.read_csv(self.path, sep=self.sep, decimal=self.decimal)
        return df.fillna('')

    def rename_columns_name(self, column_names: dict[str, str]):
        df = self.get_file_content()
        df.rename(columns=column_names, inplace=True)

    def update_column(self, column_name: str, data: list):
        df = self.get_file_content()
        df[column_name] = data
        df.to_csv(self.path, index=False)

        # df[column_name] = df[column_name].apply(len)

    def get_colum_value_by_date(self, column_name: str, date: str) -> str | int | float:
        df = self.get_file_content()
        return df.loc[df["Date"] == date, column_name].values[0]


if __name__ == "__main__":
    csv_file = CSVFile("data/energy_production.csv")
    print(csv_file.get_file_content().head())
    # x = csv_file.get_colum_value_by_date("Load (kW)", "01.01.2015 03:00:00")
