import pandas as pd
import numpy as np
import json
import joblib
from pathlib import Path
import matplotlib.pyplot as plt
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error

# ======================
# CONFIG (YEARLY)
# ======================
MIN_YEARS = 3
FORECAST_YEARS = 1
TRAIN_RATIO = 0.8
MAX_ZERO_RATIO = 0.7

LEAD_TIME_YEARS = 1
DEFAULT_STOCK_YEARS = 1

# ======================
# ROOT & PATH
# ======================
ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = ROOT / "data" / "raw" / "sales_raw.csv"

MODEL_DIR = ROOT / "models" / "yearly"
LOG_DIR = ROOT / "logs" / "yearly"
PLOT_DIR = ROOT / "plots" / "yearly"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
PLOT_DIR.mkdir(parents=True, exist_ok=True)

# ======================
# LOAD → YEARLY
# ======================
def load_yearly_data():
    df = pd.read_csv(DATA_PATH, parse_dates=["move_date"])

    yearly = (
        df.groupby(
            [
                pd.Grouper(key="move_date", freq="YS"),
                "product_code",
            ],
            as_index=False
        )
        .agg({"qty_sold": "sum"})
        .rename(columns={
            "move_date": "year",
            "qty_sold": "qty"
        })
    )

    result = []
    for code, g in yearly.groupby("product_code"):
        g = g.sort_values("year")

        full_range = pd.date_range(
            g["year"].min(),
            g["year"].max(),
            freq="YS"
        )

        g = (
            g.set_index("year")
             .reindex(full_range, fill_value=0)
             .rename_axis("year")
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
    df["lag_2"] = df["qty"].shift(2)
    df["rolling_2"] = df["qty"].rolling(2).mean()
    df["time_idx"] = np.arange(len(df))
    return df.dropna()

# ======================
# TRAIN PER PRODUCT
# ======================
def train_product(product_code, df_yearly):
    df = df_yearly[df_yearly["product_code"] == product_code]

    if df["year"].nunique() < MIN_YEARS:
        print(f"⚠️ Skip {product_code} (data < {MIN_YEARS} tahun)")
        return

    zero_ratio = (df["qty"] == 0).mean()
    if zero_ratio > MAX_ZERO_RATIO:
        print(f"⚠️ Skip {product_code} (intermittent demand)")
        return

    df_feat = make_features(df)

    X = df_feat[["lag_1", "lag_2", "rolling_2", "time_idx"]]
    y = df_feat["qty"]

    split = int(len(df_feat) * TRAIN_RATIO)
    X_train, X_val = X.iloc[:split], X.iloc[split:]
    y_train, y_val = y.iloc[:split], y.iloc[split:]

    model = XGBRegressor(
        n_estimators=150,
        max_depth=3,
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

    for _ in range(FORECAST_YEARS):
        pred = max(0, model.predict(last[X.columns])[0])
        forecasts.append(pred)

        last["lag_2"] = last["lag_1"].values
        last["lag_1"] = pred
        last["rolling_2"] = (last["rolling_2"] + pred) / 2
        last["time_idx"] += 1

    avg_yearly = float(np.mean(forecasts))

    meta = {
        "product_code": product_code,
        "avg_yearly_demand": round(avg_yearly, 2),
        "forecast_years": FORECAST_YEARS,
        "mae_validation": round(mae, 2),
        "bae_validation": round(bae, 2),
        "zero_ratio": round(zero_ratio, 2),
        "reorder_point": round(avg_yearly * LEAD_TIME_YEARS, 0),
        "model_path": str(model_path),
    }

    with open(LOG_DIR / f"{product_code}_meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    # ======================
    # PLOT
    # ======================
    future_years = pd.date_range(
        df["year"].max(),
        periods=FORECAST_YEARS + 1,
        freq="YS"
    )[1:]

    plt.figure(figsize=(8, 4))
    plt.plot(df["year"], df["qty"], marker="o", label="Actual")
    plt.plot(future_years, forecasts, marker="o", label="Forecast")

    plt.title(f"Yearly Forecast {product_code}")
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()

    plt.savefig(PLOT_DIR / f"{product_code}_forecast.png")
    plt.close()

    print(f"✅ {product_code} YEARLY selesai | MAE: {mae:.2f}")

# ======================
# MAIN
# ======================
def main():
    df_yearly = load_yearly_data()

    for product_code in df_yearly["product_code"].unique():
        if "PE" in product_code:
            continue
        try:
            train_product(product_code, df_yearly)
        except Exception as e:
            print(f"❌ {product_code}: {e}")

if __name__ == "__main__":
    main()