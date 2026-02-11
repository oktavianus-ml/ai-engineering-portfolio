import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.infrastructure.loaders.csv_loader import CsvSalesLoader
from app.application.forecasting.backtesting import backtest_engine
from app.application.forecasting.baseline_forecast_engine import BaselineForecastEngine
from app.application.forecasting.xgb_forecast_engine import XGBForecastEngine
from app.application.chat.product_resolver import ProductResolver


class TmpSalesRepo:
    def __init__(self, df):
        self._df = df

    def get_all_sales(self):
        return self._df


def main():
    # 🔎 Test input
    #product_input = "FD01"
    product_input = "CNI Ginseng Coffee"
    # product_input = "6456"

    # 1️⃣ Load data
    loader = CsvSalesLoader(
        folder_path="data/raw",
        debug=True,
    )
    sales_df = loader.load()

    # 2️⃣ Resolve product
    repo = TmpSalesRepo(sales_df)
    resolver = ProductResolver(repo)

    result = resolver.resolve(product_input)

    if result["status"] == "not_found":
        print("❌ Product tidak ditemukan")
        return

    if result["status"] == "ambiguous":
        print("⚠️ Saya menemukan beberapa varian produk 👇")
        for i, p in enumerate(result["candidates"], 1):
            print(f"{i}. {p['product_code']} – {p['product_name']}")

        while True:
            try:
                user_choice = input("\nPilih nomor atau kode produk: ")
            except KeyboardInterrupt:
                print("\n⛔ Dibatalkan oleh user")
                return

            resolved = resolver.resolve_from_candidates(
                result["candidates"],
                user_choice
            )

            if resolved["status"] == "resolved":
                result = resolved
                break

            print("❌ Pilihan tidak valid. Coba lagi.")

    # ✅ resolved
    product_id = result["product_id"]

    # 3️⃣ Filter product sales
    product_sales_df = sales_df[
        sales_df["product_id"] == product_id
    ].copy()

    print(
        f"\nProduct {product_id} | "
        f"Transaction days: {product_sales_df['move_date'].nunique()} | "
        f"Date range: {product_sales_df['move_date'].min().date()} "
        f"to {product_sales_df['move_date'].max().date()}"
    )

    # 4️⃣ Init engines
    baseline_engine = BaselineForecastEngine()
    xgb_engine = XGBForecastEngine()

    # 5️⃣ Baseline backtest
    baseline_mae = backtest_engine(
        product_sales_df,
        baseline_engine,
        horizon=7,
        min_train_days=14
    )
    print("Baseline MAE:", round(baseline_mae, 2))

    # 6️⃣ XGBoost backtest
    try:
        xgb_mae = backtest_engine(
            product_sales_df,
            xgb_engine,
            horizon=7,
            min_train_days=30
        )
        print("XGBoost MAE :", round(xgb_mae, 2))
    except ValueError as e:
        print("XGBoost skipped:", e)


if __name__ == "__main__":
    main()