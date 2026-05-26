"""Time slot recommendation: prefer slots with lowest utilization (booked/capacity)."""
from typing import Any, Dict, List, Optional


def slot_utilization(capacity: int, booked: int) -> float:
    if capacity <= 0:
        return 1.0
    return min(1.0, booked / float(capacity))


def recommend_least_busy_slot(slots: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    slots: list of dicts with keys id, slot, capacity, booked
    Returns the slot dict with minimum utilization, or None if empty.
    """
    if not slots:
        return None
    best = None
    best_score = float("inf")
    for s in slots:
        cap = int(s.get("capacity") or 0)
        book = int(s.get("booked") or 0)
        util = slot_utilization(cap, book)
        remaining = cap - book
        # Prefer lower utilization; tie-break by more remaining capacity
        score = util - (remaining * 0.001)
        if score < best_score:
            best_score = score
            best = dict(s)
    if best:
        best["recommended"] = True
        best["utilization_pct"] = round(
            100.0 * slot_utilization(int(best.get("capacity") or 0), int(best.get("booked") or 0)), 1
        )
    return best
