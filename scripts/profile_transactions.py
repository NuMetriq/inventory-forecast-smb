from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
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

    print(f"Sheet: {SHEET_NAME}")
    print(f"Rows: {len(transactions):,}")
    print(f"Unique products: {transactions['StockCode'].nunique():,}")
    print(f"First transaction: {transactions['InvoiceDate'].min()}")
    print(f"Last transaction: {transactions['InvoiceDate'].max()}")

    print("\nMissing values by column:")
    print(transactions.isna().sum().to_string())

    cancelled = (
        transactions["Invoice"]
        .str.strip()
        .str.upper()
        .str.startswith("C", na=False)
    )

    print("\nRecords to investigate:")
    print(f"Cancellation invoices: {cancelled.sum():,}")
    print(f"Negative quantities: {transactions['Quantity'].lt(0).sum():,}")
    print(f"Zero quantities: {transactions['Quantity'].eq(0).sum():,}")
    print(f"Nonpositive prices: {transactions['Price'].le(0).sum():,}")
    print(f"Exact duplicate rows: {transactions.duplicated().sum():,}")

    print("\nTop 10 countries by transaction-row count:")
    print(
        transactions["Country"]
        .value_counts(dropna=False)
        .head(10)
        .to_string()
    )

    print("\n20 most frequent product codes and descriptions:")
    product_counts = (
        transactions.groupby(
            ["StockCode", "Description"],
            dropna=False,
        )
        .size()
        .sort_values(ascending=False)
        .head(20)
    )
    print(product_counts.to_string())

    # A review flag, not a rule for deleting records.
    unusual_codes = ~transactions["StockCode"].str.fullmatch(
        r"\d{5}[A-Za-z]*",
        na=False,
    )

    print("\nProduct codes requiring review:")
    unusual_summary = (
        transactions.loc[unusual_codes]
        .groupby(["StockCode", "Description"], dropna=False)
        .size()
        .sort_values(ascending=False)
        .head(30)
    )
    print(unusual_summary.to_string())

    duplicate_rows = transactions.loc[
        transactions.duplicated(keep=False)
    ]

    print("\nSample of exact duplicate rows:")
    print(duplicate_rows.head(12).to_string(index=False))


if __name__ == "__main__":
    main()