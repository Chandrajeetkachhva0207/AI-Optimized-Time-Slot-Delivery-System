"""
models.py - SQLAlchemy ORM models for SmartParcel AI
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, DECIMAL
from sqlalchemy.sql import func
from database import Base


class User(Base):
    """
    User model for customers and admins.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Order(Base):
    """
    Order model storing delivery details and AI predictions.
    """
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Product info
    product_name = Column(String(255), nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    
    # Delivery context (features for ML)
    distance = Column(DECIMAL(8, 2), nullable=False)
    traffic = Column(String(20), nullable=False)
    weather = Column(String(20), nullable=False)
    order_hour = Column(Integer, nullable=False)
    previous_customer_availability = Column(Integer, nullable=False)
    
    # AI prediction result
    predicted_slot = Column(String(20), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
