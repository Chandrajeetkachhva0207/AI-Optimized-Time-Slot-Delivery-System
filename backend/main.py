"""
main.py - FastAPI backend for SmartParcel AI

Run with:
    cd backend
    uvicorn main:app --reload
"""

import os
from typing import List, Literal, Optional
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field, validator
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import User, Order
from auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_token,
)
from predict import predict_slot

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="SmartParcel AI API",
    description="E-commerce style AI-optimized parcel delivery platform",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT security
security = HTTPBearer()


# ==================== Pydantic Models ====================

class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=6)
    is_admin: bool = False


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    is_admin: bool


class CartItem(BaseModel):
    product_name: str
    price: float = Field(..., gt=0)


class PredictRequest(BaseModel):
    items: List[CartItem] = Field(..., min_items=1)
    distance: float = Field(..., gt=0, le=5000)
    traffic: Literal["Low", "Medium", "High"]
    weather: Literal["Clear", "Rainy"]
    order_hour: int = Field(..., ge=0, le=23)
    previous_customer_availability: int = Field(..., ge=0, le=1)


class PredictResponse(BaseModel):
    recommended_time_slot: Literal["Morning", "Afternoon", "Evening"]
    order_id: int
    total_price: float


# ==================== Authentication Helpers ====================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    payload = decode_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return user


# ==================== API Endpoints ====================

@app.get("/")
def root():
    """Health check endpoint."""
    return {
        "message": "SmartParcel AI API is running",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.post("/api/register", response_model=TokenResponse)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user (customer or admin)."""
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hashed_password,
        is_admin=user_data.is_admin
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate JWT token
    access_token = create_access_token(data={"sub": str(new_user.id)})
    
    return TokenResponse(
        access_token=access_token,
        user_id=new_user.id,
        is_admin=new_user.is_admin
    )


@app.post("/api/login", response_model=TokenResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user and return JWT token."""
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Generate JWT token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        user_id=user.id,
        is_admin=user.is_admin
    )


@app.get("/api/me")
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "is_admin": current_user.is_admin
    }


@app.post("/api/predict-slot", response_model=PredictResponse)
def predict_delivery_slot(
    payload: PredictRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Predict best delivery time slot using AI model.
    Requires authentication.
    """
    try:
        # Calculate total price
        total_price = sum(item.price for item in payload.items)
        product_names = ", ".join(item.product_name for item in payload.items)
        
        # Get AI prediction
        predicted_slot = predict_slot(
            distance=payload.distance,
            traffic=payload.traffic,
            weather=payload.weather,
            order_hour=payload.order_hour,
            previous_customer_availability=payload.previous_customer_availability,
        )
        
        # Save order to database
        order = Order(
            user_id=current_user.id,
            product_name=product_names,
            price=float(total_price),
            distance=float(payload.distance),
            traffic=payload.traffic,
            weather=payload.weather,
            order_hour=payload.order_hour,
            previous_customer_availability=payload.previous_customer_availability,
            predicted_slot=predicted_slot,
        )
        
        db.add(order)
        db.commit()
        db.refresh(order)
        
        return PredictResponse(
            recommended_time_slot=predicted_slot,
            order_id=order.id,
            total_price=total_price
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction error: {str(e)}"
        )


@app.get("/api/orders")
def get_user_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all orders for the current user."""
    orders = db.query(Order).filter(Order.user_id == current_user.id).order_by(Order.created_at.desc()).all()
    
    return {
        "orders": [
            {
                "id": order.id,
                "product_name": order.product_name,
                "price": float(order.price),
                "predicted_slot": order.predicted_slot,
                "created_at": order.created_at.isoformat(),
            }
            for order in orders
        ]
    }
