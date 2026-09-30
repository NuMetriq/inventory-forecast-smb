# Inventory Planning v2 — NuMetriq

A Streamlit dashboard demonstrating how recent recorded sales and historical
forecast errors contribute to a four-week stock target.

Users can select a product and historical forecast date, inspect recent sales,
and download the planning scenario as a CSV.

This is a historical planning demonstration. The stock target is not an order
recommendation.

## Setup

Developed using Python 3.11.9. Run the following commands from the repository
root in PowerShell.

Create the environment if it does not already exist:

```powershell
py -3.11 -m venv .venv-v2
```

Install the recorded dependencies:

```powershell
.\.venv-v2\Scripts\python.exe -m pip install -r requirements-v2.txt
```

Verified in a fresh environment using Python 3.11.9 on Windows:
dependency installation, pip check, all nine tests, data preparation,
dashboard startup, and scenario CSV download passed. Product 85123A
on 2011-10-10 reproduced the expected 3,902-unit stock target.

## Prepare the data

Place the Online Retail II workbook at:

```text
data/raw/online_retail_II.xlsx
```

The preparation script reads the worksheet named `Year 2010-2011`.

Run:

```powershell
.\.venv-v2\Scripts\python.exe scripts/check_cleaning.py
```

The script cleans transactions, aggregates weekly sales, constructs the sales
panel, and extracts dated product descriptions.

It writes four files under `data/processed/v2/`:

| File | Purpose |
|---|---|
| `weekly_sales_panel.csv` | Product-level weekly recorded sales and record status |
| `week_calendar.csv` | Calendar coverage information |
| `cleaning_audit.csv` | Counts of rows removed during cleaning |
| `product_descriptions.csv` | Product descriptions with observation timestamps |

Checks verify that the cleaning audit reconciles, aggregation preserves sales
totals, product-week pairs are unique, and saving the panel preserves its row
count, missing values, and total sales.

Successful completion ends with:

```text
Saved panel verified.
```

## Run the dashboard

```powershell
.\.venv-v2\Scripts\python.exe -m streamlit run app/inventory_v2.py
```

Choose a historical forecast date and product in the sidebar.

The dashboard displays:

- Four-week sales forecast
- Historical error buffer
- Whole-unit stock target
- Recent weekly recorded sales
- Downloadable scenario and calculation assumptions

For product `85123A` on `2011-10-10`, the expected values are:

| Component | Units |
|---|---:|
| Four-week forecast | 1,946.0 |
| Historical error buffer | 1,955.2 |
| Rounded stock target | 3,902 |

## Methodology

### Forecast

The weekly forecast is the mean of the four preceding calendar weeks of
recorded sales. All four values must be known.

The four-week forecast is four times that weekly average.

### Historical error buffer

For each eligible historical forecast origin:

```text
error = actual four-week recorded sales − forecast four-week sales
```

Only error windows completed and available by the selected forecast date
contribute to the buffer.

The buffer is the product's historical 90th-percentile error, clipped at zero.
At least 20 completed error windows are required. Insufficient history remains
unknown rather than being treated as a zero buffer.

These four-week windows overlap and are not independent observations.

### Stock target

```text
stock target = ceil(four-week forecast + historical error buffer)
```

Only the final target is rounded up to a whole unit. The forecast and buffer
must cover the same horizon.

Product descriptions are selected from records dated before the forecast date.

## Historical evaluation

Run:

```powershell
.\.venv-v2\Scripts\python.exe scripts/evaluate_buffers.py
```

The recorded evaluation covers five weekly forecast origins from
October 10 through November 7, 2011.

Of 18,241 candidate product-origin rows, 15,797 had sufficient buffer history.
Both methods were compared on those same eligible rows; 2,444 rows were excluded.

| Measure | Forecast only | Forecast plus buffer |
|---|---:|---:|
| Four-week sales coverage | 56.07% | 83.52% |
| Mean target units | 138.33 | 249.61 |
| Mean shortfall units | 48.86 | 17.50 |
| Mean excess units | 31.44 | 111.37 |
| Coverage among positive-sales windows | 39.55% | 77.32% |

Coverage is the share of observed four-week sales totals at or below the target.
Shortfall and excess are target-versus-sales differences, averaged across all
scored rows, including zeros.

Of the scored windows, 4,319 (27.34%) had zero recorded sales.

The buffer improved coverage and reduced shortfall while substantially increasing
the target and excess relative to recorded sales.

## Limitations

- Recorded sales may understate demand when products were unavailable.
- A historical 90th-percentile buffer does not guarantee 90% future coverage.
- Overlapping windows can cause one elevated-sales period to influence several
  historical errors.
- The comparison does not simulate orders, deliveries, or inventory balances.
- Targets do not account for outstanding orders, backorders, ordering schedules,
  or inventory costs.
- Mean excess is not measured inventory remaining on a shelf.
- Results cover a short historical evaluation period and exclude rows without
  sufficient buffer history.
- Some selectable dashboard dates lack four subsequent weeks of data. Targets
  can be generated for those dates without evaluating their eventual coverage.
- These results do not establish cost savings or an optimal inventory policy.

## Tests

```powershell
.\.venv-v2\Scripts\python.exe -m unittest discover -s tests -v
```

The current suite contains nine tests, including checks that unavailable future
errors cannot change a buffer and that insufficient history remains distinct
from an estimated zero buffer.