import pandas as pd


def build_lead_time_errors(
    forecasts: pd.DataFrame,
    horizon_weeks: int = 4,
) -> pd.DataFrame:
    """Build historical MA4 errors and the dates they become available."""
    if horizon_weeks < 1:
        raise ValueError("Forecast horizon must be at least one week.")

    ordered = (
        forecasts.sort_values(["stock_code", "week_start"])
        .reset_index(drop=True)
        .copy()
    )

    grouped_sales = ordered.groupby("stock_code")["units_sold"]

    future_sales = pd.concat(
        [
            grouped_sales.shift(-offset)
            for offset in range(horizon_weeks)
        ],
        axis=1,
    )

    errors = ordered[["stock_code", "week_start"]].copy()
    errors = errors.rename(columns={"week_start": "forecast_origin"})

    errors["forecast_units"] = (
        horizon_weeks * ordered["forecast_ma4"]
    )

    errors["actual_units"] = future_sales.sum(
        axis=1,
        min_count=horizon_weeks,
    )

    # Positive error means sales exceeded the forecast.
    errors["error_units"] = (
        errors["actual_units"] - errors["forecast_units"]
    )

    errors["available_from"] = (
        errors["forecast_origin"]
        + pd.Timedelta(weeks=horizon_weeks)
    )

    return errors.dropna(
        subset=["forecast_units", "actual_units"]
    ).reset_index(drop=True)


def estimate_product_buffers(
    errors: pd.DataFrame,
    as_of: pd.Timestamp,
    quantile: float = 0.90,
    min_windows: int = 20,
) -> pd.DataFrame:
    """Estimate buffers using only errors available by the forecast date."""
    if not 0 < quantile < 1:
        raise ValueError("Quantile must be between zero and one.")

    if min_windows < 1:
        raise ValueError("Minimum windows must be positive.")

    available = errors.loc[
        errors["available_from"].le(pd.Timestamp(as_of))
    ].copy()

    grouped = available.groupby("stock_code")["error_units"]

    summary = grouped.agg(
        error_windows="count",
    )

    summary["error_quantile_units"] = grouped.quantile(quantile)

    summary["buffer_units"] = (
        summary["error_quantile_units"].clip(lower=0)
    )

    enough_history = summary["error_windows"].ge(min_windows)

    summary.loc[~enough_history, "buffer_units"] = float("nan")
    summary["buffer_status"] = "insufficient_history"
    summary.loc[enough_history, "buffer_status"] = "estimated"

    return summary.reset_index()