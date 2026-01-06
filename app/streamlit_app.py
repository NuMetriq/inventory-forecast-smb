import sys
from pathlib import Path

# Allow imports from /src when running streamlit from repo root
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
st.set_page_config(
    page_title="Inventory Reorder Dashboard",
    page_icon="📦",
    layout="wide"
)
from src.inventory_logic import order_quantity, z_value


# ----------------------------
# Forecast helpers (SMB-friendly)
# ----------------------------


def seasonal_naive_forecast(y: np.ndarray, horizon: int = 8, season_len: int = 52) -> np.ndarray:
    if len(y) >= season_len:
        base = y[-season_len]
    else:
        base = y[-1]
    return np.repeat(base, horizon)


def residual_std(y: np.ndarray, season_len: int = 52) -> float:
    errs = []
    if len(y) >= season_len + 1:
        for t in range(season_len, len(y)):
            pred = y[t - season_len]
            errs.append(y[t] - pred)
    return float(np.std(errs)) if errs else float(np.std(y))


@st.cache_data
def load_weekly() -> pd.DataFrame:
    path = project_root / "data" / "processed" / "weekly_sku_demand.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"Missing file: {path}\n"
            "Create it first by running notebooks/01_eda_and_weekly_aggregation.ipynb"
        )
    df = pd.read_csv(path, parse_dates=["WeekStart"])
    df["StockCode"] = df["StockCode"].astype(str)
    return df.sort_values(["StockCode", "WeekStart"])

@st.cache_data
def load_sku_segment_mix() -> pd.DataFrame:
    path = project_root / "data" / "processed" / "sku_segment_mix.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    df["StockCode"] = df["StockCode"].astype(str)
    return df

def recommended_service_level_from_mix(mix_df: pd.DataFrame) -> float:
    """
    Heuristic: choose service level based on how much revenue comes from high-value segments.
    Returns a value in [0.80, 0.99].
    """
    if mix_df is None or mix_df.empty:
        return 0.95

    weights = {
        "High-Value Loyal": 0.99,
        "Growing Repeat": 0.97,
        "Bulk / Wholesale": 0.96,
        "At-Risk / Churned": 0.93,
        "Low-Value / One-Time": 0.92,
    }

    s = 0.0
    for _, r in mix_df.iterrows():
        seg = r.get("segment_name")
        share = float(r.get("revenue_share", 0.0))
        s += share * weights.get(seg, 0.95)

    return float(np.clip(s, 0.80, 0.99))

def segment_mix_summary_sentence(mix_df: pd.DataFrame, top_n: int = 2) -> str:
    """
    Generate a short narrative sentence summarizing who buys the SKU.
    """
    if mix_df is None or mix_df.empty:
        return "Customer segment mix is not available for this SKU."

    top = (
        mix_df.sort_values("revenue_share", ascending=False)
              .head(top_n)
              .assign(pct=lambda d: (d["revenue_share"] * 100).round(0).astype(int))
    )

    parts = [f"{r.segment_name} ({r.pct}%)" for r in top.itertuples()]
    joined = " and ".join(parts)

    return f"This SKU is primarily purchased by {joined} customers."


# ----------------------------
# UI
# ----------------------------


st.title("Inventory Reorder Decision Dashboard")

st.markdown(
    """
    This dashboard provides **risk-aware reorder recommendations** based on historical demand,
    supplier lead time, and desired service level.

    It is designed to support **practical inventory decisions**, not precise point forecasts.
    """
)

weekly = load_weekly()
sku_seg = load_sku_segment_mix()

left, right = st.columns([1, 2])

with left:
    st.subheader("Scenario inputs")

    sku_list = weekly["StockCode"].drop_duplicates().tolist()
    sku = st.selectbox(
        "Select Product (SKU)",
        sku_list,
        index=0,
        help="Recommendations are calculated per SKU using historical weekly demand."
    )

    lead_time = st.slider(
        "Supplier Lead Time (weeks)",
        min_value=2,
        max_value=8,
        value=4,
        step=1,
        help="Time between placing an order and receiving inventory."
    )

    service_level = st.slider(
        "Target Service Level",
        min_value=0.80,
        max_value=0.99,
        value=0.95,
        step=0.01,
        help="Probability of avoiding a stockout during lead time."
    )

    use_recommended_sl = st.checkbox(
        "Use recommended service level (based on customer segments)",
        value=False,
        help="If enabled, the dashboard suggests a service level based on which customer segments purchase this SKU."
    )

    current_inventory = st.number_input(
        "Current On-Hand Inventory (units)",
        min_value=0,
        value=50,
        step=1,
        help="Enter your current physical count (or best estimate)."
    )

    st.markdown("---")
    st.write("**How to read this dashboard**")
    st.write("- The forecast is conservative for spiky SKUs; uncertainty drives safety stock.")
    st.write("- Safety stock increases with higher service levels and longer lead times.")
    st.write("- Reorder point = expected lead-time demand + safety stock.")

with right:
    sku_df = weekly[weekly["StockCode"] == sku].sort_values("WeekStart")
    weeks_of_history = sku_df["WeekStart"].nunique()
    st.caption(f"Data coverage: {weeks_of_history} weeks of history for SKU {sku}.")
    y = sku_df["weekly_units"].to_numpy(dtype=float)
    
    st.subheader("Who buys this SKU? (Customer segment mix)")

    if sku_seg.empty:
        st.info("Customer segmentation data not found. Generate data/processed/sku_segment_mix.csv to enable this section.")
        mix = pd.DataFrame()
    else:
        mix = sku_seg[sku_seg["StockCode"] == sku].sort_values("revenue_share", ascending=False)

        if mix.empty:
            st.info("No segment mix available for this SKU.")
        else:
            show_cols = ["segment_name", "revenue_share", "unit_share", "customers", "orders"]
            mix_view = (
                mix[show_cols]
                .assign(
                    revenue_share=lambda d: (d["revenue_share"] * 100).round(1),
                    unit_share=lambda d: (d["unit_share"] * 100).round(1),
                )
                .rename(columns={
                    "segment_name": "Segment",
                    "revenue_share": "Revenue Share (%)",
                    "unit_share": "Unit Share (%)",
                    "customers": "Customers",
                    "orders": "Orders",
                })
            )
            st.dataframe(mix_view, use_container_width=True)
            st.markdown(
                f"**Insight:** {segment_mix_summary_sentence(mix)}"
            )

    if "use_recommended_sl" in locals() and use_recommended_sl and mix is not None and not mix.empty:
        service_level = recommended_service_level_from_mix(mix)
        st.caption(f"Suggested service level for this SKU (based on segment mix): {service_level:.0%}")

    # Forecast longer than slider range so we can sum lead-time demand
    horizon = 8
    mu = seasonal_naive_forecast(y, horizon=horizon)
    sigma = residual_std(y)

    # Build forecast dict for inventory logic
    forecast_mean_by_week = {i + 1: float(mu[i]) for i in range(horizon)}

    # Inventory policy result
    qty, rop, ss = order_quantity(
        current_inventory=float(current_inventory),
        forecast_mean_by_week=forecast_mean_by_week,
        forecast_std=float(sigma),
        lead_time_weeks=int(lead_time),
        service_level=float(service_level),
    )

    # Interval bounds (cap lower at 0)
    z = z_value(service_level)
    lower = np.maximum(0, mu - z * sigma)
    upper = mu + z * sigma

    # Future dates
    last_date = sku_df["WeekStart"].iloc[-1]
    future_dates = pd.date_range(start=last_date + pd.Timedelta(weeks=1), periods=horizon, freq="W-MON")

    st.subheader("Reorder recommendation")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric(
        "Reorder Point (units)",
        f"{rop:.0f}",
        help="Inventory level at which a new order should be placed to reduce stockout risk during lead time."
    )
    k2.metric(
        "Safety Stock (units)",
        f"{ss:.0f}",
        help="Buffer inventory held to protect against demand volatility and supplier delays."
    )
    k3.metric(
        "Recommended Order Quantity (units)",
        f"{qty:.0f}",
        help="Suggested order size based on current inventory, forecast uncertainty, and lead time."
    )
    k4.metric(
        "Demand Uncertainty σ (units)",
        f"{sigma:.0f}",
        help="Estimated typical forecast error scale. Higher σ implies more volatile demand."
    )

    # Plot
    fig = plt.figure()
    plt.plot(sku_df["WeekStart"], sku_df["weekly_units"], label="History")
    plt.plot(future_dates, mu, label="Forecast")
    plt.fill_between(future_dates, lower, upper, alpha=0.2, label=f"{service_level:.0%} interval")
    plt.title(f"SKU {sku} — Historical weekly demand with forecast context")
    plt.xlabel("Week")
    plt.ylabel("Units")
    plt.legend()
    st.pyplot(fig, clear_figure=True)
    st.caption(
        "Forecasts are intentionally conservative for volatile SKUs. "
        "Uncertainty is incorporated into reorder decisions rather than optimized away."
    )

    ltd = sum(forecast_mean_by_week[h] for h in range(1, lead_time + 1))

    st.markdown("### Interpretation")
    st.write(
        f"With a lead time of **{lead_time} weeks** and a target service level of **{service_level:.0%}**, "
        f"place a new order when inventory falls to approximately **{rop:.0f} units**."
    )
    st.write(
        "Increasing lead time or service level raises the reorder point and safety stock to reduce the risk of stockouts."
    )

    with st.expander("Show calculation details"):
        st.write(f"- Expected demand during lead time: **{ltd:.1f} units**")
        st.write(f"- Safety stock: **{ss:.1f} units**")
        st.write(f"- Reorder point (ROP): **{rop:.1f} units**")
        st.write(f"- Current inventory: **{float(current_inventory):.1f} units**")
        st.write(f"- Recommended order quantity: **{qty:.1f} units**")


    # ----------------------------
    # Download recommendation
    # ----------------------------


    recommendation_df = pd.DataFrame(
        [{
            "SKU": sku,
            "Lead_Time_Weeks": lead_time,
            "Service_Level": service_level,
            "Current_Inventory_Units": int(current_inventory),
            "Forecast_Uncertainty_Sigma": round(float(sigma), 2),
            "Safety_Stock_Units": round(float(ss), 1),
            "Reorder_Point_Units": round(float(rop), 1),
            "Recommended_Order_Quantity_Units": round(float(qty), 1),
            "Generated_At": pd.Timestamp.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        }]
    )

    st.download_button(
        label="Download reorder recommendation (CSV)",
        data=recommendation_df.to_csv(index=False),
        file_name=f"reorder_recommendation_{sku}.csv",
        mime="text/csv",
    )

st.markdown("---")
st.caption(
    "This tool is designed for decision support. Outputs should be interpreted alongside real-world context and business judgment."
)