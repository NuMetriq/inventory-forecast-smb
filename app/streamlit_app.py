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
st.set_page_config(page_title="SMB Inventory Forecast & Reorder", layout="wide")
st.title("SMB Inventory Forecast & Reorder Decision System")
st.caption("Forecast weekly demand with uncertainty and compute reorder recommendations (ROP + safety stock).")

weekly = load_weekly()

left, right = st.columns([1, 2])

with left:
    st.subheader("Inputs")

    sku_list = weekly["StockCode"].drop_duplicates().tolist()
    sku = st.selectbox("Select SKU", sku_list, index=0)

    lead_time = st.slider("Lead time (weeks)", min_value=2, max_value=8, value=4, step=1)
    service_level = st.slider("Service level", min_value=0.80, max_value=0.99, value=0.95, step=0.01)

    current_inventory = st.number_input("Current on-hand inventory (units)", min_value=0, value=50, step=1)

    st.markdown("---")
    st.write("**Notes**")
    st.write("- Forecast method: seasonal-naive (52-week) with residual-based uncertainty.")
    st.write("- Safety stock: z × σ × √(lead time)")
    st.write("- Reorder point: expected lead-time demand + safety stock")

with right:
    sku_df = weekly[weekly["StockCode"] == sku].sort_values("WeekStart")
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

    # KPI cards
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Reorder point (units)", f"{rop:.1f}")
    k2.metric("Safety stock (units)", f"{ss:.1f}")
    k3.metric("Recommended order qty (units)", f"{qty:.1f}")
    k4.metric("Forecast σ (units)", f"{sigma:.1f}")

    # Plot
    fig = plt.figure()
    plt.plot(sku_df["WeekStart"], sku_df["weekly_units"], label="History")
    plt.plot(future_dates, mu, label="Forecast")
    plt.fill_between(future_dates, lower, upper, alpha=0.2, label=f"{int(service_level*100)}% interval")
    plt.title(f"SKU {sku} — Weekly demand forecast")
    plt.xlabel("Week")
    plt.ylabel("Units")
    plt.legend()
    st.pyplot(fig, clear_figure=True)

    # Explain the calculation (owner-friendly)
    ltd = sum(forecast_mean_by_week[h] for h in range(1, lead_time + 1))
    st.markdown("### How the recommendation is computed")
    st.write(f"- Expected demand during lead time ({lead_time} weeks): **{ltd:.1f} units**")
    st.write(f"- Safety stock at ~{int(service_level*100)}% service level: **{ss:.1f} units**")
    st.write(f"- Reorder point (ROP): **{rop:.1f} units**")
    st.write(f"- Current inventory: **{float(current_inventory):.1f} units**")
    st.write(f"- **Recommended order quantity:** **{qty:.1f} units**")