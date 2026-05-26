import razorpay
from flask import current_app

class PaymentService:
    @staticmethod
    def get_client():
        """Initialize and return Razorpay client"""
        return razorpay.Client(
            auth=(
                current_app.config['RAZORPAY_KEY_ID'], 
                current_app.config['RAZORPAY_KEY_SECRET']
            )
        )

    @staticmethod
    def create_order(amount, currency='INR'):
        """Create a new Razorpay order"""
        client = PaymentService.get_client()
        data = {
            'amount': int(amount * 100), # amount in paise
            'currency': currency,
            'payment_capture': 1 # auto capture
        }
        try:
            order = client.order.create(data=data)
            return order
        except Exception as e:
            print(f"Error creating Razorpay order: {str(e)}")
            return None

    @staticmethod
    def verify_payment(payment_id, order_id, signature):
        """Verify the payment signature"""
        client = PaymentService.get_client()
        params_dict = {
            'razorpay_payment_id': payment_id,
            'razorpay_order_id': order_id,
            'razorpay_signature': signature
        }
        try:
            client.utility.verify_payment_signature(params_dict)
            return True
        except Exception as e:
            print(f"Payment verification failed: {str(e)}")
            return False
