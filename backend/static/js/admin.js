// Admin Panel JavaScript

const API_BASE_URL = 'http://localhost:5000/api';

// Load dashboard data on page load
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardData();
});

async function loadDashboardData() {
    try {
        const response = await fetch(`${API_BASE_URL}/admin/dashboard`);
        const data = await response.json();
        
        if (data.success) {
            const stats = data.dashboard.statistics;
            
            // Update statistics
            document.getElementById('totalDeliveries').textContent = stats.total_deliveries;
            document.getElementById('totalCustomers').textContent = stats.total_customers;
            document.getElementById('pendingDeliveries').textContent = stats.pending_deliveries;
            document.getElementById('todayDeliveries').textContent = stats.today_deliveries;
            
            // Display recent deliveries
            displayRecentDeliveries(data.dashboard.recent_deliveries);
        }
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

function displayRecentDeliveries(deliveries) {
    const tbody = document.getElementById('recentDeliveries');
    
    if (deliveries.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center">No recent deliveries</td></tr>';
        return;
    }
    
    tbody.innerHTML = deliveries.map(d => `
        <tr>
            <td>${d.id}</td>
            <td>${d.customer_name || 'N/A'}</td>
            <td><small>${d.delivery_location}</small></td>
            <td><span class="badge bg-info">${d.predicted_slot || 'N/A'}</span></td>
            <td><span class="badge badge-${d.status}">${d.status}</span></td>
            <td>${d.delivery_date || 'N/A'}</td>
        </tr>
    `).join('');
}

async function trainModels() {
    if (!confirm('This will retrain all ML models. Continue?')) {
        return;
    }
    
    // Show loading spinner
    document.getElementById('loadingSpinner').style.display = 'flex';
    
    try {
        const response = await fetch(`${API_BASE_URL}/admin/train_model`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model_type: 'all'
            })
        });
        
        const data = await response.json();
        
        document.getElementById('loadingSpinner').style.display = 'none';
        
        if (data.success) {
            let message = 'Models trained successfully!\n\n';
            
            if (data.results.classifier) {
                message += `Time Slot Classifier:\n`;
                message += `- Accuracy: ${(data.results.classifier.accuracy * 100).toFixed(2)}%\n`;
                message += `- F1 Score: ${(data.results.classifier.f1_score * 100).toFixed(2)}%\n\n`;
            }
            
            if (data.results.regressor) {
                message += `Delivery Time Regressor:\n`;
                message += `- MAE: ${data.results.regressor.mae.toFixed(2)} min\n`;
                message += `- RMSE: ${data.results.regressor.rmse.toFixed(2)} min\n\n`;
            }
            
            if (data.results.optimizer) {
                message += `Route Optimizer:\n`;
                message += `- Clusters: ${data.results.optimizer.n_clusters}\n`;
            }
            
            alert(message);
        } else {
            alert('Error training models: ' + data.error);
        }
        
    } catch (error) {
        document.getElementById('loadingSpinner').style.display = 'none';
        console.error('Error training models:', error);
        alert('Error training models. Please check if the server is running.');
    }
}

async function optimizeRoutes() {
    try {
        // Get all pending deliveries
        const response = await fetch(`${API_BASE_URL}/deliveries?status=pending`);
        const data = await response.json();
        
        if (data.success && data.deliveries.length > 0) {
            document.getElementById('loadingSpinner').style.display = 'flex';
            
            const deliveriesData = data.deliveries.map(d => ({
                delivery_latitude: d.delivery_latitude || 40.7128,
                delivery_longitude: d.delivery_longitude || -74.0060,
                hour: new Date().getHours()
            }));
            
            const routeResponse = await fetch(`${API_BASE_URL}/predict_route`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    deliveries: deliveriesData
                })
            });
            
            const routeData = await routeResponse.json();
            
            document.getElementById('loadingSpinner').style.display = 'none';
            
            if (routeData.success) {
                const optimization = routeData.optimization;
                alert(`Routes optimized successfully!\n\nTotal Deliveries: ${optimization.total_deliveries}\nOptimal Routes: ${optimization.num_routes}`);
            }
        } else {
            alert('No pending deliveries to optimize');
        }
        
    } catch (error) {
        document.getElementById('loadingSpinner').style.display = 'none';
        console.error('Error optimizing routes:', error);
        alert('Error optimizing routes');
    }
}

// Export data function
async function exportData(type) {
    try {
        const response = await fetch(`${API_BASE_URL}/admin/export_data?type=${type}`);
        const data = await response.json();
        
        if (data.success) {
            // Convert to CSV
            const csv = convertToCSV(data.data);
            
            // Download file
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${type}_export_${new Date().toISOString().split('T')[0]}.csv`;
            a.click();
        }
    } catch (error) {
        console.error('Error exporting data:', error);
        alert('Error exporting data');
    }
}

function convertToCSV(data) {
    if (data.length === 0) return '';
    
    const headers = Object.keys(data[0]);
    const csvRows = [];
    
    csvRows.push(headers.join(','));
    
    for (const row of data) {
        const values = headers.map(header => {
            const val = row[header];
            return typeof val === 'string' ? `"${val}"` : val;
        });
        csvRows.push(values.join(','));
    }
    
    return csvRows.join('\n');
}


