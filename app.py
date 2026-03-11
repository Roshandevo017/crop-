from flask import Flask, render_template, request, jsonify, send_file
import numpy as np
import joblib
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from location_service import LocationService
from tamilnadu_district_profiles import get_nearest_district_profile

app = Flask(__name__)

# Load XGBoost Model with CORRECT FILENAMES
print("🔄 Loading XGBoost ML model...")
model, label_encoder = None, None
for model_path, encoder_path in [
    ("xgboost_crop_model.joblib", "label_encoder.joblib"),
    ("xgboost_crop_classifier.joblib", "label_encoder_crop.joblib"),
]:
    try:
        model = joblib.load(model_path)
        label_encoder = joblib.load(encoder_path)
        print(f"✅ Model loaded from {model_path}")
        print(f"✅ Label encoder loaded from {encoder_path}")
        print(f"✅ Model can predict {len(label_encoder.classes_)} crops")
        break
    except Exception:
        continue

if model is None or label_encoder is None:
    print("❌ Error loading model artifacts")
    print("⚠️ Expected one of:")
    print("   - xgboost_crop_model.joblib + label_encoder.joblib")
    print("   - xgboost_crop_classifier.joblib + label_encoder_crop.joblib")

# Initialize Location Service (NO DATABASE)
location_service = LocationService()

def get_tamil_season():
    """Current Tamil Nadu agricultural season"""
    month = datetime.now().month
    if month in [6, 7]: 
        return {"name": "Kuruvai Pattam", "desc": "Short-term crop season", "crops": "Quick-maturing crops"}
    elif month in [8, 9, 10, 11]: 
        return {"name": "Samba Pattam", "desc": "Main monsoon season", "crops": "Rice, Cotton, Sugarcane"}
    elif month in [1, 2]: 
        return {"name": "Navarai Pattam", "desc": "Summer/Dry season", "crops": "Summer crops with irrigation"}
    elif month in [4, 5]: 
        return {"name": "Sornavari Pattam", "desc": "Pre-monsoon season", "crops": "Heat-tolerant crops"}
    else:
        return {"name": "Thaladi Season", "desc": "Late season", "crops": "Mixed crops"}

def analyze_soil_fertility(N, P, K, pH):
    """Analyze soil fertility based on NPK and pH"""
    n_status = "High" if N > 75 else ("Medium" if N > 40 else "Low")
    p_status = "High" if P > 55 else ("Medium" if P > 35 else "Low")
    k_status = "High" if K > 55 else ("Medium" if K > 35 else "Low")
    
    if pH < 5.5:
        ph_status = "Acidic (Low pH)"
    elif pH < 6.5:
        ph_status = "Slightly Acidic"
    elif pH < 7.5:
        ph_status = "Neutral (Optimal)"
    elif pH < 8.5:
        ph_status = "Slightly Alkaline"
    else:
        ph_status = "Alkaline (High pH)"
    
    scores = {"High": 3, "Medium": 2, "Low": 1}
    avg_score = (scores[n_status] + scores[p_status] + scores[k_status]) / 3
    
    if avg_score >= 2.5:
        overall = "High"
    elif avg_score >= 1.7:
        overall = "Medium"
    else:
        overall = "Low"
    
    return {
        "overall": overall,
        "N": n_status,
        "P": p_status,
        "K": k_status,
        "pH": ph_status
    }

def determine_soil_type(N, P, K, pH):
    """Determine soil type based on parameters"""
    if N > 70 and pH < 7.0:
        return "Clayey Loam"
    elif N > 70:
        return "Alluvial"
    elif K > 55:
        return "Black Cotton"
    elif pH > 7.5:
        return "Sandy"
    elif pH < 6.0:
        return "Red Loamy"
    else:
        return "Loamy"

# ============================================================
# NEW: LOCATION-BASED DEFAULT VALUES (NO DATABASE)
# ============================================================

@app.route('/')
def home():
    return render_template("index3.html")

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'GET':
        return render_template("prediction3.html")
    
    try:
        # Get form data
        N = float(request.form['N'])
        P = float(request.form['P'])
        K = float(request.form['K'])
        temp = float(request.form['temperature'])
        hum = float(request.form['humidity'])
        ph = float(request.form['pH'])
        rain = float(request.form['rainfall'])
        district = request.form.get('district', 'Tamil Nadu')

        validation_errors = []
        if not 0 <= N <= 140: validation_errors.append("N must be in range 0-140")
        if not 0 <= P <= 145: validation_errors.append("P must be in range 0-145")
        if not 0 <= K <= 210: validation_errors.append("K must be in range 0-210")
        if not 8 <= temp <= 45: validation_errors.append("Temperature must be in range 8-45°C")
        if not 20 <= hum <= 100: validation_errors.append("Humidity must be in range 20-100%")
        if not 3.5 <= ph <= 10: validation_errors.append("pH must be in range 3.5-10")
        if not 20 <= rain <= 500: validation_errors.append("Rainfall must be in range 20-500 mm")
        if validation_errors:
            return render_template("prediction3.html", error="; ".join(validation_errors))

        print(f"\n🌾 XGBoost Prediction: N={N}, P={P}, K={K}, T={temp}, H={hum}, pH={ph}, R={rain}")

        # Check if model is loaded
        if model is None or label_encoder is None:
            print("❌ Model not loaded!")
            return render_template("prediction3.html", 
                error="Model files not found. Please ensure xgboost_crop_classifier.joblib and label_encoder_crop.joblib are in the project folder.")

        # Prepare input for XGBoost
        features = np.array([[N, P, K, temp, hum, ph, rain]])

        # Get probabilities
        try:
            probabilities = model.predict_proba(features)[0]
            all_crops = label_encoder.classes_
            
            # Sort by confidence
            crop_ranking = sorted(zip(all_crops, probabilities * 100), 
                                key=lambda x: x[1], reverse=True)
            
            # Get TOP 3 with PROPER TYPE CONVERSION
            top_3 = []
            for i in range(min(3, len(crop_ranking))):
                conf_value = float(crop_ranking[i][1])
                top_3.append({
                    'rank': int(i + 1),
                    'name': str(crop_ranking[i][0]).capitalize(),
                    'confidence': round(conf_value, 1),
                    'suitability': 'Excellent' if conf_value > 80 else 
                                 ('Very Good' if conf_value > 60 else 'Good')
                })
            
            print(f"✅ Top 3: {top_3[0]['name']} ({top_3[0]['confidence']}%), "
                  f"{top_3[1]['name']} ({top_3[1]['confidence']}%), "
                  f"{top_3[2]['name']} ({top_3[2]['confidence']}%)")
            
        except Exception as model_error:
            print(f"⚠️ Model prediction error: {model_error}")
            return render_template("prediction3.html", 
                error=f"Prediction failed: {str(model_error)}")

        season = get_tamil_season()
        fertility = analyze_soil_fertility(N, P, K, ph)
        soil_type = determine_soil_type(N, P, K, ph)

        return render_template("Result.html", 
                             top_crops=top_3,
                             season=season,
                             district=str(district),
                             N=float(N), 
                             P=float(P), 
                             K=float(K), 
                             temperature=float(temp), 
                             humidity=float(hum), 
                             pH=float(ph), 
                             rainfall=float(rain),
                             soil_type=str(soil_type),
                             fertility=fertility)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return render_template("prediction3.html", 
            error="Please ensure all values are entered correctly.")

@app.route('/get-soil-data', methods=['POST'])
def get_soil_data():
    """
    NEW IMPLEMENTATION: Direct API + Regional defaults
    NO DATABASE NEEDED!
    """
    try:
        data = request.get_json()
        lat = float(data['latitude'])
        lon = float(data['longitude'])
        
        print(f"\n📍 Location request: {lat:.4f}, {lon:.4f}")
        
        # Validate India coordinates (roughly)
        if not (6.0 <= lat <= 38.0 and 68.0 <= lon <= 98.0):
            print("⚠️ Location outside India")
            return jsonify({
                'success': False, 
                'message': 'Please use a location within India'
            })
        
        # Get location name
        location_info = location_service.get_location_name(lat, lon)
        
        if location_info:
            district = location_info.get('district', 'Unknown')
            state = location_info.get('state', 'India')
            city = location_info.get('city', '')
            location_name = f"{city}, {district}" if city else district
            print(f"📌 Location: {location_name}, {state}")
        else:
            district = "Unknown"
            state = "India"
            location_name = "Unknown Location"
            print("⚠️ Could not get location name")
        
        # Get REAL-TIME weather
        print("🌤️ Fetching real-time weather...")
        weather_data = location_service.get_weather_data(lat, lon)
        
        if not weather_data:
            print("⚠️ Weather API failed, using defaults")
            weather_data = {
                'temperature': 28.0,
                'humidity': 75.0,
                'rainfall': 100.0
            }
        else:
            print(f"✅ Weather: {weather_data['temperature']}°C, "
                  f"{weather_data['humidity']}%, {weather_data['rainfall']}mm")
        
        # District-level defaults for all Tamil Nadu districts
        soil_defaults = get_nearest_district_profile(lat, lon)
        print(f"✅ Nearest district profile: {soil_defaults['district']} ({soil_defaults['distance_km']} km)")
        
        return jsonify({
            'success': True,
            'district': f"{soil_defaults['district']}, Tamil Nadu",
            'N': float(soil_defaults['N']),
            'P': float(soil_defaults['P']),
            'K': float(soil_defaults['K']),
            'pH': float(soil_defaults['pH']),
            'temperature': float(weather_data.get('temperature') or 28.0),
            'humidity': float(weather_data.get('humidity') or 75.0),
            'rainfall': float(weather_data.get('rainfall') or 100.0),
            'soil_type': soil_defaults['soil_type'],
            'message': f"✅ Real-time weather + district defaults from {soil_defaults['district']}"
        })
    
    except Exception as e:
        print(f"❌ Server Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False, 
            'message': f'Error: {str(e)}'
        })

@app.route('/download-report', methods=['POST'])
def download_report():
    """Generate PDF report"""
    try:
        data = request.get_json()
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                              topMargin=0.5*inch, bottomMargin=0.5*inch)
        story = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], 
            fontSize=24, textColor=colors.HexColor('#2e7d32'), 
            spaceAfter=30, alignment=TA_CENTER, fontName='Helvetica-Bold')
        
        heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'], 
            fontSize=16, textColor=colors.HexColor('#1b5e20'), 
            spaceAfter=12, spaceBefore=12, fontName='Helvetica-Bold')
        
        story.append(Paragraph("🌾 SoilSense Crop Recommendation Report", title_style))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(
            f"<b>Generated:</b> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", 
            styles['Normal']))
        story.append(Paragraph(
            f"<b>Location:</b> {data.get('district', 'India')}", 
            styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Top 3 Crops
        story.append(Paragraph("Top 3 Recommended Crops", heading_style))
        crop_data = [['Rank', 'Crop', 'Confidence', 'Suitability']]
        for crop in data.get('top_crops', []):
            crop_data.append([
                f"#{crop.get('rank', '')}",
                crop.get('name', ''),
                f"{crop.get('confidence', 0)}%",
                crop.get('suitability', '')
            ])
        
        crop_table = Table(crop_data, colWidths=[0.8*inch, 2.5*inch, 1.5*inch, 1.5*inch])
        crop_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e7d32')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(crop_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Soil Analysis
        story.append(Paragraph("Soil Analysis Report", heading_style))
        soil_data = [
            ['Parameter', 'Value', 'Status'],
            ['Nitrogen (N)', f"{data.get('N', 0)} mg/kg", 
             data.get('fertility', {}).get('N', 'Medium')],
            ['Phosphorus (P)', f"{data.get('P', 0)} mg/kg", 
             data.get('fertility', {}).get('P', 'Medium')],
            ['Potassium (K)', f"{data.get('K', 0)} mg/kg", 
             data.get('fertility', {}).get('K', 'Medium')],
            ['pH Level', str(data.get('pH', 0)), 
             data.get('fertility', {}).get('pH', 'Neutral')],
            ['Soil Type', data.get('soil_type', 'Loamy'), ''],
            ['Overall Fertility', 
             data.get('fertility', {}).get('overall', 'Medium'), '']
        ]
        
        soil_table = Table(soil_data, colWidths=[2*inch, 2*inch, 2*inch])
        soil_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1b5e20')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(soil_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Climate
        story.append(Paragraph("Climate Conditions", heading_style))
        climate_data = [
            ['Parameter', 'Value'],
            ['Temperature', f"{data.get('temperature', 0)}°C"],
            ['Humidity', f"{data.get('humidity', 0)}%"],
            ['Rainfall', f"{data.get('rainfall', 0)} mm"],
            ['Current Season', data.get('season', {}).get('name', '')],
            ['Season Description', data.get('season', {}).get('desc', '')]
        ]
        
        climate_table = Table(climate_data, colWidths=[2.5*inch, 3.5*inch])
        climate_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d47a1')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(climate_table)
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph("_" * 80, styles['Normal']))
        story.append(Paragraph(
            "<b>SoilSense</b> - ML-Powered Crop Recommendation System", 
            ParagraphStyle('Footer', parent=styles['Normal'], 
                         alignment=TA_CENTER, textColor=colors.grey)))
        
        doc.build(story)
        buffer.seek(0)
        
        return send_file(buffer, as_attachment=True, 
            download_name=f'crop_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
            mimetype='application/pdf')
    
    except Exception as e:
        print(f"❌ PDF Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🌾 SOILSENSE - ML CROP RECOMMENDATION")
    print("="*60)
    
    if model is not None:
        print(f"✅ XGBoost model loaded")
        print(f"✅ Can predict {len(label_encoder.classes_)} different crops")
    else:
        print("❌ Model NOT loaded - predictions will fail!")
        print("   Please ensure these files exist:")
        print("   - xgboost_crop_classifier.joblib")
        print("   - label_encoder_crop.joblib")
    
    print("✅ Real-time weather integration (Open-Meteo)")
    print("✅ District-wise Tamil Nadu soil defaults (39 districts)")
    print("✅ No database required!")
    print("✅ Top 3 crop recommendations")
    print("✅ Soil fertility analysis")
    print("✅ PDF report generation")
    print("="*60 + "\n")
    
    print("🚀 Starting Flask server...")
    print("📍 Visit: http://localhost:5000\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)