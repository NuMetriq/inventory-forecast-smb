import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.forecasting import add_baseline_forecasts
from src.uncertainty import (
    build_lead_time_errors,
    estimate_product_buffers,
)


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
    errors = build_lead_time_errors(forecasts)

    last_week = panel["week_start"].max()
    first_origin = last_week - pd.Timedelta(weeks=7)
    last_origin = last_week - pd.Timedelta(weeks=3)

    evaluation = errors.loc[
        errors["forecast_origin"].between(first_origin, last_origin)
    ].copy()

    if evaluation.empty:
        raise ValueError("No complete outcomes available for evaluation.")

    evaluated = []

    for origin, outcomes in evaluation.groupby("forecast_origin"):
        # Buffer estimation sees only outcomes completed by this origin.
        buffers = estimate_product_buffers(errors, as_of=origin)

        joined = outcomes.merge(
            buffers,
            on="stock_code",
            how="left",
            validate="many_to_one",
        )

        evaluated.append(joined)

    candidates = pd.concat(evaluated, ignore_index=True)
    scored = candidates.dropna(subset=["buffer_units"]).copy()

    if scored.empty:
        raise ValueError("No products have sufficient buffer history.")

    scored["buffered_target"] = (
        scored["forecast_units"] + scored["buffer_units"]
    )

    print(f"Forecast origins: {first_origin.date()} to {last_origin.date()}")
    print(f"Candidate product-origin rows: {len(candidates):,}")
    print(f"Scored product-origin rows: {len(scored):,}")
    print(f"Insufficient-history rows: {len(candidates) - len(scored):,}")

    results = []

    for name, column in [
        ("Forecast only", "forecast_units"),
        ("Forecast plus buffer", "buffered_target"),
    ]:
        target = scored[column]
        actual = scored["actual_units"]

        results.append({
            "method": name,
            "coverage_percent": 100 * actual.le(target).mean(),
            "mean_target_units": target.mean(),
            "mean_shortfall_units": (actual - target).clip(lower=0).mean(),
            "mean_excess_units": (target - actual).clip(lower=0).mean(),
        })

    print("\nTarget comparison:")
    print(
        pd.DataFrame(results).to_string(
            index=False,
            float_format=lambda value: f"{value:,.2f}",
        )
    )

    positive = scored.loc[scored["actual_units"].gt(0)]
    zero_count = scored["actual_units"].eq(0).sum()

    print("\nSales activity in scored windows:")
    print(f"Positive-sales windows: {len(positive):,}")
    print(f"Zero-sales windows: {zero_count:,}")
    print(f"Zero-sales share: {100 * zero_count / len(scored):.2f}%")

    print("\nCoverage on positive-sales windows:")

    for name, column in [
        ("Forecast only", "forecast_units"),
        ("Forecast plus buffer", "buffered_target"),
    ]:
        coverage = (
            100 * positive["actual_units"].le(positive[column]).mean()
        )
        print(f"{name}: {coverage:.2f}%")


if __name__ == "__main__":
    main()