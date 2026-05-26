// SmartParcel AI - Frontend JavaScript

const API_BASE_URL = 'http://127.0.0.1:5000/api/auth';

// Sample products data
const PRODUCTS = [
    { id: 1, name: 'Smartphone Pro Max', price: 69999, emoji: '📱' },
    { id: 2, name: 'Wireless Headphones', price: 4999, emoji: '🎧' },
    { id: 3, name: 'Gaming Laptop', price: 89999, emoji: '💻' },
    { id: 4, name: 'Fitness Smartwatch', price: 7999, emoji: '⌚' },
    { id: 5, name: 'Bluetooth Speaker', price: 2999, emoji: '🔊' },
    { id: 6, name: 'DSLR Camera', price: 54999, emoji: '📷' },
    { id: 7, name: 'Tablet Pro', price: 34999, emoji: '📱' },
    { id: 8, name: 'Smart TV 55"', price: 49999, emoji: '📺' },
];

// ==================== Cart Management ====================

function getCart() {
    const cart = localStorage.getItem('cart');
    return cart ? JSON.parse(cart) : [];
}

function saveCart(cart) {
    localStorage.setItem('cart', JSON.stringify(cart));
}

function addToCart(product) {
    const cart = getCart();
    cart.push(product);
    saveCart(cart);
    updateCartBadge();
    showNotification('Product added to cart!');
}

function removeFromCart(index) {
    const cart = getCart();
    cart.splice(index, 1);
    saveCart(cart);
    updateCartBadge();
    if (window.location.pathname.includes('cart')) {
        renderCart();
    }
}

function clearCart() {
    localStorage.removeItem('cart');
    updateCartBadge();
}

function updateCartBadge() {
    const badge = document.getElementById('cart-badge');
    if (badge) {
        const cart = getCart();
        badge.textContent = cart.length;
    }
}

// ==================== Authentication ====================

function getToken() {
    return localStorage.getItem('token');
}

function setToken(token) {
    localStorage.setItem('token', token);
}

function removeToken() {
    localStorage.removeItem('token');
}

function isAuthenticated() {
    return !!getToken();
}

async function registerUser(name, email, password, isAdmin = false) {
    try {
        const response = await fetch(`${API_BASE_URL}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, password, is_admin: isAdmin })
        });
        
        const data = await response.json();
        
        if (!response.ok || !data.success) {
            throw new Error(data.detail || data.message || 'Registration failed');
        }
        
        if (data.access_token) {
            setToken(data.access_token);
            showNotification('Registration successful!');
            
            if (data.is_admin) {
                window.location.href = '/admin/dashboard';
            } else {
                window.location.href = '/';
            }
        } else {
            throw new Error('No token received from server');
        }
    } catch (error) {
        showError(error.message);
    }
}

async function loginUser(email, password) {
    try {
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (!response.ok || !data.success) {
            throw new Error(data.detail || data.message || 'Login failed');
        }
        
        if (data.access_token) {
            setToken(data.access_token);
            showNotification('Login successful!');
            
            if (data.is_admin) {
                window.location.href = '/admin/dashboard';
            } else {
                window.location.href = '/';
            }
        } else {
            throw new Error('No token received from server');
        }
    } catch (error) {
        showError(error.message);
    }
}

function logout() {
    removeToken();
    showNotification('Logged out successfully');
    window.location.href = '/';
}

// ==================== Product Rendering ====================

function renderProducts() {
    const grid = document.getElementById('products-grid');
    if (!grid) return;
    
    grid.innerHTML = PRODUCTS.map(product => `
        <div class="product-card">
            <div class="product-image">${product.emoji}</div>
            <div class="product-info">
                <div class="product-name">${product.name}</div>
                <div class="product-price">₹${product.price.toLocaleString()}</div>
                <button class="add-to-cart-btn" onclick="addToCart(${JSON.stringify(product).replace(/"/g, '&quot;')})">
                    Add to Cart
                </button>
            </div>
        </div>
    `).join('');
}

// ==================== Cart Rendering ====================

function renderCart() {
    const container = document.getElementById('cart-items');
    if (!container) return;
    
    const cart = getCart();
    
    if (cart.length === 0) {
        container.innerHTML = '<p style="text-align: center; padding: 2rem; color: var(--text-secondary);">Your cart is empty.</p>';
        document.getElementById('cart-items-count').textContent = '0';
        document.getElementById('cart-subtotal').textContent = '₹0.00';
        document.getElementById('cart-total').textContent = '₹0.00';
        return;
    }
    
    container.innerHTML = cart.map((item, index) => `
        <div class="cart-item">
            <div class="cart-item-info">
                <div class="cart-item-name">${item.name}</div>
                <div class="cart-item-price">₹${item.price.toLocaleString()}</div>
            </div>
            <button class="remove-btn" onclick="removeFromCart(${index})">Remove</button>
        </div>
    `).join('');
    
    const total = cart.reduce((sum, item) => sum + item.price, 0);
    document.getElementById('cart-items-count').textContent = cart.length;
    document.getElementById('cart-subtotal').textContent = `₹${total.toLocaleString()}`;
    document.getElementById('cart-total').textContent = `₹${total.toLocaleString()}`;
}

// ==================== AI Prediction ====================

async function predictDeliverySlot(data) {
    const token = getToken();
    if (!token) {
        throw new Error('Please login first');
    }
    
    const response = await fetch('http://127.0.0.1:5000/api/predict-slot', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(data)
    });
    
    const result = await response.json();
    
    if (!response.ok || !result.success) {
        throw new Error(result.detail || result.error || 'Prediction failed');
    }
    
    return result;
}

// ==================== UI Helpers ====================

function showError(message) {
    const errorEl = document.getElementById('error-message');
    if (errorEl) {
        errorEl.textContent = message;
        errorEl.classList.remove('hidden');
    } else {
        alert(message);
    }
}

function showNotification(message) {
    // Simple notification (can be enhanced with toast library)
    alert(message);
}

function updateNavbar() {
    const token = getToken();
    const loginLink = document.getElementById('login-link');
    const registerLink = document.getElementById('register-link');
    const logoutLink = document.getElementById('logout-link');
    
    if (token) {
        if (loginLink) loginLink.classList.add('hidden');
        if (registerLink) registerLink.classList.add('hidden');
        if (logoutLink) logoutLink.classList.remove('hidden');
    } else {
        if (loginLink) loginLink.classList.remove('hidden');
        if (registerLink) registerLink.classList.remove('hidden');
        if (logoutLink) logoutLink.classList.add('hidden');
    }
}

// ==================== Initialize ====================

document.addEventListener('DOMContentLoaded', () => {
    // Render products on home page
    if (document.getElementById('products-grid')) {
        renderProducts();
    }
    
    // Render cart on cart page
    if (document.getElementById('cart-items')) {
        renderCart();
    }
    
    // Update navbar
    updateNavbar();
    updateCartBadge();
});
