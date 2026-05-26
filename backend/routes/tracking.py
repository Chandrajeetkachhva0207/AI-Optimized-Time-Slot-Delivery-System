"""
Live Location Tracking API for product delivery.
Prefix: /api/tracking

Provides:
  - GET  /api/tracking/<order_id>       → current delivery location, ETA, route, status
  - POST /api/tracking/<order_id>/start  → admin starts delivery (sets agent, origin)
  - GET  /api/tracking/active            → all currently active deliveries
"""
import math
import random
import time
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, session, request
from models.database import db, Order, Agent

tracking_bp = Blueprint("tracking", __name__, url_prefix="/api/tracking")

# ─── In-memory delivery simulations ───
# Keyed by order_id → simulation state dict
_active_deliveries = {}

# Warehouse coordinates (Mumbai)
WAREHOUSE = (19.0760, 72.8777)

# Simulated destination coordinates around Mumbai for demo
DEMO_DESTINATIONS = [
    (19.2183, 72.9781, "Thane"),
    (19.0330, 73.0297, "Navi Mumbai"),
    (18.9388, 72.8354, "Colaba"),
    (19.1136, 72.8697, "Andheri"),
    (19.1760, 72.9477, "Mulund"),
    (19.0596, 72.8295, "Worli"),
    (19.0176, 72.8562, "Dadar"),
    (19.1335, 72.9146, "Powai"),
    (19.0454, 72.8220, "Bandra"),
    (19.1969, 72.8478, "Borivali"),
]


def _haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(min(1.0, a)))


def _interpolate(lat1, lon1, lat2, lon2, fraction):
    """Linear interpolation between two points."""
    return (
        lat1 + (lat2 - lat1) * fraction,
        lon1 + (lon2 - lon1) * fraction,
    )


def _generate_route_points(origin, destination, num_points=12):
    """Generate intermediate waypoints with slight random offsets for realism."""
    points = [origin]
    for i in range(1, num_points):
        frac = i / num_points
        lat, lon = _interpolate(origin[0], origin[1], destination[0], destination[1], frac)
        # Add slight random deviation for realistic road movement
        lat += random.uniform(-0.003, 0.003)
        lon += random.uniform(-0.003, 0.003)
        points.append((round(lat, 6), round(lon, 6)))
    points.append(destination)
    return points


def _get_delivery_status_label(progress_pct):
    if progress_pct >= 100:
        return "Delivered"
    if progress_pct >= 85:
        return "Arriving Soon"
    if progress_pct >= 60:
        return "On The Way"
    if progress_pct >= 30:
        return "In Transit"
    if progress_pct >= 5:
        return "Picked Up"
    return "Preparing"


def _ensure_simulation(order_id):
    """Ensure a simulation exists for this order, create one if needed."""
    if order_id in _active_deliveries:
        sim = _active_deliveries[order_id]
        # Advance the simulation
        elapsed = time.time() - sim["start_time"]
        # Full journey takes ~180 seconds for demo purposes
        journey_duration = sim.get("journey_duration", 180)
        progress = min(1.0, elapsed / journey_duration)
        sim["progress"] = progress

        route = sim["route_points"]
        idx = min(int(progress * (len(route) - 1)), len(route) - 1)
        # Smooth interpolation between waypoints
        segment_frac = (progress * (len(route) - 1)) - idx
        if idx < len(route) - 1:
            cur_lat, cur_lon = _interpolate(
                route[idx][0], route[idx][1],
                route[idx + 1][0], route[idx + 1][1],
                segment_frac
            )
        else:
            cur_lat, cur_lon = route[-1]

        sim["current_lat"] = round(cur_lat, 6)
        sim["current_lon"] = round(cur_lon, 6)

        total_km = sim["total_distance_km"]
        remaining_km = total_km * (1 - progress)
        # Estimated speed ~30 km/h in city
        eta_minutes = max(0, int((remaining_km / 30) * 60))
        sim["eta_minutes"] = eta_minutes
        sim["remaining_km"] = round(remaining_km, 2)
        sim["status"] = _get_delivery_status_label(progress * 100)

        return sim

    # Create new simulation
    dest = random.choice(DEMO_DESTINATIONS)
    route = _generate_route_points(WAREHOUSE, (dest[0], dest[1]), num_points=15)
    total_km = 0
    for i in range(len(route) - 1):
        total_km += _haversine_km(route[i][0], route[i][1], route[i + 1][0], route[i + 1][1])

    agent_names = ["Ramesh Kumar", "Priya Shah", "Vikram Desai", "Sneha Iyer", "Amit Verma"]

    sim = {
        "order_id": order_id,
        "agent_name": random.choice(agent_names),
        "agent_phone": f"+91 98{random.randint(100,999)}  {random.randint(10000,99999)}",
        "vehicle": random.choice(["Bike", "Van", "Tempo"]),
        "vehicle_number": f"MH-{random.randint(1,50):02d}-{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}-{random.randint(1000,9999)}",
        "origin": {"lat": WAREHOUSE[0], "lon": WAREHOUSE[1], "label": "SmartParcel Warehouse"},
        "destination": {"lat": dest[0], "lon": dest[1], "label": dest[2]},
        "route_points": route,
        "total_distance_km": round(total_km, 2),
        "current_lat": WAREHOUSE[0],
        "current_lon": WAREHOUSE[1],
        "progress": 0.0,
        "eta_minutes": int((total_km / 30) * 60),
        "remaining_km": round(total_km, 2),
        "status": "Preparing",
        "start_time": time.time(),
        "journey_duration": random.randint(150, 240),  # 2.5 to 4 minutes demo
        "timeline": [
            {"time": datetime.now().strftime("%H:%M"), "event": "Order Confirmed", "done": True},
            {"time": (datetime.now() + timedelta(minutes=2)).strftime("%H:%M"), "event": "Packed & Ready", "done": True},
            {"time": (datetime.now() + timedelta(minutes=5)).strftime("%H:%M"), "event": "Picked Up by Agent", "done": False},
            {"time": (datetime.now() + timedelta(minutes=15)).strftime("%H:%M"), "event": "In Transit", "done": False},
            {"time": (datetime.now() + timedelta(minutes=25)).strftime("%H:%M"), "event": "Near Destination", "done": False},
            {"time": (datetime.now() + timedelta(minutes=35)).strftime("%H:%M"), "event": "Delivered", "done": False},
        ],
    }
    _active_deliveries[order_id] = sim
    return sim


def _build_timeline(sim):
    """Update timeline based on progress."""
    progress = sim["progress"]
    thresholds = [0, 0.05, 0.15, 0.40, 0.80, 1.0]
    timeline = sim["timeline"]
    for i, t in enumerate(thresholds):
        if i < len(timeline):
            timeline[i]["done"] = progress >= t
            if progress >= t and i > 0:
                timeline[i]["time"] = datetime.now().strftime("%H:%M")
    return timeline


# ─── ROUTES ───


def _login_required_or_admin(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id") and not session.get("is_admin"):
            return jsonify({"success": False, "error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated


@tracking_bp.route("/<int:order_id>", methods=["GET"])
@_login_required_or_admin
def get_tracking(order_id):
    """Get live tracking data for a specific order."""
    # Verify order belongs to user (or user is admin)
    if not session.get("is_admin"):
        order = Order.query.filter_by(id=order_id, user_id=session.get("user_id")).first()
        if not order:
            return jsonify({"success": False, "error": "Order not found"}), 404

    sim = _ensure_simulation(order_id)
    timeline = _build_timeline(sim)

    # Route polyline for the map
    route_coords = [[p[0], p[1]] for p in sim["route_points"]]

    # Completed portion of route
    progress = sim["progress"]
    completed_idx = int(progress * (len(route_coords) - 1))
    completed_route = route_coords[:completed_idx + 1]
    remaining_route = route_coords[completed_idx:]

    return jsonify({
        "success": True,
        "order_id": order_id,
        "agent": {
            "name": sim["agent_name"],
            "phone": sim["agent_phone"],
            "vehicle": sim["vehicle"],
            "vehicle_number": sim["vehicle_number"],
        },
        "current_location": {
            "lat": sim["current_lat"],
            "lon": sim["current_lon"],
        },
        "origin": sim["origin"],
        "destination": sim["destination"],
        "status": sim["status"],
        "progress_pct": round(sim["progress"] * 100, 1),
        "eta_minutes": sim["eta_minutes"],
        "remaining_km": sim["remaining_km"],
        "total_distance_km": sim["total_distance_km"],
        "route": route_coords,
        "completed_route": completed_route,
        "remaining_route": remaining_route,
        "timeline": timeline,
        "updated_at": datetime.now().isoformat(),
    })


@tracking_bp.route("/active", methods=["GET"])
@_login_required_or_admin
def active_deliveries():
    """Get all active deliveries for current user."""
    user_id = session.get("user_id")
    is_admin = session.get("is_admin")

    if is_admin:
        orders = Order.query.filter(
            Order.order_status.in_(["Pending", "Packed", "Shipped", "Out for Delivery"])
        ).all()
    else:
        orders = Order.query.filter_by(user_id=user_id).filter(
            Order.order_status.in_(["Pending", "Packed", "Shipped", "Out for Delivery"])
        ).all()

    active = []
    for order in orders:
        sim = _ensure_simulation(order.id)
        active.append({
            "order_id": order.id,
            "product_name": order.product_name,
            "status": sim["status"],
            "progress_pct": round(sim["progress"] * 100, 1),
            "eta_minutes": sim["eta_minutes"],
            "agent_name": sim["agent_name"],
            "current_location": {
                "lat": sim["current_lat"],
                "lon": sim["current_lon"],
            },
        })

    return jsonify({"success": True, "deliveries": active})


@tracking_bp.route("/<int:order_id>/start", methods=["POST"])
@_login_required_or_admin
def start_tracking(order_id):
    """Start or restart tracking simulation for an order."""
    # Remove existing simulation to restart
    if order_id in _active_deliveries:
        del _active_deliveries[order_id]

    sim = _ensure_simulation(order_id)
    return jsonify({
        "success": True,
        "message": f"Tracking started for order #{order_id}",
        "agent": sim["agent_name"],
        "eta_minutes": sim["eta_minutes"],
    })
