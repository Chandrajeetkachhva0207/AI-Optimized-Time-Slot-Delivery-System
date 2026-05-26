"""Simple demand / peak-hour prediction using scikit-learn (RandomForestRegressor)."""
import os
from datetime import datetime
from typing import Any, Dict, List, Tuple

import numpy as np

_model = None
_feature_cols = ("hour", "day_of_week")


def _build_synthetic_training() -> Tuple[np.ndarray, np.ndarray]:
    """Synthetic hourly demand pattern for demo when DB has few rows."""
    rng = np.random.default_rng(42)
    X = []
    y = []
    for _ in range(200):
        h = rng.integers(0, 24)
        dow = rng.integers(0, 7)
        # Peak around 11-13 and 18-20
        base = 10 + 8 * np.sin((h - 8) * np.pi / 12) ** 2
        noise = rng.normal(0, 3)
        demand = max(0, base + noise + (5 if h in (11, 12, 13, 18, 19, 20) else 0))
        X.append([h, dow])
        y.append(demand)
    return np.array(X), np.array(y)


def train_demand_model_if_needed(orders_hour_counts: List[Tuple[int, float]]) -> Dict[str, Any]:
    """
    Train RandomForest on hourly counts if enough samples; else synthetic.
    orders_hour_counts: list of (hour_0_23, demand_count)
    """
    global _model
    try:
        from sklearn.ensemble import RandomForestRegressor
    except ImportError:
        return {"success": False, "error": "scikit-learn not installed"}

    if len(orders_hour_counts) >= 8:
        X = np.array([[h, datetime.now().weekday()] for h, _ in orders_hour_counts])
        y = np.array([c for _, c in orders_hour_counts])
    else:
        X, y = _build_synthetic_training()

    _model = RandomForestRegressor(n_estimators=50, max_depth=8, random_state=42)
    _model.fit(X, y)
    return {"success": True, "samples": len(y)}


def predict_peak_hours() -> Dict[str, Any]:
    """Predict demand for each hour 0-23; return sorted peak hours and chart series."""
    global _model
    try:
        from sklearn.ensemble import RandomForestRegressor  # noqa: F401
    except ImportError:
        hours = list(range(24))
        demand = [10 + abs(h - 12) * 0.5 + (8 if h in (11, 12, 13, 18, 19) else 0) for h in hours]
        peak = sorted(range(24), key=lambda i: demand[i], reverse=True)[:5]
        return {
            "success": True,
            "hourly_demand": [{"hour": h, "predicted": round(demand[h], 2)} for h in hours],
            "peak_hours": peak,
            "note": "Heuristic fallback (sklearn unavailable)",
        }

    if _model is None:
        train_demand_model_if_needed([])

    if _model is None:
        hours = list(range(24))
        demand = [10 + abs(h - 12) * 0.5 + (8 if h in (11, 12, 13, 18, 19) else 0) for h in hours]
        peak = sorted(range(24), key=lambda i: demand[i], reverse=True)[:5]
        return {
            "success": True,
            "hourly_demand": [{"hour": h, "predicted": round(demand[h], 2)} for h in hours],
            "peak_hours": peak,
            "note": "Heuristic fallback (model train failed)",
        }

    dow = datetime.now().weekday()
    preds = []
    for h in range(24):
        p = float(_model.predict(np.array([[h, dow]]))[0])
        preds.append({"hour": h, "predicted": round(max(0, p), 2)})

    peak_idx = sorted(range(24), key=lambda i: preds[i]["predicted"], reverse=True)[:5]
    return {
        "success": True,
        "hourly_demand": preds,
        "peak_hours": peak_idx,
        "note": "RandomForest demand model",
    }
