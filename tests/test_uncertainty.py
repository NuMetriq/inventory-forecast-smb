import unittest

import pandas as pd

from src.forecasting import add_baseline_forecasts
from src.uncertainty import (
    build_lead_time_errors,
    estimate_product_buffers,
)


class TestLeadTimeErrors(unittest.TestCase):
    def make_forecasts(self, sales):
        panel = pd.DataFrame({
            "stock_code": ["A"] * len(sales),
            "week_start": pd.date_range(
                "2024-01-01",
                periods=len(sales),
                freq="W-MON",
            ),
            "units_sold": sales,
        })
        return add_baseline_forecasts(panel)

    def test_error_requires_four_completed_weeks(self):
        forecasts = self.make_forecasts(
            [10, 20, 30, 40, 50, 60, 70, 80]
        )

        errors = build_lead_time_errors(forecasts)

        # Only one origin has both four prior weeks and four outcomes.
        self.assertEqual(len(errors), 1)
        row = errors.iloc[0]

        self.assertEqual(
            row["forecast_origin"], pd.Timestamp("2024-01-29")
        )

        # Prior average = 25; four-week forecast = 100.
        self.assertEqual(row["forecast_units"], 100)

        # Actual outcome = 50 + 60 + 70 + 80.
        self.assertEqual(row["actual_units"], 260)
        self.assertEqual(row["error_units"], 160)

        self.assertEqual(
            row["available_from"], pd.Timestamp("2024-02-26")
        )

        # The outcome is still incomplete at the preceding Monday.
        available_early = errors.loc[
            errors["available_from"] <= pd.Timestamp("2024-02-19")
        ]
        self.assertTrue(available_early.empty)

        available_on_time = errors.loc[
            errors["available_from"] <= pd.Timestamp("2024-02-26")
        ]
        self.assertEqual(len(available_on_time), 1)

    def test_unknown_outcome_does_not_become_zero(self):
        forecasts = self.make_forecasts(
            [10, 20, 30, 40, 50, None, 70, 80]
        )

        errors = build_lead_time_errors(forecasts)

        # The only otherwise eligible outcome contains an unknown week.
        self.assertTrue(errors.empty)


class TestProductBuffers(unittest.TestCase):
    def test_future_errors_do_not_affect_buffer(self):
        errors = pd.DataFrame({
            "stock_code": ["A"] * 21,
            "available_from": (
                [pd.Timestamp("2024-01-01")] * 20
                + [pd.Timestamp("2024-02-01")]
            ),
            "error_units": list(range(20)) + [1000],
        })

        as_of = pd.Timestamp("2024-01-15")
        original = estimate_product_buffers(errors, as_of)

        self.assertEqual(original.loc[0, "error_windows"], 20)
        self.assertAlmostEqual(original.loc[0, "buffer_units"], 17.1)
        self.assertEqual(original.loc[0, "buffer_status"], "estimated")

        changed_errors = errors.copy()
        changed_errors.loc[20, "error_units"] = -1000

        changed = estimate_product_buffers(changed_errors, as_of)

        pd.testing.assert_frame_equal(original, changed)

    def test_insufficient_history_returns_unknown_buffer(self):
        errors = pd.DataFrame({
            "stock_code": ["A"] * 19,
            "available_from": [pd.Timestamp("2024-01-01")] * 19,
            "error_units": list(range(19)),
        })

        result = estimate_product_buffers(
            errors,
            as_of=pd.Timestamp("2024-01-15"),
        )

        self.assertEqual(result.loc[0, "error_windows"], 19)
        self.assertTrue(pd.isna(result.loc[0, "buffer_units"]))
        self.assertEqual(
            result.loc[0, "buffer_status"],
            "insufficient_history",
        )

    def test_negative_error_quantile_produces_zero_buffer(self):
        errors = pd.DataFrame({
            "stock_code": ["A"] * 20,
            "available_from": [pd.Timestamp("2024-01-01")] * 20,
            "error_units": [-5] * 20,
        })

        result = estimate_product_buffers(
            errors,
            as_of=pd.Timestamp("2024-01-15"),
        )

        self.assertEqual(result.loc[0, "buffer_units"], 0)
        self.assertEqual(result.loc[0, "buffer_status"], "estimated")


if __name__ == "__main__":
    unittest.main()