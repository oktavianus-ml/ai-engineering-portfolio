import pandas as pd
import xgboost as xgb
from datetime import timedelta
from app.domain.forecasting.forecast_engine import ForecastEngine


class XGBForecastEngine(ForecastEngine):
    """
    XGBoost weekly forecaster with DAILY output.
    - Train on weekly aggregated data
    - Recursive weekly prediction
    - Convert weekly forecast -> daily (for daily backtest)
    """

    FEATURE_COLS = ["lag_1", "lag_2", "rolling_4", "weekofyear"]

    def __init__(self, model_params=None):
        self.model_params = model_params or {
            "objective": "reg:squarederror",
            "n_estimators": 300,
            "learning_rate": 0.05,
            "max_depth": 4,
            "random_state": 42,
            "n_jobs": -1,
        }

    # ======================================================
    # PUBLIC API
    # ======================================================
    def run(self, sales_df: pd.DataFrame, horizon: int) -> pd.DataFrame:
        daily_df = self._prepare_daily(sales_df)
        weekly_df = self._aggregate_weekly(daily_df)

        X, y = self._build_features(weekly_df)
        model = self._train_model(X, y)

        weekly_forecast = self._recursive_weekly_forecast(
            history=weekly_df[["move_date", "qty_sold"]],
            model=model,
            horizon=horizon,
        )

        # 🔥 CRITICAL STEP: weekly -> daily
        daily_forecast = self._weekly_to_daily(
            weekly_forecast,
            horizon=horizon,
        )

        return daily_forecast

    # ======================================================
    # DATA PREP
    # ======================================================
    def _prepare_daily(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["move_date"] = pd.to_datetime(df["move_date"])
        return df.sort_values("move_date")

    def _aggregate_weekly(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df
            .set_index("move_date")
            .resample("W-MON")["qty_sold"]
            .sum()
            .reset_index()
        )

    # ======================================================
    # FEATURE ENGINEERING
    # ======================================================
    def _build_features(self, weekly_df: pd.DataFrame):
        df = weekly_df.copy()

        df["lag_1"] = df["qty_sold"].shift(1)
        df["lag_2"] = df["qty_sold"].shift(2)
        df["rolling_4"] = df["qty_sold"].rolling(4).mean()
        df["weekofyear"] = df["move_date"].dt.isocalendar().week.astype(int)

        df = df.dropna().reset_index(drop=True)

        X = df[self.FEATURE_COLS]
        y = df["qty_sold"]

        return X, y

    # ======================================================
    # MODEL
    # ======================================================
    def _train_model(self, X: pd.DataFrame, y: pd.Series):
        model = xgb.XGBRegressor(**self.model_params)
        model.fit(X, y)
           # 🔎 DEBUG SEKALI SAJA
        #print("=== DEBUG XGB TREES ===")
        #print(model.get_booster().trees_to_dataframe().head())
        return model

    # ======================================================
    # WEEKLY FORECASTING
    # ======================================================
    def _recursive_weekly_forecast(
        self,
        history: pd.DataFrame,
        model: xgb.XGBRegressor,
        horizon: int,
    ) -> pd.DataFrame:
        history = history.copy().reset_index(drop=True)

        weekly_preds = []
        weekly_dates = []

        last_date = history["move_date"].iloc[-1]

        for _ in range(horizon):
            next_date = last_date + timedelta(weeks=1)

            features = self._make_feature_row(history, next_date)
            pred = float(model.predict(features)[0])
            pred = max(pred, 0.0)

            weekly_preds.append(pred)
            weekly_dates.append(next_date)

            history = pd.concat(
                [
                    history,
                    pd.DataFrame(
                        {"move_date": [next_date], "qty_sold": [pred]}
                    ),
                ],
                ignore_index=True,
            )

            last_date = next_date

        return pd.DataFrame(
            {
                "forecast_date": weekly_dates,
                "forecast_qty": weekly_preds,
            }
        )

    # ======================================================
    # WEEKLY -> DAILY (FOR BACKTEST)
    # ======================================================
    def _weekly_to_daily(
        self,
        weekly_forecast: pd.DataFrame,
        horizon: int,
    ) -> pd.DataFrame:
        daily_dates = []
        daily_forecasts = []

        for week_date, week_qty in zip(
            weekly_forecast["forecast_date"],
            weekly_forecast["forecast_qty"],
        ):
            # distribute weekly total evenly
            for i in range(7):
                d = week_date + pd.Timedelta(days=i)
                daily_dates.append(d)
                daily_forecasts.append(week_qty / 7)

        return pd.DataFrame(
            {
                "forecast_date": daily_dates[:horizon],
                "forecast_qty": daily_forecasts[:horizon],
            }
        )

    # ======================================================
    # FEATURE ROW
    # ======================================================
    def _make_feature_row(
        self,
        history: pd.DataFrame,
        next_date: pd.Timestamp,
    ) -> pd.DataFrame:
        lag_1 = history["qty_sold"].iloc[-1]
        lag_2 = history["qty_sold"].iloc[-2] if len(history) >= 2 else lag_1
        rolling_4 = history["qty_sold"].tail(4).mean()
        weekofyear = int(next_date.isocalendar().week)

        return pd.DataFrame(
            [
                {
                    "lag_1": lag_1,
                    "lag_2": lag_2,
                    "rolling_4": rolling_4,
                    "weekofyear": weekofyear,
                }
            ]
        )
