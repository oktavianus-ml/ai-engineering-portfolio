# app/infrastructure/repositories/sales_repository.py

class SalesRepository:
    def __init__(self, loader):
        self.loader = loader

    def get_all_sales(self):
        df = self.loader.load()

        # 🔒 HARD GUARD — SALES WAJIB PUNYA move_date
        if "move_date" not in df.columns:
            raise ValueError(
                "Invalid sales data source: 'move_date' column missing. "
                "Check loader wiring (stock CSV loaded as sales)."
            )

        return df

    def get_sales_by_product(self, product_id: int):
        df = self.get_all_sales()
        return df[df["product_id"] == product_id].sort_values("move_date")

    def get_sales_by_customer(self, customer_code: str):
        df = self.get_all_sales()
        return df[df["customer_code"] == customer_code].sort_values("move_date")