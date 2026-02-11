from pathlib import Path
import json
import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]

MODEL_DIR = ROOT / "models" / "weekly"
LOG_DIR = ROOT / "logs" / "weekly"
PLOT_DIR = ROOT / "plots" / "weekly"


class WeeklyForecastService:

    def forecast(self, product_code: str, horizon: int = 4):
        """
        Return dummy forecast dataframe (weekly)
        Actual forecasting already done during training
        """
        meta = self._load_meta(product_code)

        avg = meta["avg_weekly_demand"]

        future = pd.DataFrame({
            "week_idx": range(1, horizon + 1),
            "forecast_qty": [avg] * horizon
        })

        return future

    def load_artifacts(self, product_code: str):
        return {
            "meta": self._load_meta(product_code),
            "plot": self._load_plot(product_code)
        }

    def _load_meta(self, product_code):
        path = LOG_DIR / f"{product_code}_meta.json"
        return json.loads(path.read_text())

    def _load_plot(self, product_code):
        path = PLOT_DIR / f"{product_code}_forecast.png"
        return path if path.exists() else None