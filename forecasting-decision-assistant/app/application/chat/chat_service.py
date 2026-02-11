import logging
import json
from pathlib import Path
from app.application.chat.session_state import session_state
from app.planning.stock_planner import StockPlanner
from app.application.decision.decision_engine import DecisionEngine
from app.application.scenario.scenario_engine import ScenarioEngine
from app.application.scenario.scenario_interpreter import ScenarioInterpreter
from app.application.scenario.sensitivity_engine import SensitivityEngine
from app.application.scenario.sensitivity_plotter import SensitivityPlotter
from app.application.explanation.llm_explainer import LLMDecisionExplainer
from app.application.action.action_recommender import ActionRecommendationEngine


logger = logging.getLogger(__name__)

# =========================
# ROOT PATH
# =========================
ROOT = Path(__file__).resolve().parents[3]


class ChatService:
    def __init__(
        self,
        intent_classifier,
        product_resolver,
        horizon_parser,
        forecast_service,
        llm_service,
        inventory_repository=None,
        kpi_calculator=None,
    ):
        self.intent_classifier = intent_classifier
        self.product_resolver = product_resolver
        self.horizon_parser = horizon_parser
        self.forecast_service = forecast_service
        self.llm_service = llm_service
        self.inventory_repository = inventory_repository
        self.kpi_calculator = kpi_calculator
        self.scenario_interpreter = ScenarioInterpreter()
        self.decision_engine = DecisionEngine()
        self.sensitivity_engine = SensitivityEngine(
            decision_engine=self.decision_engine
        )
        self.scenario_engine = ScenarioEngine(
            kpi_calculator=self.kpi_calculator,
            decision_engine=self.decision_engine
        )
        self.sensitivity_plotter = SensitivityPlotter(
            output_dir=ROOT / "plots" / "sensitivity"
        )
        self.llm_explainer = LLMDecisionExplainer()
        self.action_recommender = ActionRecommendationEngine()


    # ─────────────────────────────
    # PARSING ONLY
    # ─────────────────────────────
    def parse_user_input(self, text: str) -> dict:
        return {
            "intent": self.intent_classifier.classify(text),
            "product": self.product_resolver.resolve(text),
            "horizon": self.horizon_parser.parse(text),
            "raw_text": text,
        }

    # ─────────────────────────────
    # MAIN ORCHESTRATION
    # ─────────────────────────────
    def handle_message(self, text: str, chat_id: int):

        # =========================
        # STEP 0: HANDLE PENDING SELECTION
        # =========================
        pending = session_state.get(f"pending_product:{chat_id}")

        if text.strip().isdigit() and pending:
            resolved = self.product_resolver.resolve_from_candidates(
                pending["candidates"],
                text
            )

            if resolved.get("status") != "resolved":
                return "❌ Pilihan tidak valid."

            session_state.pop(f"pending_product:{chat_id}")

            parsed = {
                "intent": "forecast",
                "product": resolved,
                "horizon": self.horizon_parser.parse(pending["raw_text"]),
                "raw_text": pending["raw_text"],
            }
        else:
            parsed = self.parse_user_input(text)

        # =========================
        # GREETING & INTENT CHECK
        # =========================
        if parsed["intent"] == "greeting":
            return (
                "Halo! 👋\n"
                "Saya bisa membantu prediksi penjualan.\n"
                "Contoh:\n"
                "Prediksi penjualan CNI Ginseng Coffee"
            )

        if parsed["intent"] != "forecast":
            return "Maaf, saya belum bisa memproses permintaan tersebut."

        product = parsed["product"]

        if product.get("status") == "not_found":
            return "Saya tidak menemukan produk tersebut."

        # =========================
        # AMBIGUOUS PRODUCT (WAJIB EARLY)
        # =========================
        if product.get("status") == "ambiguous":
            session_state.set(
                f"pending_product:{chat_id}",
                {
                    "candidates": product["candidates"],
                    "raw_text": parsed["raw_text"],
                }
            )

            options = "\n".join(
                f"{i}. {p['product_code']} – {p['product_name']}"
                for i, p in enumerate(product["candidates"], start=1)
            )

            return (
                "Saya menemukan beberapa varian produk 👇\n"
                f"{options}\n\n"
                "Balas dengan nomor produk."
            )

        # =========================
        # NOT FOUND (SETELAH AMBIGUOUS)
        # =========================
        if product.get("status") == "not_found":
            return "Saya tidak menemukan produk tersebut."

        # =========================
        # LOAD META
        # =========================
        product_code = product["product_code"]
        product_name = product["product_name"]
        product_id = product.get("product_id")
        print("DEBUG product_id:", product_id)


        weekly_meta = self._load_meta("weekly", product_code)
        monthly_meta = self._load_meta("monthly", product_code)
        yearly_meta = self._load_meta("yearly", product_code)


        

        # =========================
        # STOCK & PLANNING (SAFE)
        # =========================
        decision = None  # 🔥 WAJIB, di scope fungsi
        available_stock = None
        stock_coverage = None
        reorder_point = None
        scenario_results = None
        scenario_insight = None
        sensitivity_results = None
        sensitivity_insight = None


        avg_daily_demand = weekly_meta.get("avg_daily_demand") if weekly_meta else None
        lead_time_days = weekly_meta.get("lead_time_days", 7) if weekly_meta else 7

        # 1️⃣ Coba ambil stok REAL
        if self.inventory_repository:
            available_stock = self.inventory_repository.get_available_stock(
                product_code=product_code
            )

        # 2️⃣ HITUNG coverage jika stok REAL tersedia
        if available_stock is not None and avg_daily_demand and avg_daily_demand > 0:
            stock_coverage = round(available_stock / avg_daily_demand, 1)

        # 3️⃣ FALLBACK DERIVED (JIKA stok REAL TIDAK ADA)
        if stock_coverage is None and avg_daily_demand and avg_daily_demand > 0:
            assumed_days = min(lead_time_days, 3)
            stock_coverage = assumed_days
            available_stock = round(avg_daily_demand * assumed_days, 0)

        # 4️⃣ HITUNG ROP (selalu bisa kalau avg_daily_demand ada)
        if avg_daily_demand and avg_daily_demand > 0:
            reorder_point = round(
                (avg_daily_demand * lead_time_days)
                + (avg_daily_demand * 3),
                0
            )

        # 5️⃣ INJECT ke weekly_meta (SATU TEMPAT)
        if weekly_meta:
            weekly_meta["available_stock"] = available_stock
            weekly_meta["stock_coverage_days"] = stock_coverage
            weekly_meta["reorder_point"] = reorder_point


                
            # =========================
            # FALLBACK STOCK (DERIVED)
            # =========================
            if weekly_meta and weekly_meta.get("stock_coverage_days") is None:
                avg_daily_demand = weekly_meta.get("avg_daily_demand")

                if avg_daily_demand and avg_daily_demand > 0:
                    # asumsi stok = 3 hari demand (derived, bukan magic qty)
                    assumed_days = min(
                        weekly_meta.get("lead_time_days", 7),
                        3
                    )

                    weekly_meta["stock_coverage_days"] = assumed_days
                    weekly_meta["available_stock"] = round(
                        avg_daily_demand * assumed_days,
                        0
                    )

            # =========================
            # KPI + DECISION (FINAL, SAFE)
            # =========================
            if (
                product_id
                and weekly_meta
                and self.kpi_calculator
            ):
                sales_df = self.forecast_service.sales_repository.get_sales_by_product(
                    product_id
                )

                available_stock = weekly_meta.get("available_stock")

                if sales_df is not None and not sales_df.empty:
                    kpi = self.kpi_calculator.calculate(
                        sales_df=sales_df,
                        forecast_df=None,  # eksplisit
                        current_stock=available_stock,
                        lead_time=weekly_meta.get("lead_time_days", 7),
                    )

                    if kpi:
                        weekly_meta.update(kpi)

                        decision_engine = DecisionEngine()
                        decision = decision_engine.evaluate(weekly_meta)


            

            # =========================
            # 📊 SCENARIO & WHAT-IF ANALYSIS
            # =========================
            scenario_results = None

            if decision and weekly_meta.get("avg_daily_demand"):
                scenarios = {
                    "worst": -0.2,  # demand turun 20%
                    "best": 0.2,    # demand naik 20%
                }

                scenario_results = self.scenario_engine.run(
                    base_avg_daily_demand=weekly_meta["avg_daily_demand"],
                    sales_df=sales_df,
                    current_stock=weekly_meta.get("available_stock"),
                    lead_time=weekly_meta.get("lead_time_days", 7),
                    scenarios=scenarios,
                )

                # =========================
                # 🧠 SCENARIO INTERPRETATION
                # =========================
                scenario_insight = None

                if scenario_results:
                    scenario_insight = self.scenario_interpreter.interpret(
                        scenario_results
                    )


                # =========================
                # 🔢 SENSITIVITY ANALYSIS
                # =========================

                if decision and weekly_meta.get("avg_daily_demand"):
                    steps = [-0.4, -0.2, 0, 0.2, 0.4, 0.6]

                    sensitivity_results = self.sensitivity_engine.run(
                        base_avg_daily_demand=weekly_meta["avg_daily_demand"],
                        sales_df=sales_df,
                        current_stock=weekly_meta.get("available_stock"),
                        lead_time=weekly_meta.get("lead_time_days", 7),
                        steps=steps,
                    )

                # =========================
                # 🔢 SENSITIVITY INSIGHT
                # =========================
                sensitivity_insight = self._interpret_sensitivity(
                    sensitivity_results
                )

            #print("DEBUG scenario_results:", scenario_results)


        # =========================
        # 📊 SENSITIVITY PLOT
        # =========================
        sensitivity_plot = None

        if sensitivity_results:
            sensitivity_plot = self.sensitivity_plotter.plot(
                product_code=product_code,
                sensitivity_results=sensitivity_results,
            )

        #print("DEBUG sensitivity_results:", sensitivity_results is not None)
        #print("DEBUG sensitivity_plot:", sensitivity_plot)

        # =========================
        # 🧠 LLM EXPLANATION (WOW FACTOR)
        # =========================
        llm_explanation = None

        if decision:
            llm_explanation = self.llm_explainer.explain(
                product_name=product_name,
                decision=decision,
                scenario_results=scenario_results,
                sensitivity_insight=sensitivity_insight
            )


        # =========================
        # 🎯 ACTION RECOMMENDATION
        # =========================
        action_recommendation = None

        if decision:
            action_recommendation = self.action_recommender.recommend(
                decision=decision,
                weekly_meta=weekly_meta
            )


        if not weekly_meta:
            return "⚠️ Data forecast mingguan belum tersedia."
    
        # =========================
        # BUILD SUMMARY
        # =========================
        summary_message = self._format_trend_summary(
            product_name,
            weekly_meta,
            monthly_meta,
            yearly_meta,
            decision=decision,
            scenario_results=scenario_results,
            scenario_insight=scenario_insight,
            sensitivity_insight=sensitivity_insight,
            llm_explanation=llm_explanation,
            action_recommendation=action_recommendation  
        )

        # =========================
        # BUILD IMAGES (SAFE)
        # =========================
        images = {}

        weekly_plot = self._load_plot("weekly", product_code)
        if weekly_plot:
            images["weekly"] = str(weekly_plot)

        if monthly_meta:
            monthly_plot = self._load_plot("monthly", product_code)
            if monthly_plot:
                images["monthly"] = str(monthly_plot)

        if yearly_meta:
            yearly_plot = self._load_plot("yearly", product_code)
            if yearly_plot:
                images["yearly"] = str(yearly_plot)


        if sensitivity_plot:
            images["sensitivity"] = str(sensitivity_plot)

        print("DEBUG images sent to bot:", images)

        return {
            "text": summary_message,
            "images": images
        }

    # ─────────────────────────────
    # GENERIC LOADERS
    # ─────────────────────────────
    def _load_meta(self, horizon: str, product_code: str):
        path = ROOT / "logs" / horizon / f"{product_code}_meta.json"
        if not path.exists():
            logger.warning(f"Meta not found: {path}")
            return None
        return json.loads(path.read_text())

    def _load_plot(self, horizon: str, product_code: str):
        path = ROOT / "plots" / horizon / f"{product_code}_forecast.png"
        return path if path.exists() else None

    # ─────────────────────────────
    # TREND LOGIC
    # ─────────────────────────────
    def _detect_trend(self, current, previous):
        if not previous or previous == 0:
            return "Stabil ➖"

        change = (current - previous) / previous
        if change > 0.1:
            return "Naik 📈"
        elif change < -0.1:
            return "Turun 📉"
        return "Stabil ➖"

    # ─────────────────────────────
    # FORMATTERS
    # ─────────────────────────────
    def _format_horizon_block(self, title, meta, avg_key, reorder_key=None):
        lines = [
            title,
            f"📐 BAE Model: {meta.get('bae_validation')}",
            f"📊 MAE Model: {meta.get('mae_validation')}",
            f"📦 Zero Ratio: {meta.get('zero_ratio')}",
            f"📈 Avg Demand: {meta.get(avg_key)}",
        ]

        if reorder_key and meta.get(reorder_key) is not None:
            lines.append(f"🔁 Reorder Point: {meta.get(reorder_key)}")

        return "\n".join(lines)

    def _format_trend_summary(
        self,
        product_name,
        weekly_meta,
        monthly_meta=None,
        yearly_meta=None,
        decision=None,
        scenario_results=None,
        scenario_insight=None,
        sensitivity_insight=None,
        llm_explanation=None,
        action_recommendation=None
    ):
        blocks = [
            f"🔮 *Ringkasan Tren Penjualan – {product_name}*\n"
        ]

        # WEEKLY
        blocks.append(
            self._format_horizon_block(
                "📈 *Jangka Pendek (Weekly)*",
                weekly_meta,
                avg_key="avg_weekly_demand",
                reorder_key="reorder_point"
            )
        )

        # MONTHLY
        if monthly_meta:
            trend_monthly = self._detect_trend(
                monthly_meta.get("avg_monthly_demand"),
                weekly_meta.get("avg_weekly_demand") * 4
            )

            blocks.append(
                self._format_horizon_block(
                    "\n📊 *Jangka Menengah (Monthly)*",
                    monthly_meta,
                    avg_key="avg_monthly_demand"
                )
                + f"\n📊 Trend: {trend_monthly}"
            )

        # YEARLY
        if yearly_meta:
            trend_yearly = self._detect_trend(
                yearly_meta.get("avg_yearly_demand"),
                (monthly_meta.get("avg_monthly_demand") if monthly_meta else 0) * 12
            )

            blocks.append(
                self._format_horizon_block(
                    "\n🧭 *Jangka Panjang (Yearly)*",
                    yearly_meta,
                    avg_key="avg_yearly_demand"
                )
                + f"\n📊 Trend: {trend_yearly}"
            )


        # =========================
        # 🎯 ACTION RECOMMENDATION
        # =========================
        if action_recommendation:
            blocks.append(
                "🎯 *Rekomendasi Tindakan*\n"
                f"• Action: *{action_recommendation['action']}*\n"
                f"• Qty: {action_recommendation['recommended_qty']}\n"
                f"• Waktu: {action_recommendation['recommended_date']}\n"
                f"• Alasan: {action_recommendation['reason']}"
            )


        # =========================
        # INSIGHT
        # =========================
        blocks.append(
            "\n🧠 *Insight*\n"
            "• Weekly → reorder & kontrol stok\n"
            "• Monthly → planning & alokasi\n"
            "• Yearly → budgeting & strategi"
        )
        
        # =========================
        # 🚦 DECISION
        # =========================
        if decision:
            blocks.append(
                "\n🚦 *Rekomendasi Sistem*\n"
                f"• Action: *{decision['action']}*\n"
                f"• Urgency: *{decision['urgency']}*\n"
                f"• Confidence: {decision['confidence']}\n"
                "• Alasan:\n"
                + "\n".join(
                    f"  - {reason}"
                    for reason in decision.get("reasons", [])
                )
            )


        # =========================
        # 📊 SCENARIO & WHAT-IF
        # =========================
        if scenario_results:
            blocks.append("\n📊 Scenario & What-if Analysis")

            for name, data in scenario_results.items():
                label = "📉 Worst Case" if name == "worst" else "📈 Best Case"

                decision_data = data.get("decision", {})
                kpi = data.get("kpi", {})

                blocks.append(
                    f"\n{label}\n"
                    f"- Avg Daily Demand: {round(float(data.get('avg_daily_demand')), 1)}\n"
                    f"- Action: {decision_data.get('action')}\n"
                    f"- Urgency: {decision_data.get('urgency')}\n"
                    f"- Stock Coverage: {round(float(kpi.get('stock_coverage_days')), 1)} hari"
                )

        # =========================
        # 🧠 SCENARIO INTERPRETATION
        # =========================
        if scenario_insight:
            blocks.append(
                "\n🧠 Interpretasi Skenario\n"
                f"{scenario_insight}"
            )

        # =========================
        # 🔢 SENSITIVITY ANALYSIS
        # =========================
        if sensitivity_insight:
            blocks.append(
                "\n🔢 Sensitivity Analysis\n"
                f"{sensitivity_insight}"
            )


        # =========================
        # 🤖 AI EXPLANATION
        # =========================
        if llm_explanation:
            blocks.append(
                "\n🤖 *Penjelasan Sistem (AI)*\n"
                f"{llm_explanation}"
         )


        return "\n\n".join(blocks)
    

    
    # ─────────────────────────────
    # 🔢 SENSITIVITY INTERPRETATION
    # ─────────────────────────────
    def _interpret_sensitivity(self, sensitivity_results):
        if not sensitivity_results:
            return None

        base_action = sensitivity_results[0].get("action")

        for row in sensitivity_results:
            if row.get("action") != base_action:
                pct = int(row["delta"] * 100)
                return (
                    f"Rekomendasi berubah ketika demand berubah "
                    f"sekitar {pct}%."
                )

        return (
            "Rekomendasi tetap sama meskipun demand berubah signifikan, "
            "menandakan keputusan sangat stabil."
        )