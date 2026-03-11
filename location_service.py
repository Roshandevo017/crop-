import requests
import time

class LocationService:
    """
    Handles reverse geocoding and weather data fetching
    Uses only FREE APIs with no registration required
    """
    
    def __init__(self):
        self.last_api_call = 0
        self.min_interval = 1.0  # Rate limit: 1 request per second
    
    def _rate_limit(self):
        """Respect API rate limits"""
        now = time.time()
        time_since_last = now - self.last_api_call
        
        if time_since_last < self.min_interval:
            time.sleep(self.min_interval - time_since_last)
        
        self.last_api_call = time.time()
    
    def get_location_name(self, latitude, longitude):
        """
        Get location name from coordinates using Nominatim (OpenStreetMap)
        FREE, no API key required
        Rate limit: 1 request/second
        """
        try:
            self._rate_limit()
            
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                'lat': latitude,
                'lon': longitude,
                'format': 'json',
                'addressdetails': 1,
                'accept-language': 'en'
            }
            headers = {
                'User-Agent': 'CropRecommendationApp/1.0 (Educational Project)'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                address = data.get('address', {})
                
                # Extract location details
                location_info = {
                    'location_name': data.get('display_name', 'Unknown Location'),
                    'state': address.get('state', ''),
                    'district': address.get('state_district', '') or address.get('county', ''),
                    'city': address.get('city', '') or address.get('town', '') or address.get('village', ''),
                    'country': address.get('country', ''),
                    'country_code': address.get('country_code', '').upper()
                }
                
                print(f"✅ Geocoding success: {location_info['location_name']}")
                return location_info
            else:
                print(f"⚠️ Geocoding failed: Status {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Geocoding error: {e}")
            return None
    
    def get_weather_data(self, latitude, longitude):
        """
        Get weather data from Open-Meteo
        FREE, no API key required, unlimited requests
        
        IMPORTANT: Scales rainfall to crop season (4 months)
        """
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                'latitude': latitude,
                'longitude': longitude,
                'current_weather': True,
                'daily': [
                    'temperature_2m_max',
                    'temperature_2m_min',
                    'precipitation_sum',
                    'relative_humidity_2m_max'
                ],
                'timezone': 'auto',
                'past_days': 30  # Get last 30 days for averages
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                current = data.get('current_weather', {})
                daily = data.get('daily', {})
                
                # Calculate 30-day averages
                temp_max_list = daily.get('temperature_2m_max', [])
                temp_min_list = daily.get('temperature_2m_min', [])
                precipitation_list = daily.get('precipitation_sum', [])
                humidity_list = daily.get('relative_humidity_2m_max', [])
                
                # Average temperature
                if temp_max_list and temp_min_list:
                    avg_max = sum(temp_max_list) / len(temp_max_list)
                    avg_min = sum(temp_min_list) / len(temp_min_list)
                    temperature = round((avg_max + avg_min) / 2, 1)
                else:
                    temperature = round(current.get('temperature', 25), 1)
                
                # ============================================================
                # RAINFALL CALCULATION - FIXED FOR CROP PREDICTIONS
                # ============================================================
                
                if precipitation_list:
                    # Monthly total from last 30 days
                    monthly_total = round(sum(precipitation_list), 1)
                    
                    # Scale to crop season (4 months average)
                    # Most crops need 3-6 months, so 4 is reasonable average
                    rainfall = round(monthly_total * 4, 1)
                    
                    # Clamp to realistic range
                    # Minimum: Even desert crops need 60mm+
                    # Maximum: Very high rainfall crops need up to 400mm
                    rainfall = min(max(rainfall, 60), 400)
                    
                    print(f"📊 Rainfall calculation:")
                    print(f"   30-day total: {monthly_total}mm")
                    print(f"   Scaled (×4 months): {rainfall}mm")
                else:
                    rainfall = 100  # Default
                
                # Average humidity
                if humidity_list:
                    humidity = round(sum(humidity_list) / len(humidity_list), 1)
                else:
                    humidity = 70  # Default
                
                weather_info = {
                    'temperature': temperature,
                    'rainfall': rainfall,
                    'humidity': humidity,
                    'current_temp': current.get('temperature', temperature),
                    'monthly_rainfall': monthly_total if precipitation_list else 0
                }
                
                print(f"✅ Weather data: Temp={temperature}°C, Rain={rainfall}mm (seasonal), Humidity={humidity}%")
                return weather_info
            else:
                print(f"⚠️ Weather API failed: Status {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Weather API error: {e}")
            return None
    
    def get_complete_location_data(self, latitude, longitude):
        """
        Get both location name and weather data in one call
        """
        location_info = self.get_location_name(latitude, longitude)
        weather_info = self.get_weather_data(latitude, longitude)
        
        result = {}
        
        if location_info:
            result.update(location_info)
        
        if weather_info:
            result.update(weather_info)
        
        return result if result else None


# Test the service
if __name__ == "__main__":
    service = LocationService()
    
    print("\n🧪 Testing LocationService...")
    print("=" * 60)
    
    # Test with Madurai coordinates (dry region)
    lat, lon = 9.8804, 78.0585
    print(f"\n📍 Testing location: Madurai ({lat}, {lon})")
    
    # Test geocoding
    print("\n1️⃣ Testing reverse geocoding...")
    location = service.get_location_name(lat, lon)
    if location:
        print(f"   Location: {location['location_name']}")
        print(f"   State: {location['state']}")
        print(f"   District: {location['district']}")
    
    # Test weather
    print("\n2️⃣ Testing weather data...")
    weather = service.get_weather_data(lat, lon)
    if weather:
        print(f"   Temperature: {weather['temperature']}°C")
        print(f"   Rainfall (seasonal): {weather['rainfall']}mm")
        print(f"   Monthly rainfall: {weather.get('monthly_rainfall', 0)}mm")
        print(f"   Humidity: {weather['humidity']}%")
    
    # Test combined
    print("\n3️⃣ Testing combined data...")
    complete = service.get_complete_location_data(lat, lon)
    if complete:
        print(f"   ✅ Complete data fetched successfully")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("\n💡 Note: Rainfall is now scaled to crop season (4 months)")
    print("   This prevents unrealistic low values like 38mm!")