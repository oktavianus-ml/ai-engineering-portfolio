class ScenarioInterpreter:
    """
    Mengubah hasil scenario menjadi insight manusia
    (rule-based, deterministic)
    """

    def interpret(self, scenario_results: dict) -> str | None:
        if not scenario_results:
            return None

        actions = []
        urgencies = []
        coverages = []

        for _, data in scenario_results.items():
            decision = data.get("decision", {})
            kpi = data.get("kpi", {})

            if decision.get("action"):
                actions.append(decision["action"])

            if decision.get("urgency"):
                urgencies.append(decision["urgency"])

            if kpi.get("stock_coverage_days") is not None:
                coverages.append(float(kpi["stock_coverage_days"]))

        if not actions:
            return None

        # =========================
        # RULE 1: ACTION STABILITY
        # =========================
        if len(set(actions)) == 1:
            action = actions[0]

            if coverages and min(coverages) > 30:
                return (
                    f"Meskipun demand berubah (worst & best case), "
                    f"rekomendasi tetap {action}. "
                    f"Ini menunjukkan keputusan relatif stabil karena "
                    f"stok masih sangat aman."
                )

            return (
                f"Rekomendasi tetap {action} di semua skenario, "
                f"menandakan keputusan cukup stabil."
            )

        # =========================
        # RULE 2: ACTION CHANGE
        # =========================
        return (
            "Rekomendasi berubah antar skenario, "
            "menandakan keputusan sensitif terhadap perubahan demand. "
            "Perlu monitoring ketat."
        )
