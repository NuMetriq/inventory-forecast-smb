import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.cleaning import clean_transactions
from src.weekly import (
    aggregate_weekly_sales,
    retain_complete_weeks,
    build_week_calendar,
    build_product_series,
    build_sales_panel,
)


WORKBOOK_PATH = PROJECT_ROOT / "data" / "raw" / "online_retail_II.xlsx"
SHEET_NAME = "Year 2010-2011"


def main() -> None:
    transactions = pd.read_excel(
        WORKBOOK_PATH,
        sheet_name=SHEET_NAME,
        engine="openpyxl",
        dtype={
            "Invoice": "string",
            "StockCode": "string",
            "Customer ID": "string",
        },
    )

    cleaned, audit = clean_transactions(transactions)

    print("\nCleaning audit:")
    print(audit.to_string(index=False))

    print("\nRetained sales:")
    print(f"Rows: {len(cleaned):,}")
    print(f"Products: {cleaned['StockCode'].nunique():,}")
    print(f"Units sold: {cleaned['Quantity'].sum():,.0f}")
    print(
        "Rows without customer ID: "
        f"{cleaned['Customer ID'].isna().sum():,}"
    )
    print(
        "Exact duplicate rows retained: "
        f"{cleaned.duplicated().sum():,}"
    )

    removed = int(audit["rows_removed"].sum())
    if len(transactions) != len(cleaned) + removed:
        raise AssertionError("Cleaning audit does not reconcile.")

    print("\nAudit reconciles: input rows = retained rows + removed rows.")

    weekly = aggregate_weekly_sales(cleaned)

    print("\nWeekly sales sample:")
    print(weekly.head(10).to_string(index=False))

    print(f"\nProduct-week rows: {len(weekly):,}")
    print(f"First week: {weekly['week_start'].min()}")
    print(f"Last week: {weekly['week_start'].max()}")

    if weekly["units_sold"].sum() != cleaned["Quantity"].sum():
        raise AssertionError("Weekly aggregation changed total units.")

    print("Weekly totals reconcile with cleaned transaction units.")

    complete = retain_complete_weeks(
        weekly,
        coverage_start=transactions["InvoiceDate"].min(),
        coverage_end=transactions["InvoiceDate"].max(),
    )

    print("\nComplete-week sales:")
    print(f"Product-week rows: {len(complete):,}")
    print(f"Calendar weeks represented: {complete['week_start'].nunique()}")
    print(f"First week: {complete['week_start'].min()}")
    print(f"Last week: {complete['week_start'].max()}")

    excluded_units = (
        weekly["units_sold"].sum()
        - complete["units_sold"].sum()
    )
    print(f"Units excluded in partial weeks: {excluded_units:,.0f}")

    expected_weeks = pd.date_range(
        start="2010-12-06",
        end="2011-11-28",
        freq="W-MON",
    )

    observed_weeks = pd.DatetimeIndex(
        complete["week_start"].unique()
    )
    missing_weeks = expected_weeks.difference(observed_weeks)

    print("\nWeeks with no retained sales:")

    for week_start in missing_weeks:
        next_week = week_start + pd.Timedelta(days=7)

        raw_mask = (
            transactions["InvoiceDate"].ge(week_start)
            & transactions["InvoiceDate"].lt(next_week)
        )
        clean_mask = (
            cleaned["InvoiceDate"].ge(week_start)
            & cleaned["InvoiceDate"].lt(next_week)
        )

        print(f"\nWeek starting: {week_start.date()}")
        print(f"Raw transaction rows: {raw_mask.sum():,}")
        print(f"Retained sales rows: {clean_mask.sum():,}")

    calendar = build_week_calendar(
        transactions,
        first_week=complete["week_start"].min(),
        last_week=complete["week_start"].max(),
    )

    print("\nCalendar summary:")
    print(f"Calendar weeks: {len(calendar)}")
    print(
        "Weeks with raw transactions: "
        f"{calendar['has_raw_transactions'].sum()}"
    )

    print("\nWeeks without raw transactions:")
    print(
        calendar.loc[~calendar["has_raw_transactions"]]
        .to_string(index=False)
    )

    product_series = build_product_series(
        weekly,
        calendar,
        stock_code="10002",
    )

    print("\nProduct 10002 — first eight calendar weeks:")
    print(
        product_series[[
            "week_start",
            "units_sold",
            "sales_status",
        ]].head(8).to_string(index=False)
    )

    print("\nProduct 10002 — status counts:")
    print(product_series["sales_status"].value_counts().to_string())

    panel = build_sales_panel(weekly, calendar)

    expected_rows = weekly["stock_code"].nunique() * len(calendar)

    if len(panel) != expected_rows:
        raise AssertionError("Unexpected number of product-week rows.")

    if panel.duplicated(["stock_code", "week_start"]).any():
        raise AssertionError("Duplicate product-week pairs found.")

    if panel["units_sold"].sum() != complete["units_sold"].sum():
        raise AssertionError("Panel construction changed total sales.")

    print("\nSales panel summary:")
    print(f"Products: {panel['stock_code'].nunique():,}")
    print(f"Weeks: {panel['week_start'].nunique()}")
    print(f"Rows: {len(panel):,}")

    print("\nSales status counts:")
    print(panel["sales_status"].value_counts().to_string())

    print("\nPanel checks passed.")

    output_dir = PROJECT_ROOT / "data" / "processed" / "v2"
    output_dir.mkdir(parents=True, exist_ok=True)

    product_descriptions = cleaned[[
        "StockCode",
        "Description",
        "InvoiceDate",
    ]].copy()

    product_descriptions["Description"] = (
        product_descriptions["Description"]
        .astype("string")
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
    )

    valid_description = (
        product_descriptions["Description"].notna()
        & product_descriptions["Description"].ne("")
    )

    product_descriptions = (
        product_descriptions.loc[valid_description]
        .rename(columns={
            "StockCode": "stock_code",
            "Description": "description",
            "InvoiceDate": "observed_at",
        })
        .drop_duplicates()
        .sort_values(["stock_code", "observed_at", "description"])
        .reset_index(drop=True)
    )

    outputs = {
        "weekly_sales_panel.csv": panel,
        "week_calendar.csv": calendar,
        "cleaning_audit.csv": audit,
        "product_descriptions.csv": product_descriptions,
    }

    for filename, table in outputs.items():
        output_path = output_dir / filename
        table.to_csv(output_path, index=False)
        print(f"Saved: {output_path}")

    # Read the saved panel back to verify the important data properties.
    saved_panel = pd.read_csv(
        output_dir / "weekly_sales_panel.csv",
        dtype={"stock_code": "string"},
        parse_dates=["week_start"],
    )

    if len(saved_panel) != len(panel):
        raise AssertionError("Saved panel row count changed.")

    if saved_panel["units_sold"].isna().sum() != panel["units_sold"].isna().sum():
        raise AssertionError("Missing sales values changed during saving.")

    if saved_panel["units_sold"].sum() != panel["units_sold"].sum():
        raise AssertionError("Sales totals changed during saving.")

    print("Saved panel verified.")


if __name__ == "__main__":
    main()