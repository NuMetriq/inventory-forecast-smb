# inventory-forecast-smb

Inventory forecasting and decision system for a small retailer using real transaction data



\# SMB Inventory Forecasting \& Reorder Decision System (Online Retail II)



\*\*TL;DR:\*\* I built a decision system for a small retailer/manufacturer that forecasts weekly SKU demand, quantifies stockout vs overstock risk, and recommends reorder quantities under uncertainty.



\## 1) Business problem

Small businesses often reorder inventory with limited cash, limited storage, and uncertain demand. Ordering too little causes stockouts and lost repeat customers; ordering too much ties up cash and creates holding/spoilage risk.



\*\*Decision this supports:\*\* For each SKU, \*how much to reorder (and when)\* given lead time and desired service level.



\*\*Success looks like:\*\*

\- Fewer stockouts on fast movers

\- Less cash trapped in slow movers

\- Clear, explainable reorder recommendations an owner can trust



\## 2) Data

\*\*Dataset:\*\* Online Retail II (transaction-level e-commerce orders).  

\*\*Grain:\*\* invoice line items → aggregated to weekly SKU units.



\*\*Key fields used:\*\* InvoiceDate, StockCode, Quantity, UnitPrice, Invoice (cancellations), CustomerID.



\*\*Cleaning rules (documented and enforced):\*\*

\- Remove cancellations/returns (e.g., invoices starting with `C`, negative quantities)

\- Drop zero/negative prices

\- Aggregate to weekly demand per SKU



\## 3) Deliverable

A Streamlit dashboard that shows:

\- SKU demand history + 4-week forecast with uncertainty bands

\- Recommended reorder point and order quantity

\- What-if sliders for lead time and service level



\## 4) Repo structure

\- `notebooks/` — EDA \& modeling

\- `src/` — reusable pipeline (data prep, forecasting, inventory logic)

\- `app/` — Streamlit dashboard

\- `reports/` — 1–2 page executive summary



\## 5) Status

Work in progress.

