# Weather Utility Functions
import requests
from datetime import datetime
import os

# Try to import current_app, but handle case when not in Flask context
try:
    from flask import current_app
    _has_flask_context = True
except:
    _has_flask_context = False

def get_weather(location="Kerala, India"):
    """
    Fetch weather data for a location using OpenWeatherMap API.
    
    Args:
        location: Location string (e.g., "Kerala, India" or "Kochi, IN")
    
    Returns:
        dict: {
            'temperature': float (Celsius),
            'humidity': int (percentage),
            'rain_chance': float (0-1),
            'wind_speed': float (km/h),
            'condition': str,
            'description': str,
            'location': str,
            'forecast': list of forecast data,
            'last_updated': str
        }
    """
    # Try to get API key from environment or Flask config
    api_key = None
    try:
        if _has_flask_context:
            try:
                if current_app:
                    api_key = current_app.config.get('WEATHER_API_KEY')
            except RuntimeError:
                # Not in Flask application context
                pass
    except:
        pass
    
    if not api_key:
        api_key = os.environ.get('WEATHER_API_KEY')
    
    # If no API key, return mock data
    if not api_key:
        return _get_mock_weather(location)
    
    try:
        # Get current weather
        try:
            if _has_flask_context and current_app:
                weather_url = current_app.config.get('WEATHER_API_URL', 'https://api.openweathermap.org/data/2.5/weather')
            else:
                weather_url = 'https://api.openweathermap.org/data/2.5/weather'
        except:
            weather_url = 'https://api.openweathermap.org/data/2.5/weather'
        
        params = {
            'q': location,
            'appid': api_key,
            'units': 'metric'  # Get temperature in Celsius
        }
        
        response = requests.get(weather_url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract current weather data
            temperature = data['main']['temp']
            humidity = data['main']['humidity']
            wind_speed = data['wind']['speed'] * 3.6  # Convert m/s to km/h
            condition = data['weather'][0]['main']
            description = data['weather'][0]['description']
            
            # Get rain chance from rain data if available
            rain_chance = 0.0
            if 'rain' in data:
                rain_chance = min(1.0, data['rain'].get('1h', 0) / 10.0)  # Normalize to 0-1
            elif 'clouds' in data:
                # Estimate rain chance from cloud coverage
                cloud_coverage = data['clouds']['all']
                rain_chance = cloud_coverage / 100.0 if cloud_coverage > 50 else 0.0
            
            # Get forecast (next 5 days, 3-hour intervals)
            try:
                forecast = _get_forecast(location, api_key)
            except:
                forecast = []
            
            return {
                'temperature': round(temperature, 1),
                'humidity': humidity,
                'rain_chance': round(rain_chance, 2),
                'wind_speed': round(wind_speed, 1),
                'condition': condition,
                'description': description.title(),
                'location': location,
                'forecast': forecast,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        else:
            # API error, return mock data
            return _get_mock_weather(location)
            
    except Exception as e:
        # Error fetching weather, return mock data
        return _get_mock_weather(location)

def _get_forecast(location, api_key):
    """Get 5-day weather forecast"""
    try:
        try:
            if _has_flask_context and current_app:
                forecast_url = current_app.config.get('WEATHER_FORECAST_URL', 'https://api.openweathermap.org/data/2.5/forecast')
            else:
                forecast_url = 'https://api.openweathermap.org/data/2.5/forecast'
        except:
            forecast_url = 'https://api.openweathermap.org/data/2.5/forecast'
        
        params = {
            'q': location,
            'appid': api_key,
            'units': 'metric'
        }
        
        response = requests.get(forecast_url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            forecast = []
            
            # Get forecast for next 5 days (one per day)
            seen_dates = set()
            for item in data.get('list', [])[:40]:  # Limit to 40 items (5 days * 8 intervals)
                date_str = item['dt_txt'].split(' ')[0]
                if date_str not in seen_dates:
                    seen_dates.add(date_str)
                    forecast.append({
                        'date': date_str,
                        'temperature': round(item['main']['temp'], 1),
                        'condition': item['weather'][0]['main'],
                        'description': item['weather'][0]['description'].title(),
                        'rain_chance': min(1.0, item.get('rain', {}).get('3h', 0) / 10.0) if 'rain' in item else 0.0
                    })
                    if len(forecast) >= 5:
                        break
            
            return forecast
    except:
        pass
    
    return []

def _get_mock_weather(location):
    """Return mock weather data when API is not available"""
    return {
        'temperature': 28.5,
        'humidity': 75,
        'rain_chance': 0.3,
        'wind_speed': 12.5,
        'condition': 'Partly Cloudy',
        'description': 'Partly cloudy',
        'location': location,
        'forecast': [
            {'date': datetime.now().strftime('%Y-%m-%d'), 'temperature': 28.5, 'condition': 'Clouds', 'description': 'Partly cloudy', 'rain_chance': 0.3},
            {'date': (datetime.now().replace(day=datetime.now().day+1) if datetime.now().day < 28 else datetime.now().replace(month=datetime.now().month+1, day=1)).strftime('%Y-%m-%d'), 'temperature': 29.0, 'condition': 'Clear', 'description': 'Clear sky', 'rain_chance': 0.1},
        ],
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

def get_weather_data(location="Kerala, India"):
    """
    Alias for get_weather() for backward compatibility.
    Fetch weather data for a location.
    """
    return get_weather(location)

def get_temperature_for_location(location="Kerala, India"):
    """Get current temperature for yield prediction"""
    weather = get_weather(location)
    return weather.get('temperature', 28.0)

