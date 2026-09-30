import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.forecasting import add_baseline_forecasts


PANEL_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "v2"
    / "weekly_sales_panel.csv"
)


def main() -> None:
    panel = pd.read_csv(
        PANEL_PATH,
        dtype={"stock_code": "string"},
        parse_dates=["week_start"],
    )

    forecasts = add_baseline_forecasts(panel)

    last_week = forecasts["week_start"].max()
    first_test_week = last_week - pd.Timedelta(weeks=7)

    test = forecasts.loc[
        forecasts["week_start"].between(first_test_week, last_week)
    ].copy()

    # Both methods are scored on the same known actuals and forecasts.
    scored = test.dropna(subset=[
        "units_sold",
        "forecast_naive",
        "forecast_ma4",
    ])

    if scored.empty:
        raise ValueError("No common product-week rows available for scoring.")

    print(f"Evaluation: {first_test_week.date()} to {last_week.date()}")
    print(f"Candidate product-week rows: {len(test):,}")
    print(f"Scored product-week rows: {len(scored):,}")
    print(f"Excluded rows: {len(test) - len(scored):,}")
    print(f"Products scored: {scored['stock_code'].nunique():,}")

    actual = scored["units_sold"]
    total_units = actual.sum()

    results = []

    for name, column in [
        ("Naive", "forecast_naive"),
        ("Four-week average", "forecast_ma4"),
    ]:
        error = scored[column] - actual

        results.append({
            "method": name,
            "MAE": error.abs().mean(),
            "RMSE": (error.pow(2).mean()) ** 0.5,
            "WAPE_percent": (
                100 * error.abs().sum() / total_units
                if total_units > 0
                else float("nan")
            ),
            "bias_units": error.mean(),
        })

    print("\nForecast results:")
    print(
        pd.DataFrame(results).to_string(
            index=False,
            float_format=lambda value: f"{value:,.2f}",
        )
    )

    weekly_results = []

    for week_start, group in scored.groupby("week_start"):
        actual = group["units_sold"]
        total_units = actual.sum()

        row = {
            "week_start": week_start.date(),
            "products_scored": len(group),
            "actual_units": total_units,
        }

        for label, column in [
            ("naive", "forecast_naive"),
            ("ma4", "forecast_ma4"),
        ]:
            absolute_error = (group[column] - actual).abs()

            row[f"{label}_WAPE"] = (
                100 * absolute_error.sum() / total_units
                if total_units > 0
                else float("nan")
            )

        weekly_results.append(row)

    print("\nWeekly comparison — WAPE (%):")
    print(
        pd.DataFrame(weekly_results).to_string(
            index=False,
            float_format=lambda value: f"{value:,.2f}",
        )
    )


if __name__ == "__main__":
    main()