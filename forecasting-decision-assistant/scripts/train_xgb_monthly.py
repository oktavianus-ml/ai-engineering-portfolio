import pandas as pd
import numpy as np
import json
import joblib
from pathlib import Path
import matplotlib.pyplot as plt
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error

# ======================
# CONFIG (MONTHLY)
# ======================
MIN_MONTHS = 12
FORECAST_MONTHS = 3
TRAIN_RATIO = 0.8
MAX_ZERO_RATIO = 0.6

DEFAULT_STOCK_MONTHS = 3
LEAD_TIME_MONTHS = 1

# ======================
# ROOT & PATH
# ======================
ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = ROOT / "data" / "raw" / "sales_raw.csv"

MODEL_DIR = ROOT / "models" / "monthly"
LOG_DIR = ROOT / "logs" / "monthly"
PLOT_DIR = ROOT / "plots" / "monthly"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
PLOT_DIR.mkdir(parents=True, exist_ok=True)


# ======================
# LOAD → MONTHLY
# ======================
def load_monthly_data():
    df = pd.read_csv(DATA_PATH, parse_dates=["move_date"])

    monthly = (
        df.groupby(
            [
                pd.Grouper(key="move_date", freq="MS"),
                "product_code"
            ],
            as_index=False
        )
        .agg({"qty_sold": "sum"})
        .rename(columns={
            "move_date": "month",
            "qty_sold": "qty"
        })
    )

    result = []
    for code, g in monthly.groupby("product_code"):
        g = g.sort_values("month")

        full_range = pd.date_range(
            g["month"].min(),
            g["month"].max(),
            freq="MS"
        )

        g = (
            g.set_index("month")
             .reindex(full_range, fill_value=0)
             .rename_axis("month")
             .reset_index()
        )

        g["product_code"] = code
        result.append(g)

    return pd.concat(result, ignore_index=True)


# ======================
# FEATURES
# ======================
def make_features(df):
    df = df.copy()
    df["lag_1"] = df["qty"].shift(1)
    df["lag_3"] = df["qty"].shift(3)
    df["rolling_3"] = df["qty"].rolling(3).mean()
    df["time_idx"] = np.arange(len(df))
    return df.dropna()


# ======================
# TRAIN PER PRODUCT
# ======================
def train_product(product_code, df_monthly):
    df = df_monthly[df_monthly["product_code"] == product_code]

    if df["month"].nunique() < MIN_MONTHS:
        return

    zero_ratio = (df["qty"] == 0).mean()
    if zero_ratio > MAX_ZERO_RATIO:
        return

    df_feat = make_features(df)

    X = df_feat[["lag_1", "lag_3", "rolling_3", "time_idx"]]
    y = df_feat["qty"]

    split = int(len(df_feat) * TRAIN_RATIO)
    X_train, X_val = X.iloc[:split], X.iloc[split:]
    y_train, y_val = y.iloc[:split], y.iloc[split:]

    model = XGBRegressor(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        objective="reg:squarederror",
        random_state=42
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_val)
    mae = mean_absolute_error(y_val, y_pred)
    bae = float((y_pred - y_val).mean())

    model_path = MODEL_DIR / f"{product_code}_xgb.pkl"
    joblib.dump(model, model_path)

    # ======================
    # FORECAST
    # ======================
    last = df_feat.iloc[-1:].copy()
    forecasts = []

    for _ in range(FORECAST_MONTHS):
        pred = max(0, model.predict(last[X.columns])[0])
        forecasts.append(pred)

        last["lag_3"] = last["lag_1"].values
        last["lag_1"] = pred
        last["rolling_3"] = (last["rolling_3"] * 2 + pred) / 3
        last["time_idx"] += 1

    avg_monthly = float(np.mean(forecasts))

    meta = {
        "product_code": product_code,
        "avg_monthly_demand": round(avg_monthly, 2),
        "forecast_months": FORECAST_MONTHS,
        "mae_validation": round(mae, 2),
        "bae_validation": round(bae, 2),
        "zero_ratio": round(zero_ratio, 2),
        "reorder_point": round(avg_monthly * LEAD_TIME_MONTHS, 0),
        "model_path": str(model_path)
    }

    with open(LOG_DIR / f"{product_code}_meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    # ======================
    # PLOT (Telegram-ready)
    # ======================
    future_months = pd.date_range(
        df["month"].max(),
        periods=FORECAST_MONTHS + 1,
        freq="MS"
    )[1:]

    plt.figure(figsize=(10, 4))
    plt.plot(df["month"].tail(12), df["qty"].tail(12), label="Actual", marker="o")
    plt.plot(future_months, forecasts, label="Forecast", marker="o")

    plt.title(f"Monthly Forecast – {product_code}")
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()

    plt.savefig(PLOT_DIR / f"{product_code}_forecast.png")
    plt.close()


# ======================
# MAIN
# ======================
def main():
    df_monthly = load_monthly_data()

    for product_code in df_monthly["product_code"].unique():
        if "PE" in product_code:
            continue
        try:
            train_product(product_code, df_monthly)
        except Exception as e:
            print(f"❌ {product_code}: {e}")


if __name__ == "__main__":
    main()