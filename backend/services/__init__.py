"""Business logic and AI helpers for delivery operations."""
from .slot_ai import recommend_least_busy_slot, slot_utilization
from .demand_ml import predict_peak_hours, train_demand_model_if_needed
from .route_opt import optimize_delivery_order

__all__ = [
    "recommend_least_busy_slot",
    "slot_utilization",
    "predict_peak_hours",
    "train_demand_model_if_needed",
    "optimize_delivery_order",
]
