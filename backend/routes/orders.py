"""Orders blueprint - products, cart, checkout"""
from flask import Blueprint, request, jsonify, session
from models.database import db, User, Product, Cart, Order

orders_bp = Blueprint('orders', __name__, url_prefix='/api')


def login_required(f):
    """Decorator to require login - check session or return 401"""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"success": False, "error": "Login required"}), 401
        return f(*args, **kwargs)
    return decorated


@orders_bp.route('/products', methods=['GET'])
def get_products():
    """Get all products"""
    try:
        products = Product.query.all()
        return jsonify({
            "success": True,
            "products": [p.to_dict() for p in products]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@orders_bp.route('/add-to-cart', methods=['POST'])
@login_required
def add_to_cart():
    """Add product to cart"""
    try:
        user_id = session.get('user_id')
        data = request.get_json(silent=True) or request.form or {}

        def _to_int(val, default=None):
            try:
                return int(val)
            except Exception:
                return default

        product_id = _to_int(data.get('product_id'))
        quantity = _to_int(data.get('quantity', 1), 1)
        
        if not product_id:
            return jsonify({"success": False, "error": "product_id required"}), 400
        
        product = Product.query.get(product_id)
        if not product:
            return jsonify({"success": False, "error": "Product not found"}), 404
        
        if quantity < 1:
            quantity = 1
        
        cart_item = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()
        if cart_item:
            cart_item.quantity += quantity
        else:
            cart_item = Cart(user_id=user_id, product_id=product_id, quantity=quantity)
            db.session.add(cart_item)
        
        db.session.commit()
        return jsonify({"success": True, "message": f"{product.name} added to cart"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@orders_bp.route('/cart', methods=['GET'])
@login_required
def get_cart():
    """Get current user's cart"""
    try:
        user_id = session.get('user_id')
        cart_items = Cart.query.filter_by(user_id=user_id).all()
        total = sum(item.quantity * item.product.price for item in cart_items)
        return jsonify({
            "success": True,
            "cart": [item.to_dict() for item in cart_items],
            "total": round(total, 2)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@orders_bp.route('/cart/<int:item_id>', methods=['DELETE'])
@login_required
def remove_from_cart(item_id):
    """Remove item from cart"""
    try:
        user_id = session.get('user_id')
        item = Cart.query.filter_by(id=item_id, user_id=user_id).first()
        if not item:
            return jsonify({"success": False, "error": "Item not found"}), 404
        db.session.delete(item)
        db.session.commit()
        return jsonify({"success": True, "message": "Removed from cart"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@orders_bp.route('/cart/<int:item_id>', methods=['PUT'])
@login_required
def update_cart_item(item_id):
    """Update quantity for a cart item"""
    try:
        user_id = session.get('user_id')
        data = request.get_json() or {}
        qty = int(data.get('quantity', 1))
        if qty < 1:
            # If qty < 1 behave like delete
            item = Cart.query.filter_by(id=item_id, user_id=user_id).first()
            if item:
                db.session.delete(item)
                db.session.commit()
            return jsonify({"success": True})

        item = Cart.query.filter_by(id=item_id, user_id=user_id).first()
        if not item:
            return jsonify({"success": False, "error": "Item not found"}), 404
        item.quantity = qty
        db.session.commit()
        return jsonify({"success": True, "item": item.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@orders_bp.route('/checkout', methods=['POST'])
@login_required
def checkout():
    """
    Place order - calls predict_slot, saves order.
    Expects: distance, traffic, weather (optional - defaults used)
    """
    try:
        user_id = session.get('user_id')
        data = request.get_json() or request.form
        
        cart_items = Cart.query.filter_by(user_id=user_id).all()
        if not cart_items:
            return jsonify({"success": False, "error": "Cart is empty"}), 400
        
        distance = float(data.get('distance', 10))
        traffic = data.get('traffic', 'medium')
        weather = data.get('weather', 'sunny')
        order_hour = int(data.get('order_hour', __import__('datetime').datetime.now().hour))
        package_weight = float(data.get('package_weight', 2.0))
        prev_avail = int(data.get('previous_customer_availability', 1))
        
        product_names = []
        total_price = 0
        for item in cart_items:
            product_names.append(f"{item.product.name} x{item.quantity}")
            total_price += item.product.price * item.quantity
        
        product_name_str = ", ".join(product_names)
        
        # Get prediction from predict_slot logic
        from routes.delivery import predict_slot_internal
        predicted_slot = predict_slot_internal(distance, traffic, weather, order_hour, package_weight=package_weight)
        
        # Simulated successful payment
        payment_id = f"PAY-{user_id}-{order_hour}"
        order = Order(
            user_id=user_id,
            product_name=product_name_str,
            price=total_price,
            distance=distance,
            traffic=traffic,
            weather=weather,
            order_hour=order_hour,
            previous_customer_availability=prev_avail,
            predicted_slot=predicted_slot,
            payment_status="Paid",
            payment_id=payment_id,
            order_status="Pending"
        )
        db.session.add(order)
        
        # Clear cart
        for item in cart_items:
            db.session.delete(item)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "order_id": order.id,
            "predicted_slot": predicted_slot,
            "total_price": total_price
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@orders_bp.route('/orders', methods=['GET', 'POST'])
@login_required
def get_orders():
    if request.method == 'POST':
        """Place order directly from cart page (localStorage cart)"""
        try:
            user_id = session.get('user_id')
            data = request.get_json() or {}
            
            items = data.get('items', [])
            if not items:
                return jsonify({"success": False, "error": "Cart is empty"}), 400
            
            import datetime
            order_hour = int(data.get('order_hour', datetime.datetime.now().hour))
            distance = float(data.get('distance', 10) or 10)
            traffic = data.get('traffic', 'medium') or 'medium'
            weather = data.get('weather', 'sunny') or 'sunny'
            package_weight = float(data.get('package_weight', 2.0) or 2.0)
            
            product_name_str = ", ".join([f"{i.get('name','Item')} x{i.get('qty',1)}" for i in items])
            total_price = float(data.get('total', sum(i.get('price', 0) * i.get('qty', 1) for i in items)))
            
            from routes.delivery import predict_slot_internal
            predicted_slot = predict_slot_internal(distance, traffic, weather, order_hour, package_weight=package_weight)
            
            payment_status = data.get('payment_status', "Paid")
            payment_id = data.get('payment_id', f"PAY-{user_id}-{order_hour}")
            
            order = Order(
                user_id=user_id,
                product_name=product_name_str,
                price=total_price,
                distance=distance,
                traffic=traffic,
                weather=weather,
                order_hour=order_hour,
                previous_customer_availability=1,
                predicted_slot=predicted_slot,
                payment_status=payment_status,
                payment_id=payment_id,
                order_status="Pending"
            )
            db.session.add(order)
            db.session.commit()
            
            return jsonify({
                "success": True,
                "order_id": order.id,
                "predicted_slot": predicted_slot
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 500
    
    # GET — order history
    try:
        user_id = session.get('user_id')
        orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
        return jsonify({
            "success": True,
            "orders": [o.to_dict() for o in orders]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
        # ===============================
# VIEW ORDER DETAILS API
# ===============================
@orders_bp.route('/orders/<int:order_id>', methods=['GET'])
@login_required
def get_order_detail(order_id):
    try:
        user_id = session.get('user_id')

        order = Order.query.filter_by(id=order_id, user_id=user_id).first()

        if not order:
            return jsonify({"success": False, "error": "Order not found"}), 404

        return jsonify({
            "success": True,
            "order": order.to_dict()
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ===============================
# CANCEL ORDER API
# ===============================
@orders_bp.route('/orders/<int:order_id>/cancel', methods=['PUT'])
@login_required
def cancel_order(order_id):
    try:
        user_id = session.get('user_id')

        order = Order.query.filter_by(id=order_id, user_id=user_id).first()

        if not order:
            return jsonify({"success": False, "error": "Order not found"}), 404

        # Cancel only if not shipped/delivered
        if order.order_status in ["Shipped", "Delivered"]:
            return jsonify({"success": False, "error": "Cannot cancel now"}), 400

        order.order_status = "Cancelled"
        db.session.commit()

        return jsonify({"success": True, "message": "Order cancelled"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500