"""Admin blueprint - dashboard, orders, customers"""
from flask import Blueprint, request, jsonify, session
from sqlalchemy import func
from models.database import db, User, Order

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


def admin_required(f):
    """Require admin session"""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('is_admin'):
            return jsonify({"success": False, "error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/orders', methods=['GET'])
@admin_required
def get_orders():
    """Get all orders"""
    try:
        orders = Order.query.order_by(Order.created_at.desc()).all()
        return jsonify({
            "success": True,
            "orders": [o.to_dict() for o in orders]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route('/customers', methods=['GET'])
@admin_required
def get_customers():
    """Get all customers (users where is_admin=0)"""
    try:
        customers = User.query.filter_by(is_admin=0).order_by(User.id.desc()).all()
        return jsonify({
            "success": True,
            "customers": [c.to_dict() for c in customers]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def get_dashboard():
    """Dashboard stats - total customers, total orders"""
    try:
        total_customers = User.query.filter_by(is_admin=0).count()
        total_orders = Order.query.count()
        recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
        pending_orders = Order.query.filter(func.lower(Order.order_status) == 'pending').count()
        packed_orders = Order.query.filter(func.lower(Order.order_status) == 'packed').count()
        shipped_orders = Order.query.filter(func.lower(Order.order_status) == 'shipped').count()
        out_for_delivery_orders = Order.query.filter(func.lower(Order.order_status) == 'out for delivery').count()
        delivered_orders = Order.query.filter(func.lower(Order.order_status) == 'delivered').count()
        failed_orders = Order.query.filter(func.lower(Order.order_status) == 'failed').count()
        return jsonify({
            "success": True,
            "dashboard": {
                "total_customers": total_customers,
                "total_orders": total_orders,
                "pending_orders": pending_orders,
                "packed_orders": packed_orders,
                "shipped_orders": shipped_orders,
                "out_for_delivery_orders": out_for_delivery_orders,
                "delivered_orders": delivered_orders,
                "failed_orders": failed_orders,
                "recent_orders": [o.to_dict() for o in recent_orders]
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route('/orders/<int:order_id>/status', methods=['PUT'])
@admin_required
def update_order_status(order_id):
    """Admin updates order status"""
    try:
        data = request.get_json(silent=True) or {}
        status = (data.get('order_status') or data.get('status') or '').strip()
        normalized_statuses = {
            'pending': 'Pending',
            'packed': 'Packed',
            'shipped': 'Shipped',
            'out for delivery': 'Out for Delivery',
            'delivered': 'Delivered',
            'failed': 'Failed',
        }
        status_key = status.lower()
        status = normalized_statuses.get(status_key)
        if not status:
            return jsonify({"success": False, "error": "Valid order_status required"}), 400

        order = Order.query.get(order_id)
        if not order:
            return jsonify({"success": False, "error": "Order not found"}), 404

        order.order_status = status
        db.session.commit()
        return jsonify({"success": True, "message": "Order status updated", "order_status": order.order_status})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route('/deleteOrder/<int:order_id>', methods=['DELETE'])
@admin_required
def delete_order(order_id):
    """Delete an order from the database"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({"success": False, "error": "Order not found"}), 404

        db.session.delete(order)
        db.session.commit()
        return jsonify({"success": True, "message": "Order deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
