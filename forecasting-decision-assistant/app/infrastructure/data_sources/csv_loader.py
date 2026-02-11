import pandas as pd
from pathlib import Path

class CsvSalesLoader:
    def load_multiple(self, folder_path: str) -> pd.DataFrame:
        csv_files = Path(folder_path).glob("*.csv")

        dfs = []
        for file in csv_files:
            df = pd.read_csv(file)
            df["move_date"] = pd.to_datetime(df["move_date"])
            df["qty_sold"] = df["qty_sold"].astype(float)
            dfs.append(df)

        unified_df = pd.concat(dfs, ignore_index=True)
        return unified_df
