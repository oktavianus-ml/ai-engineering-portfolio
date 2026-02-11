class ScenarioEngine:
    """
    Engine untuk menjalankan what-if scenario
    berbasis perubahan demand (%)
    """

    def __init__(self, kpi_calculator, decision_engine):
        self.kpi_calculator = kpi_calculator
        self.decision_engine = decision_engine

    def run(
        self,
        base_avg_daily_demand: float,
        sales_df,
        current_stock: float | None,
        lead_time: int,
        scenarios: dict,
    ) -> dict:
        """
        scenarios example:
        {
            "worst": -0.2,
            "best": 0.2
        }
        """

        results = {}

        for name, delta in scenarios.items():
            # 1️⃣ adjust demand
            scenario_demand = base_avg_daily_demand * (1 + delta)

            # guard
            if scenario_demand <= 0:
                continue

            # 2️⃣ hitung KPI berbasis demand baru
            kpi = self._calculate_kpi_from_demand(
                scenario_demand,
                sales_df,
                current_stock,
                lead_time
            )

            # 3️⃣ decision
            decision = self.decision_engine.evaluate(kpi)

            results[name] = {
                "avg_daily_demand": round(scenario_demand, 2),
                "kpi": kpi,
                "decision": decision
            }

        return results
    

    def _calculate_kpi_from_demand(
        self,
        avg_daily_demand: float,
        sales_df,
        current_stock: float | None,
        lead_time: int,
    ) -> dict:
        """
        KPI minimal untuk scenario:
        - avg_daily_demand
        - stock_coverage_days
        - reorder_point
        """

        kpi = {
            "avg_daily_demand": round(avg_daily_demand, 2),
            "avg_weekly_demand": round(avg_daily_demand * 7, 2),
        }

        # Safety stock proxy (simple, konsisten)
        sigma = sales_df["qty_sold"].std() if sales_df is not None else None
        if not sigma or sigma <= 0:
            sigma = avg_daily_demand * 0.3

        safety_stock = 1.65 * sigma * (lead_time ** 0.5)
        reorder_point = (avg_daily_demand * lead_time) + safety_stock

        kpi["safety_stock"] = round(safety_stock, 0)
        kpi["reorder_point"] = round(reorder_point, 0)

        if current_stock is not None:
            kpi["stock_coverage_days"] = round(
                current_stock / avg_daily_demand,
                1
            )

        return kpi

