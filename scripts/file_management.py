from typing import Dict, List

import pandas as pd

from lib.config import DataTypes


class CSVManager:
    @staticmethod
    def get_content(path: str) -> pd.DataFrame:
        return pd.read_csv(path)

    @staticmethod
    def save_content(path: str, df: pd.DataFrame, date_format: str, sep: str = ',') -> None:
        df.to_csv(path, index=False, date_format=date_format, sep=sep)


class DfManager:
    def __init__(self, path: str, date_col: str = "Date"):
        self.path = path
        self.date_col = date_col
        self.csv_manager = CSVManager()
        self.date_format = "%d.%m.%Y %H:%M:%S"

    def get_from_file(self) -> pd.DataFrame:
        df = self.csv_manager.get_content(self.path)
        if self.date_col is not None and self.date_col in df.columns:
            df[self.date_col] = pd.to_datetime(df[self.date_col], format=self.date_format)
        return df.fillna('')

    def save_to_file(self, df: pd.DataFrame, sep: str = ',') -> None:
        self.csv_manager.save_content(self.path, df, self.date_format, sep)

    def update_columns_names(self, cols_names: Dict[str, str]) -> None:
        df = self.get_from_file()
        if any([x == self.date_col for x in cols_names.keys()]):
            self.date_col = cols_names[self.date_col]
        df.rename(columns=cols_names, inplace=True)
        self.save_to_file(df)

    def update_cell_by_date(self, date_col: str, date_in: pd.Timestamp, val_col: str, val_new: DataTypes.DF_VAL) -> None:
        df = self.get_from_file()
        if date_col in df.columns and df[date_col].dtype == "datetime64[ns]":
            df.loc[df[date_col] == date_in, val_col] = val_new
            self.save_to_file(df)
        else:
            raise Exception(f"Column {val_col} is not valid")

    def get_cell_by_date(self, date_col: str, date_in: pd.Timestamp, val_col: str) -> DataTypes.DF_VAL:
        df = self.get_from_file()
        if date_col in df.columns and df[date_col].dtype == "datetime64[ns]":
            return df.loc[df[date_col] == date_in, val_col].values[0]
        else:
            raise Exception(f"Column {val_col} is not valid")

    def get_subset_by_date(self, date_col: str, date_start: pd.Timestamp, date_end: pd.Timestamp) -> pd.DataFrame:
        df = self.get_from_file()
        return df[(df[date_col] >= date_start) & (df[date_col] <= date_end)]

    def is_date_in_file(self, date_col: str, date_in: pd.Timestamp) -> bool:
        first_date, last_date = self.get_from_file()[date_col].iloc[[0, -1]]
        if not (first_date <= date_in <= last_date):
            return False
        return True

    def update_column_by_name(self, col_name: str, data: List[DataTypes.DF_VAL]) -> None:
        df = self.get_from_file()
        if col_name in df.columns and len(data) == df.shape[0]:
            df.update({col_name: data})
            self.save_to_file(df)
        else:
            raise Exception(f"{col_name} not in {df.columns.to_list()} or {df.shape[0]} != {len(data)}")


if __name__ == "__main__":
    df_example = pd.DataFrame(
        {'D': [pd.to_datetime(f"01.0{i}.2015 06:00:00", format="%d.%m.%Y %H:%M:%S") for i in range(1, 8)],
         'A': [x for x in range(1, 8)],
         'B': [x * 100 for x in range(1, 8)]})

    df_manager = DfManager("test_prices_delete.csv")
    df_manager.save_to_file(df_example)
    df_example = df_manager.get_from_file()
    df_manager.update_columns_names({'D': "Date"})
    df_manager.update_cell_by_date("Date", pd.to_datetime("01.02.2015 06:00:00", format="%d.%m.%Y %H:%M:%S"), 'A', 999)
    df_manager.update_column_by_name('B', [9 for _ in range(1, 8)])
