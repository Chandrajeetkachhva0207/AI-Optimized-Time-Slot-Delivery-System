"""AI Optimized Time Slot Delivery System - Flask Application"""
from flask import Flask, jsonify, redirect, session, request, render_template
from flask_cors import CORS
from config import config
from models.database import db, User, Product
from routes.delivery import delivery_bp, init_ml_models
from routes.orders import orders_bp
from routes.admin import admin_bp
from routes.auth import auth_bp
from routes.delivery_ops import delivery_ops_bp
from routes.tracking import tracking_bp
from routes.payments import payments_bp
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def create_app(config_name='development'):
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Ensure SECRET_KEY for sessions
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
    
    # Initialize CORS
    CORS(app)
    
    # Initialize database
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        # Lightweight migration for new Order columns if database already exists
        from sqlalchemy import text
        for col_sql in [
            "ALTER TABLE orders ADD COLUMN payment_status VARCHAR(50)",
            "ALTER TABLE orders ADD COLUMN payment_id VARCHAR(100)",
            "ALTER TABLE orders ADD COLUMN order_status VARCHAR(50)"
        ]:
            try:
                db.session.execute(text(col_sql))
                db.session.commit()
            except Exception:
                db.session.rollback()
                # Column probably already exists – ignore
        seed_products()
        seed_admin()
        seed_delivery_ops()
        print("[OK] Database tables created")
        
        # Initialize ML models (optional)
        try:
            model_path = app.config.get('MODEL_PATH', 'backend/data/trained_models')
            if not os.path.isabs(model_path):
                model_path = os.path.join(os.path.dirname(__file__), 'data', 'trained_models')
            init_ml_models(model_path)
            print("[OK] ML models loaded (or using fallback)")
        except Exception as e:
            print(f"[INFO] ML models: {e}")
    
    # Register blueprints
    app.register_blueprint(delivery_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(delivery_ops_bp)
    app.register_blueprint(tracking_bp)
    app.register_blueprint(payments_bp)
    
    # ========== Page Routes ==========
    @app.route('/')
    def home():
        return render_template("index.html")
    
    @app.route('/register')
    def register_page():
        return render_template("register.html")
    
    @app.route('/login')
    def login_page():
        return render_template("login.html")
    
    @app.route('/admin-login')
    def admin_login_page():
        return render_template("admin-login.html")
    
    @app.route('/admin')
    @app.route('/admin-dashboard')
    def admin_page():
        if not session.get('is_admin'):
            return redirect("/admin-login")
        return render_template("admin-dashboard.html")

    @app.route('/admin/delivery')
    def admin_delivery_hub():
        """AI Time Slot Delivery — full admin hub (REST-connected)."""
        if not session.get('is_admin'):
            return redirect("/admin-login")
        return render_template("admin_delivery_hub.html")
    
    @app.route('/dashboard')
    def dashboard():
        if not session.get('user_id') and not session.get('is_admin'):
            return redirect("/login")
        return render_template("dashboard.html", user_name=session.get('user_name'))

    @app.route("/product")
    def product_page():
        # Optional: protect behind login
        if not session.get('user_id') and not session.get('is_admin'):
            return redirect("/login")
        return render_template("product.html")

    @app.route("/ai-predictor")
    def ai_predictor_page():
        if not session.get('user_id') and not session.get('is_admin'):
            return redirect("/login")
        return redirect("/dashboard#ai")

    @app.route("/route-map")
    def route_map_page():
        if not session.get('user_id') and not session.get('is_admin'):
            return redirect("/login")
        return render_template("route-map.html")

    @app.route("/live-tracking")
    def live_tracking_page():
        if not session.get('user_id') and not session.get('is_admin'):
            return redirect("/login")
        return render_template("live-tracking.html")

    @app.route("/track/<int:order_id>")
    def track_order_page(order_id):
        if not session.get('user_id') and not session.get('is_admin'):
            return redirect("/login")
        return render_template("track-order.html", order_id=order_id)

    # Simple product search over local products (used by dashboard search)
    @app.route("/search")
    def search():
        q = (request.args.get("q") or "").strip()
        if not q:
            return jsonify({"success": True, "products": []})
        products = Product.query.filter(Product.name.ilike(f"%{q}%")).all()
        return jsonify({
            "success": True,
            "products": [p.to_dict() for p in products]
        })

    @app.route("/cart")
    def cart_page():
        if not session.get('user_id'):
            return redirect("/login")
        return render_template("cart.html")
    
    @app.route('/checkout')
    def checkout_page():
        if not session.get('user_id'):
            return redirect("/login")
        return render_template("checkout.html", razorpay_key_id=app.config.get('RAZORPAY_KEY_ID'))
    
    @app.route("/orders")
    def orders_page():
        if not session.get('user_id'):
            return redirect("/login")
        return render_template("orders.html")
    
    @app.route('/route')
    def route():
        return render_template("route-map.html")
    
    @app.route('/logout')
    def logout_route():
        session.clear()
        return redirect("/login")


    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy'})
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'success': False, 'error': 'Resource not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
    
    return app


def seed_products():
    """Seed sample products if empty"""
    if Product.query.count() > 0:
        return
    products = [
        {"name": "Pro Smartphone X12", "price": 25000, "description": "Latest smartphone", "stock": 50},
        {"name": "UltraBook Pro 15", "price": 70000, "description": "Premium laptop", "stock": 20},
        {"name": "SoundMax ANC Pro", "price": 3000, "description": "Noise cancelling headphones", "stock": 100},
        {"name": "Nexus Watch GT5", "price": 6000, "description": "Smart watch", "stock": 75},
    ]
    for p in products:
        db.session.add(Product(**p))
    db.session.commit()
    print("[OK] Sample products seeded")


def seed_admin():
    """Ensure admin user exists"""
    from routes.auth import ensure_admin_exists
    ensure_admin_exists()


def seed_delivery_ops():
    """Seed agents, time slots, sample delivery orders for admin hub."""
    from models.database import Agent, TimeSlot, DeliveryOrder

    if Agent.query.count() == 0:
        for name, st, loc in [
            ("Ramesh Kumar", "busy", "19.076,72.877"),
            ("Priya Shah", "available", "18.520,73.856"),
            ("Amit Verma", "offline", "28.613,77.209"),
        ]:
            db.session.add(Agent(name=name, status=st, location=loc))
        db.session.commit()
        print("[OK] Sample agents seeded")

    if TimeSlot.query.count() == 0:
        defaults = [
            ("06:00 - 08:00", 15, 4),
            ("09:00 - 11:00", 25, 18),
            ("12:00 - 14:00", 30, 22),
            ("15:00 - 17:00", 20, 12),
            ("18:00 - 21:00", 35, 28),
        ]
        for slot, cap, book in defaults:
            db.session.add(TimeSlot(slot=slot, capacity=cap, booked=book))
        db.session.commit()
        print("[OK] Time slots seeded")

    if DeliveryOrder.query.count() == 0:
        agents = Agent.query.all()
        slots = TimeSlot.query.all()
        samples = [
            ("Anita Desai", "221 B Baker Street, Mumbai", "09:00 - 11:00", "Shipped", 0, 1),
            ("Rohit Mehta", "12 MG Road, Pune", "12:00 - 14:00", "Pending", 1, 2),
            ("Sneha Iyer", "88 Indiranagar, Bangalore", "18:00 - 21:00", "Failed", None, 4),
        ]
        for cust, addr, sl, st, ag_i, ts_i in samples:
            aid = None
            if ag_i is not None and agents and ag_i < len(agents):
                aid = agents[ag_i].id
            tid = slots[ts_i - 1].id if ts_i <= len(slots) else None
            db.session.add(
                DeliveryOrder(
                    customer=cust,
                    address=addr,
                    slot=sl,
                    status=st,
                    agent_id=aid,
                    timeslot_id=tid,
                )
            )
        db.session.commit()
        print("[OK] Sample delivery orders seeded")


if __name__ == '__main__':
    env = os.environ.get('FLASK_ENV', 'development')
    app = create_app(env)
    
    print("\n" + "="*60)
    print("AI OPTIMIZED DELIVERY SYSTEM - BACKEND SERVER")
    print("="*60)
    print(f"Environment: {env}")
    print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print("="*60)
    print("\nServer: http://localhost:5000")
    print("Press CTRL+C to stop\n")
    
    app.run(host='0.0.0.0', port=5000, debug=(env == 'development'))
