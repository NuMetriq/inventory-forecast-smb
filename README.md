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

## Flagship Case Study: Integrated Inventory, Customer, and Pricing Analytics for an SMB

This flagship case study represents an end-to-end analytics engagement for a small retailer or light manufacturer, built using real transaction-level data.

Rather than treating inventory, customers, and pricing as isolated problems, the project integrates them into a single decision framework that adapts operational and pricing decisions based on customer value and demand behavior.

📁 Project folder:  
`inventory-forecast-smb/`

---

### Integrated Decision Framework (The “Triad”)

This project connects three business decisions that are often handled independently:

1) Customer Value (Segmentation) — who drives revenue and should be prioritized
2) Pricing & Promotions — which products respond to discounts and when promotions are worthwhile
3) Inventory Policy — how much to stock, and how conservative buffers should be under uncertainty

The system dynamically adjusts inventory service levels and reorder decisions based on:

- which customer segments purchase each SKU
- whether a SKU is price-responsive
- whether a promotion is likely to increase revenue

This allows an SMB to answer, for each product:

-Who are we serving?
-Should we discount this item?
-How should we stock it to avoid losing our best customers during promotions?

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
- Integrated customer segmentation to adapt service levels and inventory buffers based on customer value
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

### Module 3: Pricing, Demand Elasticity & Promotion Effectiveness

**Business question:**
When do discounts actually increase revenue, and when do they destroy margin?

**What I built:**
- Identified SKUs with sufficient price variation to support pricing analysis
- Used visual diagnostics to distinguish elastic, inelastic, and noisy demand patterns
- Estimated demand response using appropriate elasticity and semi-elasticity models
- Evaluated promotion effectiveness by comparing discounted vs non-discounted periods
- Classified SKUs by price responsiveness using a precomputed pricing flag artifact
- Integrated pricing insights into inventory policy to increase buffers during revenue-accretive promotions

**Key decisions supported:**
- Which SKUs should be discounted
- When promotions are revenue-accretive versus wasteful
- How promotions should influence inventory risk management

**Artifacts:**
- Pricing and elasticity analysis notebooks
- Promotion effectiveness evaluation
- SKU-level pricing classification artifact
- Pricing executive summary (PDF)

---

## Interactive Dashboard

The Streamlit dashboard integrates all three modules into a single decision-support interface:
- SKU-level demand history and uncertainty-aware forecasts
- Customer segment mix for each SKU narrative insights
- Pricing responsiveness flags and promotion evidence
- Inventory service levels and reorder recommendations that adapt dynamically
- Downloadable, business-ready CSV recommendations

This dashboard is designed for **practical use by non-technical stakeholders**, not just exploration.

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
- Python (pandas, numpy, scikit-learn, statsmodels)
- Time-series forecasting with uncertainty
- Clustering and customer segmentation
- Pricing elasticity and promotion analysis
- Streamlit dashboards
- Git-based, reproducible project structure
- Executive-level written communication

---

## About me

I focus on applying data science to **real operational and strategic problems**, particularly in small and mid-sized organizations where data is imperfect and decisions carry immediate consequences.

My goal is to build analytics that **inform action**, not just optimize metrics.

---

## Contact / Next Steps

If you’re interested in:
- applied analytics consulting
- inventory or operations analytics
- pricing and promotion strategy
- customer growth strategy
- or portfolio collaboration

Feel free to reach out via GitHub.
