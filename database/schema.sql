-- SmartParcel AI Database Schema
-- MySQL Database Setup

CREATE DATABASE IF NOT EXISTS smartparcel_ai
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE smartparcel_ai;

-- Users table (for customers and admins)
CREATE TABLE IF NOT EXISTS users (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  is_admin TINYINT(1) DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  product_name VARCHAR(255) NOT NULL,
  price DECIMAL(10, 2) NOT NULL,
  distance DECIMAL(8, 2) NOT NULL,
  traffic VARCHAR(20) NOT NULL,
  weather VARCHAR(20) NOT NULL,
  order_hour INT NOT NULL,
  previous_customer_availability TINYINT(1) NOT NULL,
  predicted_slot VARCHAR(20) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for better performance
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_order_user_id ON orders(user_id);
CREATE INDEX idx_order_created_at ON orders(created_at);
