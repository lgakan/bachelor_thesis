from typing import Dict, Union, List

import pandas
import pandas as pd

from lib.config import DataTypes


class CSVFile:
    """
    A class created to handle CSV file management.
    """
    def __init__(self, path: str, sep: str = ',', decimal: str = '.'):
        self.path = path
        self.sep = sep
        self.decimal = decimal

    def get_file_content(self) -> pd.DataFrame:
        df = pd.read_csv(self.path, sep=self.sep, decimal=self.decimal, parse_dates=["Date"])
        df["Date"] = pd.to_datetime(df["Date"], format="%d.%m.%Y %H:%M:%S")
        return df.fillna('')

    def rename_columns_name(self, column_names: Dict[str, str]) -> None:
        df = self.get_file_content()
        df.rename(columns=column_names, inplace=True)

    def update_column(self, column_name: str, data: List[DataTypes.DF_VALUES]) -> None:
        df = self.get_file_content()
        df[column_name] = data
        df.to_csv(self.path, index=False)

    def get_colum_value_by_date(self, column_name: str, date: pandas.Timestamp) -> Union[DataTypes.DF_VALUES]:
        df = self.get_file_content()
        return df.loc[df["Date"] == date, column_name].values[0]


if __name__ == "__main__":
    csv_file = CSVFile("data/energy_production.csv")
    print(csv_file.get_file_content().head())
