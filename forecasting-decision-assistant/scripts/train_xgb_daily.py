import pandas as pd
import numpy as np
import json
import joblib
from pathlib import Path
import matplotlib.pyplot as plt
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error

# ======================
# CONFIG
# ======================
MIN_DAYS = 90
FORECAST_DAYS = 7
TRAIN_RATIO = 0.8
MAX_ZERO_RATIO = 0.6
HISTORY_PLOT_DAYS = 60

LEAD_TIME_DAYS = 7
DEFAULT_STOCK_DAYS = 14

# ======================
# ROOT & PATH
# ======================
ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = ROOT / "Data" / "Raw" / "sales_raw.csv"
MODEL_DIR = ROOT / "models" / "daily"
LOG_DIR = ROOT / "logs" / "daily"
PLOT_DIR = ROOT / "plots" / "daily"

MODEL_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)
PLOT_DIR.mkdir(exist_ok=True)


def build_sales_raw_if_needed():
    raw_dir = ROOT / "data" / "raw"
    output_path = raw_dir / "sales_raw.csv"

    csv_files = list(raw_dir.glob("*.csv"))
    csv_files = [f for f in csv_files if f.name != "sales_raw.csv"]

    if not csv_files:
        raise FileNotFoundError("❌ Tidak ada file CSV raw di data/raw")

    # Build jika belum ada
    if not output_path.exists():
        print("🔄 sales_raw.csv belum ada, membuat otomatis...")
    else:
        print("ℹ️ sales_raw.csv sudah ada, gunakan yang ada")
        return output_path

    dfs = []
    for f in csv_files:
        print(f"📥 Load {f.name}")
        dfs.append(pd.read_csv(f))

    combined = pd.concat(dfs, ignore_index=True).drop_duplicates()
    combined.to_csv(output_path, index=False)

    print(f"✅ sales_raw.csv dibuat: {output_path}")
    return output_path


# ======================
# PREPROCESS RAW → DAILY
# ======================
def load_daily_data():
    df = pd.read_csv(DATA_PATH, parse_dates=["move_date"])

    daily = (
        df.groupby(["move_date", "product_code"], as_index=False)
          .agg({"qty_sold": "sum"})
    )

    daily.rename(columns={
        "move_date": "date",
        "qty_sold": "qty"
    }, inplace=True)

    result = []
    for code, g in daily.groupby("product_code"):
        g = g.sort_values("date")
        full_range = pd.date_range(g["date"].min(), g["date"].max(), freq="D")

        g = (
            g.set_index("date")
             .reindex(full_range, fill_value=0)
             .rename_axis("date")
             .reset_index()
        )
        g["product_code"] = code
        result.append(g)

    return pd.concat(result, ignore_index=True)


# ======================
# FEATURE ENGINEERING
# ======================
def make_features(df):
    df = df.copy()
    df["lag_1"] = df["qty"].shift(1)
    df["lag_7"] = df["qty"].shift(7)
    df["rolling_7"] = df["qty"].rolling(7).mean()
    df["time_idx"] = (df["date"] - df["date"].min()).dt.days
    return df.dropna()


# ======================
# TRAIN PER PRODUCT
# ======================
def train_product(product_code, df_daily):
    df = df_daily[df_daily["product_code"] == product_code].sort_values("date")

    if df["date"].nunique() < MIN_DAYS:
        print(f"⚠️ Skip {product_code} (data < {MIN_DAYS} hari)")
        return

    zero_ratio = (df["qty"] == 0).mean()
    if zero_ratio > MAX_ZERO_RATIO:
        print(f"⚠️ Skip {product_code} (intermittent demand)")
        return

    df_feat = make_features(df)

    X = df_feat[["lag_1", "lag_7", "rolling_7", "time_idx"]]
    y = df_feat["qty"]

    split_idx = int(len(df_feat) * TRAIN_RATIO)
    X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]

    model = XGBRegressor(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        objective="reg:squarederror",
        random_state=42
    )

    model.fit(
        X_train,
        y_train,
        eval_set=[(X_val, y_val)],
        eval_metric="mae",
        verbose=False
    )

    y_val_pred = model.predict(X_val)
    mae = mean_absolute_error(y_val, y_val_pred)

    model_path = MODEL_DIR / f"{product_code}_xgb.pkl"
    joblib.dump(model, model_path)

    # ======================
    # FORECAST
    # ======================
    last_row = df_feat.iloc[-1:].copy()
    forecasts = []

    for _ in range(FORECAST_DAYS):
        X_future = last_row[X.columns]
        y_pred = max(0, model.predict(X_future)[0])  # clamp
        forecasts.append(y_pred)

        last_row["lag_7"] = last_row["lag_1"].values
        last_row["lag_1"] = y_pred
        last_row["rolling_7"] = (last_row["rolling_7"] * 6 + y_pred) / 7
        last_row["time_idx"] += 1

    avg_daily = float(np.mean(forecasts))

    current_stock = avg_daily * DEFAULT_STOCK_DAYS
    stock_coverage = round(current_stock / avg_daily, 1)
    reorder_point = round(avg_daily * LEAD_TIME_DAYS, 0)

    meta = {
        "product_code": product_code,
        "avg_daily_demand": round(avg_daily, 2),
        "forecast_days": FORECAST_DAYS,
        "mae_validation": round(mae, 2),
        "zero_ratio": round(zero_ratio, 2),
        "current_stock": round(current_stock, 0),
        "stock_coverage_days": stock_coverage,
        "lead_time_days": LEAD_TIME_DAYS,
        "reorder_point": reorder_point,
        "model_path": str(model_path)
    }

    with open(LOG_DIR / f"{product_code}_meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    # ======================
    # PLOT
    # ======================
    history_days = min(HISTORY_PLOT_DAYS, len(df))
    future_dates = pd.date_range(df["date"].max() + pd.Timedelta(days=1), periods=FORECAST_DAYS)

    plt.figure(figsize=(10, 4))
    plt.plot(df["date"].tail(history_days), df["qty"].tail(history_days), label="Actual")
    plt.plot(future_dates, forecasts, label="Forecast", marker="o")
    plt.title(f"Forecast {product_code}")
    plt.legend()
    plt.tight_layout()
    plt.savefig(PLOT_DIR / f"{product_code}_forecast.png")
    plt.close()

    print(f"✅ {product_code} selesai | MAE: {mae:.2f}")


# ======================
# MAIN
# ======================
def main():

    # ======================
    # AUTO BUILD RAW DATA
    # ======================
    build_sales_raw_if_needed()


    df_daily = load_daily_data()

    for product_code in df_daily["product_code"].unique():
        if "PE" in product_code:
            continue

        try:
            train_product(product_code, df_daily)
        except Exception as e:
            print(f"❌ Error {product_code}: {e}")


if __name__ == "__main__":
    main()