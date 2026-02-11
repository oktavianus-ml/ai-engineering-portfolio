from app.application.forecasting.baseline_forecast_engine import BaselineForecastEngine
from app.application.forecasting.xgb_forecast_engine import XGBForecastEngine


def get_forecast_engine(engine_type: str = "baseline"):
    if engine_type == "xgb":
        return XGBForecastEngine()
    return BaselineForecastEngine()