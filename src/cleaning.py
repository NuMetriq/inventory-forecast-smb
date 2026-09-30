import pandas as pd


EXCLUDED_STOCK_CODES = {
    "POST",
    "DOT",
    "C2",
    "D",
    "BANK CHARGES",
    "AMAZONFEE",
    "CRUK",
    "B",
    "M",
    "S",
}


def clean_transactions(
    transactions: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return eligible sales and a sequential row-count audit."""
    required_columns = {
        "Invoice",
        "StockCode",
        "Quantity",
        "InvoiceDate",
        "Price",
    }

    missing = required_columns - set(transactions.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    cleaned = transactions.copy()

    for column in ["Invoice", "StockCode"]:
        cleaned[column] = (
            cleaned[column]
            .astype("string")
            .str.strip()
            .str.upper()
        )

    audit = [{
        "step": "Input",
        "rows_removed": 0,
        "rows_remaining": len(cleaned),
    }]

    rules = [
        (
            "Missing or blank identifiers",
            cleaned["Invoice"].fillna("").eq("")
            | cleaned["StockCode"].fillna("").eq(""),
        ),
        (
            "Cancellation invoices",
            cleaned["Invoice"].str.startswith("C", na=False),
        ),
        (
            "Missing or nonpositive quantity",
            cleaned["Quantity"].isna() | cleaned["Quantity"].le(0),
        ),
        (
            "Missing or nonpositive price",
            cleaned["Price"].isna() | cleaned["Price"].le(0),
        ),
        (
            "Missing transaction date",
            cleaned["InvoiceDate"].isna(),
        ),
        (
            "Excluded non-merchandise or ambiguous codes",
            cleaned["StockCode"].isin(EXCLUDED_STOCK_CODES),
        ),
        (
            "Gift vouchers",
            cleaned["StockCode"].str.startswith("GIFT_", na=False),
        ),
    ]

    for label, exclusion_mask in rules:
        rows_before = len(cleaned)

        # Apply each rule only to rows that survived earlier rules.
        exclude = exclusion_mask.loc[cleaned.index]
        cleaned = cleaned.loc[~exclude].copy()

        audit.append({
            "step": label,
            "rows_removed": rows_before - len(cleaned),
            "rows_remaining": len(cleaned),
        })

    return cleaned, pd.DataFrame(audit)