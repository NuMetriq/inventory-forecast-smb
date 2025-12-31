# Applied Data Science Portfolio
## Business-First Analytics for Small & Mid-Sized Organizations

### Overview

This portfolio showcases applied data science projects focused on **real business decisions**, not just model accuracy.

My work emphasizes:
- Interpretable, decision-oriented analytics
- Real-world constraints (limited data, cash, operations)
- Clear communication with non-technical stakeholders
- End-to-end delivery: data → analysis → decision support → executive summary

The projects below are designed to resemble **consulting or in-house analytics engagements**, using real data and producing client-ready artifacts.

---

## Flagship Case Study: Inventory & Customer Analytics for an SMB

This case study represents an end-to-end analytics engagement for a small retailer or light manufacturer, built using real transaction-level data.

The work is organized into two complementary decision modules that operate on the same underlying data source.

📁 Project folder:  
`inventory-forecast-smb/`

---

### Module 1: Inventory Forecasting & Reorder Decision System

**Business question:**  
How should a small business reorder inventory under uncertain demand and limited cash?

**What I built:**
- Cleaned and aggregated transaction-level data into weekly SKU demand
- Evaluated baseline forecasting approaches using rolling backtests
- Explicitly modeled demand uncertainty
- Translated forecasts into safety stock, reorder points, and order quantities
- Delivered an interactive dashboard with scenario sliders
- Produced a client-ready executive summary (PDF)

**Key decisions supported:**
- How much inventory to reorder
- How lead time and service level affect risk
- Which SKUs require conservative buffers

**Artifacts:**
- Interactive Streamlit dashboard
- Inventory executive summary (PDF)
- Reproducible notebooks and reusable logic

---

### Module 2: Customer Segmentation & Growth Strategy

**Business question:**  
Which customers should the business prioritize to grow revenue efficiently?

**What I built:**
- Engineered customer-level behavioral features (recency, frequency, value, basket size)
- Segmented customers using interpretable clustering
- Identified high-value, growth, wholesale, and at-risk customer groups
- Translated segments into concrete marketing, pricing, and operational actions
- Produced a client-ready executive summary (PDF)

**Key decisions supported:**
- Where to focus retention efforts
- Which customers warrant discounts or perks
- How to avoid wasted marketing spend

**Artifacts:**
- Segmentation analysis notebooks
- Strategy-focused interpretation notebook
- Customer segmentation executive summary (PDF)

---

## Methodological principles

Across projects, I prioritize:

- **Decision impact over marginal accuracy gains**
- **Uncertainty awareness**, especially with sparse or volatile data
- **Explainability**, so outputs can be trusted and acted upon
- **Business framing**, not model-centric storytelling

I intentionally avoid unnecessary complexity when it does not materially improve decisions.

---

## Tools & techniques

- Python (pandas, numpy, scikit-learn)
- Time-series forecasting (baseline + uncertainty)
- Clustering and segmentation
- Feature engineering
- Streamlit dashboards
- Git & reproducible project structure
- Executive-level written communication

---

## About me

I am focused on applying data science to **real operational and strategic problems**, particularly in small and mid-sized organizations where data is imperfect and decisions carry immediate consequences.

My goal is to build analytics that **inform action**, not just optimize metrics.

---

## Contact / next steps

If you’re interested in:
- applied analytics consulting
- inventory or operations analytics
- customer growth strategy
- or portfolio collaboration

Feel free to reach out via GitHub.
