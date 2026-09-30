import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.forecasting import add_baseline_forecasts
from src.inventory_targets import calculate_stock_target
from src.uncertainty import (
    build_lead_time_errors,
    estimate_product_buffers,
)


PANEL_PATH = (
    PROJECT_ROOT / "data" / "processed" / "v2"
    / "weekly_sales_panel.csv"
)

STOCK_CODE = "85123A"
AS_OF = pd.Timestamp("2011-10-10")
HORIZON_WEEKS = 4


def main() -> None:
    panel = pd.read_csv(
        PANEL_PATH,
        dtype={"stock_code": "string"},
        parse_dates=["week_start"],
    )

    # Only completed weeks are available at the forecast date.
    history = panel.loc[
        panel["week_start"].lt(AS_OF)
    ].copy()

    recent_weeks = pd.date_range(
        end=AS_OF - pd.Timedelta(weeks=1),
        periods=4,
        freq="W-MON",
    )

    recent_sales = (
        history.loc[history["stock_code"].eq(STOCK_CODE)]
        .set_index("week_start")["units_sold"]
        .reindex(recent_weeks)
    )

    if recent_sales.isna().any():
        raise ValueError("Four known prior weeks are required.")

    weekly_forecast = float(recent_sales.mean())

    forecasts = add_baseline_forecasts(history)
    errors = build_lead_time_errors(
        forecasts,
        horizon_weeks=HORIZON_WEEKS,
    )
    buffers = estimate_product_buffers(errors, as_of=AS_OF)

    product_buffer = buffers.loc[
        buffers["stock_code"].eq(STOCK_CODE)
    ]

    if (
        product_buffer.empty
        or product_buffer.iloc[0]["buffer_status"] != "estimated"
    ):
        raise ValueError("Insufficient completed error history for a buffer.")

    buffer_row = product_buffer.iloc[0]

    target = calculate_stock_target(
        weekly_forecast=weekly_forecast,
        buffer_units=float(buffer_row["buffer_units"]),
        horizon_weeks=HORIZON_WEEKS,
    )

    print(f"Product: {STOCK_CODE}")
    print(f"Forecast date: {AS_OF.date()}")

    print("\nPrior four weeks of recorded sales:")
    print(recent_sales.to_string())

    print(f"\nWeekly forecast: {weekly_forecast:,.2f} units")
    print(f"Completed error windows: {int(buffer_row['error_windows'])}")
    print(f"Four-week forecast: {target['forecast_units']:,.2f} units")
    print(f"Historical error buffer: {target['buffer_units']:,.2f} units")
    print(f"Four-week stock target: {target['target_units']:,} units")

    product_errors = errors.loc[
        errors["stock_code"].eq(STOCK_CODE)
        & errors["available_from"].le(AS_OF)
    ].copy()

    print("\nHistorical four-week error distribution:")
    print(
        product_errors["error_units"]
        .describe(percentiles=[0.10, 0.50, 0.90])
        .to_string()
    )

    print("\nFive largest historical underforecast errors:")
    print(
        product_errors.nlargest(5, "error_units")[[
            "forecast_origin",
            "available_from",
            "forecast_units",
            "actual_units",
            "error_units",
        ]].to_string(index=False)
    )


if __name__ == "__main__":
    main()