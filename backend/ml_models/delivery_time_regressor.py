import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import os
import math


class DeliveryTimeRegressor:
    """
    Random Forest Regressor to estimate delivery time
    based on distance, traffic, weather, package weight, and other factors
    """
    
    def __init__(self, model_path=None):
        self.model = GradientBoostingRegressor(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=6,
            random_state=42
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

    @staticmethod
    def eta_to_slot(minutes):
        if minutes <= 30:
            return 'Morning'
        if minutes <= 50:
            return 'Afternoon'
        if minutes <= 70:
            return 'Evening'
        return 'Night'

    @staticmethod
    def confidence_from_std(predicted_time, std_dev):
        score = 1.0 - min(0.35, max(0.0, std_dev / max(10.0, predicted_time)))
        return round(max(0.55, min(0.99, score)), 2)

    def train(self, data_path):
        """Train the delivery time regressor"""
        # Load data
        df = pd.read_csv(data_path)
        
        # Prepare features
        X = self.prepare_data(df, fit=True)
        y = df['delivery_time']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train model
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        
        mae = mean_absolute_error(y_test, y_pred)
        rmse = math.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        
        metrics = {
            'mae': mae,
            'rmse': rmse,
            'r2_score': r2,
            'num_samples': len(df)
        }
        
        print("\nDelivery Time Regressor - Performance Metrics:")
        print(f"Mean Absolute Error (MAE): {mae:.2f} minutes")
        print(f"Root Mean Squared Error (RMSE): {rmse:.2f} minutes")
        print(f"R² Score: {r2:.4f}")
        
        return metrics
    
    def predict(self, input_data):
        """Predict delivery time"""
        X = self.prepare_data(input_data, fit=False)
        predicted_time = self.model.predict(X)[0]
        
        # Calculate confidence interval based on ensemble uncertainty
        tree_predictions = np.array([tree.predict(X)[0] for tree in self.model.estimators_])
        std_dev = np.std(tree_predictions)
        confidence = self.confidence_from_std(predicted_time, std_dev)
        slot = self.eta_to_slot(int(round(predicted_time)))
        
        result = {
            'estimated_time': round(predicted_time, 2),
            'estimated_time_minutes': int(round(predicted_time)),
            'estimated_time_readable': f'{int(round(predicted_time))} mins',
            'estimated_slot': slot,
            'confidence': confidence,
            'confidence_pct': int(round(confidence * 100)),
            'confidence_interval': {
                'lower': round(predicted_time - std_dev, 2),
                'upper': round(predicted_time + std_dev, 2)
            },
            'std_deviation': round(std_dev, 2)
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


