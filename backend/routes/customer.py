from flask import Blueprint, render_template, request, jsonify, session
from models.database import db, Customer, Delivery

customer_bp = Blueprint('customer', __name__, url_prefix='/customer')

@customer_bp.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", user_name=session.get('user_name'))

@customer_bp.route("/place_order")
def place_order():
    return render_template("place_order.html")

@customer_bp.route("/predict-slot", methods=["POST"])
def predict_slot():

    data = request.get_json()

    distance = data.get("distance")
    traffic = data.get("traffic")

    slot = "4 PM - 6 PM"

    return jsonify({
        "success": True,
        "slot": slot
    })


@customer_bp.route("/order-status/<int:id>")
def order_status(id):

    delivery = Delivery.query.get(id)

    if not delivery:
        return jsonify({
            "success": False,
            "message": "Order not found"
        })

    return jsonify({
        "success": True,
        "status": delivery.status
    })

@customer_bp.route('/customers', methods=['GET'])
def get_customers():
    """Get all customers"""
    try:
        customers = Customer.query.order_by(Customer.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'customers': [c.to_dict() for c in customers]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@customer_bp.route('/customers/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    """Get customer by ID"""
    try:
        customer = Customer.query.get(customer_id)
        
        if not customer:
            return jsonify({
                'success': False,
                'error': 'Customer not found'
            }), 404
        
        # Get customer's deliveries
        deliveries = Delivery.query.filter_by(customer_id=customer_id).all()
        
        customer_data = customer.to_dict()
        customer_data['deliveries'] = [d.to_dict() for d in deliveries]
        
        return jsonify({
            'success': True,
            'customer': customer_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@customer_bp.route('/customers', methods=['POST'])
def create_customer():
    """Create new customer"""
    try:
        data = request.get_json()
        
        # Check if email already exists
        existing = Customer.query.filter_by(email=data.get('email')).first()
        if existing:
            return jsonify({
                'success': False,
                'error': 'Customer with this email already exists'
            }), 400
        
        customer = Customer(
            name=data.get('name'),
            email=data.get('email'),
            phone=data.get('phone'),
            address=data.get('address'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude')
        )
        
        db.session.add(customer)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'customer': customer.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@customer_bp.route('/customers/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    """Update customer"""
    try:
        customer = Customer.query.get(customer_id)
        
        if not customer:
            return jsonify({
                'success': False,
                'error': 'Customer not found'
            }), 404
        
        data = request.get_json()
        
        # Update fields
        if 'name' in data:
            customer.name = data['name']
        if 'phone' in data:
            customer.phone = data['phone']
        if 'address' in data:
            customer.address = data['address']
        if 'latitude' in data:
            customer.latitude = data['latitude']
        if 'longitude' in data:
            customer.longitude = data['longitude']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'customer': customer.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@customer_bp.route('/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    """Delete customer"""
    try:
        customer = Customer.query.get(customer_id)
        
        if not customer:
            return jsonify({
                'success': False,
                'error': 'Customer not found'
            }), 404
        
        db.session.delete(customer)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Customer deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@customer_bp.route('/customers/search', methods=['GET'])
def search_customers():
    """Search customers by name or email"""
    try:
        query_param = request.args.get('q', '')
        
        if not query_param:
            return jsonify({
                'success': False,
                'error': 'Please provide search query'
            }), 400
        
        customers = Customer.query.filter(
            db.or_(
                Customer.name.ilike(f'%{query_param}%'),
                Customer.email.ilike(f'%{query_param}%')
            )
        ).all()
        
        return jsonify({
            'success': True,
            'customers': [c.to_dict() for c in customers]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


