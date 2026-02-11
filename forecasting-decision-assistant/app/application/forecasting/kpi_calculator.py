import numpy as np
import pandas as pd


class ForecastKPICalculator:
    """
    KPI Calculator yang aman:
    - Bisa jalan TANPA forecast_df
    - Bisa jalan TANPA inventory real
    - Tidak pernah raise exception keras
    """

    DEFAULT_Z_TABLE = {
        0.90: 1.28,
        0.95: 1.65,
        0.99: 2.33,
    }

    def calculate(
        self,
        sales_df: pd.DataFrame | None,
        forecast_df: pd.DataFrame | None = None,
        current_stock: float | None = None,
        lead_time: int = 7,
        service_level: float = 0.95,
    ) -> dict:

        kpi: dict = {}

        # ─────────────────────────────
        # 1️⃣ AVG DAILY DEMAND
        # Priority:
        #   a. forecast_df (jika ada & valid)
        #   b. sales_df (fallback)
        # ─────────────────────────────
        avg_daily_demand = None

        if (
            forecast_df is not None
            and isinstance(forecast_df, pd.DataFrame)
            and "forecast_qty" in forecast_df.columns
        ):
            avg_daily_demand = forecast_df["forecast_qty"].mean()

        if (
            avg_daily_demand is None
            and sales_df is not None
            and not sales_df.empty
            and "qty_sold" in sales_df.columns
        ):
            avg_daily_demand = sales_df["qty_sold"].mean()

        # Kalau tetap tidak dapat, stop secara HALUS
        if avg_daily_demand is None or avg_daily_demand <= 0:
            return kpi  # kosong tapi AMAN

        kpi["avg_daily_demand"] = round(avg_daily_demand, 2)
        kpi["avg_weekly_demand"] = round(avg_daily_demand * 7, 2)

        # ─────────────────────────────
        # 2️⃣ DEMAND VARIABILITY (σ)
        # ─────────────────────────────
        sigma = None

        if sales_df is not None and not sales_df.empty:
            sigma = sales_df["qty_sold"].std()

        # fallback aman jika data sales minim
        if sigma is None or pd.isna(sigma) or sigma <= 0:
            sigma = avg_daily_demand * 0.3

        # ─────────────────────────────
        # 3️⃣ SERVICE LEVEL → Z SCORE
        # ─────────────────────────────
        Z = self.DEFAULT_Z_TABLE.get(
            service_level,
            self.DEFAULT_Z_TABLE[0.95]
        )

        # ─────────────────────────────
        # 4️⃣ SAFETY STOCK
        # ─────────────────────────────
        safety_stock = Z * sigma * np.sqrt(max(lead_time, 1))
        kpi["safety_stock"] = round(safety_stock, 0)

        # ─────────────────────────────
        # 5️⃣ REORDER POINT (ROP)
        # ─────────────────────────────
        reorder_point = (avg_daily_demand * lead_time) + safety_stock
        kpi["reorder_point"] = round(reorder_point, 0)

        # ─────────────────────────────
        # 6️⃣ STOCK COVERAGE (OPTIONAL)
        # ─────────────────────────────
        if current_stock is not None and current_stock >= 0:
            stock_coverage_days = current_stock / avg_daily_demand
            kpi["stock_coverage_days"] = round(stock_coverage_days, 1)

        return kpi
