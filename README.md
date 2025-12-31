# SMB Inventory Forecasting & Reorder Decision System
(Online Retail II — real transaction data)

TL;DR:
I built a decision system for a small retailer/manufacturer that forecasts weekly SKU demand, explicitly models uncertainty, and recommends reorder quantities based on lead time and desired service level.

---

## 1) Business problem

Small businesses often reorder inventory with limited cash, limited storage, and uncertain demand.
Ordering too little causes stockouts and lost repeat customers; ordering too much ties up cash and creates holding or spoilage risk.

Decision this system supports:
For each SKU, how much to reorder (and when) given supplier lead time and a target service level.

Success looks like:
- Fewer stockouts on fast-moving products
- Less cash trapped in slow movers
- Clear, explainable reorder recommendations an owner can trust

---

## 2) Data

Dataset:
Online Retail II (real transaction-level e-commerce orders)

Grain:
Invoice line items aggregated to weekly SKU demand

Key fields used:
- InvoiceDate
- StockCode
- Quantity
- UnitPrice
- Invoice (to detect cancellations/returns)
- CustomerID

Cleaning rules (documented and enforced):
- Remove cancellations/returns (e.g., invoices starting with C, negative quantities)
- Drop zero or negative prices
- Aggregate demand to weekly units per SKU
- Filter to SKUs with sufficient sales history for forecasting

---

## 3) How it works (plain language)

- Weekly demand is forecast per SKU using a simple, explainable seasonal-naive baseline
- Forecast uncertainty is estimated from historical residuals
- Safety stock is computed as:
  z × σ × √(lead time)
- Reorder point (ROP) is:
  Expected lead-time demand + safety stock
- Recommended order quantity is:
  max(0, ROP − current inventory)

Lead time and service level are adjustable via dashboard sliders.

---

## 4) Deliverable

A Streamlit dashboard that provides:
- SKU demand history with 4-week forecasts and uncertainty bands
- Recommended reorder point, safety stock, and order quantity
- What-if sliders for lead time and service level

---

## Results

### Forecast accuracy (baseline comparison)

Forecasts were evaluated using rolling backtests across a representative set of SKUs with sufficient sales history (≥20 weeks).

Average error metrics across the evaluated SKUs:

- Mean Absolute Error (MAE):
  - Naive baseline: ~122 units per week
  - 4-week moving average: ~102 units per week
- Root Mean Squared Error (RMSE):
  - Naive baseline: ~148 units per week
  - 4-week moving average: ~127 units per week

The modest improvement from simple smoothing reflects the highly variable and intermittent nature of demand in this dataset, where large, infrequent orders drive much of the error.

---

### Decision impact

While point forecast accuracy is inherently limited for spiky SKUs, explicitly modeling uncertainty enables actionable inventory decisions:

- Safety stock increases appropriately with demand volatility and lead time
- Reorder points scale monotonically with lead time and service level
- Order quantities respond smoothly to scenario changes via dashboard sliders

Rather than optimizing for marginal gains in RMSE, the system prioritizes **risk-aware ordering** over false precision, which is more appropriate for small businesses with limited data and cash constraints.

---

### Example outcome (single SKU)

For a representative SKU with spiky demand:

- Lead time: 2 weeks → Reorder point ≈ 73 units  
- Lead time: 4 weeks → Reorder point ≈ 117 units  
- Lead time: 6 weeks → Reorder point ≈ 157 units  

This behavior aligns with operational intuition and provides owners with transparent, adjustable reorder guidance.

---

## Executive Summary

A 1-2 page, client-ready summary of the problem, methodology, results, and recommendations is available here:

- [Executive Summary (PDF)](reports/executive_summary.pdf)

---

## 5) Repo structure

notebooks/   — EDA, data cleaning, forecasting experiments  
src/         — reusable pipeline (data prep, forecasting, inventory logic)  
app/         — Streamlit dashboard  
reports/     — 1–2 page executive summary  

---

## 6) Run the dashboard

Install dependencies:
    pip install -r requirements.txt

Run the app:
    python -m streamlit run app/streamlit_app.py

---

## 7) Limitations & next steps

Limitations:
- Demand is intermittent and spiky; forecasts are intentionally conservative
- Inventory on-hand is a manual input (would integrate with POS/ERP in production)
- Holding and stockout costs are proxies

Next steps:
- ABC classification and cash-constrained ordering
- Model monitoring and drift detection
- Pilot deployment to measure stockout and overstock reduction

---

## Status

Core system complete; polishing documentation and report.