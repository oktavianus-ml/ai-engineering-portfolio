import pandas as pd


def make_daily_continuous(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure time series is daily continuous.
    Missing days will be filled with qty_sold = 0.
    """
    df = df.copy()
    df["move_date"] = pd.to_datetime(df["move_date"])

    daily = (
        df.groupby("move_date", as_index=False)["qty_sold"]
        .sum()
    )

    full_dates = pd.date_range(
        start=daily["move_date"].min(),
        end=daily["move_date"].max(),
        freq="D"
    )

    daily = (
        daily
        .set_index("move_date")
        .reindex(full_dates, fill_value=0)
        .rename_axis("move_date")
        .reset_index()
    )

    return daily
