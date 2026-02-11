import pandas as pd


class StockPlanner:

    @staticmethod
    def stock_coverage(
        available_stock: float,
        forecast_df: pd.DataFrame,
        window: int = 7
    ) -> float:
        avg_daily = forecast_df["forecast_qty"].head(window).mean()
        if avg_daily <= 0:
            return float("inf")
        return round(available_stock / avg_daily, 1)

    @staticmethod
    def reorder_point(
        forecast_df: pd.DataFrame,
        lead_time_days: int,
        safety_days: int = 3
    ) -> float:
        avg_daily = forecast_df["forecast_qty"].mean()
        safety_stock = avg_daily * safety_days
        return round((avg_daily * lead_time_days) + safety_stock, 0)

    @staticmethod
    def decision(
        available_stock: float,
        rop: float,
        coverage_days: float
    ) -> str:
        if available_stock <= rop:
            return "🚨 REORDER NOW"
        elif coverage_days < 7:
            return "⚠️ MONITOR"
        return "✅ SAFE"