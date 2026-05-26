from datetime import datetime
import random


def get_current_time_slot():
    """Get current time slot based on hour of day"""
    current_hour = datetime.now().hour
    
    if 6 <= current_hour < 12:
        return 'morning'
    elif 12 <= current_hour < 18:
        return 'afternoon'
    else:
        return 'evening'


def get_day_of_week():
    """Get current day of week (0=Monday, 6=Sunday)"""
    return datetime.now().weekday()


def get_hour():
    """Get current hour (0-23)"""
    return datetime.now().hour


def format_delivery_time(minutes):
    """Format delivery time in minutes to readable format"""
    if minutes < 60:
        return f"{int(minutes)} minutes"
    else:
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        if mins == 0:
            return f"{hours} hour{'s' if hours > 1 else ''}"
        return f"{hours} hour{'s' if hours > 1 else ''} {mins} minutes"


def validate_coordinates(lat, lon):
    """Validate latitude and longitude"""
    try:
        lat = float(lat)
        lon = float(lon)
        return -90 <= lat <= 90 and -180 <= lon <= 180
    except (TypeError, ValueError):
        return False


def generate_tracking_id():
    """Generate unique tracking ID for delivery"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_suffix = ''.join([str(random.randint(0, 9)) for _ in range(4)])
    return f"DEL{timestamp}{random_suffix}"


def calculate_delivery_fee(distance, package_weight):
    """Calculate delivery fee based on distance and weight"""
    base_fee = 5.0
    distance_fee = distance * 0.5  # $0.5 per km
    weight_fee = max(0, (package_weight - 2) * 1.0)  # $1 per kg over 2kg
    
    total_fee = base_fee + distance_fee + weight_fee
    return round(total_fee, 2)


def get_time_slot_display_name(slot):
    """Get display name for time slot"""
    slot_names = {
        'morning': 'Morning (9 AM - 12 PM)',
        'afternoon': 'Afternoon (12 PM - 6 PM)',
        'evening': 'Evening (6 PM - 9 PM)'
    }
    return slot_names.get(slot, slot)


def parse_traffic_level(level):
    """Parse traffic level string to numeric value"""
    traffic_map = {
        'low': 1,
        'medium': 2,
        'high': 3
    }
    return traffic_map.get(level.lower(), 2)


