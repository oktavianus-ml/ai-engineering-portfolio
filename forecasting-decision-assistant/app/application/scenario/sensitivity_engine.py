class SensitivityEngine:
    """
    Menemukan titik perubahan keputusan
    berdasarkan variasi demand (%)
    """

    def __init__(self, decision_engine):
        self.decision_engine = decision_engine

    def run(
        self,
        base_avg_daily_demand: float,
        sales_df,
        current_stock: float | None,
        lead_time: int,
        steps: list[float],
    ) -> list[dict]:
        """
        steps contoh:
        [-0.4, -0.2, 0, 0.2, 0.4, 0.6]
        """

        results = []

        for delta in steps:
            demand = base_avg_daily_demand * (1 + delta)

            if demand <= 0:
                continue

            kpi = self._kpi_from_demand(
                demand,
                sales_df,
                current_stock,
                lead_time,
            )

            decision = self.decision_engine.evaluate(kpi)

            results.append({
                "delta": delta,
                "avg_daily_demand": round(demand, 2),
                "action": decision.get("action"),
                "urgency": decision.get("urgency"),
            })

        return results


    # =========================
    # KPI HELPER (PRIVATE)
    # =========================
    def _kpi_from_demand(
        self,
        avg_daily_demand: float,
        sales_df,
        current_stock,
        lead_time,
    ) -> dict:
        """
        KPI minimal untuk sensitivity analysis.
        Tidak pakai forecast_df.
        """

        sigma = None
        if sales_df is not None:
            sigma = sales_df["qty_sold"].std()

        if not sigma or sigma <= 0:
            sigma = avg_daily_demand * 0.3

        safety_stock = 1.65 * sigma * (lead_time ** 0.5)
        reorder_point = (avg_daily_demand * lead_time) + safety_stock

        kpi = {
            "avg_daily_demand": round(avg_daily_demand, 2),
            "avg_weekly_demand": round(avg_daily_demand * 7, 2),
            "safety_stock": round(safety_stock, 0),
            "reorder_point": round(reorder_point, 0),
        }

        if current_stock is not None:
            kpi["stock_coverage_days"] = round(
                current_stock / avg_daily_demand,
                1
            )

        return kpi