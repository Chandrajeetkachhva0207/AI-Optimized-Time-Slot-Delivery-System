"""Route optimization utilities for the SmartParcel AI delivery system."""
from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from utils.helpers import parse_traffic_level, validate_coordinates

DEFAULT_TRAFFIC_LEVEL = "medium"
DISTANCE_SCORE_WEIGHT = 0.6
TRAFFIC_SCORE_WEIGHT = 0.4
BASE_SPEED_KMH = 50.0
MIN_SPEED_KMH = 18.0
TRAFFIC_SPEED_FACTORS = {
    "low": 0.92,
    "medium": 0.72,
    "high": 0.52,
}
TRAFFIC_ORDER = {"low": 0, "medium": 1, "high": 2}


def _normalize_traffic_level(value: Union[str, int, float, None]) -> str:
    if value is None:
        return DEFAULT_TRAFFIC_LEVEL

    if isinstance(value, (int, float)):
        if value <= 1:
            return "low"
        if value >= 3:
            return "high"
        return "medium"

    text = str(value).strip().lower()
    if text in {"low", "l", "1"}:
        return "low"
    if text in {"medium", "med", "m", "2"}:
        return "medium"
    if text in {"high", "h", "3"}:
        return "high"
    if text.isdigit():
        return _normalize_traffic_level(int(text))
    return DEFAULT_TRAFFIC_LEVEL


def _parse_coordinate_like(raw: Any) -> Optional[Dict[str, float]]:
    if raw is None:
        return None

    if isinstance(raw, dict):
        for lat_key, lon_key in [("lat", "lon"), ("latitude", "longitude"), ("current_lat", "current_lon")]:
            if lat_key in raw and lon_key in raw:
                try:
                    lat = float(raw[lat_key])
                    lon = float(raw[lon_key])
                except (TypeError, ValueError):
                    continue
                if validate_coordinates(lat, lon):
                    return {"lat": lat, "lon": lon}
        return None

    if isinstance(raw, (list, tuple)) and len(raw) == 2:
        try:
            lat = float(raw[0])
            lon = float(raw[1])
            if validate_coordinates(lat, lon):
                return {"lat": lat, "lon": lon}
        except (TypeError, ValueError):
            return None

    if isinstance(raw, str):
        parts = [p.strip() for p in raw.split(",") if p.strip()]
        if len(parts) == 2:
            try:
                lat = float(parts[0])
                lon = float(parts[1])
                if validate_coordinates(lat, lon):
                    return {"lat": lat, "lon": lon}
            except (TypeError, ValueError):
                pass

    return None


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lon1)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(math.radians(lat2)) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(min(1.0, a)))


def _traffic_value(level: Union[str, int, float, None]) -> float:
    level_str = _normalize_traffic_level(level)
    return float(parse_traffic_level(level_str))


def _estimate_speed_kmh(traffic_level: Union[str, int, float, None]) -> float:
    level = _normalize_traffic_level(traffic_level)
    speed = BASE_SPEED_KMH * TRAFFIC_SPEED_FACTORS.get(level, TRAFFIC_SPEED_FACTORS[DEFAULT_TRAFFIC_LEVEL])
    return max(speed, MIN_SPEED_KMH)


def format_eta(minutes: float) -> str:
    total_minutes = int(round(max(1.0, minutes)))
    if total_minutes < 60:
        return f"{total_minutes} mins"
    hours = total_minutes // 60
    mins = total_minutes % 60
    return f"{hours}h {mins}m" if mins else f"{hours}h"


def calculate_eta(distance_km: float, traffic_level: Union[str, int, float, None]) -> float:
    speed = _estimate_speed_kmh(traffic_level)
    return max(1.0, (distance_km / speed) * 60.0)


def calculate_route_score(distance_km: float, traffic_level: Union[str, int, float, None]) -> float:
    traffic_numeric = _traffic_value(traffic_level)
    return round(distance_km * DISTANCE_SCORE_WEIGHT + traffic_numeric * TRAFFIC_SCORE_WEIGHT, 3)


def _build_stop(stop: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not isinstance(stop, dict):
        return None
    coords = _parse_coordinate_like(stop)
    if not coords:
        return None
    return {
        "id": stop.get("id"),
        "label": stop.get("label") or stop.get("name") or stop.get("id"),
        "lat": coords["lat"],
        "lon": coords["lon"],
    }


def _normalize_stops(stops: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for stop in stops:
        if stop is None:
            continue
        if isinstance(stop, dict):
            built = _build_stop(stop)
        else:
            coords = _parse_coordinate_like(stop)
            built = {"id": None, "label": None, "lat": coords["lat"], "lon": coords["lon"]} if coords else None
        if built:
            normalized.append(built)
    return normalized


def _sequence_stops(start: Dict[str, float], stops: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], float]:
    remaining = [dict(stop) for stop in stops]
    ordered: List[Dict[str, Any]] = []
    legs: List[Dict[str, Any]] = []
    current = {"lat": float(start["lat"]), "lon": float(start["lon"])}
    total_distance = 0.0

    while remaining:
        nearest_index = 0
        nearest_distance = float("inf")
        for index, stop in enumerate(remaining):
            dist = _haversine_km(current["lat"], current["lon"], float(stop["lat"]), float(stop["lon"]))
            if dist < nearest_distance:
                nearest_distance = dist
                nearest_index = index
        next_stop = remaining.pop(nearest_index)
        legs.append(
            {
                "from": [current["lat"], current["lon"]],
                "to": [next_stop["lat"], next_stop["lon"]],
                "km": round(nearest_distance, 3),
                "stop_id": next_stop.get("id"),
                "label": next_stop.get("label"),
            }
        )
        total_distance += nearest_distance
        current = {"lat": float(next_stop["lat"]), "lon": float(next_stop["lon"])}
        ordered.append(next_stop)

    return ordered, legs, round(total_distance, 3)


def _improve_route_2opt(start: Dict[str, float], stops: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], float]:
    if len(stops) < 3:
        return _sequence_stops(start, stops)

    ordered, _, total_distance = _sequence_stops(start, stops)
    best_distance = total_distance
    improved = True

    while improved:
        improved = False
        for i in range(len(ordered) - 2):
            for j in range(i + 2, len(ordered)):
                new_order = ordered[: i + 1] + ordered[i + 1 : j + 1][::-1] + ordered[j + 1 :]
                current = {"lat": float(start["lat"]), "lon": float(start["lon"])}
                candidate_distance = 0.0
                for node in new_order:
                    candidate_distance += _haversine_km(current["lat"], current["lon"], node["lat"], node["lon"])
                    current = {"lat": float(node["lat"]), "lon": float(node["lon"])}
                if candidate_distance + 1e-6 < best_distance:
                    ordered = new_order
                    best_distance = candidate_distance
                    improved = True
                    break
            if improved:
                break

    _, legs, total_distance = _sequence_stops(start, ordered)
    return ordered, legs, round(total_distance, 3)


def optimize_multi_stop_route(
    start: Dict[str, float],
    stops: List[Dict[str, Any]],
    traffic_level: Union[str, int, float, None] = None,
) -> Dict[str, Any]:
    normalized_stops = _normalize_stops(stops)
    if not normalized_stops:
        return {
            "ordered_stops": [],
            "legs": [],
            "total_distance_km": 0.0,
            "route_score": calculate_route_score(0.0, traffic_level),
        }

    ordered_stops, legs, total_distance = _improve_route_2opt(start, normalized_stops)
    return {
        "ordered_stops": ordered_stops,
        "legs": legs,
        "total_distance_km": total_distance,
        "route_score": calculate_route_score(total_distance, traffic_level),
    }


def _build_driver_record(driver: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    location = _parse_coordinate_like(driver.get("location") if isinstance(driver.get("location"), (str, list, tuple, dict)) else driver)
    if not location:
        return None
    return {
        "id": driver.get("id"),
        "name": driver.get("name"),
        "status": str(driver.get("status", "available")).lower(),
        "location": location,
        "assigned_orders": int(driver.get("assigned_orders", 0) or 0),
    }


def select_available_drivers(drivers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    available = []
    for driver in drivers:
        record = _build_driver_record(driver)
        if not record:
            continue
        if record["status"] in {"available", "idle", "ready"}:
            available.append(record)
    return available or [_build_driver_record(driver) for driver in drivers if _build_driver_record(driver)]


def find_best_driver(
    customer_location: Dict[str, float],
    drivers: List[Dict[str, Any]],
    traffic_level: Union[str, int, float, None] = None,
    stops: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    candidates = select_available_drivers(drivers)
    if not candidates:
        return None, {
            "ordered_stops": [],
            "legs": [],
            "total_distance_km": 0.0,
            "route_score": calculate_route_score(0.0, traffic_level),
        }

    best_candidate = None
    best_plan: Dict[str, Any] = {}
    best_score = float("inf")

    route_targets: List[Dict[str, Any]] = []
    if stops:
        route_targets.extend(stops)
    route_targets.append({"lat": customer_location["lat"], "lon": customer_location["lon"], "id": customer_location.get("id"), "label": customer_location.get("label")})

    for driver in candidates:
        start = driver["location"]
        plan = optimize_multi_stop_route(start, route_targets, traffic_level)
        penalty = min(driver.get("assigned_orders", 0) * 0.2, 2.0)
        score = plan["route_score"] + penalty
        if score < best_score:
            best_score = score
            best_candidate = driver
            best_plan = plan

    return best_candidate, best_plan


def optimize_route(
    driver_location: Any,
    customer_location: Any,
    traffic_level: Union[str, int, float, None] = None,
    drivers: Optional[List[Dict[str, Any]]] = None,
    stops: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    traffic = _normalize_traffic_level(traffic_level)
    start = _parse_coordinate_like(driver_location) if driver_location is not None else None
    destination = _parse_coordinate_like(customer_location)

    if not destination:
        raise ValueError("customer_location must contain valid latitude and longitude")

    if drivers:
        best_driver, plan = find_best_driver(destination, drivers, traffic, stops)
    else:
        if not start:
            raise ValueError("driver_location is required when no driver list is provided")
        route_targets: List[Dict[str, Any]] = stops or []
        route_targets.append({"lat": destination["lat"], "lon": destination["lon"], "id": "customer", "label": "Customer"})
        plan = optimize_multi_stop_route(start, route_targets, traffic)
        best_driver = {
            "id": None,
            "name": None,
            "status": "unassigned",
            "location": start,
            "assigned_orders": 0,
        }

    total_distance = float(plan.get("total_distance_km", 0.0))
    eta_minutes = calculate_eta(total_distance, traffic)

    return {
        "driver_id": best_driver.get("id"),
        "driver_name": best_driver.get("name"),
        "driver_status": best_driver.get("status"),
        "driver_location": best_driver.get("location"),
        "customer_location": destination,
        "traffic": traffic,
        "distance": f"{total_distance:.2f} km",
        "distance_km": round(total_distance, 3),
        "eta": format_eta(eta_minutes),
        "eta_minutes": round(eta_minutes, 1),
        "route_score": round(calculate_route_score(total_distance, traffic), 3),
        "assigned_orders": best_driver.get("assigned_orders"),
        "ordered_stops": plan.get("ordered_stops", []),
        "legs": plan.get("legs", []),
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }


def recalculate_route_if_needed(
    current_plan: Dict[str, Any],
    drivers: List[Dict[str, Any]],
    new_traffic_level: Union[str, int, float, None] = None,
    unavailable_driver_ids: Optional[List[Any]] = None,
) -> Dict[str, Any]:
    unavailable_driver_ids = unavailable_driver_ids or []
    current_driver_id = current_plan.get("driver_id")
    current_traffic = current_plan.get("traffic")
    destination = current_plan.get("customer_location")
    stops = current_plan.get("ordered_stops") or []

    if current_driver_id in unavailable_driver_ids:
        reason = "Assigned driver became unavailable"
    elif new_traffic_level is not None and TRAFFIC_ORDER[_normalize_traffic_level(new_traffic_level)] > TRAFFIC_ORDER[_normalize_traffic_level(current_traffic)]:
        reason = "Traffic increased"
    else:
        return {**current_plan, "recalculated": False, "reason": "No reoptimization needed"}

    new_plan = optimize_route(
        driver_location=current_plan.get("driver_location", {}),
        customer_location=destination,
        traffic_level=new_traffic_level or current_traffic,
        drivers=drivers,
        stops=stops,
    )
    return {**new_plan, "recalculated": True, "reason": reason}


def optimize_delivery_order(
    depot: Dict[str, float],
    stops: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    depot: {lat, lon}
    stops: [{id, lat, lon, label?}, ...]
    Returns ordered stop ids using nearest neighbor from depot then chain.
    """
    if not stops:
        return {"ordered_ids": [], "total_km": 0.0, "legs": []}

    remaining = [dict(s) for s in stops]
    ordered: List[Dict[str, Any]] = []
    cur_lat, cur_lon = float(depot["lat"]), float(depot["lon"])
    total_km = 0.0
    legs: List[Dict[str, Any]] = []

    while remaining:
        best_i = 0
        best_d = float("inf")
        for i, s in enumerate(remaining):
            d = _haversine_km(cur_lat, cur_lon, float(s["lat"]), float(s["lon"]))
            if d < best_d:
                best_d = d
                best_i = i
        nxt = remaining.pop(best_i)
        total_km += best_d
        legs.append(
            {
                "from": [cur_lat, cur_lon],
                "to": [float(nxt["lat"]), float(nxt["lon"])],
                "km": round(best_d, 3),
                "stop_id": nxt.get("id"),
            }
        )
        cur_lat, cur_lon = float(nxt["lat"]), float(nxt["lon"])
        ordered.append(nxt)

    return {
        "ordered_ids": [s.get("id") for s in ordered],
        "ordered_stops": ordered,
        "total_km": round(total_km, 3),
        "legs": legs,
        "algorithm": "nearest_neighbor",
    }
