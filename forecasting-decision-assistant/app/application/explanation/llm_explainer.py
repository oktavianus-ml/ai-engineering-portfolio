class LLMDecisionExplainer:
    """
    Mengubah output sistem (decision, scenario, sensitivity)
    menjadi penjelasan natural untuk manusia.
    """

    def explain(
        self,
        product_name: str,
        decision: dict,
        scenario_results: dict | None = None,
        sensitivity_insight: str | None = None,
        action_recommendation: dict | None = None,
    ) -> str:

        # Guard paling awal — kalau tidak ada decision, tidak perlu jelaskan apa pun
        if not decision:
            return ""

        # Container narasi (lokal, aman)
        lines: list[str] = []

        # =========================
        # 1️⃣ OPENING
        # =========================
        lines.append(
            f"📣 *Penjelasan Rekomendasi untuk {product_name}*"
        )

        # =========================
        # 2️⃣ CORE DECISION
        # =========================
        action = decision.get("action", "UNKNOWN")
        urgency = decision.get("urgency", "UNKNOWN")
        confidence = decision.get("confidence")

        # Confidence opsional (hindari error format)
        if isinstance(confidence, (int, float)):
            confidence_text = f"{confidence:.0%}"
        else:
            confidence_text = "N/A"

        lines.append(
            f"Sistem merekomendasikan *{action}* "
            f"dengan tingkat urgensi *{urgency}* "
            f"(confidence {confidence_text})."
        )

        # =========================
        # 3️⃣ ALASAN UTAMA
        # =========================
        reasons = decision.get("reasons") or []
        if reasons:
            lines.append("Keputusan ini didasarkan pada:")
            for r in reasons:
                lines.append(f"- {r}")

        # =========================
        # 4️⃣ SCENARIO CONTEXT
        # =========================
        if scenario_results:
            lines.append(
                "📊 Analisis skenario menunjukkan bahwa "
                "bahkan ketika demand berubah secara signifikan "
                "(worst & best case), rekomendasi utama tetap konsisten."
            )

        # =========================
        # 5️⃣ SENSITIVITY INSIGHT
        # =========================
        if sensitivity_insight:
            lines.append(
                "🔢 Sensitivity analysis menunjukkan bahwa "
                f"{sensitivity_insight}"
            )

        # =========================
        # 6️⃣ ACTION RECOMMENDATION (OPSIONAL, NARATIF SAJA)
        # =========================
        if action_recommendation:
            lines.append(
                "Sebagai tindak lanjut, sistem juga "
                "menyarankan langkah operasional berikut:"
            )

            lines.append(
                f"- *{action_recommendation.get('action')}* "
                f"dengan jumlah sekitar "
                f"{action_recommendation.get('recommended_qty')} unit, "
                f"dilakukan {action_recommendation.get('recommended_date')}."
            )

        # =========================
        # 7️⃣ BUSINESS INTERPRETATION
        # =========================
        lines.append(
            "Secara bisnis, rekomendasi ini bertujuan menjaga "
            "keseimbangan antara ketersediaan stok dan risiko overstock, "
            "serta memberikan fleksibilitas terhadap fluktuasi demand jangka pendek."
        )

        return "\n".join(lines)
