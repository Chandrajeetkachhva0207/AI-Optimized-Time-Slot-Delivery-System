import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
import joblib
import os


class TimeSlotClassifier:
    """
    Random Forest Classifier to predict optimal delivery time slot
    based on distance, traffic, weather, temperature, and historical preferences
    """
    
    def __init__(self, model_path=None):
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        self.label_encoders = {}
        self.model_path = model_path
        self.feature_columns = [
            'distance', 'traffic_level_encoded', 'weather_condition_encoded',
            'temperature', 'package_weight', 'day_of_week', 'hour'
        ]
        
    def encode_features(self, df, fit=True):
        """Encode categorical features"""
        df_encoded = df.copy()
        
        categorical_columns = ['traffic_level', 'weather_condition']
        
        for col in categorical_columns:
            if fit:
                self.label_encoders[col] = LabelEncoder()
                df_encoded[f'{col}_encoded'] = self.label_encoders[col].fit_transform(df[col])
            else:
                # Handle unseen labels during prediction
                df_encoded[f'{col}_encoded'] = df[col].apply(
                    lambda x: self.label_encoders[col].transform([x])[0] 
                    if x in self.label_encoders[col].classes_ 
                    else -1
                )
        
        return df_encoded
    
    def prepare_data(self, data, fit=True):
        """Prepare data for training or prediction"""
        if isinstance(data, dict):
            df = pd.DataFrame([data])
        else:
            df = data.copy()
        
        # Encode categorical features
        df_encoded = self.encode_features(df, fit=fit)
        
        # Extract features
        X = df_encoded[self.feature_columns]
        
        return X
    
    def train(self, data_path):
        """Train the time slot classifier"""
        # Load data
        df = pd.read_csv(data_path)
        
        # Prepare features
        X = self.prepare_data(df, fit=True)
        
        # Encode target variable
        self.label_encoders['preferred_time_slot'] = LabelEncoder()
        y = self.label_encoders['preferred_time_slot'].fit_transform(df['preferred_time_slot'])
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train model
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, average='weighted'),
            'recall': recall_score(y_test, y_pred, average='weighted'),
            'f1_score': f1_score(y_test, y_pred, average='weighted'),
            'num_samples': len(df)
        }
        
        # Print classification report
        target_names = self.label_encoders['preferred_time_slot'].classes_
        print("\nTime Slot Classifier - Classification Report:")
        print(classification_report(y_test, y_pred, target_names=target_names))
        
        return metrics
    
    def predict(self, input_data):
        """Predict optimal time slot"""
        X = self.prepare_data(input_data, fit=False)
        prediction = self.model.predict(X)
        
        # Decode prediction
        time_slot = self.label_encoders['preferred_time_slot'].inverse_transform(prediction)[0]
        
        # Get probability scores
        probabilities = self.model.predict_proba(X)[0]
        slot_names = self.label_encoders['preferred_time_slot'].classes_
        
        result = {
            'predicted_slot': time_slot,
            'confidence': float(max(probabilities)),
            'probabilities': {
                slot: float(prob) for slot, prob in zip(slot_names, probabilities)
            }
        }
        
        return result
    
    def save_model(self, path=None):
        """Save trained model"""
        save_path = path or self.model_path
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            joblib.dump({
                'model': self.model,
                'label_encoders': self.label_encoders,
                'feature_columns': self.feature_columns
            }, save_path)
            print(f"Model saved to {save_path}")
    
    def load_model(self, path=None):
        """Load trained model"""
        load_path = path or self.model_path
        if load_path and os.path.exists(load_path):
            data = joblib.load(load_path)
            self.model = data['model']
            self.label_encoders = data['label_encoders']
            self.feature_columns = data['feature_columns']
            print(f"Model loaded from {load_path}")
            return True
        return False


