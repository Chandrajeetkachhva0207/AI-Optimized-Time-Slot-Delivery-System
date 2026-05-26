# API Documentation
## AI Optimized Delivery System

Base URL: `http://localhost:5000/api`

---

## 📋 Table of Contents

1. [Delivery Endpoints](#delivery-endpoints)
2. [Customer Endpoints](#customer-endpoints)
3. [Admin Endpoints](#admin-endpoints)
4. [Utility Endpoints](#utility-endpoints)
5. [Error Handling](#error-handling)
6. [Data Models](#data-models)

---

## 🚚 Delivery Endpoints

### 1. Predict Time Slot

Predict the optimal delivery time slot using AI.

**Endpoint:** `POST /api/predict_slot`

**Request Body:**
```json
{
  "delivery_latitude": 40.7128,
  "delivery_longitude": -74.0060,
  "pickup_location": [40.7589, -73.9851],
  "package_weight": 2.5,
  "preferred_hour": 14
}
```

**Response:**
```json
{
  "success": true,
  "predicted_slot": "afternoon",
  "confidence": 0.85,
  "probabilities": {
    "morning": 0.15,
    "afternoon": 0.85,
    "evening": 0.00
  },
  "weather": {
    "temperature": 22.5,
    "condition": "sunny",
    "humidity": 65
  },
  "distance": {
    "distance_km": 5.2,
    "traffic_level": "medium",
    "duration_minutes": 32
  }
}
```

---

### 2. Estimate Delivery Time

Estimate delivery time based on multiple factors.

**Endpoint:** `POST /api/estimate_time`

**Request Body:**
```json
{
  "delivery_latitude": 40.7128,
  "delivery_longitude": -74.0060,
  "pickup_location": [40.7589, -73.9851],
  "package_weight": 2.5,
  "hour": 14
}
```

**Response:**
```json
{
  "success": true,
  "estimated_time": 35,
  "confidence_interval": {
    "lower": 30.5,
    "upper": 39.5
  },
  "weather": {...},
  "distance": {...}
}
```

---

### 3. Optimize Route

Optimize routes for multiple deliveries using clustering.

**Endpoint:** `POST /api/predict_route`

**Request Body:**
```json
{
  "deliveries": [
    {
      "delivery_latitude": 40.7128,
      "delivery_longitude": -74.0060,
      "hour": 14
    },
    {
      "delivery_latitude": 40.7589,
      "delivery_longitude": -73.9851,
      "hour": 14
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "optimization": {
    "total_deliveries": 2,
    "num_routes": 1,
    "routes": {
      "route_0": {
        "cluster_id": 0,
        "num_deliveries": 2,
        "deliveries": [...],
        "center": {
          "latitude": 40.7358,
          "longitude": -73.9955
        },
        "optimized": true
      }
    }
  }
}
```

---

### 4. Get All Deliveries

Retrieve all deliveries with optional filtering.

**Endpoint:** `GET /api/deliveries`

**Query Parameters:**
- `status` (optional): Filter by status (pending, in_transit, delivered, cancelled)
- `customer_id` (optional): Filter by customer ID

**Example:** `GET /api/deliveries?status=pending`

**Response:**
```json
{
  "success": true,
  "deliveries": [
    {
      "id": 1,
      "customer_id": 1,
      "customer_name": "John Doe",
      "delivery_location": "123 Main St, New York",
      "distance": 5.2,
      "predicted_slot": "morning",
      "estimated_time": 32,
      "status": "pending",
      "delivery_date": "2024-01-20"
    }
  ]
}
```

---

### 5. Create Delivery

Book a new delivery.

**Endpoint:** `POST /api/deliveries`

**Request Body:**
```json
{
  "customer_name": "John Doe",
  "customer_email": "john@example.com",
  "customer_phone": "1234567890",
  "pickup_location": "Warehouse A",
  "pickup_latitude": 40.7589,
  "pickup_longitude": -73.9851,
  "delivery_location": "123 Main St, New York",
  "delivery_latitude": 40.7128,
  "delivery_longitude": -74.0060,
  "package_type": "electronics",
  "package_weight": 2.5,
  "delivery_date": "2024-01-20",
  "preferred_time": "morning"
}
```

**Response:**
```json
{
  "success": true,
  "delivery": {
    "id": 1,
    "customer_id": 1,
    "predicted_slot": "morning",
    "estimated_time": 32,
    "status": "pending"
  },
  "tracking_id": "DEL20240120143052001",
  "prediction": {
    "slot": {...},
    "time": {...}
  }
}
```

---

### 6. Get Delivery by ID

Retrieve a specific delivery.

**Endpoint:** `GET /api/deliveries/{id}`

**Response:**
```json
{
  "success": true,
  "delivery": {
    "id": 1,
    "customer_name": "John Doe",
    "pickup_location": "Warehouse A",
    "delivery_location": "123 Main St",
    "distance": 5.2,
    "traffic_level": "medium",
    "weather_condition": "sunny",
    "temperature": 22.5,
    "predicted_slot": "morning",
    "estimated_time": 32,
    "status": "pending"
  }
}
```

---

### 7. Update Delivery

Update delivery information.

**Endpoint:** `PUT /api/deliveries/{id}`

**Request Body:**
```json
{
  "status": "in_transit",
  "actual_time": 35,
  "route_cluster": 0
}
```

**Response:**
```json
{
  "success": true,
  "delivery": {...}
}
```

---

### 8. Delete Delivery

Delete a delivery.

**Endpoint:** `DELETE /api/deliveries/{id}`

**Response:**
```json
{
  "success": true,
  "message": "Delivery deleted successfully"
}
```

---

## 👥 Customer Endpoints

### 1. Get All Customers

**Endpoint:** `GET /api/customers`

**Response:**
```json
{
  "success": true,
  "customers": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "phone": "1234567890",
      "address": "123 Main St, New York",
      "latitude": 40.7128,
      "longitude": -74.0060
    }
  ]
}
```

---

### 2. Get Customer by ID

**Endpoint:** `GET /api/customers/{id}`

**Response:**
```json
{
  "success": true,
  "customer": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "deliveries": [...]
  }
}
```

---

### 3. Create Customer

**Endpoint:** `POST /api/customers`

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "1234567890",
  "address": "123 Main St, New York",
  "latitude": 40.7128,
  "longitude": -74.0060
}
```

---

### 4. Update Customer

**Endpoint:** `PUT /api/customers/{id}`

---

### 5. Delete Customer

**Endpoint:** `DELETE /api/customers/{id}`

---

### 6. Search Customers

**Endpoint:** `GET /api/customers/search?q=john`

---

## 🔐 Admin Endpoints

### 1. Get Analytics

**Endpoint:** `GET /api/admin/analytics`

**Response:**
```json
{
  "success": true,
  "analytics": {
    "total_deliveries": 100,
    "deliveries_by_status": {
      "pending": 20,
      "in_transit": 15,
      "delivered": 60,
      "cancelled": 5
    },
    "deliveries_by_slot": {
      "morning": 35,
      "afternoon": 40,
      "evening": 25
    },
    "average_delivery_time": 38.5,
    "average_distance": 6.2,
    "recent_deliveries_7days": 25,
    "traffic_distribution": {
      "low": 40,
      "medium": 45,
      "high": 15
    },
    "weather_distribution": {
      "sunny": 60,
      "cloudy": 25,
      "rainy": 10,
      "foggy": 5
    }
  }
}
```

---

### 2. Get Model Metrics

**Endpoint:** `GET /api/admin/model_metrics`

**Response:**
```json
{
  "success": true,
  "metrics": {
    "latest_logs": [
      {
        "model_name": "Time Slot Classifier",
        "model_type": "classifier",
        "training_date": "2024-01-20T10:30:00",
        "accuracy": 0.85,
        "precision_score": 0.83,
        "recall_score": 0.86,
        "f1_score": 0.84,
        "num_samples": 50
      }
    ],
    "model_statistics": [...]
  }
}
```

---

### 3. Train Models

**Endpoint:** `POST /api/admin/train_model`

**Request Body:**
```json
{
  "model_type": "all"
}
```

Options: `all`, `classifier`, `regressor`, `optimizer`

**Response:**
```json
{
  "success": true,
  "message": "Models retrained successfully",
  "results": {
    "classifier": {
      "accuracy": 0.85,
      "precision": 0.83,
      "recall": 0.86,
      "f1_score": 0.84
    },
    "regressor": {
      "mae": 5.2,
      "rmse": 7.3,
      "r2_score": 0.78
    }
  }
}
```

---

### 4. Get Dashboard Data

**Endpoint:** `GET /api/admin/dashboard`

---

### 5. Export Data

**Endpoint:** `GET /api/admin/export_data?type=deliveries`

Options: `deliveries`, `customers`

---

## 🔧 Utility Endpoints

### 1. Get Weather

**Endpoint:** `POST /api/get_weather`

**Request Body:**
```json
{
  "latitude": 40.7128,
  "longitude": -74.0060
}
```

Or:
```json
{
  "city": "New York"
}
```

**Response:**
```json
{
  "success": true,
  "weather": {
    "temperature": 22.5,
    "feels_like": 21.8,
    "condition": "sunny",
    "description": "clear sky",
    "humidity": 65,
    "wind_speed": 5.2,
    "location": "New York"
  }
}
```

---

### 2. Get Distance

**Endpoint:** `POST /api/get_distance`

**Request Body:**
```json
{
  "origin": "New York, NY",
  "destination": "Boston, MA"
}
```

Or use coordinates:
```json
{
  "origin": [40.7128, -74.0060],
  "destination": [42.3601, -71.0589]
}
```

**Response:**
```json
{
  "success": true,
  "distance": {
    "distance_km": 306.5,
    "distance_text": "306 km",
    "duration_minutes": 245.3,
    "duration_text": "4 hours 5 mins",
    "traffic_duration_minutes": 280.5,
    "traffic_level": "medium",
    "traffic_ratio": 1.14
  }
}
```

---

## ⚠️ Error Handling

All endpoints return errors in this format:

```json
{
  "success": false,
  "error": "Error message description"
}
```

### HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `404` - Not Found
- `500` - Internal Server Error

---

## 📊 Data Models

### Delivery Model
```json
{
  "id": 1,
  "customer_id": 1,
  "pickup_location": "Warehouse A",
  "pickup_latitude": 40.7589,
  "pickup_longitude": -73.9851,
  "delivery_location": "123 Main St",
  "delivery_latitude": 40.7128,
  "delivery_longitude": -74.0060,
  "distance": 5.2,
  "traffic_level": "medium",
  "weather_condition": "sunny",
  "temperature": 22.5,
  "package_weight": 2.5,
  "package_type": "electronics",
  "predicted_slot": "morning",
  "estimated_time": 32,
  "actual_time": 35,
  "route_cluster": 0,
  "status": "delivered",
  "delivery_date": "2024-01-20"
}
```

### Customer Model
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "1234567890",
  "address": "123 Main St, New York",
  "latitude": 40.7128,
  "longitude": -74.0060
}
```

---

## 🔑 Authentication

Currently, the API does not require authentication. For production deployment, implement:
- JWT tokens
- API keys
- OAuth 2.0

---

## 📈 Rate Limiting

No rate limiting in development mode. For production:
- Implement rate limiting
- Use caching for frequent requests
- Monitor API usage

---

**API Documentation v1.0**


