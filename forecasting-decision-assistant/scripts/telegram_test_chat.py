# app/tests/manual_test_chat.py
import sys
from pathlib import Path

# 🔥 pastikan project root masuk PYTHONPATH
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd
from app.application.chat.chat_service import ChatService
from app.application.forecasting.kpi_calculator import ForecastKPICalculator


# ─────────────────────────────
# DUMMY DEPENDENCIES (TELEGRAM TEST)
# ─────────────────────────────
class DummyIntentClassifier:
    def classify(self, text): return "forecast"

class DummyProductResolver:
    def resolve(self, text):
        return {"product_id": 5746, "product_name": "CNI Nutrimoist"}

class DummyHorizonParser:
    def parse(self, text): return 14

class DummySalesRepository:
    def get_sales_by_product(self, product_id):
        return pd.DataFrame({"qty_sold": [2, 3, 1, 4, 2]})

class DummyForecastService:
    def __init__(self):
        self.sales_repository = DummySalesRepository()
    def forecast(self, product_id, horizon):
        return pd.DataFrame({"forecast_qty": [2.1] * horizon})

class DummyInventoryRepository:
    def get_current_stock(self, product_id): return 120
    def get_lead_time(self, product_id): return 7

class DummyLLMService:
    def explain_forecast(self, **kwargs):
        kpi = kwargs["kpi"]
        return f"""
📊 TELEGRAM BOT TEST
Avg daily demand : {kpi['avg_daily_demand']}
Stock coverage  : {kpi['stock_coverage_days']}
ROP             : {kpi['reorder_point']}
"""


# ─────────────────────────────
# RUN CHAT TEST
# ─────────────────────────────
if __name__ == "__main__":
    chat = ChatService(
        intent_classifier=DummyIntentClassifier(),
        product_resolver=DummyProductResolver(),
        horizon_parser=DummyHorizonParser(),
        forecast_service=DummyForecastService(),
        llm_service=DummyLLMService(),
        inventory_repository=DummyInventoryRepository(),
        kpi_calculator=ForecastKPICalculator(),
    )

    print(
        chat.handle_message(
            "Prediksi penjualan CNI Nutrimoist 14 hari ke depan"
        )
    )
