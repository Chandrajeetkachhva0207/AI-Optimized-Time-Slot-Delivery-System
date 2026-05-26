"""
REST API for AI Time Slot Delivery operations (admin).
Prefix: /api/delivery
"""
import os
import re
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, session, Response
from sqlalchemy import func  # noqa: F401 — used in date filters

from models.database import db, Agent, TimeSlot, DeliveryOrder, User
from services.slot_ai import recommend_least_busy_slot
from services.demand_ml import predict_peak_hours, train_demand_model_if_needed
from services.route_opt import optimize_delivery_order, optimize_route, recalculate_route_if_needed
from utils.maps_api import MapsAPI

delivery_ops_bp = Blueprint("delivery_ops", __name__, url_prefix="/api/delivery")


def admin_required(f):
    from functools import wraps

    @wraps(f)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            return jsonify({"success": False, "error": "Admin authentication required"}), 403
        return f(*args, **kwargs)

    return wrapped


# ---------------------------------------------------------------------------
# Orders (operational)
# ---------------------------------------------------------------------------


@delivery_ops_bp.route("/orders", methods=["GET"])
@admin_required
def list_orders():
    q = DeliveryOrder.query
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    status = request.args.get("status")
    slot = request.args.get("slot")

    if date_from:
        try:
            df = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
            q = q.filter(DeliveryOrder.created_at >= df)
        except Exception:
            pass
    if date_to:
        try:
            dt = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
            q = q.filter(DeliveryOrder.created_at <= dt + timedelta(days=1))
        except Exception:
            pass
    if status:
        q = q.filter(DeliveryOrder.status == status)
    if slot:
        q = q.filter(DeliveryOrder.slot.ilike(f"%{slot}%"))

    rows = q.order_by(DeliveryOrder.created_at.desc()).all()
    return jsonify({"success": True, "orders": [o.to_dict() for o in rows]})


@delivery_ops_bp.route("/orders", methods=["POST"])
@admin_required
def create_order():
    data = request.get_json() or {}
    customer = data.get("customer")
    address = data.get("address")
    slot_label = data.get("slot")
    status = data.get("status", "Pending")
    agent_id = data.get("agent_id")
    timeslot_id = data.get("timeslot_id")

    if not customer or not address:
        return jsonify({"success": False, "error": "customer and address required"}), 400

    # Increment booked if timeslot linked
    ts = None
    if timeslot_id:
        ts = TimeSlot.query.get(timeslot_id)
        if ts and ts.booked < ts.capacity:
            ts.booked = (ts.booked or 0) + 1
    elif slot_label:
        ts = TimeSlot.query.filter(TimeSlot.slot == slot_label).first()
        if ts and ts.booked < ts.capacity:
            ts.booked = (ts.booked or 0) + 1
            timeslot_id = ts.id

    order = DeliveryOrder(
        customer=customer,
        address=address,
        slot=slot_label or (ts.slot if ts else None),
        status=status,
        agent_id=agent_id if agent_id else None,
        timeslot_id=timeslot_id,
    )
    db.session.add(order)
    db.session.commit()
    return jsonify({"success": True, "order": order.to_dict()}), 201


@delivery_ops_bp.route("/orders/<int:order_id>", methods=["PATCH", "PUT"])
@admin_required
def update_order(order_id):
    order = DeliveryOrder.query.get(order_id)
    if not order:
        return jsonify({"success": False, "error": "Order not found"}), 404
    data = request.get_json() or {}
    if "status" in data:
        order.status = data["status"]
    if "agent_id" in data:
        order.agent_id = data["agent_id"]
    if "slot" in data:
        order.slot = data["slot"]
    if "address" in data:
        order.address = data["address"]
    db.session.commit()
    return jsonify({"success": True, "order": order.to_dict()})


# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------


@delivery_ops_bp.route("/agents", methods=["GET"])
@admin_required
def list_agents():
    agents = Agent.query.order_by(Agent.id).all()
    return jsonify({"success": True, "agents": [a.to_dict() for a in agents]})


@delivery_ops_bp.route("/agents", methods=["POST"])
@admin_required
def create_agent():
    data = request.get_json() or {}
    name = data.get("name")
    if not name:
        return jsonify({"success": False, "error": "name required"}), 400
    a = Agent(
        name=name,
        status=data.get("status", "available"),
        location=data.get("location", ""),
    )
    db.session.add(a)
    db.session.commit()
    return jsonify({"success": True, "agent": a.to_dict()}), 201


@delivery_ops_bp.route("/agents/<int:agent_id>", methods=["PATCH"])
@admin_required
def update_agent(agent_id):
    a = Agent.query.get(agent_id)
    if not a:
        return jsonify({"success": False, "error": "Agent not found"}), 404
    data = request.get_json() or {}
    for k in ("name", "status", "location"):
        if k in data:
            setattr(a, k, data[k])
    db.session.commit()
    return jsonify({"success": True, "agent": a.to_dict()})


# ---------------------------------------------------------------------------
# Time slots
# ---------------------------------------------------------------------------


@delivery_ops_bp.route("/timeslots", methods=["GET"])
@admin_required
def list_timeslots():
    slots = TimeSlot.query.order_by(TimeSlot.id).all()
    return jsonify({"success": True, "timeslots": [s.to_dict() for s in slots]})


@delivery_ops_bp.route("/timeslots/<int:slot_id>", methods=["PATCH", "PUT"])
@admin_required
def update_timeslot(slot_id):
    s = TimeSlot.query.get(slot_id)
    if not s:
        return jsonify({"success": False, "error": "Time slot not found"}), 404
    data = request.get_json() or {}
    if "capacity" in data:
        s.capacity = int(data["capacity"])
    if "booked" in data:
        s.booked = int(data["booked"])
    if "slot" in data:
        s.slot = data["slot"]
    db.session.commit()
    return jsonify({"success": True, "timeslot": s.to_dict()})


# ---------------------------------------------------------------------------
# Analytics & AI
# ---------------------------------------------------------------------------


@delivery_ops_bp.route("/analytics", methods=["GET"])
@admin_required
def analytics():
    total_orders = DeliveryOrder.query.count()
    active = DeliveryOrder.query.filter(
        DeliveryOrder.status.in_(["Pending", "Packed", "Shipped", "Out for Delivery"])
    ).count()
    failed = DeliveryOrder.query.filter(DeliveryOrder.status == "Failed").count()

    slots = TimeSlot.query.all()
    total_cap = sum(s.capacity or 0 for s in slots) or 1
    total_booked = sum(s.booked or 0 for s in slots)
    slot_usage_pct = round(100.0 * total_booked / total_cap, 1)

    # Hourly counts from delivery_orders for ML (Python bucket — SQLite-safe)
    from collections import defaultdict

    bucket = defaultdict(float)
    for row in DeliveryOrder.query.all():
        if row.created_at:
            bucket[row.created_at.hour] += 1.0
    oc = [(h, bucket[h]) for h in sorted(bucket.keys())] if bucket else []
    train_demand_model_if_needed(oc)
    demand = predict_peak_hours()

    # Orders per day (last 7 days) for chart
    chart_labels = []
    chart_values = []
    for i in range(6, -1, -1):
        day = datetime.utcnow().date() - timedelta(days=i)
        chart_labels.append(day.isoformat())
        c = DeliveryOrder.query.filter(
            func.date(DeliveryOrder.created_at) == day
        ).count()
        chart_values.append(c)

    return jsonify(
        {
            "success": True,
            "summary": {
                "total_orders": total_orders,
                "active_deliveries": active,
                "time_slot_usage_pct": slot_usage_pct,
                "failed_deliveries": failed,
            },
            "charts": {
                "orders_last_7_days": {"labels": chart_labels, "values": chart_values},
                "demand_by_hour": demand.get("hourly_demand", []),
            },
            "ai": {
                "peak_hours": demand.get("peak_hours", []),
                "demand_note": demand.get("note", ""),
            },
        }
    )


@delivery_ops_bp.route("/ai/recommend-slot", methods=["GET"])
@admin_required
def ai_recommend_slot():
    slots = [s.to_dict() for s in TimeSlot.query.all()]
    best = recommend_least_busy_slot(slots)
    return jsonify({"success": True, "recommended": best, "all_slots": slots})


@delivery_ops_bp.route("/ai/demand", methods=["GET"])
@admin_required
def ai_demand():
    return jsonify(predict_peak_hours())


def _known_location(raw, label=None):
    if not isinstance(raw, str):
        return None
    cities = {
        "mumbai": {"lat": 19.076, "lon": 72.8777, "label": "Mumbai"},
        "pune": {"lat": 18.5204, "lon": 73.8567, "label": "Pune"},
        "delhi": {"lat": 28.7041, "lon": 77.1025, "label": "Delhi"},
        "bangalore": {"lat": 12.9716, "lon": 77.5946, "label": "Bangalore"},
        "bengaluru": {"lat": 12.9716, "lon": 77.5946, "label": "Bengaluru"},
        "hyderabad": {"lat": 17.3850, "lon": 78.4867, "label": "Hyderabad"},
        "chennai": {"lat": 13.0827, "lon": 80.2707, "label": "Chennai"},
        "kolkata": {"lat": 22.5726, "lon": 88.3639, "label": "Kolkata"},
        "jaipur": {"lat": 26.9124, "lon": 75.7873, "label": "Jaipur"},
        "ahmedabad": {"lat": 23.0225, "lon": 72.5714, "label": "Ahmedabad"},
    }
    return cities.get(raw.strip().lower())


def _parse_location(raw, label=None):
    if not raw:
        return None

    if isinstance(raw, dict):
        lat = raw.get("lat")
        lon = raw.get("lon")
        if lat is not None and lon is not None:
            return {"id": raw.get("id") or label, "lat": float(lat), "lon": float(lon), "label": raw.get("label") or label}

    if isinstance(raw, (list, tuple)) and len(raw) == 2:
        try:
            return {"id": label, "lat": float(raw[0]), "lon": float(raw[1]), "label": label}
        except (TypeError, ValueError):
            return None

    if isinstance(raw, str):
        normalized = raw.strip()
        # Support slash-separated city pairs like "Mumbai/Pune" by parsing the first known match.
        if "/" in normalized or " to " in normalized.lower():
            for token in re.split(r"[\/\\]|\s+to\s+|->|–|—", normalized, flags=re.I):
                candidate = _parse_location(token, label=label)
                if candidate:
                    return candidate

        parts = [p.strip() for p in normalized.split(",") if p.strip()]
        if len(parts) == 2 and parts[0].replace('.', '', 1).replace('-', '', 1).isdigit() and parts[1].replace('.', '', 1).replace('-', '', 1).isdigit():
            return {"id": label, "lat": float(parts[0]), "lon": float(parts[1]), "label": label or raw}

        city = _known_location(normalized)
        if city:
            return {"id": label or city["label"].lower(), "lat": city["lat"], "lon": city["lon"], "label": raw}

        api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
        if api_key:
            geo = MapsAPI(api_key=api_key).geocode_address(raw)
            if geo and geo.get("latitude") is not None and geo.get("longitude") is not None:
                return {"id": label, "lat": float(geo["latitude"]), "lon": float(geo["longitude"]), "label": raw}

    return None


@delivery_ops_bp.route("/ai/optimize-route", methods=["POST"])
@admin_required
def ai_optimize_route():
    data = request.get_json() or {}
    traffic = data.get("traffic")
    customer_location = data.get("customer_location") or data.get("destination")
    driver_location = data.get("driver_location") or data.get("source")
    stops = data.get("stops") or []
    provided_drivers = data.get("drivers")

    if not customer_location:
        return jsonify({"success": False, "error": "customer_location or destination is required."}), 400

    try:
        if provided_drivers and not isinstance(provided_drivers, list):
            return jsonify({"success": False, "error": "drivers must be an array if provided."}), 400

        if provided_drivers:
            drivers = provided_drivers
        else:
            drivers = []
            for agent in Agent.query.order_by(Agent.id).all():
                loc = _parse_location(agent.location, label=agent.name)
                if not loc:
                    continue
                drivers.append({
                    "id": agent.id,
                    "name": agent.name,
                    "status": agent.status,
                    "location": loc,
                    "assigned_orders": agent.deliveries.count(),
                })

        result = optimize_route(
            driver_location=driver_location,
            customer_location=customer_location,
            traffic_level=traffic,
            drivers=drivers if drivers else None,
            stops=stops,
        )
        return jsonify({"success": True, **result})
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


# ---------------------------------------------------------------------------
# Agent locations for live tracking
# ---------------------------------------------------------------------------


@delivery_ops_bp.route("/agent-locations", methods=["GET"])
def agent_locations():
    if not session.get("user_id") and not session.get("is_admin"):
        return jsonify({"success": False, "error": "Authentication required"}), 401

    agents = Agent.query.order_by(Agent.id).all()
    locations = []
    for agent in agents:
        loc = _parse_location(agent.location, label=f"agent-{agent.id}")
        if not loc:
            continue
        locations.append({
            "id": agent.id,
            "name": agent.name,
            "status": agent.status,
            "lat": loc["lat"],
            "lon": loc["lon"],
        })

    return jsonify({"success": True, "agents": locations})


# ---------------------------------------------------------------------------
# Customers (registered users)
# ---------------------------------------------------------------------------


@delivery_ops_bp.route("/customers", methods=["GET"])
@admin_required
def list_customers():
    users = User.query.filter_by(is_admin=0).order_by(User.id.desc()).all()
    return jsonify(
        {
            "success": True,
            "customers": [
                {"id": u.id, "name": u.name, "email": u.email} for u in users
            ],
        }
    )


# ---------------------------------------------------------------------------
# Export CSV
# ---------------------------------------------------------------------------


@delivery_ops_bp.route("/export/orders", methods=["GET"])
@admin_required
def export_orders_csv():
    rows = DeliveryOrder.query.order_by(DeliveryOrder.created_at.desc()).all()
    lines = ["id,customer,address,slot,status,agent_id,created_at"]
    for o in rows:
        safe = lambda s: (s or "").replace('"', '""')
        lines.append(
            f'{o.id},"{safe(o.customer)}","{safe(o.address)}","{safe(o.slot)}",{o.status},{o.agent_id or ""},{o.created_at}'
        )
    csv_data = "\n".join(lines)
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=delivery_orders.csv"},
    )
