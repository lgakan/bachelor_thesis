from typing import Dict, Union, List

import pandas
import pandas as pd

from lib.config import DataTypes


class CSVFile:
    """A class created to handle CSV file management."""

    def __init__(self, path: str, date_column: None | str = None):
        self.path = path
        self.date_column = date_column
        self.date_format = "%d.%m.%Y %H:%M:%S"

    def get_file_content(self) -> pd.DataFrame:
        df = pd.read_csv(self.path)
        if self.date_column is not None and self.date_column in df.columns:
            df[self.date_column] = pd.to_datetime(df[self.date_column], format=self.date_format)
        return df.fillna('')

    def save_file_content(self, content: pandas.DataFrame, sep: str = ','):
        content.to_csv(self.path, index=False, date_format=self.date_format, sep=sep)

    def update_columns_names(self, columns_names: Dict[str, str]) -> None:
        df = self.get_file_content()
        df.rename(columns=columns_names, inplace=True)
        self.save_file_content(df)

    def update_cell_by_date(self, column_name: str, date_in: pandas.Timestamp, new_value: DataTypes.DF_VALUES):
        df = self.get_file_content()
        if self.date_column is not None:
            df[self.date_column] = pd.to_datetime(df[self.date_column])
            df.loc[df[self.date_column] == date_in, column_name] = new_value
            self.save_file_content(df)
        else:
            raise Exception("Date column is not specified")

    def get_cell_by_date(self, column_name: str, date_in: DataTypes.TIMESTAMP) -> DataTypes.DF_VALUES:
        if self.date_column is not None:
            df = self.get_file_content()
            return df.loc[df["Date"] == date_in, column_name].values[0]
        else:
            raise Exception("Date column is not specified")

    def update_column_by_name(self, column_name: str, data: List[DataTypes.DF_VALUES]) -> None:
        df = self.get_file_content()
        if column_name in df.columns and len(data) == df.shape[0]:
            df.update({column_name: data})
            self.save_file_content(df)
        else:
            raise Exception(f"{column_name} not in {df.columns.to_list()} or {df.shape[0]} != {len(data)}")


if __name__ == "__main__":
    df_example = pd.DataFrame(
        {'D': [pd.to_datetime(f"01.0{i}.2015 06:00:00", format="%d.%m.%Y %H:%M:%S") for i in range(1, 4)],
         'A': [1, 2, 3],
         'B': [400, 500, 600]})
    csv_file = CSVFile("test_prices_delete.csv", "Date")
    csv_file.save_file_content(df_example)
    df_new = csv_file.get_file_content()
    csv_file.update_columns_names({'D': "Date"})
    csv_file.update_cell_by_date('A', pd.to_datetime("01.02.2015 06:00:00"), 999)
    csv_file.update_column_by_name('B', [9, 9, 9])
