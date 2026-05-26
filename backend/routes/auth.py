"""Auth blueprint - register, login, logout (customer + admin)"""
from flask import Blueprint, request, redirect, jsonify, session
from models.database import db, User
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def ensure_admin_exists():
    """Ensure admin user exists in database"""
    admin = User.query.filter_by(is_admin=1).first()
    if not admin:
        admin = User(
            name="Admin",
            email="admin@delivery.com",
            password=generate_password_hash("admin@123"),
            is_admin=1
        )
        db.session.add(admin)
        db.session.commit()


@auth_bp.route('/register', methods=['POST'])
def register():
    """Customer registration"""
    try:
        name = request.form.get('name') or (request.get_json() or {}).get('name')
        email = request.form.get('email') or (request.get_json() or {}).get('email')
        password = request.form.get('password') or (request.get_json() or {}).get('password')
        
        if not all([name, email, password]):
            if request.is_json:
                return jsonify({"success": False, "detail": "Name, email and password required"}), 400
            return redirect("/register?error=missing")
        
        if User.query.filter_by(email=email).first():
            if request.is_json:
                return jsonify({"success": False, "detail": "Email already registered"}), 400
            return redirect("/register?error=exists")
        
        user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            is_admin=0
        )
        db.session.add(user)
        db.session.commit()
        
        if request.is_json:
            return jsonify({"success": True, "message": "Registered successfully"})
        return redirect("/login")
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({"success": False, "detail": str(e)}), 500
        return redirect("/register?error=server")


@auth_bp.route('/login', methods=['POST'])
def login():
    """Customer login - uses sessions"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "detail": "No data provided"}), 400
        
        email = data.get('email')
        password = data.get('password')
        if not email or not password:
            return jsonify({"success": False, "detail": "Email and password required"}), 400
        
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"success": False, "detail": "Incorrect email or password"}), 401
        
        if not check_password_hash(user.password, password):
            return jsonify({"success": False, "detail": "Incorrect email or password"}), 401
        
        if user.is_admin:
            return jsonify({"success": False, "detail": "Use admin login page"}), 401
        
        session['user_id'] = user.id
        session['user_name'] = user.name
        session['is_admin'] = False
        
        return jsonify({
            "success": True,
            "user_id": user.id,
            "user_name": user.name,
            "is_admin": False
        })
    except Exception as e:
        return jsonify({"success": False, "detail": str(e)}), 500


@auth_bp.route('/admin-login', methods=['POST'])
def admin_login():
    """Admin login - fixed credentials or DB admin"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "detail": "No data provided"}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        ensure_admin_exists()
        
        # Check fixed credentials or DB admin
        admin = User.query.filter_by(is_admin=1).first()
        if admin and admin.email in [username, 'admin@delivery.com']:
            if check_password_hash(admin.password, password):
                session['user_id'] = admin.id
                session['user_name'] = admin.name
                session['is_admin'] = True
                return jsonify({
                    "success": True,
                    "access_token": "admin-session",
                    "is_admin": True
                })
        
        # Legacy: fixed username/password
        if username == "admin" and password == "admin@123":
            admin = User.query.filter_by(is_admin=1).first()
            if admin:
                session['user_id'] = admin.id
                session['user_name'] = admin.name
                session['is_admin'] = True
            return jsonify({"success": True, "access_token": "admin-session", "is_admin": True})
        
        return jsonify({"success": False, "detail": "Invalid admin credentials"}), 401
    except Exception as e:
        return jsonify({"success": False, "detail": str(e)}), 500


@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """Logout - clear session"""
    session.clear()
    return jsonify({"success": True})
