"""
train_model.py - Train RandomForestClassifier for delivery time slot prediction

Run this once to generate model.pkl:
    python train_model.py
"""

import os
import pickle
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)


def generate_synthetic_data(n_samples: int = 2000) -> pd.DataFrame:
    """
    Generate synthetic dataset for training.
    
    Features:
    - distance: 0.5 to 50 km
    - traffic: Low, Medium, High
    - weather: Clear, Rainy
    - order_hour: 0-23
    - previous_customer_availability: 0 or 1
    
    Target:
    - best_time_slot: Morning, Afternoon, Evening
    """
    print(f"Generating {n_samples} synthetic samples...")
    
    # Generate features
    distance = np.round(np.random.uniform(0.5, 50, n_samples), 2)
    traffic = np.random.choice(["Low", "Medium", "High"], size=n_samples, p=[0.4, 0.4, 0.2])
    weather = np.random.choice(["Clear", "Rainy"], size=n_samples, p=[0.7, 0.3])
    order_hour = np.random.randint(0, 24, size=n_samples)
    prev_avail = np.random.choice([0, 1], size=n_samples, p=[0.3, 0.7])
    
    # Generate labels with logic + noise
    labels = []
    for d, t, w, h, pa in zip(distance, traffic, weather, order_hour, prev_avail):
        score_morning = 0
        score_afternoon = 0
        score_evening = 0
        
        # Distance influence
        if d < 8:
            score_morning += 2
            score_afternoon += 1
        elif d < 25:
            score_afternoon += 2
        else:
            score_evening += 3
        
        # Traffic influence
        if t == "Low":
            score_morning += 1
            score_afternoon += 1
        elif t == "Medium":
            score_afternoon += 1
        else:  # High
            score_evening += 2
        
        # Weather influence
        if w == "Rainy":
            score_evening += 1
        else:
            score_morning += 1
        
        # Order hour influence
        if 7 <= h < 11:
            score_morning += 2
        elif 11 <= h < 17:
            score_afternoon += 2
        else:
            score_evening += 2
        
        # Previous availability influence
        if pa == 0:  # previously unavailable
            score_evening += 2
        else:
            score_afternoon += 1
        
        # Choose label with highest score
        scores = {"Morning": score_morning, "Afternoon": score_afternoon, "Evening": score_evening}
        label = max(scores, key=scores.get)
        
        # Add 5% noise
        if np.random.rand() < 0.05:
            label = np.random.choice(["Morning", "Afternoon", "Evening"])
        
        labels.append(label)
    
    # Create DataFrame
    df = pd.DataFrame({
        "distance": distance,
        "traffic": traffic,
        "weather": weather,
        "order_hour": order_hour,
        "previous_customer_availability": prev_avail,
        "best_time_slot": labels,
    })
    
    return df


def train_and_save_model():
    """Train RandomForestClassifier and save to model.pkl"""
    
    # Generate data
    df = generate_synthetic_data(n_samples=2000)
    
    # Prepare features and target
    X = df[["distance", "traffic", "weather", "order_hour", "previous_customer_availability"]]
    y = df["best_time_slot"]
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED, stratify=y
    )
    
    # Preprocessing pipeline
    categorical_features = ["traffic", "weather"]
    numeric_features = ["distance", "order_hour", "previous_customer_availability"]
    
    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
            ("num", "passthrough", numeric_features),
        ]
    )
    
    # Create pipeline with RandomForest
    clf = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", RandomForestClassifier(
                n_estimators=200,
                max_depth=15,
                min_samples_split=5,
                random_state=RANDOM_SEED,
                n_jobs=-1
            )),
        ]
    )
    
    print("Training RandomForestClassifier...")
    clf.fit(X_train, y_train)
    
    # Evaluate
    y_pred = clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print("\n" + "="*60)
    print("MODEL PERFORMANCE")
    print("="*60)
    print(f"Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred, labels=["Morning", "Afternoon", "Evening"]))
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, labels=["Morning", "Afternoon", "Evening"]))
    print("="*60)
    
    # Save model
    base_dir = os.path.dirname(__file__)
    model_path = os.path.join(base_dir, "model.pkl")
    
    with open(model_path, "wb") as f:
        pickle.dump(clf, f)
    
    print(f"\n✅ Model saved to: {model_path}")
    print("You can now use this model in the FastAPI backend.")


if __name__ == "__main__":
    train_and_save_model()
