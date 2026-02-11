import pandas as pd
import numpy as np
import json
import joblib
from pathlib import Path
import matplotlib.pyplot as plt
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error
import matplotlib.dates as mdates

# ======================
# CONFIG (WEEKLY)
# ======================
MIN_WEEKS = 26              # ± 6 bulan
FORECAST_WEEKS = 4          # 1 bulan ke depan
TRAIN_RATIO = 0.8
MAX_ZERO_RATIO = 0.6
HISTORY_PLOT_WEEKS = 26

LEAD_TIME_WEEKS = 1
DEFAULT_STOCK_WEEKS = 4

# ======================
# ROOT & PATH
# ======================
ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = ROOT / "Data" / "Raw" / "sales_raw.csv"
MODEL_DIR = ROOT / "models" / "weekly"
LOG_DIR = ROOT / "logs" / "weekly"
PLOT_DIR = ROOT / "plots" / "weekly"

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
def load_weekly_data():
    df = pd.read_csv(DATA_PATH, parse_dates=["move_date"])

    weekly = (
        df.groupby(
            [
                pd.Grouper(key="move_date", freq="W-MON"),
                "product_code",
            ],
            as_index=False
        )
        .agg({"qty_sold": "sum"})
    )

    weekly.rename(
        columns={
            "move_date": "week",
            "qty_sold": "qty",
        },
        inplace=True,
    )

    result = []
    for code, g in weekly.groupby("product_code"):
        g = g.sort_values("week")

        full_range = pd.date_range(
            g["week"].min(),
            g["week"].max(),
            freq="W-MON"
        )

        g = (
            g.set_index("week")
             .reindex(full_range, fill_value=0)
             .rename_axis("week")
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
    df["lag_1"] = df["qty"].shift(1)      # minggu lalu
    df["lag_4"] = df["qty"].shift(4)      # 1 bulan lalu
    df["rolling_4"] = df["qty"].rolling(4).mean()
    df["time_idx"] = np.arange(len(df))

    return df.dropna()

# ======================
# TRAIN PER PRODUCT
# ======================
def train_product(product_code, df_weekly):
    df = df_weekly[df_weekly["product_code"] == product_code].sort_values("week")

    if df["week"].nunique() < MIN_WEEKS:
        print(f"⚠️ Skip {product_code} (data < {MIN_WEEKS} minggu)")
        return

    zero_ratio = (df["qty"] == 0).mean()
    if zero_ratio > MAX_ZERO_RATIO:
        print(f"⚠️ Skip {product_code} (intermittent demand)")
        return

    df_feat = make_features(df)

    X = df_feat[["lag_1", "lag_4", "rolling_4", "time_idx"]]
    y = df_feat["qty"]

    split_idx = int(len(df_feat) * TRAIN_RATIO)
    X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]

    model = XGBRegressor(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        objective="reg:squarederror",
        random_state=42,
    )

    model.fit(
        X_train,
        y_train,
        eval_set=[(X_val, y_val)],
        eval_metric="mae",
        verbose=False,
    )

    y_val_pred = model.predict(X_val)

    mae = mean_absolute_error(y_val, y_val_pred)
    bae = float((y_val_pred - y_val).mean())

    model_path = MODEL_DIR / f"{product_code}_xgb.pkl"
    joblib.dump(model, model_path)

    # ======================
    # FORECAST
    # ======================
    last_row = df_feat.iloc[-1:].copy()
    forecasts = []

    for _ in range(FORECAST_WEEKS):
        X_future = last_row[X.columns]
        y_pred = max(0, model.predict(X_future)[0])
        forecasts.append(y_pred)

        last_row["lag_4"] = last_row["lag_1"].values
        last_row["lag_1"] = y_pred
        last_row["rolling_4"] = (last_row["rolling_4"] * 3 + y_pred) / 4
        last_row["time_idx"] += 1



    #KPI → WEEKLY
    avg_weekly = float(np.mean(forecasts))

    current_stock = avg_weekly * DEFAULT_STOCK_WEEKS
    stock_coverage = round(current_stock / avg_weekly, 1)
    reorder_point = round(avg_weekly * LEAD_TIME_WEEKS, 0)

    meta = {
        "product_code": product_code,
        "avg_weekly_demand": round(avg_weekly, 2),
        "forecast_weeks": FORECAST_WEEKS,
        "mae_validation": round(mae, 2),
        "bae_validation": round(bae, 2),
        "zero_ratio": round(zero_ratio, 2),
        "current_stock": round(current_stock, 0),
        "stock_coverage_weeks": stock_coverage,
        "lead_time_weeks": LEAD_TIME_WEEKS,
        "reorder_point": reorder_point,
        "model_path": str(model_path),
    }

    with open(LOG_DIR / f"{product_code}_meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    # ======================
    # PLOT
    # ======================
    history_weeks = min(HISTORY_PLOT_WEEKS, len(df))
    future_weeks = pd.date_range(
        df["week"].max() + pd.Timedelta(weeks=1),
        periods=FORECAST_WEEKS,
        freq="W-MON",
    )

    plt.figure(figsize=(12, 5))

    # Actual
    plt.plot(
        df["week"].tail(history_weeks),
        df["qty"].tail(history_weeks),
        label="Actual",
        marker="o"
    )

    # Forecast
    plt.plot(
        future_weeks,
        forecasts,
        label="Forecast",
        marker="o"
    )

    ax = plt.gca()

    # =========================
    # WEEKLY TICKS
    # =========================
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO, interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m (W%W)"))

    # Rotate labels (VERTICAL)
    plt.xticks(rotation=90)

    plt.title(f"Weekly Forecast {product_code}")
    plt.xlabel("Week")
    plt.ylabel("Quantity")
    plt.legend()
    plt.grid(alpha=0.3)

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

    df_weekly = load_weekly_data()

    for product_code in df_weekly["product_code"].unique():
        if "PE" in product_code:
            continue

        try:
            train_product(product_code, df_weekly)
        except Exception as e:
            print(f"❌ Error {product_code}: {e}")


if __name__ == "__main__":
    main()