# Executive Summary
## Inventory Forecasting & Reorder Decision System

### Client context
This project is framed around a small retailer or light manufacturer with limited cash, limited storage capacity, and highly variable demand across a large SKU catalog.

The business must regularly decide how much inventory to reorder without reliable forecasts, often relying on intuition or simple heuristics.

---

### Business problem
Ordering too little inventory leads to stockouts, lost revenue, and dissatisfied repeat customers.  
Ordering too much ties up cash and increases holding or spoilage risk.

The core decision is:
**How much of each SKU should be reordered, and when, given uncertain demand and supplier lead times?**

---

### Solution overview
I built an inventory decision system that:

- Aggregates real transaction data into weekly SKU-level demand
- Forecasts near-term demand using an explainable baseline
- Explicitly models demand uncertainty
- Computes safety stock, reorder points, and recommended order quantities
- Allows scenario testing via lead-time and service-level inputs

The output is a simple, transparent reorder recommendation that can be adjusted to reflect real-world operational constraints.

---

### Data
- Source: Online Retail II (real e-commerce transaction data)
- Grain: Invoice line items aggregated to weekly SKU demand
- Time span: ~1 year of sales history
- SKUs evaluated: 2,000+ (filtered to those with sufficient sales history)

Cleaning steps included:
- Removing cancellations and returns
- Dropping invalid prices and quantities
- Aggregating demand to weekly totals per SKU

---

### Methodology (plain language)
- Forecasting approach: seasonal-naive baseline with simple smoothing
- Evaluation: rolling backtests on historical data
- Uncertainty estimation: historical forecast residuals
- Safety stock calculation:
  z × σ × √(lead time)
- Reorder point (ROP):
  expected demand during lead time + safety stock
- Order quantity:
  max(0, ROP − current inventory)

This approach favors interpretability and robustness over complex models that may overfit limited data.

---

### Results

**Forecast accuracy (baseline comparison):**
- Mean Absolute Error (MAE):
  - Naive baseline: ~122 units/week
  - 4-week moving average: ~102 units/week
- Root Mean Squared Error (RMSE):
  - Naive baseline: ~148 units/week
  - 4-week moving average: ~127 units/week

Demand in this dataset is highly intermittent and spiky, with large infrequent orders driving most error. Modest improvements from smoothing are expected under these conditions.

**Operational impact:**
- Safety stock increases appropriately with demand volatility and lead time
- Reorder points scale monotonically with lead time and service level
- Order quantities respond smoothly to scenario changes

Rather than optimizing for marginal improvements in RMSE, the system prioritizes risk-aware ordering and avoids false precision.

---

### Example outcome (single SKU)

For a representative SKU with volatile demand:

- Lead time: 2 weeks → Reorder point ≈ 73 units
- Lead time: 4 weeks → Reorder point ≈ 117 units
- Lead time: 6 weeks → Reorder point ≈ 157 units

These results align with operational intuition and provide transparent, adjustable guidance to the business owner.

---

### Limitations
- Inventory on-hand is treated as an external input
- Holding and stockout costs are approximations
- Forecasts are conservative by design for volatile SKUs

---

### Recommended next steps
If this were a paid engagement, next steps would include:
- Integrating live inventory data
- Adding ABC classification and cash-constrained ordering
- Implementing monitoring and retraining triggers
- Piloting the system to measure stockout and overstock reduction