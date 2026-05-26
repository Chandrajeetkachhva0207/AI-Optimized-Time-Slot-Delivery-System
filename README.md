# NEXUS: AI-Powered Smart Parcel Delivery System 🚀

[![Project Status: Active](https://img.shields.io/badge/Project%20Status-Active-brightgreen.svg)](https://github.com/your-repo/nexus)
[![Python Version](https://img.shields.io/badge/Python-3.13%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**NEXUS** is a next-generation logistics intelligence platform built to solve the complex challenges of urban delivery. By combining real-time GPS tracking with advanced Machine Learning and integrated secure payments, NEXUS optimizes every step of the delivery lifecycle.

---

## 💎 The NEXUS Experience

The platform is designed with a **Premium Neo-Dark Aesthetic**, focusing on high-density information visualization and a seamless user experience.

- **Live Command Center:** Real-time visualization of the entire delivery fleet.
- **AI-First Logic:** Predictive slot allocation and ETA calculation.
- **Secure Payments:** Integrated **Razorpay** gateway for seamless transactions.
- **Glassmorphism UI:** Modern, translucent design language.
- **Smart Navigation:** Dynamic Leaflet maps with live tracking.

---

## 📁 Project Structure

```text
Major Project/
├── backend/
│   ├── app.py                         # Main Entry Point & Flask Server
│   ├── config.py                      # Global Configurations & Secrets (Razorpay keys added)
│   │
│   ├── routes/                        # API & Controllers
│   │   ├── auth.py                    # User Authentication
│   │   ├── orders.py                  # Order + Payment Order Creation
│   │   ├── payments.py                # Razorpay Payment & Verification APIs
│   │   ├── tracking.py                # Live Tracking System
│   │   ├── delivery_ops.py            # Admin Fleet Control
│   │   └── delivery.py                # Delivery Prediction Logic
│   │
│   ├── services/                      # Business Logic Layer
│   │   ├── payment_service.py         # Razorpay Integration Logic
│   │   ├── route_opt.py               # Route Optimization
│   │   └── slot_ai.py                 # AI Slot Prediction
│   │
│   ├── ml_models/                     # AI/ML Models
│   │   ├── time_slot_classifier.py
│   │   └── delivery_time_regressor.py
│   │
│   ├── templates/                     # Frontend UI
│   │   ├── dashboard.html
│   │   ├── track-order.html
│   │   ├── checkout.html              # Razorpay Payment Button Added
│   │   ├── payment_success.html       # Payment Success Page
│   │   ├── payment_failed.html        # Payment Failed Page
│   │   └── admin_delivery_hub.html
│
├── database/
│   ├── schema.sql                     # Tables (users, orders, payments)
│   └── init_db.py
│
├── data/
│   ├── datasets/
│   └── models/
│
├── static/                            # JS, CSS, Assets
│   ├── js/
│   │   ├── payment.js                 # Razorpay Frontend Logic
│   │   └── tracking.js
│   ├── css/
│   └── assets/
│
├── utils/
│   ├── helpers.py
│   └── security.py
│
├── .env                               # Environment Variables (Razorpay Keys)
├── requirements.txt
└── README.md                          # Project Documentation
```

---

## 🚀 Installation & Setup

### **1. Environment Setup**
```bash
# Clone and enter the project
git clone <repository-url>
cd "Major Project"

# Create a virtual environment
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

# Install all required libraries
pip install -r requirements.txt
```

### **2. Configuration**
Update your `.env` file with the necessary API keys:
```env
RAZORPAY_KEY_ID=your_key_id
RAZORPAY_KEY_SECRET=your_key_secret
SECRET_KEY=your_flask_secret
OPENWEATHER_API_KEY=your_weather_key
```

### **3. Execution**
```bash
cd backend
python app.py
```
Open `http://localhost:5000` in your browser.

---

## 📡 API Reference (Highlights)

### **Payments & Tracking**
| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/payments/create` | `POST` | Create a new Razorpay order. |
| `/api/payments/verify` | `POST` | Verify payment signature and update order. |
| `/api/tracking/<id>` | `GET` | Fetch live GPS and delivery status. |

---

## 🎓 Smart India Hackathon 2024
Developed for **Problem Statement SIH760** - Transportation & Logistics.

---

## 📄 License
MIT License
