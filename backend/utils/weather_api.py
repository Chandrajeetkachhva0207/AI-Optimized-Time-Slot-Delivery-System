import requests
import os


class WeatherAPI:
    """
    Integration with OpenWeather API
    Fetches real-time weather data for delivery locations
    """
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get('OPENWEATHER_API_KEY', '')
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
    
    def get_weather(self, lat, lon):
        """
        Get weather data for a location
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
            
        Returns:
            dict: Weather data including temperature, condition, etc.
        """
        if not self.api_key:
            # Return mock data if no API key
            return self._get_mock_weather(lat, lon)
        
        try:
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric'  # Celsius
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'temperature': data['main']['temp'],
                'feels_like': data['main']['feels_like'],
                'condition': data['weather'][0]['main'].lower(),
                'description': data['weather'][0]['description'],
                'humidity': data['main']['humidity'],
                'wind_speed': data['wind']['speed'],
                'location': data['name']
            }
            
        except Exception as e:
            print(f"Error fetching weather data: {str(e)}")
            return self._get_mock_weather(lat, lon)
    
    def get_weather_by_city(self, city):
        """
        Get weather data for a city
        
        Args:
            city (str): City name
            
        Returns:
            dict: Weather data
        """
        if not self.api_key:
            return self._get_mock_weather_by_city(city)
        
        try:
            params = {
                'q': city,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'temperature': data['main']['temp'],
                'feels_like': data['main']['feels_like'],
                'condition': data['weather'][0]['main'].lower(),
                'description': data['weather'][0]['description'],
                'humidity': data['main']['humidity'],
                'wind_speed': data['wind']['speed'],
                'location': data['name'],
                'coordinates': {
                    'lat': data['coord']['lat'],
                    'lon': data['coord']['lon']
                }
            }
            
        except Exception as e:
            print(f"Error fetching weather data: {str(e)}")
            return self._get_mock_weather_by_city(city)
    
    @staticmethod
    def _get_mock_weather(lat, lon):
        """Return mock weather data for testing"""
        import random
        
        conditions = ['sunny', 'cloudy', 'rainy', 'foggy']
        
        return {
            'temperature': round(random.uniform(15, 30), 1),
            'feels_like': round(random.uniform(15, 30), 1),
            'condition': random.choice(conditions),
            'description': 'Mock weather data',
            'humidity': random.randint(40, 80),
            'wind_speed': round(random.uniform(0, 15), 1),
            'location': f'Location ({lat}, {lon})'
        }
    
    @staticmethod
    def _get_mock_weather_by_city(city):
        """Return mock weather data for testing"""
        import random
        
        conditions = ['sunny', 'cloudy', 'rainy', 'foggy']
        
        return {
            'temperature': round(random.uniform(15, 30), 1),
            'feels_like': round(random.uniform(15, 30), 1),
            'condition': random.choice(conditions),
            'description': 'Mock weather data',
            'humidity': random.randint(40, 80),
            'wind_speed': round(random.uniform(0, 15), 1),
            'location': city,
            'coordinates': {
                'lat': 40.7128,
                'lon': -74.0060
            }
        }


