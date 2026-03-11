from math import radians, cos, sin, sqrt, atan2

DISTRICT_PROFILES = [
    {"district": "Ariyalur", "lat": 11.1401, "lon": 79.0753, "N": 65, "P": 50, "K": 48, "pH": 7.1, "soil_type": "Red Loamy"},
    {"district": "Chengalpattu", "lat": 12.6819, "lon": 79.9864, "N": 65, "P": 48, "K": 50, "pH": 7.0, "soil_type": "Alluvial"},
    {"district": "Chennai", "lat": 13.0827, "lon": 80.2707, "N": 60, "P": 50, "K": 48, "pH": 7.0, "soil_type": "Sandy Loam"},
    {"district": "Coimbatore", "lat": 11.0168, "lon": 76.9558, "N": 45, "P": 55, "K": 60, "pH": 6.5, "soil_type": "Red Sandy"},
    {"district": "Cuddalore", "lat": 11.7480, "lon": 79.7714, "N": 70, "P": 48, "K": 45, "pH": 6.7, "soil_type": "Loamy"},
    {"district": "Dharmapuri", "lat": 12.1211, "lon": 78.1582, "N": 48, "P": 50, "K": 52, "pH": 6.8, "soil_type": "Red Sandy"},
    {"district": "Dindigul", "lat": 10.3673, "lon": 77.9803, "N": 50, "P": 55, "K": 55, "pH": 7.0, "soil_type": "Red Loamy"},
    {"district": "Erode", "lat": 11.3410, "lon": 77.7172, "N": 50, "P": 52, "K": 58, "pH": 6.8, "soil_type": "Red Loamy"},
    {"district": "Kallakurichi", "lat": 11.7381, "lon": 78.9593, "N": 62, "P": 50, "K": 50, "pH": 6.8, "soil_type": "Red Loamy"},
    {"district": "Kanchipuram", "lat": 12.8342, "lon": 79.7036, "N": 68, "P": 50, "K": 48, "pH": 6.8, "soil_type": "Loamy"},
    {"district": "Kanyakumari", "lat": 8.0883, "lon": 77.5385, "N": 48, "P": 55, "K": 65, "pH": 6.5, "soil_type": "Laterite"},
    {"district": "Karur", "lat": 10.9601, "lon": 78.0766, "N": 55, "P": 52, "K": 52, "pH": 7.0, "soil_type": "Black Soil"},
    {"district": "Krishnagiri", "lat": 12.5186, "lon": 78.2137, "N": 50, "P": 52, "K": 50, "pH": 6.7, "soil_type": "Red Loamy"},
    {"district": "Madurai", "lat": 9.9252, "lon": 78.1198, "N": 55, "P": 52, "K": 50, "pH": 7.2, "soil_type": "Black Soil"},
    {"district": "Mayiladuthurai", "lat": 11.8745, "lon": 79.8100, "N": 80, "P": 45, "K": 42, "pH": 6.9, "soil_type": "Clayey"},
    {"district": "Nagapattinam", "lat": 10.7661, "lon": 79.8419, "N": 82, "P": 46, "K": 38, "pH": 7.0, "soil_type": "Alluvial"},
    {"district": "Namakkal", "lat": 11.2189, "lon": 78.1677, "N": 50, "P": 52, "K": 54, "pH": 7.0, "soil_type": "Black Soil"},
    {"district": "Nilgiris", "lat": 11.4102, "lon": 76.6950, "N": 35, "P": 65, "K": 55, "pH": 6.0, "soil_type": "Mountain Soil"},
    {"district": "Perambalur", "lat": 11.2324, "lon": 78.8801, "N": 68, "P": 50, "K": 48, "pH": 6.8, "soil_type": "Red Loamy"},
    {"district": "Pudukkottai", "lat": 10.3833, "lon": 78.8208, "N": 60, "P": 52, "K": 50, "pH": 7.1, "soil_type": "Red Sandy"},
    {"district": "Ramanathapuram", "lat": 9.3639, "lon": 78.8394, "N": 45, "P": 50, "K": 45, "pH": 7.5, "soil_type": "Sandy"},
    {"district": "Ranipet", "lat": 12.9249, "lon": 79.3313, "N": 58, "P": 50, "K": 52, "pH": 6.8, "soil_type": "Red Loamy"},
    {"district": "Salem", "lat": 11.6643, "lon": 78.1460, "N": 52, "P": 54, "K": 55, "pH": 6.9, "soil_type": "Red Loamy"},
    {"district": "Sivaganga", "lat": 9.8471, "lon": 78.4836, "N": 48, "P": 50, "K": 48, "pH": 7.3, "soil_type": "Red Sandy"},
    {"district": "Tenkasi", "lat": 8.9658, "lon": 77.3152, "N": 50, "P": 53, "K": 52, "pH": 6.8, "soil_type": "Red Loamy"},
    {"district": "Thanjavur", "lat": 10.7870, "lon": 79.1378, "N": 85, "P": 45, "K": 42, "pH": 6.8, "soil_type": "Clayey"},
    {"district": "Theni", "lat": 10.0104, "lon": 77.4771, "N": 52, "P": 54, "K": 52, "pH": 6.9, "soil_type": "Red Sandy"},
    {"district": "Thiruvallur", "lat": 13.1189, "lon": 79.9119, "N": 65, "P": 48, "K": 50, "pH": 6.9, "soil_type": "Clayey Loam"},
    {"district": "Thiruvarur", "lat": 10.7672, "lon": 79.6345, "N": 88, "P": 43, "K": 40, "pH": 6.9, "soil_type": "Clayey"},
    {"district": "Thoothukudi", "lat": 8.7642, "lon": 78.1348, "N": 42, "P": 50, "K": 48, "pH": 7.4, "soil_type": "Sandy"},
    {"district": "Tiruchirappalli", "lat": 10.7905, "lon": 78.7047, "N": 75, "P": 48, "K": 45, "pH": 6.9, "soil_type": "Alluvial"},
    {"district": "Tirunelveli", "lat": 8.7139, "lon": 77.7567, "N": 45, "P": 52, "K": 50, "pH": 7.2, "soil_type": "Red Loamy"},
    {"district": "Tirupathur", "lat": 12.4945, "lon": 78.5719, "N": 52, "P": 50, "K": 52, "pH": 6.8, "soil_type": "Red Soil"},
    {"district": "Tiruppur", "lat": 11.1085, "lon": 77.3411, "N": 48, "P": 54, "K": 62, "pH": 6.7, "soil_type": "Black Cotton"},
    {"district": "Tiruvannamalai", "lat": 12.2253, "lon": 79.0747, "N": 60, "P": 52, "K": 50, "pH": 6.9, "soil_type": "Red Loamy"},
    {"district": "Vellore", "lat": 12.9165, "lon": 79.1325, "N": 58, "P": 50, "K": 52, "pH": 6.8, "soil_type": "Red Soil"},
    {"district": "Viluppuram", "lat": 11.9401, "lon": 79.4861, "N": 65, "P": 48, "K": 48, "pH": 7.0, "soil_type": "Loamy"},
    {"district": "Virudhunagar", "lat": 9.5851, "lon": 77.9579, "N": 47, "P": 51, "K": 50, "pH": 7.3, "soil_type": "Black Soil"},
]


def _distance_km(lat1, lon1, lat2, lon2):
    r = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return r * 2 * atan2(sqrt(a), sqrt(1 - a))


def get_nearest_district_profile(latitude, longitude):
    nearest = min(
        DISTRICT_PROFILES,
        key=lambda row: _distance_km(latitude, longitude, row["lat"], row["lon"]),
    )
    profile = dict(nearest)
    profile["distance_km"] = round(_distance_km(latitude, longitude, profile["lat"], profile["lon"]), 1)
    return profile
