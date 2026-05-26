// Customer Portal JavaScript

const API_BASE_URL = 'http://localhost:5000/api';
let predictionData = null;

// Handle delivery form submission
document.getElementById('deliveryForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // Show loading spinner
    document.getElementById('loadingSpinner').style.display = 'flex';
    
    // Get form data
    const formData = {
        customer_name: document.getElementById('customerName').value,
        customer_email: document.getElementById('customerEmail').value,
        customer_phone: document.getElementById('customerPhone').value,
        pickup_location: document.getElementById('pickupLocation').value,
        pickup_latitude: 40.7589,  // Default warehouse location
        pickup_longitude: -73.9851,
        delivery_location: document.getElementById('deliveryLocation').value,
        delivery_latitude: parseFloat(document.getElementById('deliveryLat').value) || 40.7128,
        delivery_longitude: parseFloat(document.getElementById('deliveryLon').value) || -74.0060,
        package_type: document.getElementById('packageType').value,
        package_weight: parseFloat(document.getElementById('packageWeight').value),
        delivery_date: document.getElementById('deliveryDate').value,
        preferred_time: document.getElementById('preferredTime').value
    };
    
    try {
        // Get AI prediction first
        const predictionResponse = await fetch(`${API_BASE_URL}/predict_slot`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                delivery_latitude: formData.delivery_latitude,
                delivery_longitude: formData.delivery_longitude,
                pickup_location: [formData.pickup_latitude, formData.pickup_longitude],
                package_weight: formData.package_weight,
                preferred_hour: new Date().getHours()
            })
        });
        
        const predictionResult = await predictionResponse.json();
        
        // Get time estimation
        const timeResponse = await fetch(`${API_BASE_URL}/estimate_time`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                delivery_latitude: formData.delivery_latitude,
                delivery_longitude: formData.delivery_longitude,
                pickup_location: [formData.pickup_latitude, formData.pickup_longitude],
                package_weight: formData.package_weight,
                hour: new Date().getHours()
            })
        });
        
        const timeResult = await timeResponse.json();
        
        // Hide loading spinner
        document.getElementById('loadingSpinner').style.display = 'none';
        
        if (predictionResult.success && timeResult.success) {
            // Store prediction data for booking
            predictionData = {
                ...formData,
                predicted_slot: predictionResult.predicted_slot,
                estimated_time: timeResult.estimated_time,
                weather: predictionResult.weather,
                distance: predictionResult.distance
            };
            
            // Display prediction results
            displayPrediction(predictionResult, timeResult);
        } else {
            alert('Error getting AI prediction. Please try again.');
        }
        
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('loadingSpinner').style.display = 'none';
        alert('Error processing request. Please check if the server is running.');
    }
});

function displayPrediction(prediction, timeEstimate) {
    const resultDiv = document.getElementById('predictionResult');
    const contentDiv = document.getElementById('predictionContent');
    
    const confidence = (prediction.confidence * 100).toFixed(0);
    const timeSlot = prediction.predicted_slot;
    const estimatedTime = timeEstimate.estimated_time;
    const weather = prediction.weather;
    const distance = prediction.distance;
    
    contentDiv.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <div class="prediction-item">
                    <span class="prediction-label">
                        <i class="bi bi-clock"></i> Optimal Time Slot
                    </span>
                    <span class="prediction-value">${timeSlot.toUpperCase()}</span>
                </div>
                <div class="prediction-item">
                    <span class="prediction-label">
                        <i class="bi bi-speedometer"></i> Confidence
                    </span>
                    <span class="prediction-value">${confidence}%</span>
                </div>
                <div class="prediction-item">
                    <span class="prediction-label">
                        <i class="bi bi-stopwatch"></i> Estimated Time
                    </span>
                    <span class="prediction-value">${estimatedTime} mins</span>
                </div>
                <div class="prediction-item">
                    <span class="prediction-label">
                        <i class="bi bi-rulers"></i> Distance
                    </span>
                    <span class="prediction-value">${distance.distance_km} km</span>
                </div>
            </div>
            <div class="col-md-6">
                <div class="prediction-item">
                    <span class="prediction-label">
                        <i class="bi bi-cloud-sun"></i> Weather
                    </span>
                    <span class="prediction-value">${weather.condition}</span>
                </div>
                <div class="prediction-item">
                    <span class="prediction-label">
                        <i class="bi bi-thermometer-half"></i> Temperature
                    </span>
                    <span class="prediction-value">${weather.temperature}°C</span>
                </div>
                <div class="prediction-item">
                    <span class="prediction-label">
                        <i class="bi bi-stoplights"></i> Traffic
                    </span>
                    <span class="prediction-value">${distance.traffic_level.toUpperCase()}</span>
                </div>
                <div class="prediction-item">
                    <span class="prediction-label">
                        <i class="bi bi-geo-alt"></i> Location
                    </span>
                    <span class="prediction-value">${weather.location || 'N/A'}</span>
                </div>
            </div>
        </div>
        
        <div class="mt-3">
            <h6>Time Slot Probabilities:</h6>
            ${Object.entries(prediction.probabilities).map(([slot, prob]) => `
                <div class="mb-2">
                    <div class="d-flex justify-content-between mb-1">
                        <span>${slot.toUpperCase()}</span>
                        <span>${(prob * 100).toFixed(0)}%</span>
                    </div>
                    <div class="progress">
                        <div class="progress-bar" style="width: ${(prob * 100)}%"></div>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
    
    resultDiv.style.display = 'block';
    resultDiv.scrollIntoView({ behavior: 'smooth' });
}

async function confirmBooking() {
    if (!predictionData) {
        alert('No prediction data available');
        return;
    }
    
    // Show loading spinner
    document.getElementById('loadingSpinner').style.display = 'flex';
    
    try {
        const response = await fetch(`${API_BASE_URL}/deliveries`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(predictionData)
        });
        
        const result = await response.json();
        
        document.getElementById('loadingSpinner').style.display = 'none';
        
        if (result.success) {
            alert(`Delivery booked successfully!\nTracking ID: ${result.tracking_id}\nTime Slot: ${result.delivery.predicted_slot}`);
            window.location.href = 'dashboard.html';
        } else {
            alert('Error booking delivery: ' + result.error);
        }
        
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('loadingSpinner').style.display = 'none';
        alert('Error booking delivery. Please try again.');
    }
}


