import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.forecasting import add_baseline_forecasts


PANEL_PATH = (
    PROJECT_ROOT / "data" / "processed" / "v2"
    / "weekly_sales_panel.csv"
)


def main() -> None:
    panel = pd.read_csv(
        PANEL_PATH,
        dtype={"stock_code": "string"},
        parse_dates=["week_start"],
    )

    forecasts = add_baseline_forecasts(panel)
    grouped_sales = forecasts.groupby("stock_code")["units_sold"]

    # Each row is a forecast origin: the beginning of that week.
    future_sales = pd.concat(
        [grouped_sales.shift(-offset) for offset in range(4)],
        axis=1,
    )

    forecasts["actual_four_week_units"] = future_sales.sum(
        axis=1,
        min_count=4,
    )

    forecasts["naive_four_week_units"] = (
        4 * forecasts["forecast_naive"]
    )
    forecasts["ma4_four_week_units"] = (
        4 * forecasts["forecast_ma4"]
    )

    last_week = forecasts["week_start"].max()
    first_origin = last_week - pd.Timedelta(weeks=7)
    last_origin = last_week - pd.Timedelta(weeks=3)

    candidates = forecasts.loc[
        forecasts["week_start"].between(first_origin, last_origin)
    ]

    scored = candidates.dropna(subset=[
        "actual_four_week_units",
        "naive_four_week_units",
        "ma4_four_week_units",
    ])

    if scored.empty:
        raise ValueError("No complete four-week windows to evaluate.")

    print(f"Forecast origins: {first_origin.date()} to {last_origin.date()}")
    print(f"Scored product-origin rows: {len(scored):,}")
    print(f"Excluded rows: {len(candidates) - len(scored):,}")

    actual = scored["actual_four_week_units"]
    total_units = actual.sum()
    results = []

    for name, column in [
        ("Naive", "naive_four_week_units"),
        ("Four-week average", "ma4_four_week_units"),
    ]:
        error = scored[column] - actual

        results.append({
            "method": name,
            "MAE_units": error.abs().mean(),
            "WAPE_percent": (
                100 * error.abs().sum() / total_units
                if total_units > 0
                else float("nan")
            ),
            "bias_units": error.mean(),
            "underforecast_percent": 100 * error.lt(0).mean(),
            "shortfall_p90_units": (actual - scored[column]).quantile(0.90),
        })

    print(
        pd.DataFrame(results).to_string(
            index=False,
            float_format=lambda value: f"{value:,.2f}",
        )
    )


if __name__ == "__main__":
    main()