import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.forecasting import add_baseline_forecasts
from src.uncertainty import build_lead_time_errors


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

    # Inspect history available at the start of our evaluation period.
    as_of = pd.Timestamp("2011-10-10")

    available = errors.loc[
        errors["available_from"].le(as_of)
    ]

    # Include products with no usable error history in the summary.
    products = pd.Index(
        sorted(panel["stock_code"].unique()),
        name="stock_code",
    )

    counts = (
        available.groupby("stock_code")
        .size()
        .reindex(products, fill_value=0)
        .rename("completed_error_windows")
    )

    print(f"History available as of: {as_of.date()}")
    print(f"Products: {len(counts):,}")

    print("\nCompleted four-week error windows per product:")
    print(counts.describe().to_string())

    print("\nHistory availability:")
    for threshold in [1, 8, 12, 20]:
        print(
            f"Products with at least {threshold} windows: "
            f"{counts.ge(threshold).sum():,}"
        )

    print("\nProduct 10002:")
    print(f"Completed error windows: {counts.loc['10002']}")


if __name__ == "__main__":
    main()