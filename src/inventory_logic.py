from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class InventoryPolicyInputs:
    """
    Inputs for a simple, explainable reorder policy.

    lead_time_weeks: supplier lead time in weeks (slider in dashboard)
    service_level: probability of not stocking out during lead time (slider in dashboard)
    holding_cost_rate: annual holding cost as a fraction of unit cost (proxy); used optionally
    """
    lead_time_weeks: int
    service_level: float = 0.95
    holding_cost_rate: float = 0.25


def z_value(service_level: float) -> float:
    """
    Approximate z-score for common service levels without SciPy.
    (Good enough for business decisions and avoids heavy deps.)
    """
    # Common service levels → z (one-sided)
    common = {
        0.80: 0.8416,
        0.85: 1.0364,
        0.90: 1.2816,
        0.95: 1.6449,
        0.97: 1.8808,
        0.98: 2.0537,
        0.99: 2.3263,
    }
    # Snap to nearest common value
    nearest = min(common.keys(), key=lambda k: abs(k - service_level))
    return common[nearest]


def lead_time_demand(
    forecast_mean_by_week: Dict[int, float],
    lead_time_weeks: int,
) -> float:
    """
    Sum forecast means over the lead time horizon.

    forecast_mean_by_week: {1: mean week+1, 2: mean week+2, ...}
    """
    return sum(float(forecast_mean_by_week.get(h, 0.0)) for h in range(1, lead_time_weeks + 1))


def safety_stock(
    forecast_std: float,
    lead_time_weeks: int,
    service_level: float,
) -> float:
    """
    Safety stock from uncertainty, assuming independent weekly errors:
        SS = z * sigma * sqrt(lead_time)
    """
    z = z_value(service_level)
    sigma = max(0.0, float(forecast_std))
    return z * sigma * math.sqrt(max(1, int(lead_time_weeks)))


def reorder_point(
    forecast_mean_by_week: Dict[int, float],
    forecast_std: float,
    lead_time_weeks: int,
    service_level: float,
) -> float:
    """
    Reorder point = expected demand during lead time + safety stock
    """
    ltd = lead_time_demand(forecast_mean_by_week, lead_time_weeks)
    ss = safety_stock(forecast_std, lead_time_weeks, service_level)
    return max(0.0, ltd + ss)


def order_quantity(
    current_inventory: float,
    forecast_mean_by_week: Dict[int, float],
    forecast_std: float,
    lead_time_weeks: int,
    service_level: float,
) -> Tuple[float, float, float]:
    """
    Returns (order_qty, reorder_point, safety_stock)

    order_qty = max(0, ROP - current_inventory)
    """
    rop = reorder_point(forecast_mean_by_week, forecast_std, lead_time_weeks, service_level)
    ss = safety_stock(forecast_std, lead_time_weeks, service_level)
    inv = max(0.0, float(current_inventory))
    qty = max(0.0, rop - inv)
    return qty, rop, ss