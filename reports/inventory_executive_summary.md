# Inventory Executive Summary
## Reorder Decision Support Under Demand Uncertainty

### Decision Context
This project is framed around a smaller retailer or light manufacturer with **limited cash, limited storage capacity, and highly variable demand across a large SKU catalog.**
The business must make frequent inventory reorder decisions without access to sophisticated forecasting systems. In practice, these decisions are often driven by intuition, recent sales, or fixed reorder rules that fail to account for uncertainty.
The goal of this project is to support **practical, defensible reorder decisions** that balance stockout risk against cash and inventory constraints.

---

### Business problem
Inventory decisions for small businesses involve unavoidable tradeoffs:
- Ordering **too little** inventory leads to stockouts, lost sales, and customer dissatisfaction
- Ordering **too much** inventory ties up scarce cash and increases holding, spoilage, or obsolescence risk
- Demand is volatile and uneven across SKUs, making precise forecasting unreliable

The core question is:
**How much of each SKU should be reordered, and when, given uncertain demand and supplier lead times?**

---

### Analytical Approach
Rather than relying on complex forecasting models, the analysis focuses on **decision-relevant signals**:

- **Historical weekly demand** at the SKU level
- **Demand uncertainty**, explicitly estimated from historical variation
- **Supplier lead time**, treated as a risk exposure window
- **Service level targets**, reflecting tolerance for stockouts

Forecasts are used as **inputs to inventory decisions**, not as predictions to be optimized. The empasis is on understanding risk, not achieving marginal accuracy gains.
This approach mirrors how inventory decisions are made in practice when data is limited and uncertainty is unavoidable.

---

### Key Findings
*The analysis highlights several decision-relevant patterns*:
- Demand uncertainty varies widely across SKUs and is often more important than average demand
- Small changes in lead time or service level can materially increase required safety stock
- Point forecasts alone systematically underestimate stockout risk
- Conservative, uncertainty-aware policies provide more stable outcomes than reactive reordering

These findings suggest that **explicitly accounting for uncertainty** is more valuable than pursuing precise demand predictions.

---

### Decision Guidance
Based on the analysis, inventory decisions should follow these principles:
- Base reorder decisions on **expected lead-time demand plus safety stock**, not recent sales alone
- Adjust safety stock according to both **demand volatility** and **lead time exposure**
- Use service level assumptions as a **business lever**, reflecting risk tolerance rather than technical accuracy
- Treat SKUs independently; uniform reorder rules across products are rarely appropriate

The resulting output is a **clear reorder point and recommended order quantity** for each SKU under a given scenario.

---

### Limitations and Guardrails
- Results are based on historical demand and do not account for future structural changes
- Forecasts are intentionally simple and conservative; they are not designed for long-term planning
- Recommendations should be revisited if lead times, product assortment, or demand patterns change materially

This system is designed to **support judgement**, not replace it.

---

### How to Use This
1. Select a SKU and review its historical demand pattern
2. Set realistic assumptions for supplier lead time and desired service level
3. Review the recommended reorder point and order quantity
4. Adjust assumptions to understand tradeoffs between risk and inventory investment
5. Use the output as a decision aid alongside operational context

---

---

## Bottom Line
For small businesses, better inventory decisions come not from complex models, but from **explicitly acknowledging uncertainty and risk intentionally**.
This framework provides a practical way to make inventory reorder decisions that are **defensible, transparent, and aligned with real operational constraints**.