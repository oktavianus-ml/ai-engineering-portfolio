# app/infrastructure/repositories/inventory_repository.py

import pandas as pd


class InventoryRepository:

    def __init__(
        self,
        csv_path: str = "data/raw/available_stock_260125_jatake.csv",
        warehouse_location: str = "555000/Stock"
    ):
        self.df = pd.read_csv(csv_path)
        self.df["product_code"] = self.df["product_code"].str.strip()
        self.df["location"] = self.df["location"].str.strip()
        self.warehouse_location = warehouse_location

    def get_available_stock(
        self,
        product_code: str,
        location: str | None = None
    ) -> float:
        product_code = product_code.strip()
        location = location or self.warehouse_location

        row = self.df[
            (self.df["product_code"] == product_code) &
            (self.df["location"] == location)
        ]

        if row.empty:
            return 0.0

        return float(row["available_stock"].iloc[0])