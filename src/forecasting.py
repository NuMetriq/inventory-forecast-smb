import pandas as pd


def add_baseline_forecasts(panel: pd.DataFrame) -> pd.DataFrame:
    """Add one-week-ahead forecasts using only preceding weeks."""
    required = {"stock_code", "week_start", "units_sold"}
    missing = required - set(panel.columns)

    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    forecasts = (
        panel.copy()
        .sort_values(["stock_code", "week_start"])
        .reset_index(drop=True)
    )

    if forecasts.duplicated(["stock_code", "week_start"]).any():
        raise ValueError("Duplicate product-week pairs found.")

    week_spacing = forecasts.groupby("stock_code")["week_start"].diff()

    if (
        week_spacing.notna()
        & week_spacing.ne(pd.Timedelta(days=7))
    ).any():
        raise ValueError("Each product must have consecutive calendar weeks.")

    grouped_sales = forecasts.groupby("stock_code")["units_sold"]

    forecasts["forecast_naive"] = grouped_sales.shift(1)

    forecasts["forecast_ma4"] = grouped_sales.transform(
        lambda sales: (
            sales.shift(1)
            .rolling(window=4, min_periods=4)
            .mean()
        )
    )

    return forecasts