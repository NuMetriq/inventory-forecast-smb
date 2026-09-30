import unittest

import pandas as pd

from src.weekly import build_product_series


class TestProductSeries(unittest.TestCase):
    def test_distinguishes_sales_zeros_and_unknowns(self):
        calendar = pd.DataFrame({
            "week_start": pd.date_range(
                "2024-01-01",
                periods=5,
                freq="W-MON",
            ),
            "raw_transaction_rows": [10, 10, 10, 0, 10],
            "has_raw_transactions": [True, True, True, False, True],
        })

        weekly = pd.DataFrame({
            "stock_code": ["A", "A"],
            "week_start": pd.to_datetime([
                "2024-01-08",
                "2024-01-29",
            ]),
            "units_sold": [5, 3],
            "transaction_rows": [1, 1],
        })

        result = build_product_series(weekly, calendar, "A")

        self.assertEqual(len(result), 5)
        self.assertEqual(
            result["sales_status"].tolist(),
            [
                "before_first_sale",
                "recorded_sales",
                "no_recorded_sales",
                "dataset_gap",
                "recorded_sales",
            ],
        )

        units = result["units_sold"]
        self.assertTrue(pd.isna(units.iloc[0]))
        self.assertEqual(units.iloc[1], 5)
        self.assertEqual(units.iloc[2], 0)
        self.assertTrue(pd.isna(units.iloc[3]))
        self.assertEqual(units.iloc[4], 3)
        self.assertEqual(units.sum(), 8)


if __name__ == "__main__":
    unittest.main()