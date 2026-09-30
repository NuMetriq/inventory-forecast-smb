import sys
from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.forecasting import add_baseline_forecasts
from src.inventory_targets import calculate_stock_target
from src.uncertainty import (
    build_lead_time_errors,
    estimate_product_buffers,
)


PANEL_PATH = (
    PROJECT_ROOT / "data" / "processed" / "v2"
    / "weekly_sales_panel.csv"
)

DESCRIPTIONS_PATH = PANEL_PATH.parent / "product_descriptions.csv"

DEFAULT_FORECAST_DATE = pd.Timestamp("2011-10-10")
HORIZON_WEEKS = 4


st.set_page_config(
    page_title="Inventory Planning | NuMetriq",
    page_icon="📊",
    layout="wide",
)


@st.cache_data
def load_panel():
    return pd.read_csv(
        PANEL_PATH,
        dtype={"stock_code": "string"},
        parse_dates=["week_start"],
    )


@st.cache_data
def load_product_names(as_of):
    descriptions = pd.read_csv(
        DESCRIPTIONS_PATH,
        dtype={
            "stock_code": "string",
            "description": "string",
        },
        parse_dates=["observed_at"],
    )

    known = descriptions.loc[
        descriptions["observed_at"].lt(as_of)
    ].dropna(subset=["stock_code", "description"])

    latest = (
        known.sort_values(["stock_code", "observed_at", "description"])
        .drop_duplicates("stock_code", keep="last")
    )

    return latest.set_index("stock_code")["description"].to_dict()


@st.cache_data
def prepare_history(panel, as_of):
    history = panel.loc[panel["week_start"].lt(as_of)].copy()

    forecasts = add_baseline_forecasts(history)
    errors = build_lead_time_errors(
        forecasts,
        horizon_weeks=HORIZON_WEEKS,
    )
    buffers = estimate_product_buffers(errors, as_of=as_of)

    return history, buffers


st.title("Inventory Planning")
st.caption("NuMetriq • Public-data demonstration")
st.write(
    "Explore how recent sales and historical forecast errors "
    "contribute to a four-week stock target."
)

if not PANEL_PATH.is_file():
    st.error("Prepared sales data is missing. Run the data preparation script.")
    st.stop()

panel = load_panel()

forecast_dates = pd.date_range(
    start=DEFAULT_FORECAST_DATE,
    end=panel["week_start"].max(),
    freq="W-MON",
).tolist()

AS_OF = st.sidebar.selectbox(
    "Historical forecast date",
    options=forecast_dates,
    index=0,
    format_func=lambda date: date.strftime("%b %d, %Y"),
    help=(
        "Reconstructs a planning scenario using only sales "
        "and completed forecast errors available before this date."
    ),
)

history, buffers = prepare_history(panel, AS_OF)

products = sorted(history["stock_code"].unique())

if not DESCRIPTIONS_PATH.is_file():
    st.error("Product descriptions are missing. Run scripts/check_cleaning.py.")
    st.stop()

product_names = load_product_names(AS_OF)

with st.sidebar:
    st.header("Planning scenario")

    default_index = products.index("85123A") if "85123A" in products else 0

    stock_code = st.selectbox(
        "Product",
        options=products,
        index=default_index,
        format_func=lambda code: (
            f"{code} — {product_names.get(code, 'Description unavailable')}"
        ),
    )

    st.write(f"**Forecast date:** {AS_OF.date()}")
    st.write("**Coverage horizon:** 4 weeks")
    st.caption("Calculations use only weeks preceding the forecast date.")

product_history = (
    history.loc[history["stock_code"].eq(stock_code)]
    .sort_values("week_start")
)

recent_weeks = pd.date_range(
    end=AS_OF - pd.Timedelta(weeks=1),
    periods=4,
    freq="W-MON",
)

recent_sales = (
    product_history.set_index("week_start")["units_sold"]
    .reindex(recent_weeks)
)

st.subheader(product_names.get(stock_code, "Description unavailable"))
st.caption(f"Product code: {stock_code}")

product_buffer = buffers.loc[buffers["stock_code"].eq(stock_code)]

if recent_sales.isna().any():
    st.warning(
        "A target is unavailable because the previous four weeks "
        "do not all have known recorded sales."
    )
elif (
    product_buffer.empty
    or product_buffer.iloc[0]["buffer_status"] != "estimated"
):
    st.warning(
        "A target is unavailable because fewer than 20 completed "
        "historical error windows are available."
    )
else:
    buffer_row = product_buffer.iloc[0]

    target = calculate_stock_target(
        weekly_forecast=float(recent_sales.mean()),
        buffer_units=float(buffer_row["buffer_units"]),
        horizon_weeks=HORIZON_WEEKS,
    )

    forecast_col, buffer_col, target_col = st.columns(3)

    forecast_col.metric(
        "Four-week sales forecast",
        f"{target['forecast_units']:,.0f} units",
    )
    buffer_col.metric(
        "Historical error buffer",
        f"{target['buffer_units']:,.1f} units",
    )
    target_col.metric(
        "Four-week stock target",
        f"{target['target_units']:,} units",
    )

    st.caption(
        f"Buffer estimated from {int(buffer_row['error_windows'])} "
        "overlapping four-week error windows, using their 90th percentile. "
        "This does not guarantee 90% coverage. "
        "The stock target is rounded up to the next whole unit."
    )

    scenario_export = pd.DataFrame([{
        "stock_code": stock_code,
        "description": product_names.get(
            stock_code, "Description unavailable"
        ),
        "forecast_date": AS_OF.date().isoformat(),
        "horizon_weeks": HORIZON_WEEKS,
        "forecast_method": "Four-week moving average",
        "forecast_units": target["forecast_units"],
        "buffer_quantile": 0.90,
        "completed_error_windows": int(buffer_row["error_windows"]),
        "buffer_units": target["buffer_units"],
        "stock_target_units": target["target_units"],
        "interpretation": (
            "Historical demonstration; coverage target, not order quantity. "
            "Buffer uses overlapping historical errors. "
            "The quantile does not guarantee a service level."
        ),
    }])

    st.download_button(
        label="Download planning scenario (CSV)",
        data=scenario_export.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"inventory_scenario_{stock_code}_{AS_OF:%Y%m%d}.csv",
        mime="text/csv",
        on_click="ignore",
    )

st.subheader("Recent recorded sales")

recent_history = product_history.tail(12).copy()

chart_data = pd.DataFrame({
    "Week starting": recent_history["week_start"].dt.strftime("%Y-%m-%d"),
    "Units sold": recent_history["units_sold"],
})

st.bar_chart(
    chart_data,
    x="Week starting",
    y="Units sold",
    x_label="Week starting",
    y_label="Recorded units sold",
    color="#38BDF8",
    sort=False,
    height=320,
)

unknown_weeks = recent_history["units_sold"].isna().sum()

st.caption(
    f"Last 12 calendar weeks before {AS_OF.date()}. "
    "Bars show recorded sales, not total customer demand."
)

if unknown_weeks:
    st.caption(
        f"{unknown_weeks} week(s) have unknown sales and no bar. "
        "See the table below to distinguish unknown weeks from zeros."
    )

with st.expander("View weekly sales data"):
    table = recent_history[[
        "week_start",
        "units_sold",
        "sales_status",
    ]].copy()

    table["week_start"] = table["week_start"].dt.strftime("%Y-%m-%d")

    table["sales_status"] = table["sales_status"].replace({
        "recorded_sales": "Recorded sales",
        "no_recorded_sales": "No recorded sales",
        "before_first_sale": "Before first recorded sale",
        "dataset_gap": "Dataset gap",
    })

    table = table.rename(columns={
        "week_start": "Week starting",
        "units_sold": "Units sold",
        "sales_status": "Record status",
    })

    st.dataframe(table, hide_index=True)

st.info(
    "This is a historical planning demonstration, not an order recommendation. "
    "Recorded sales may understate demand when products were unavailable. "
    "The target does not account for outstanding orders, backorders, "
    "ordering schedules, or inventory costs."
)