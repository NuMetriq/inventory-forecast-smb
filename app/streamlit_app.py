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

st.markdown("---")
st.caption(
    "This tool is designed for decision support. Outputs should be interpreted alongside real-world context and business judgment."
)