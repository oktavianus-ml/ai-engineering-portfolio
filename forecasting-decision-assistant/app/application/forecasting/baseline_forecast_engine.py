# app/application/forecasting/baseline_forecast_engine.py

import pandas as pd
from app.domain.forecasting.forecast_engine import ForecastEngine


class BaselineForecastEngine(ForecastEngine):

    def run(self, sales_df: pd.DataFrame, horizon: int) -> pd.DataFrame:
        sales_df = sales_df.copy()
        sales_df["move_date"] = pd.to_datetime(sales_df["move_date"])

        last_qty = sales_df["qty_sold"].iloc[-1]
        last_date = sales_df["move_date"].max()

        future_dates = pd.date_range(
            start=last_date + pd.Timedelta(days=1),
            periods=horizon,
            freq="D"
        )

        return pd.DataFrame({
            "forecast_date": future_dates,
            "forecast_qty": [last_qty] * horizon
        })
