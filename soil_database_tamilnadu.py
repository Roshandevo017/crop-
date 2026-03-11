import sqlite3
from math import radians, cos, sin, sqrt, atan2

class SoilDatabase:
    def __init__(self, db_name='tamilnadu_soil_data.db'):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS soil_locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                district TEXT NOT NULL,
                N REAL NOT NULL,
                P REAL NOT NULL,
                K REAL NOT NULL,
                pH REAL NOT NULL,
                temperature REAL NOT NULL,
                humidity REAL NOT NULL,
                rainfall REAL NOT NULL,
                dominant_crop TEXT NOT NULL,
                soil_type TEXT NOT NULL,
                soil_fertility TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()
        print("✅ SoilSense database initialized")

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        R = 6371
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        return R * 2 * atan2(sqrt(a), sqrt(1-a))

    def find_nearest_location(self, latitude, longitude, radius_km=50):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM soil_locations')
        all_locations = cursor.fetchall()
        conn.close()

        nearest, min_dist = None, float('inf')
        for loc in all_locations:
            dist = self.haversine_distance(latitude, longitude, loc[1], loc[2])
            if dist < radius_km and dist < min_dist:
                min_dist, nearest = dist, loc
        
        if nearest:
            return {
                'district': nearest[3], 
                'N': float(nearest[4]) if nearest[4] is not None else 60.0,
                'P': float(nearest[5]) if nearest[5] is not None else 50.0,
                'K': float(nearest[6]) if nearest[6] is not None else 50.0,
                'pH': float(nearest[7]) if nearest[7] is not None else 6.8,
                'temperature': float(nearest[8]) if nearest[8] is not None else 28.0,
                'humidity': float(nearest[9]) if nearest[9] is not None else 75.0,
                'rainfall': float(nearest[10]) if nearest[10] is not None else 100.0,
                'dominant_crop': nearest[11] if nearest[11] is not None else 'rice',
                'soil_type': nearest[12] if nearest[12] is not None else 'Loamy',
                'soil_fertility': nearest[13] if nearest[13] is not None else 'Medium',
                'distance_km': round(min_dist, 2)
            }
        return None

    def populate_tamilnadu_data(self):
        """ALL 38 Tamil Nadu districts with realistic 2025 data + soil info"""
        
        districts = [
            # CAUVERY DELTA - Rice Belt (High Fertility, Clayey Soil)
            {'lat': 10.7870, 'lon': 79.1378, 'name': 'Thanjavur', 'N': 85, 'P': 45, 'K': 42, 'pH': 6.8, 'temp': 29, 'hum': 82, 'rain': 95, 'crop': 'rice', 'soil_type': 'Clayey', 'fertility': 'High'},
            {'lat': 10.7672, 'lon': 79.6345, 'name': 'Tiruvarur', 'N': 88, 'P': 43, 'K': 40, 'pH': 6.9, 'temp': 28, 'hum': 83, 'rain': 100, 'crop': 'rice', 'soil_type': 'Clayey', 'fertility': 'High'},
            {'lat': 10.7661, 'lon': 79.8419, 'name': 'Nagapattinam', 'N': 82, 'P': 46, 'K': 38, 'pH': 7.0, 'temp': 27, 'hum': 85, 'rain': 120, 'crop': 'rice', 'soil_type': 'Alluvial', 'fertility': 'High'},
            {'lat': 11.7480, 'lon': 79.7714, 'name': 'Cuddalore', 'N': 70, 'P': 48, 'K': 45, 'pH': 6.7, 'temp': 28, 'hum': 80, 'rain': 110, 'crop': 'rice', 'soil_type': 'Loamy', 'fertility': 'Medium'},
            {'lat': 11.8745, 'lon': 79.8100, 'name': 'Mayiladuthurai', 'N': 80, 'P': 45, 'K': 42, 'pH': 6.9, 'temp': 28, 'hum': 82, 'rain': 110, 'crop': 'rice', 'soil_type': 'Clayey', 'fertility': 'High'},
            {'lat': 11.1401, 'lon': 79.0753, 'name': 'Ariyalur', 'N': 65, 'P': 50, 'K': 48, 'pH': 7.1, 'temp': 29, 'hum': 75, 'rain': 85, 'crop': 'rice', 'soil_type': 'Red Loamy', 'fertility': 'Medium'},
            
            # WESTERN ZONE - Cotton & Coffee Belt (Medium Fertility, Red/Black Soil)
            {'lat': 11.0168, 'lon': 76.9558, 'name': 'Coimbatore', 'N': 45, 'P': 55, 'K': 60, 'pH': 6.5, 'temp': 24, 'hum': 70, 'rain': 65, 'crop': 'cotton', 'soil_type': 'Red Sandy', 'fertility': 'Medium'},
            {'lat': 11.4102, 'lon': 76.6950, 'name': 'Nilgiris', 'N': 35, 'P': 65, 'K': 55, 'pH': 6.0, 'temp': 18, 'hum': 75, 'rain': 180, 'crop': 'coffee', 'soil_type': 'Mountain Soil', 'fertility': 'Medium'},
            {'lat': 11.3410, 'lon': 77.7172, 'name': 'Erode', 'N': 50, 'P': 52, 'K': 58, 'pH': 6.8, 'temp': 26, 'hum': 68, 'rain': 70, 'crop': 'cotton', 'soil_type': 'Red Loamy', 'fertility': 'Medium'},
            {'lat': 11.1085, 'lon': 77.3411, 'name': 'Tiruppur', 'N': 48, 'P': 54, 'K': 62, 'pH': 6.7, 'temp': 25, 'hum': 65, 'rain': 60, 'crop': 'cotton', 'soil_type': 'Black Cotton', 'fertility': 'Medium'},
            
            # SOUTHERN ZONE - Cotton & Mixed (Medium Fertility)
            {'lat': 9.9252, 'lon': 78.1198, 'name': 'Madurai', 'N': 55, 'P': 52, 'K': 50, 'pH': 7.2, 'temp': 29, 'hum': 68, 'rain': 85, 'crop': 'cotton', 'soil_type': 'Black Soil', 'fertility': 'Medium'},
            {'lat': 10.0104, 'lon': 77.4771, 'name': 'Theni', 'N': 52, 'P': 54, 'K': 52, 'pH': 6.9, 'temp': 27, 'hum': 70, 'rain': 75, 'crop': 'cotton', 'soil_type': 'Red Sandy', 'fertility': 'Medium'},
            {'lat': 10.3673, 'lon': 77.9803, 'name': 'Dindigul', 'N': 50, 'P': 55, 'K': 55, 'pH': 7.0, 'temp': 28, 'hum': 72, 'rain': 80, 'crop': 'cotton', 'soil_type': 'Red Loamy', 'fertility': 'Medium'},
            {'lat': 9.5810, 'lon': 77.9624, 'name': 'Virudhunagar', 'N': 48, 'P': 53, 'K': 50, 'pH': 7.1, 'temp': 29, 'hum': 70, 'rain': 75, 'crop': 'cotton', 'soil_type': 'Red Soil', 'fertility': 'Low'},
            {'lat': 9.8433, 'lon': 78.4809, 'name': 'Sivaganga', 'N': 45, 'P': 50, 'K': 48, 'pH': 7.3, 'temp': 30, 'hum': 65, 'rain': 70, 'crop': 'cotton', 'soil_type': 'Red Sandy', 'fertility': 'Low'},
            {'lat': 9.3647, 'lon': 78.8378, 'name': 'Ramanathapuram', 'N': 40, 'P': 48, 'K': 45, 'pH': 7.5, 'temp': 30, 'hum': 72, 'rain': 85, 'crop': 'cotton', 'soil_type': 'Sandy', 'fertility': 'Low'},
            
            # NORTHERN ZONE - Urban & Coastal (Medium to High Fertility)
            {'lat': 13.0827, 'lon': 80.2707, 'name': 'Chennai', 'N': 60, 'P': 50, 'K': 48, 'pH': 7.0, 'temp': 30, 'hum': 78, 'rain': 140, 'crop': 'rice', 'soil_type': 'Sandy Loam', 'fertility': 'Medium'},
            {'lat': 13.1189, 'lon': 79.9119, 'name': 'Tiruvallur', 'N': 65, 'P': 48, 'K': 50, 'pH': 6.9, 'temp': 29, 'hum': 76, 'rain': 125, 'crop': 'rice', 'soil_type': 'Clayey Loam', 'fertility': 'High'},
            {'lat': 12.8342, 'lon': 79.7036, 'name': 'Kanchipuram', 'N': 68, 'P': 50, 'K': 48, 'pH': 6.8, 'temp': 29, 'hum': 77, 'rain': 130, 'crop': 'rice', 'soil_type': 'Loamy', 'fertility': 'High'},
            {'lat': 12.6819, 'lon': 79.9864, 'name': 'Chengalpattu', 'N': 65, 'P': 48, 'K': 50, 'pH': 7.0, 'temp': 29, 'hum': 78, 'rain': 135, 'crop': 'rice', 'soil_type': 'Alluvial', 'fertility': 'High'},
            {'lat': 12.9249, 'lon': 79.3313, 'name': 'Ranipet', 'N': 58, 'P': 50, 'K': 52, 'pH': 6.8, 'temp': 28, 'hum': 74, 'rain': 100, 'crop': 'rice', 'soil_type': 'Red Loamy', 'fertility': 'Medium'},
            
            # NORTH EASTERN ZONE (Medium Fertility)
            {'lat': 12.9165, 'lon': 79.1325, 'name': 'Vellore', 'N': 58, 'P': 50, 'K': 52, 'pH': 6.8, 'temp': 28, 'hum': 72, 'rain': 95, 'crop': 'rice', 'soil_type': 'Red Soil', 'fertility': 'Medium'},
            {'lat': 12.2253, 'lon': 79.0747, 'name': 'Tiruvannamalai', 'N': 60, 'P': 52, 'K': 50, 'pH': 6.9, 'temp': 28, 'hum': 70, 'rain': 90, 'crop': 'rice', 'soil_type': 'Red Loamy', 'fertility': 'Medium'},
            {'lat': 11.9401, 'lon': 79.4861, 'name': 'Villupuram', 'N': 65, 'P': 48, 'K': 48, 'pH': 7.0, 'temp': 28, 'hum': 78, 'rain': 105, 'crop': 'rice', 'soil_type': 'Loamy', 'fertility': 'Medium'},
            {'lat': 11.7381, 'lon': 78.9593, 'name': 'Kallakurichi', 'N': 62, 'P': 50, 'K': 50, 'pH': 6.8, 'temp': 28, 'hum': 75, 'rain': 100, 'crop': 'rice', 'soil_type': 'Red Loamy', 'fertility': 'Medium'},
            
            # CENTRAL ZONE (High to Medium Fertility)
            {'lat': 10.7905, 'lon': 78.7047, 'name': 'Tiruchirappalli', 'N': 75, 'P': 48, 'K': 45, 'pH': 6.9, 'temp': 29, 'hum': 75, 'rain': 90, 'crop': 'rice', 'soil_type': 'Alluvial', 'fertility': 'High'},
            {'lat': 10.9601, 'lon': 78.0766, 'name': 'Karur', 'N': 55, 'P': 52, 'K': 52, 'pH': 7.0, 'temp': 28, 'hum': 72, 'rain': 75, 'crop': 'cotton', 'soil_type': 'Black Soil', 'fertility': 'Medium'},
            {'lat': 11.2324, 'lon': 78.8801, 'name': 'Perambalur', 'N': 68, 'P': 50, 'K': 48, 'pH': 6.8, 'temp': 28, 'hum': 73, 'rain': 85, 'crop': 'rice', 'soil_type': 'Red Loamy', 'fertility': 'Medium'},
            {'lat': 10.3833, 'lon': 78.8208, 'name': 'Pudukottai', 'N': 60, 'P': 52, 'K': 50, 'pH': 7.1, 'temp': 29, 'hum': 70, 'rain': 80, 'crop': 'cotton', 'soil_type': 'Red Sandy', 'fertility': 'Medium'},
            
            # SOUTHERN TIP (Low to Medium Fertility)
            {'lat': 8.7642, 'lon': 78.1348, 'name': 'Thoothukudi', 'N': 42, 'P': 50, 'K': 48, 'pH': 7.4, 'temp': 30, 'hum': 75, 'rain': 65, 'crop': 'cotton', 'soil_type': 'Sandy', 'fertility': 'Low'},
            {'lat': 8.7139, 'lon': 77.7567, 'name': 'Tirunelveli', 'N': 45, 'P': 52, 'K': 50, 'pH': 7.2, 'temp': 29, 'hum': 73, 'rain': 70, 'crop': 'rice', 'soil_type': 'Red Loamy', 'fertility': 'Medium'},
            {'lat': 8.0883, 'lon': 77.5385, 'name': 'Kanyakumari', 'N': 48, 'P': 55, 'K': 65, 'pH': 6.5, 'temp': 27, 'hum': 80, 'rain': 140, 'crop': 'coconut', 'soil_type': 'Laterite', 'fertility': 'Medium'},
            {'lat': 8.9658, 'lon': 77.3152, 'name': 'Tenkasi', 'N': 50, 'P': 53, 'K': 52, 'pH': 6.8, 'temp': 28, 'hum': 75, 'rain': 90, 'crop': 'rice', 'soil_type': 'Red Loamy', 'fertility': 'Medium'},
            
            # NORTH WESTERN ZONE (Medium Fertility)
            {'lat': 11.6643, 'lon': 78.1460, 'name': 'Salem', 'N': 52, 'P': 54, 'K': 55, 'pH': 6.9, 'temp': 27, 'hum': 70, 'rain': 85, 'crop': 'cotton', 'soil_type': 'Red Loamy', 'fertility': 'Medium'},
            {'lat': 11.2189, 'lon': 78.1677, 'name': 'Namakkal', 'N': 50, 'P': 52, 'K': 54, 'pH': 7.0, 'temp': 27, 'hum': 72, 'rain': 80, 'crop': 'cotton', 'soil_type': 'Black Soil', 'fertility': 'Medium'},
            {'lat': 12.1211, 'lon': 78.1582, 'name': 'Dharmapuri', 'N': 48, 'P': 50, 'K': 52, 'pH': 6.8, 'temp': 26, 'hum': 68, 'rain': 90, 'crop': 'maize', 'soil_type': 'Red Sandy', 'fertility': 'Medium'},
            {'lat': 12.5186, 'lon': 78.2137, 'name': 'Krishnagiri', 'N': 50, 'P': 52, 'K': 50, 'pH': 6.7, 'temp': 26, 'hum': 70, 'rain': 95, 'crop': 'maize', 'soil_type': 'Red Loamy', 'fertility': 'Medium'},
            {'lat': 12.4945, 'lon': 78.5719, 'name': 'Tirupattur', 'N': 52, 'P': 50, 'K': 52, 'pH': 6.8, 'temp': 27, 'hum': 72, 'rain': 90, 'crop': 'maize', 'soil_type': 'Red Soil', 'fertility': 'Medium'},
        ]
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM soil_locations')
        
        for d in districts:
            cursor.execute('''
                INSERT INTO soil_locations 
                (latitude, longitude, district, N, P, K, pH, temperature, humidity, rainfall, dominant_crop, soil_type, soil_fertility) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (d['lat'], d['lon'], d['name'], d['N'], d['P'], d['K'], d['pH'], 
                  d['temp'], d['hum'], d['rain'], d['crop'], d['soil_type'], d['fertility']))
        
        conn.commit()
        conn.close()
        print(f"✅ ALL 38 Tamil Nadu districts loaded with 2025 data + soil types")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🌾 SOILSENSE DATABASE - 2025 COMPLETE DATA")
    print("="*60)
    db = SoilDatabase()
    db.populate_tamilnadu_data()
    result = db.find_nearest_location(13.0827, 80.2707)
    if result:
        print(f"\n✅ Chennai: N={result['N']}, Soil={result['soil_type']}, Fertility={result['soil_fertility']}")
    print("="*60 + "\n")