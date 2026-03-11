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

app = Flask(__name__)

# Load XGBoost Model with CORRECT FILENAMES
print("🔄 Loading XGBoost ML model...")
try:
    model = joblib.load("xgboost_crop_model.joblib")  # ✅ FIXED NAME
    label_encoder = joblib.load("label_encoder.joblib")  # ✅ FIXED NAME
    print("✅ XGBoost model loaded successfully")
    print(f"✅ Model can predict {len(label_encoder.classes_)} crops")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    print("⚠️ Make sure these files exist:")
    print("   - xgboost_crop_classifier.joblib")
    print("   - label_encoder_crop.joblib")
    model, label_encoder = None, None

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

def get_location_defaults(latitude, longitude):
    """
    NEW STRATEGY: Get soil defaults based on GPS location
    Uses general Tamil Nadu averages with regional variations
    NO DATABASE NEEDED!
    """
    
    # Tamil Nadu regions based on latitude/longitude
    # Northern TN (Chennai, Tiruvallur, Vellore area)
    if latitude > 12.5:
        return {
            'N': 60,
            'P': 50,
            'K': 48,
            'pH': 7.0,
            'region': 'Northern Tamil Nadu',
            'typical_crops': 'Rice, Groundnut, Sugarcane'
        }
    
    # Western TN (Coimbatore, Erode, Nilgiris area)
    elif longitude < 77.5:
        return {
            'N': 45,
            'P': 55,
            'K': 60,
            'pH': 6.5,
            'region': 'Western Tamil Nadu',
            'typical_crops': 'Cotton, Coffee, Tea, Maize'
        }
    
    # Southern TN (Madurai, Tirunelveli area)
    elif latitude < 10.0:
        return {
            'N': 50,
            'P': 52,
            'K': 50,
            'pH': 7.2,
            'region': 'Southern Tamil Nadu',
            'typical_crops': 'Cotton, Pulses, Millets'
        }
    
    # Central/Eastern TN (Thanjavur, Trichy - Rice belt)
    else:
        return {
            'N': 75,
            'P': 45,
            'K': 42,
            'pH': 6.8,
            'region': 'Central Tamil Nadu (Rice Belt)',
            'typical_crops': 'Rice, Sugarcane, Banana'
        }

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
        
        # Get regional soil defaults (NO DATABASE)
        print("🗺️ Getting regional soil defaults...")
        soil_defaults = get_location_defaults(lat, lon)
        print(f"✅ Region: {soil_defaults['region']}")
        
        return jsonify({
            'success': True,
            'district': f"{location_name}, {state}",
            'N': float(soil_defaults['N']),
            'P': float(soil_defaults['P']),
            'K': float(soil_defaults['K']),
            'pH': float(soil_defaults['pH']),
            'temperature': float(weather_data.get('temperature') or 28.0),
            'humidity': float(weather_data.get('humidity') or 75.0),
            'rainfall': float(weather_data.get('rainfall') or 100.0),
            'message': f"✅ Real-time weather + {soil_defaults['region']} soil defaults"
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
    print("✅ Regional soil defaults (4 TN regions)")
    print("✅ No database required!")
    print("✅ Top 3 crop recommendations")
    print("✅ Soil fertility analysis")
    print("✅ PDF report generation")
    print("="*60 + "\n")
    
    print("🚀 Starting Flask server...")
    print("📍 Visit: http://localhost:5000\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)