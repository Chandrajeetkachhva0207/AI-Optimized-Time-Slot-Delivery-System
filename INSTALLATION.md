# Installation Guide
## AI Optimized Route and Time Slot Delivery System

This guide will walk you through setting up the complete delivery system on your local machine.

---

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8 or higher** - [Download Python](https://www.python.org/downloads/)
- **MySQL 8.0 or PostgreSQL 13+** - [Download MySQL](https://dev.mysql.com/downloads/) or [PostgreSQL](https://www.postgresql.org/download/)
- **Git** (optional) - [Download Git](https://git-scm.com/downloads/)
- **Web Browser** - Chrome, Firefox, or Edge (latest version)

### Optional (Recommended):
- **Google Maps API Key** - [Get API Key](https://developers.google.com/maps/documentation/javascript/get-api-key)
- **OpenWeather API Key** - [Get API Key](https://openweathermap.org/api)

---

## 🚀 Step-by-Step Installation

### Step 1: Set Up Project Directory

```bash
# Navigate to your project directory
cd "D:\Major Project"

# Or create a new directory
mkdir delivery-system
cd delivery-system
```

### Step 2: Create Python Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Python Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- Flask (Backend framework)
- Scikit-learn, XGBoost (ML libraries)
- Pandas, NumPy (Data processing)
- SQLAlchemy (Database ORM)
- Flask-CORS (Cross-origin support)
- And all other dependencies

### Step 4: Database Setup

#### Option A: MySQL

1. **Create Database:**
```sql
mysql -u root -p
CREATE DATABASE delivery_system;
USE delivery_system;
SOURCE database/schema.sql;
EXIT;
```

2. **Configure Database Connection:**

Edit `backend/config.py` or set environment variables:
```python
DATABASE_TYPE = 'mysql'
DATABASE_HOST = 'localhost'
DATABASE_PORT = '3306'
DATABASE_NAME = 'delivery_system'
DATABASE_USER = 'root'
DATABASE_PASSWORD = 'your_password'
```

#### Option B: PostgreSQL

1. **Create Database:**
```bash
psql -U postgres
CREATE DATABASE delivery_system;
\c delivery_system
\i database/schema.sql
\q
```

2. **Configure Database Connection:**
```python
DATABASE_TYPE = 'postgresql'
DATABASE_HOST = 'localhost'
DATABASE_PORT = '5432'
DATABASE_NAME = 'delivery_system'
DATABASE_USER = 'postgres'
DATABASE_PASSWORD = 'your_password'
```

#### Option C: SQLite (Development Only)

SQLite requires no setup and will create a database file automatically. Just set:
```python
SQLALCHEMY_DATABASE_URI = 'sqlite:///delivery_system.db'
```

### Step 5: Configure API Keys (Optional but Recommended)

Create a `config.py` file in the `backend` folder by copying the example:

```bash
cp config.example.py backend/config.py
```

Edit `backend/config.py` and add your API keys:
```python
GOOGLE_MAPS_API_KEY = 'your_google_maps_api_key_here'
OPENWEATHER_API_KEY = 'your_openweather_api_key_here'
```

**Note:** The system will work without API keys using mock data, but real API keys provide accurate weather and traffic information.

### Step 6: Train ML Models

Before running the application, train the AI models:

```bash
python backend/ml_models/model_trainer.py
```

Expected output:
```
============================================================
AI DELIVERY SYSTEM - MODEL TRAINING
============================================================
Training Date: 2024-XX-XX XX:XX:XX
============================================================

[1/3] Training Time Slot Classifier...
✓ Time Slot Classifier trained successfully!
  - Accuracy: 0.XXXX
  - Precision: 0.XXXX
  - Recall: 0.XXXX
  - F1 Score: 0.XXXX

[2/3] Training Delivery Time Regressor...
✓ Delivery Time Regressor trained successfully!
  - MAE: XX.XX minutes
  - RMSE: XX.XX minutes
  - R² Score: 0.XXXX

[3/3] Training Route Optimizer...
✓ Route Optimizer trained successfully!

All 3 models trained successfully!
Models ready for deployment!
```

### Step 7: Start the Backend Server

```bash
python backend/app.py
```

You should see:
```
============================================================
AI OPTIMIZED DELIVERY SYSTEM - BACKEND SERVER
============================================================
Environment: development
Database: mysql+pymysql://root:***@localhost:3306/delivery_system
Model Path: D:\Major Project\backend\data\trained_models
============================================================

Server starting on http://localhost:5000
Press CTRL+C to stop
```

### Step 8: Access the Frontend

Open your web browser and navigate to:

**Option 1: Direct File Access**
```
file:///D:/Major Project/frontend/index.html
```

**Option 2: Local HTTP Server (Recommended)**

In a new terminal:
```bash
# Using Python
cd frontend
python -m http.server 8000

# Or using Node.js (if installed)
npx http-server -p 8000
```

Then open: `http://localhost:8000`

---

## 🎯 Verify Installation

### Test Backend API

Open browser and visit: `http://localhost:5000`

You should see:
```json
{
  "message": "AI Optimized Route and Time Slot Delivery System",
  "status": "running",
  "version": "1.0.0"
}
```

### Test Frontend

1. Navigate to the homepage
2. Click "Book Delivery"
3. Fill in the form with sample data:
   - Name: Test User
   - Email: test@example.com
   - Phone: 1234567890
   - Delivery Latitude: 40.7128
   - Delivery Longitude: -74.0060
   - Package Weight: 2.5 kg
4. Click "Get AI Prediction & Book"
5. You should see AI predictions!

---

## 🔧 Troubleshooting

### Issue: Database Connection Error

**Error:** `Can't connect to MySQL server`

**Solution:**
1. Ensure MySQL is running: `mysql.server status`
2. Check credentials in `backend/config.py`
3. Verify database exists: `SHOW DATABASES;`

### Issue: Module Not Found Error

**Error:** `ModuleNotFoundError: No module named 'flask'`

**Solution:**
```bash
# Ensure virtual environment is activated
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: ML Models Not Loading

**Error:** `Could not load ML models`

**Solution:**
```bash
# Retrain models
python backend/ml_models/model_trainer.py

# Check if models directory exists
ls backend/data/trained_models/
```

### Issue: CORS Error in Browser

**Error:** `Access to fetch blocked by CORS policy`

**Solution:**
1. Ensure Flask-CORS is installed: `pip install flask-cors`
2. Backend must be running on `http://localhost:5000`
3. Use HTTP server for frontend instead of `file://`

### Issue: API Keys Not Working

If you don't have API keys, the system will use mock data automatically. To get real data:

1. **Google Maps API:**
   - Visit: https://console.cloud.google.com/
   - Enable "Distance Matrix API" and "Geocoding API"
   - Create API key

2. **OpenWeather API:**
   - Visit: https://openweathermap.org/api
   - Sign up for free tier
   - Get API key from account dashboard

---

## 📱 Access Points

After successful installation:

- **Homepage:** `http://localhost:8000/index.html`
- **Customer Portal:** `http://localhost:8000/customer/dashboard.html`
- **Book Delivery:** `http://localhost:8000/customer/book-delivery.html`
- **Admin Dashboard:** `http://localhost:8000/admin/dashboard.html`
- **Backend API:** `http://localhost:5000`

---

## 🎓 Next Steps

1. **Explore Features:**
   - Book a test delivery
   - View predictions
   - Check admin analytics

2. **Customize:**
   - Modify ML models in `backend/ml_models/`
   - Update frontend styles in `frontend/css/style.css`
   - Add new API endpoints in `backend/routes/`

3. **Production Deployment:**
   - See `DEPLOYMENT.md` for production setup
   - Configure production database
   - Set up proper security

---

## 💡 Tips

- **Development Mode:** Keep `DEBUG = True` in config during development
- **Model Retraining:** Retrain models periodically with new data
- **Database Backup:** Regularly backup your database
- **API Limits:** Free API tiers have rate limits

---

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review logs in terminal/console
3. Ensure all dependencies are installed
4. Verify database connection

---

**Installation Complete! 🎉**

Your AI-powered delivery system is ready to use!


