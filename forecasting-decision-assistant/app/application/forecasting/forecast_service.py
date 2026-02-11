class ForecastService:
    def __init__(
        self,
        sales_repository,
        forecast_engine,
        inventory_repository=None,
        kpi_calculator=None,
    ):
        self.sales_repository = sales_repository
        self.forecast_engine = forecast_engine
        self.inventory_repository = inventory_repository
        self.kpi_calculator = kpi_calculator

    # ✅ EXISTING (dipakai ChatService) — JANGAN DIUBAH
    def forecast(self, product_id: int, horizon: int):
        sales_df = self.sales_repository.get_sales_by_product(product_id)

        if sales_df is None or sales_df.empty:
            raise ValueError("No sales data found for this product")

        return self.forecast_engine.run(
            sales_df=sales_df,
            horizon=horizon
        )

    # 🔥 EXTENDED – PHASE 5 (API + KPI + Safety Stock)
    def run_forecast_api(
        self,
        product_id: int,
        horizon: int,
        service_level: float = 0.95
    ):
        sales_df = self.sales_repository.get_sales_by_product(product_id)

        if sales_df is None or sales_df.empty:
            raise ValueError("No sales data found for this product")

        # 1️⃣ history
        history = [
            {
                "date": str(row["move_date"]),
                "qty": float(row["qty_sold"])
            }
            for _, row in sales_df.iterrows()
        ]

        # 2️⃣ forecast (reuse engine)
        forecast_df = self.forecast_engine.run(
            sales_df=sales_df,
            horizon=horizon
        )

        forecast = [
            {
                "date": str(row["date"]),
                "qty": float(row["forecast_qty"])
            }
            for _, row in forecast_df.iterrows()
        ]

        # 3️⃣ summary basic
        total = sum(item["qty"] for item in forecast)
        avg_daily = total / horizon

        summary = {
            "total_forecast": round(total),
            "avg_daily": round(avg_daily, 2),
        }



        return {
            "product_id": product_id,
            "horizon": horizon,
            "history": history,
            "forecast": forecast,
            "summary": summary,
        }
