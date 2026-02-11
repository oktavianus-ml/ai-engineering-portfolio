def build_time_features(df):
    df = df.copy()

    df["day"] = df["move_date"].dt.day
    df["month"] = df["move_date"].dt.month
    df["day_of_week"] = df["move_date"].dt.dayofweek

    return df
