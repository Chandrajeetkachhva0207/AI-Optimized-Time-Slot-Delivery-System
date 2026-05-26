"""
Model Training Script
Trains all ML models and saves them to disk
"""

import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_models.time_slot_classifier import TimeSlotClassifier
from ml_models.delivery_time_regressor import DeliveryTimeRegressor
from ml_models.route_optimizer import RouteOptimizer
import pandas as pd


def train_all_models():
    """Train all ML models"""
    
    # Get paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(os.path.dirname(current_dir), 'data')
    sample_data_path = os.path.join(data_dir, 'sample_data.csv')
    models_dir = os.path.join(data_dir, 'trained_models')
    
    # Create models directory
    os.makedirs(models_dir, exist_ok=True)
    
    print("="*60)
    print("AI DELIVERY SYSTEM - MODEL TRAINING")
    print("="*60)
    print(f"Training Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Data Source: {sample_data_path}")
    print("="*60)
    
    # 1. Train Time Slot Classifier
    print("\n[1/3] Training Time Slot Classifier...")
    print("-"*60)
    classifier = TimeSlotClassifier(
        model_path=os.path.join(models_dir, 'time_slot_classifier.pkl')
    )
    classifier_metrics = classifier.train(sample_data_path)
    classifier.save_model()
    
    print(f"\n✓ Time Slot Classifier trained successfully!")
    print(f"  - Accuracy: {classifier_metrics['accuracy']:.4f}")
    print(f"  - Precision: {classifier_metrics['precision']:.4f}")
    print(f"  - Recall: {classifier_metrics['recall']:.4f}")
    print(f"  - F1 Score: {classifier_metrics['f1_score']:.4f}")
    
    # 2. Train Delivery Time Regressor
    print("\n[2/3] Training Delivery Time Regressor...")
    print("-"*60)
    regressor = DeliveryTimeRegressor(
        model_path=os.path.join(models_dir, 'delivery_time_regressor.pkl')
    )
    regressor_metrics = regressor.train(sample_data_path)
    regressor.save_model()
    
    print(f"\n✓ Delivery Time Regressor trained successfully!")
    print(f"  - MAE: {regressor_metrics['mae']:.2f} minutes")
    print(f"  - RMSE: {regressor_metrics['rmse']:.2f} minutes")
    print(f"  - R² Score: {regressor_metrics['r2_score']:.4f}")
    
    # 3. Train Route Optimizer
    print("\n[3/3] Training Route Optimizer (KMeans Clustering)...")
    print("-"*60)
    
    # Load sample data for clustering
    df = pd.read_csv(sample_data_path)
    
    # Create synthetic lat/lon data for demonstration
    # In production, use actual delivery coordinates
    df['delivery_latitude'] = 40.7128 + (df.index % 10 - 5) * 0.1
    df['delivery_longitude'] = -74.0060 + (df.index % 10 - 5) * 0.1
    
    optimizer = RouteOptimizer(
        n_clusters=3,
        model_path=os.path.join(models_dir, 'route_optimizer.pkl')
    )
    optimizer_metrics = optimizer.train(df)
    optimizer.save_model()
    
    print(f"\n✓ Route Optimizer trained successfully!")
    print(f"  - Number of Clusters: {optimizer_metrics['n_clusters']}")
    print(f"  - Inertia: {optimizer_metrics['inertia']:.2f}")
    
    # Summary
    print("\n" + "="*60)
    print("TRAINING SUMMARY")
    print("="*60)
    print(f"✓ All 3 models trained successfully")
    print(f"✓ Models saved to: {models_dir}")
    print(f"✓ Total training samples: {classifier_metrics['num_samples']}")
    print("\nModels ready for deployment!")
    print("="*60)
    
    return {
        'classifier': classifier_metrics,
        'regressor': regressor_metrics,
        'optimizer': optimizer_metrics
    }


if __name__ == '__main__':
    try:
        train_all_models()
    except Exception as e:
        print(f"\n❌ Error during training: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


