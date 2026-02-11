import pandas as pd
from sklearn.metrics import mean_absolute_error
from app.domain.forecasting.utils import make_daily_continuous

def backtest_engine(
    sales_df: pd.DataFrame,
    engine,
    horizon: int = 7,
    min_train_days: int = 30,
) -> float:
    """
    Rolling backtest for time series forecasting.
    Returns mean MAE across rolling windows.
    """

    # 1️⃣ Validasi input
    required_cols = {"move_date", "qty_sold"}
    missing = required_cols - set(sales_df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    sales_df = sales_df.copy()
    sales_df["move_date"] = pd.to_datetime(sales_df["move_date"])

    # 🔥 2️⃣ Daily continuous (HARUS SAMA DENGAN ENGINE)
    daily = make_daily_continuous(sales_df)

    n_days = len(daily)
    max_i = n_days - horizon

    # 3️⃣ Early guard
    if max_i <= min_train_days:
        raise ValueError(
            "Not enough data for backtesting. "
            f"len(daily)={n_days}, "
            f"min_train_days={min_train_days}, "
            f"horizon={horizon}"
        )

    maes: list[float] = []

    # 4️⃣ Rolling backtest
    for i in range(min_train_days, max_i):
        train_df = daily.iloc[:i]
        test_df = daily.iloc[i : i + horizon]

        forecast_df = engine.run(
            sales_df=train_df,
            horizon=horizon
        )

        # safety check
        if (
            forecast_df is None
            or len(forecast_df) != horizon
            or "forecast_qty" not in forecast_df.columns
        ):
            continue

        y_true = test_df["qty_sold"].to_numpy()
        y_pred = forecast_df["forecast_qty"].to_numpy()

        mae = mean_absolute_error(y_true, y_pred)
        maes.append(mae)

    # 5️⃣ Final guard
    if not maes:
        raise ValueError(
            "Backtest completed but produced no MAE values. "
            "Check forecasting engine output."
        )

    return float(sum(maes) / len(maes))