class DecisionEngine:

    def evaluate(self, kpi: dict) -> dict:
        """
        kpi diambil dari ForecastKPICalculator + meta weekly
        """

        stock_coverage = kpi["stock_coverage_days"]
        lead_time = kpi.get("lead_time_days", 7)

        # ─────────────────────────────
        # RISK
        # ─────────────────────────────
        stockout_risk = min(1.0, lead_time / max(stock_coverage, 1))
        overstock_risk = min(1.0, stock_coverage / 30)

        # ─────────────────────────────
        # ACTION
        # ─────────────────────────────
        if stock_coverage < lead_time:
            action = "REORDER_NOW"
            urgency = "HIGH"
        elif stock_coverage < lead_time + 3:
            action = "REORDER_SOON"
            urgency = "MEDIUM"
        elif overstock_risk > 0.8:
            action = "DELAY"
            urgency = "LOW"
        else:
            action = "HOLD"
            urgency = "LOW"

        # ─────────────────────────────
        # REASONS
        # ─────────────────────────────
        reasons = []

        if stock_coverage < lead_time:
            reasons.append(
                "Stock coverage lebih pendek dari lead time"
            )

        if kpi.get("safety_stock", 0) > 0:
            reasons.append(
                "Safety stock dihitung untuk menjaga service level"
            )

        # ─────────────────────────────
        # CONFIDENCE
        # ─────────────────────────────
        confidence = round(
            min(1.0, 0.55 + stockout_risk * 0.45),
            2
        )

        return {
            "action": action,
            "urgency": urgency,
            "risk": {
                "stockout": round(stockout_risk, 2),
                "overstock": round(overstock_risk, 2),
            },
            "reasons": reasons,
            "confidence": confidence,
        }
