import requests
import os
import math


class MapsAPI:
    """
    Integration with Google Maps API
    Fetches distance, duration, and traffic data
    """
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get('GOOGLE_MAPS_API_KEY', '')
        self.distance_matrix_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        self.geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
    
    def get_distance_and_traffic(self, origin, destination, mode='driving'):
        """
        Get distance, duration, and traffic data between two locations
        
        Args:
            origin (str or tuple): Origin address or (lat, lon)
            destination (str or tuple): Destination address or (lat, lon)
            mode (str): Travel mode (driving, walking, bicycling, transit)
            
        Returns:
            dict: Distance and duration data
        """
        if not self.api_key:
            return self._get_mock_distance(origin, destination)
        
        try:
            # Format coordinates if provided as tuples
            if isinstance(origin, (tuple, list)):
                origin = f"{origin[0]},{origin[1]}"
            if isinstance(destination, (tuple, list)):
                destination = f"{destination[0]},{destination[1]}"
            
            params = {
                'origins': origin,
                'destinations': destination,
                'mode': mode,
                'departure_time': 'now',  # For traffic data
                'key': self.api_key
            }
            
            response = requests.get(self.distance_matrix_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK':
                element = data['rows'][0]['elements'][0]
                
                if element['status'] == 'OK':
                    distance_meters = element['distance']['value']
                    duration_seconds = element['duration']['value']
                    
                    # Check for traffic data
                    duration_in_traffic = element.get('duration_in_traffic', {})
                    traffic_duration = duration_in_traffic.get('value', duration_seconds)
                    
                    # Calculate traffic level
                    traffic_ratio = traffic_duration / duration_seconds if duration_seconds > 0 else 1
                    if traffic_ratio < 1.2:
                        traffic_level = 'low'
                    elif traffic_ratio < 1.5:
                        traffic_level = 'medium'
                    else:
                        traffic_level = 'high'
                    
                    return {
                        'distance_km': round(distance_meters / 1000, 2),
                        'distance_text': element['distance']['text'],
                        'duration_minutes': round(duration_seconds / 60, 2),
                        'duration_text': element['duration']['text'],
                        'traffic_duration_minutes': round(traffic_duration / 60, 2),
                        'traffic_level': traffic_level,
                        'traffic_ratio': round(traffic_ratio, 2)
                    }
            
            return self._get_mock_distance(origin, destination)
            
        except Exception as e:
            print(f"Error fetching distance data: {str(e)}")
            return self._get_mock_distance(origin, destination)
    
    def geocode_address(self, address):
        """
        Convert address to coordinates
        
        Args:
            address (str): Address to geocode
            
        Returns:
            dict: Latitude and longitude
        """
        if not self.api_key:
            return self._get_mock_geocode(address)
        
        try:
            params = {
                'address': address,
                'key': self.api_key
            }
            
            response = requests.get(self.geocode_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                location = data['results'][0]['geometry']['location']
                return {
                    'latitude': location['lat'],
                    'longitude': location['lng'],
                    'formatted_address': data['results'][0]['formatted_address']
                }
            
            return self._get_mock_geocode(address)
            
        except Exception as e:
            print(f"Error geocoding address: {str(e)}")
            return self._get_mock_geocode(address)
    
    @staticmethod
    def calculate_haversine_distance(lat1, lon1, lat2, lon2):
        """
        Calculate distance between two points using Haversine formula
        
        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates
            
        Returns:
            float: Distance in kilometers
        """
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        distance = R * c
        return round(distance, 2)
    
    @staticmethod
    def _get_mock_distance(origin, destination):
        """Return mock distance data for testing"""
        import random
        
        # Generate random but realistic values
        distance = round(random.uniform(1, 20), 2)
        duration = round(distance * random.uniform(3, 8), 2)  # 3-8 min per km
        
        traffic_levels = ['low', 'medium', 'high']
        traffic_level = random.choice(traffic_levels)
        
        traffic_multiplier = {'low': 1.1, 'medium': 1.3, 'high': 1.6}
        traffic_duration = round(duration * traffic_multiplier[traffic_level], 2)
        
        return {
            'distance_km': distance,
            'distance_text': f'{distance} km',
            'duration_minutes': duration,
            'duration_text': f'{int(duration)} mins',
            'traffic_duration_minutes': traffic_duration,
            'traffic_level': traffic_level,
            'traffic_ratio': round(traffic_duration / duration, 2)
        }
    
    @staticmethod
    def _get_mock_geocode(address):
        """Return mock geocoding data for testing"""
        import random
        
        return {
            'latitude': round(40.7128 + random.uniform(-0.5, 0.5), 6),
            'longitude': round(-74.0060 + random.uniform(-0.5, 0.5), 6),
            'formatted_address': address
        }


