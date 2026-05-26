"""
predict.py - Load trained model and make predictions
"""

import os
import pickle
import pandas as pd
from typing import Literal


MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")
MODEL = None


def load_model():
    """Load the trained model from disk."""
    global MODEL
    if MODEL is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Model file not found at '{MODEL_PATH}'. "
                "Please run train_model.py first to generate model.pkl."
            )
        try:
            with open(MODEL_PATH, "rb") as f:
                MODEL = pickle.load(f)
        except Exception as e:
            raise RuntimeError(f"Could not load model: {e}") from e
    return MODEL


def predict_slot(
    distance: float,
    traffic: Literal["Low", "Medium", "High"],
    weather: Literal["Clear", "Rainy"],
    order_hour: int,
    previous_customer_availability: int,
) -> str:
    """
    Predict the best delivery time slot.
    
    Returns:
        One of: 'Morning', 'Afternoon', 'Evening'
    """
    model = load_model()
    
    # Prepare input DataFrame
    input_df = pd.DataFrame([{
        "distance": distance,
        "traffic": traffic,
        "weather": weather,
        "order_hour": order_hour,
        "previous_customer_availability": previous_customer_availability,
    }])
    
    # Predict
    prediction = model.predict(input_df)
    return str(prediction[0])
