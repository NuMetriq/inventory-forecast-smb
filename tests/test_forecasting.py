import unittest

import pandas as pd

from src.forecasting import add_baseline_forecasts


class TestBaselineForecasts(unittest.TestCase):
    def make_panel(self, sales):
        return pd.DataFrame({
            "stock_code": ["A"] * len(sales),
            "week_start": pd.date_range(
                "2024-01-01",
                periods=len(sales),
                freq="W-MON",
            ),
            "units_sold": sales,
        })

    def test_forecasts_use_only_past_sales(self):
        panel = self.make_panel([10, 20, 30, 40, 50, 60])
        original = add_baseline_forecasts(panel)

        self.assertEqual(original.loc[4, "forecast_naive"], 40)
        self.assertEqual(original.loc[4, "forecast_ma4"], 25)

        # Change this week's actual sales and all later sales.
        changed_panel = panel.copy()
        changed_panel.loc[4:, "units_sold"] = [5000, 6000]
        changed = add_baseline_forecasts(changed_panel)

        forecast_columns = ["forecast_naive", "forecast_ma4"]

        pd.testing.assert_frame_equal(
            original.loc[:4, forecast_columns],
            changed.loc[:4, forecast_columns],
        )

    def test_unknown_week_is_not_skipped_or_filled(self):
        panel = self.make_panel([10, 20, None, 40, 50, 60, 70, 80])
        result = add_baseline_forecasts(panel)

        # The week immediately after the gap has no naive forecast.
        self.assertTrue(pd.isna(result.loc[3, "forecast_naive"]))

        # Four-week averages remain unknown while the gap is in the window.
        self.assertTrue(
            result.loc[3:6, "forecast_ma4"].isna().all()
        )

        # Once four known weeks are available, forecasting resumes.
        self.assertEqual(result.loc[7, "forecast_naive"], 70)
        self.assertEqual(result.loc[7, "forecast_ma4"], 55)

    def test_product_histories_stay_separate(self):
        product_a = self.make_panel([10, 20, 30, 40, 50])
        product_b = self.make_panel([100, 200, 300, 400, 500])
        product_b["stock_code"] = "B"

        panel = pd.concat([product_a, product_b], ignore_index=True)
        result = add_baseline_forecasts(panel)

        b = result.loc[result["stock_code"].eq("B")].reset_index(drop=True)

        self.assertTrue(pd.isna(b.loc[0, "forecast_naive"]))
        self.assertEqual(b.loc[4, "forecast_naive"], 400)
        self.assertEqual(b.loc[4, "forecast_ma4"], 250)


if __name__ == "__main__":
    unittest.main()