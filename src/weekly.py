import pandas as pd


def aggregate_weekly_sales(
    transactions: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate recorded sales into Monday–Sunday product weeks."""
    required = {"StockCode", "InvoiceDate", "Quantity"}
    missing = required - set(transactions.columns)

    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    sales = transactions[[
        "StockCode",
        "InvoiceDate",
        "Quantity",
    ]].copy()

    sales["week_start"] = (
        sales["InvoiceDate"]
        .dt.to_period("W-SUN")
        .dt.start_time
    )

    weekly = (
        sales.groupby(["StockCode", "week_start"], as_index=False)
        .agg(
            units_sold=("Quantity", "sum"),
            transaction_rows=("Quantity", "size"),
        )
        .rename(columns={"StockCode": "stock_code"})
        .sort_values(["stock_code", "week_start"])
        .reset_index(drop=True)
    )

    return weekly

def retain_complete_weeks(
    weekly: pd.DataFrame,
    coverage_start: pd.Timestamp,
    coverage_end: pd.Timestamp,
) -> pd.DataFrame:
    """Keep weeks fully inside the supplied calendar-date coverage."""
    start = pd.Timestamp(coverage_start).normalize()
    end = pd.Timestamp(coverage_end).normalize()

    if start > end:
        raise ValueError("Coverage start must not follow coverage end.")

    week_end = weekly["week_start"] + pd.Timedelta(days=6)

    keep = (
        weekly["week_start"].ge(start)
        & week_end.le(end)
    )

    return weekly.loc[keep].copy().reset_index(drop=True)


def build_week_calendar(
    transactions: pd.DataFrame,
    first_week: pd.Timestamp,
    last_week: pd.Timestamp,
) -> pd.DataFrame:
    """Create a weekly calendar with dataset-level activity indicators."""
    calendar = pd.DataFrame({
        "week_start": pd.date_range(
            start=first_week,
            end=last_week,
            freq="W-MON",
        )
    })

    raw_week_starts = (
        transactions["InvoiceDate"]
        .dt.to_period("W-SUN")
        .dt.start_time
    )

    raw_counts = (
        raw_week_starts.value_counts()
        .rename_axis("week_start")
        .reset_index(name="raw_transaction_rows")
    )

    calendar = calendar.merge(
        raw_counts,
        on="week_start",
        how="left",
        validate="one_to_one",
    )

    calendar["raw_transaction_rows"] = (
        calendar["raw_transaction_rows"]
        .fillna(0)
        .astype("int64")
    )

    calendar["has_raw_transactions"] = (
        calendar["raw_transaction_rows"].gt(0)
    )

    return calendar


def build_product_series(
    weekly: pd.DataFrame,
    calendar: pd.DataFrame,
    stock_code: str,
) -> pd.DataFrame:
    """Build a calendar-aligned sales series for one product."""
    product = weekly.loc[
        weekly["stock_code"].eq(stock_code),
        ["week_start", "units_sold", "transaction_rows"],
    ].copy()

    if product.empty:
        raise ValueError(f"No weekly sales found for product {stock_code}")

    first_sale_week = product["week_start"].min()

    series = calendar.merge(
        product,
        on="week_start",
        how="left",
        validate="one_to_one",
    )

    series.insert(0, "stock_code", stock_code)

    recorded = series["units_sold"].notna()
    dataset_active = series["has_raw_transactions"]
    before_first_sale = series["week_start"].lt(first_sale_week)

    if (recorded & ~dataset_active).any():
        raise ValueError("Product sales conflict with the raw-data calendar.")

    zero_recorded_sales = (
        ~recorded
        & dataset_active
        & ~before_first_sale
    )

    series["sales_status"] = "recorded_sales"
    series.loc[
        zero_recorded_sales, "sales_status"
    ] = "no_recorded_sales"
    series.loc[
        before_first_sale, "sales_status"
    ] = "before_first_sale"
    series.loc[
        ~dataset_active, "sales_status"
    ] = "dataset_gap"

    series.loc[
        zero_recorded_sales,
        ["units_sold", "transaction_rows"],
    ] = 0

    return series


def build_sales_panel(
    weekly: pd.DataFrame,
    calendar: pd.DataFrame,
) -> pd.DataFrame:
    """Combine calendar-aligned weekly series for all products."""
    stock_codes = sorted(weekly["stock_code"].unique())

    if not stock_codes:
        raise ValueError("No products available to build the sales panel.")

    product_series = [
        build_product_series(weekly, calendar, stock_code)
        for stock_code in stock_codes
    ]

    return pd.concat(product_series, ignore_index=True)