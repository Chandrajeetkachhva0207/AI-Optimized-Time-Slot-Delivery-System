from flask import Blueprint, request, jsonify, session, render_template, redirect
from models.database import db, Order, User
from services.payment_service import PaymentService
import json

payments_bp = Blueprint('payments', __name__)

@payments_bp.route('/api/payments/create', methods=['POST'])
def create_payment_order():
    """Endpoint to create a Razorpay order"""
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    amount = data.get('amount')
    
    if not amount:
        return jsonify({'success': False, 'error': 'Amount is required'}), 400
    
    order = PaymentService.create_order(amount)
    
    if order:
        return jsonify({
            'success': True,
            'order_id': order['id'],
            'amount': order['amount'],
            'currency': order['currency']
        })
    else:
        return jsonify({'success': False, 'error': 'Could not create order'}), 500

@payments_bp.route('/api/payments/verify', methods=['POST'])
def verify_payment():
    """Endpoint to verify Razorpay payment signature"""
    data = request.get_json()
    
    payment_id = data.get('razorpay_payment_id')
    order_id = data.get('razorpay_order_id')
    signature = data.get('razorpay_signature')
    internal_order_id = data.get('internal_order_id')
    
    if not all([payment_id, order_id, signature]):
        return jsonify({'success': False, 'error': 'Missing payment credentials'}), 400
    
    is_valid = PaymentService.verify_payment(payment_id, order_id, signature)
    
    if is_valid:
        # Update order status in database if needed
        # order = Order.query.get(internal_order_id)
        # if order:
        #     order.status = 'Paid'
        #     order.payment_id = payment_id
        #     db.session.commit()
        
        return jsonify({'success': True, 'message': 'Payment verified successfully'})
    else:
        return jsonify({'success': False, 'error': 'Payment verification failed'}), 400

@payments_bp.route('/payment-success')
def payment_success():
    return render_template('payment_success.html')

@payments_bp.route('/payment-failed')
def payment_failed():
    return render_template('payment_failed.html')
