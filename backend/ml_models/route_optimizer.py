import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import joblib
import os


class RouteOptimizer:
    """
    KMeans Clustering for route optimization
    Groups deliveries by location and time for efficient routing
    """
    
    def __init__(self, n_clusters=5, model_path=None):
        self.n_clusters = n_clusters
        self.model = KMeans(
            n_clusters=n_clusters,
            random_state=42,
            n_init=10
        )
        self.scaler = StandardScaler()
        self.model_path = model_path
        self.feature_columns = ['delivery_latitude', 'delivery_longitude', 'hour']
        
    def prepare_data(self, data, fit=True):
        """Prepare data for clustering"""
        if isinstance(data, dict):
            df = pd.DataFrame([data])
        elif isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = data.copy()
        
        # Extract features
        X = df[self.feature_columns]
        
        # Scale features
        if fit:
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = self.scaler.transform(X)
        
        return X_scaled, df
    
    def train(self, deliveries_data):
        """Train the clustering model"""
        X_scaled, df = self.prepare_data(deliveries_data, fit=True)
        
        # Fit clustering model
        self.model.fit(X_scaled)
        
        # Get cluster assignments
        clusters = self.model.predict(X_scaled)
        
        # Calculate metrics
        inertia = self.model.inertia_
        
        metrics = {
            'inertia': inertia,
            'n_clusters': self.n_clusters,
            'num_samples': len(df)
        }
        
        print("\nRoute Optimizer - Clustering Metrics:")
        print(f"Number of Clusters: {self.n_clusters}")
        print(f"Inertia (Within-cluster sum of squares): {inertia:.2f}")
        print(f"Number of Deliveries: {len(df)}")
        
        return metrics
    
    def predict(self, deliveries_data):
        """Assign deliveries to optimal routes/clusters"""
        X_scaled, df = self.prepare_data(deliveries_data, fit=False)
        
        # Predict clusters
        clusters = self.model.predict(X_scaled)
        
        # Add cluster information to deliveries
        df['route_cluster'] = clusters
        
        # Organize deliveries by cluster
        routes = {}
        for cluster_id in range(self.n_clusters):
            cluster_deliveries = df[df['route_cluster'] == cluster_id]
            if len(cluster_deliveries) > 0:
                routes[f'route_{cluster_id}'] = {
                    'cluster_id': int(cluster_id),
                    'num_deliveries': len(cluster_deliveries),
                    'deliveries': cluster_deliveries.to_dict('records'),
                    'center': {
                        'latitude': float(self.model.cluster_centers_[cluster_id][0]),
                        'longitude': float(self.model.cluster_centers_[cluster_id][1])
                    }
                }
        
        result = {
            'total_deliveries': len(df),
            'num_routes': len(routes),
            'routes': routes
        }
        
        return result
    
    def optimize_single_route(self, deliveries):
        """
        Optimize the order of deliveries within a single route
        using nearest neighbor heuristic (simple TSP approximation)
        """
        if len(deliveries) <= 1:
            return deliveries
        
        # Convert to list if dict
        if isinstance(deliveries, dict):
            deliveries = [deliveries]
        
        # Start from first delivery
        optimized_route = [deliveries[0]]
        remaining = deliveries[1:].copy()
        
        while remaining:
            last_delivery = optimized_route[-1]
            last_lat = last_delivery.get('delivery_latitude', 0)
            last_lon = last_delivery.get('delivery_longitude', 0)
            
            # Find nearest delivery
            min_distance = float('inf')
            nearest_idx = 0
            
            for idx, delivery in enumerate(remaining):
                lat = delivery.get('delivery_latitude', 0)
                lon = delivery.get('delivery_longitude', 0)
                
                # Calculate Euclidean distance
                distance = np.sqrt((lat - last_lat)**2 + (lon - last_lon)**2)
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_idx = idx
            
            # Add nearest delivery to route
            optimized_route.append(remaining.pop(nearest_idx))
        
        return optimized_route
    
    def save_model(self, path=None):
        """Save trained model"""
        save_path = path or self.model_path
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            joblib.dump({
                'model': self.model,
                'scaler': self.scaler,
                'n_clusters': self.n_clusters,
                'feature_columns': self.feature_columns
            }, save_path)
            print(f"Model saved to {save_path}")
    
    def load_model(self, path=None):
        """Load trained model"""
        load_path = path or self.model_path
        if load_path and os.path.exists(load_path):
            data = joblib.load(load_path)
            self.model = data['model']
            self.scaler = data['scaler']
            self.n_clusters = data['n_clusters']
            self.feature_columns = data['feature_columns']
            print(f"Model loaded from {load_path}")
            return True
        return False


