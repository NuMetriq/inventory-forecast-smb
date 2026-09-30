import math


def calculate_stock_target(
    weekly_forecast: float,
    buffer_units: float,
    horizon_weeks: int = 4,
) -> dict[str, float | int]:
    """Calculate a whole-unit target for a fixed coverage horizon."""
    if not math.isfinite(weekly_forecast) or weekly_forecast < 0:
        raise ValueError("Weekly forecast must be finite and nonnegative.")

    if not math.isfinite(buffer_units) or buffer_units < 0:
        raise ValueError("Buffer must be finite and nonnegative.")

    if (
        isinstance(horizon_weeks, bool)
        or not isinstance(horizon_weeks, int)
        or horizon_weeks < 1
    ):
        raise ValueError("Horizon must be a positive integer.")

    forecast_units = weekly_forecast * horizon_weeks
    target_units = math.ceil(forecast_units + buffer_units)

    return {
        "horizon_weeks": horizon_weeks,
        "forecast_units": forecast_units,
        "buffer_units": buffer_units,
        "target_units": target_units,
    }