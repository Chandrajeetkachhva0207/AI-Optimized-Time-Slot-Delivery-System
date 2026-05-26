"""Database models for AI Time Slot Delivery System"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    """User model - customers and admin"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "is_admin": bool(self.is_admin)
        }


class Product(db.Model):
    """Product model"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    stock = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "description": self.description or "",
            "stock": self.stock
        }


class Cart(db.Model):
    """Shopping cart"""
    __tablename__ = 'cart'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    
    product = db.relationship('Product', backref='cart_items')
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "product": self.product.to_dict() if self.product else None
        }


class Order(db.Model):
    """Order model - stores order with AI predicted slot"""
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_name = db.Column(db.String(500), nullable=False)
    price = db.Column(db.Float, nullable=False)
    distance = db.Column(db.Float)
    traffic = db.Column(db.String(50))
    weather = db.Column(db.String(50))
    order_hour = db.Column(db.Integer)
    previous_customer_availability = db.Column(db.Integer)
    predicted_slot = db.Column(db.String(100))
    # New fields for payments and status
    payment_status = db.Column(db.String(50), default="Paid")  # Pending / Paid / Failed
    payment_id = db.Column(db.String(100))
    order_status = db.Column(db.String(50), default="Pending")  # Pending/Packed/Shipped/Out for Delivery/Delivered
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='orders')
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "product_name": self.product_name,
            "price": self.price,
            "distance": self.distance,
            "traffic": self.traffic,
            "weather": self.weather,
            "order_hour": self.order_hour,
            "predicted_slot": self.predicted_slot,
            "payment_status": self.payment_status,
            "payment_id": self.payment_id,
            "order_status": self.order_status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


# --- Operational delivery (admin hub): separate from e-commerce `orders` table ---


class Agent(db.Model):
    """Delivery agents / drivers"""
    __tablename__ = "agents"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default="available")  # available, busy, offline
    location = db.Column(db.String(255))  # free text or "lat,lon"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    deliveries = db.relationship("DeliveryOrder", backref="agent", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "location": self.location or "",
            "assigned_orders": self.deliveries.count(),
        }


class TimeSlot(db.Model):
    """Time windows with capacity for slot-based delivery"""
    __tablename__ = "time_slots"

    id = db.Column(db.Integer, primary_key=True)
    slot = db.Column(db.String(100), nullable=False)  # e.g. "09:00 - 11:00"
    capacity = db.Column(db.Integer, default=20)
    booked = db.Column(db.Integer, default=0)

    def to_dict(self):
        rem = max(0, (self.capacity or 0) - (self.booked or 0))
        util = 0.0
        if self.capacity:
            util = round(100.0 * (self.booked or 0) / float(self.capacity), 1)
        return {
            "id": self.id,
            "slot": self.slot,
            "capacity": self.capacity,
            "booked": self.booked,
            "remaining": rem,
            "utilization_pct": util,
        }


class DeliveryOrder(db.Model):
    """Operational delivery orders (admin hub) — customer, address, slot, agent"""
    __tablename__ = "delivery_orders"

    id = db.Column(db.Integer, primary_key=True)
    customer = db.Column(db.String(255), nullable=False)
    address = db.Column(db.Text, nullable=False)
    slot = db.Column(db.String(100))  # label snapshot
    status = db.Column(db.String(50), default="Pending")  # Pending, Packed, Shipped, Out for Delivery, Delivered, Failed
    agent_id = db.Column(db.Integer, db.ForeignKey("agents.id"), nullable=True)
    timeslot_id = db.Column(db.Integer, db.ForeignKey("time_slots.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    timeslot = db.relationship("TimeSlot", backref="delivery_orders")

    def to_dict(self):
        return {
            "id": self.id,
            "customer": self.customer,
            "address": self.address,
            "slot": self.slot,
            "status": self.status,
            "agent_id": self.agent_id,
            "agent_name": self.agent.name if self.agent else None,
            "timeslot_id": self.timeslot_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
