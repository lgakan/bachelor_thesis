from scripts.file_management import DfManager
import pytest
import os
import pandas as pd


class TestDfManager:
    TEST_PATH = "test_df_manager.csv"
    DF_TEST = pd.DataFrame({'D': [pd.to_datetime(f"01.0{i}.2015 06:00:00", format="%d.%m.%Y %H:%M:%S") for i in range(1, 8)],
                            'A': [x for x in range(1, 8)],
                            'B': [x * 100 for x in range(1, 8)]})

    @pytest.fixture(scope="function")
    def df_manager(self) -> DfManager:
        yield DfManager(path=self.TEST_PATH, date_col="D")
        if os.path.exists(self.TEST_PATH):
            os.remove(self.TEST_PATH)

    def test_save_to_file(self, df_manager: DfManager) -> None:
        df_manager.save_to_file(self.DF_TEST)
        assert os.path.exists(self.TEST_PATH)

    def test_read_from_file(self, df_manager: DfManager) -> None:
        df_manager.save_to_file(self.DF_TEST)
        df = df_manager.get_from_file()
        assert df.columns.tolist() == ['D', 'A', 'B']
        assert df.size == 3 * 7
        assert df['D'].tolist() == [pd.to_datetime(f"01.0{i}.2015 06:00:00", format="%d.%m.%Y %H:%M:%S") for i in range(1, 8)]

    def test_update_column_names(self, df_manager: DfManager) -> None:
        df_manager.save_to_file(self.DF_TEST)
        df_manager.update_columns_names({'D': 'Date', 'A': "A_column"})
        df = df_manager.get_from_file()
        assert df.columns.tolist() == ["Date", "A_column", 'B']
        assert df_manager.date_col == "Date"

    @pytest.mark.parametrize("date_in, state", [(pd.to_datetime(f"01.01.2015 06:00:00", format="%d.%m.%Y %H:%M:%S"), True),
                                                (pd.to_datetime(f"30.01.2017 06:00:00", format="%d.%m.%Y %H:%M:%S"), False)])
    def test_is_date_in_file(self, date_in: pd.Timestamp, state: bool, df_manager: DfManager) -> None:
        df_manager.save_to_file(self.DF_TEST)
        assert df_manager.is_date_in_file(df_manager.date_col, date_in) == state
