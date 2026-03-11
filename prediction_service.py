import numpy as np

def get_suitability_level(confidence):

    if confidence >= 70:

        return "Highly Suitable"

    elif confidence >= 50:

        return "Moderately Suitable"

    else:

        return "Low Suitable"

def get_multiple_crop_recommendations(model, N, P, K, temperature, humidity, pH, rainfall, top_n=5):

    input_data = np.array([[N, P, K, temperature, humidity, pH, rainfall]])

    probabilities = model.predict_proba(input_data)[0]

    all_crops = model.classes_

    crop_confidences = list(zip(all_crops, probabilities * 100))

    crop_confidences.sort(key=lambda x: x[1], reverse=True)

    top_crops = []

    for i, (crop, confidence) in enumerate(crop_confidences[:top_n]):

        top_crops.append({

            "rank": i + 1,

            "crop": crop,

            "confidence": round(confidence, 1),

            "suitability": get_suitability_level(confidence)

        })

    return top_crops