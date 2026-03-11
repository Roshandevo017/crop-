import csv
import random
from tamilnadu_district_profiles import DISTRICT_PROFILES

random.seed(42)

# Crop ranges are inspired by common crop recommendation datasets, then adapted by district soil profile.
CROP_PROFILES = {
    "rice":        {"N": (70, 99), "P": (35, 55), "K": (30, 50), "temp": (20, 32), "hum": (75, 92), "ph": (5.5, 7.2), "rain": (180, 320)},
    "maize":       {"N": (60, 95), "P": (35, 60), "K": (20, 45), "temp": (18, 33), "hum": (50, 75), "ph": (5.8, 7.8), "rain": (60, 140)},
    "cotton":      {"N": (45, 80), "P": (35, 60), "K": (40, 70), "temp": (23, 36), "hum": (45, 70), "ph": (6.0, 8.0), "rain": (55, 140)},
    "sugarcane":   {"N": (80, 120), "P": (35, 60), "K": (40, 70), "temp": (21, 35), "hum": (65, 85), "ph": (6.0, 7.8), "rain": (110, 240)},
    "groundnut":   {"N": (20, 55), "P": (35, 70), "K": (20, 50), "temp": (21, 34), "hum": (50, 75), "ph": (6.0, 8.0), "rain": (45, 110)},
    "banana":      {"N": (85, 120), "P": (45, 70), "K": (45, 85), "temp": (21, 35), "hum": (65, 92), "ph": (5.5, 7.5), "rain": (120, 280)},
    "millets":     {"N": (30, 65), "P": (20, 45), "K": (25, 55), "temp": (20, 36), "hum": (35, 65), "ph": (5.8, 8.2), "rain": (35, 95)},
    "pulses":      {"N": (20, 55), "P": (30, 60), "K": (20, 45), "temp": (18, 34), "hum": (40, 70), "ph": (6.0, 8.2), "rain": (35, 110)},
    "coconut":     {"N": (45, 80), "P": (30, 55), "K": (70, 110), "temp": (23, 35), "hum": (68, 92), "ph": (5.2, 7.5), "rain": (140, 320)},
    "coffee":      {"N": (35, 65), "P": (35, 65), "K": (45, 80), "temp": (15, 28), "hum": (65, 90), "ph": (5.0, 6.8), "rain": (130, 300)},
}

DISTRICT_CROP_WEIGHTS = {
    "Thanjavur": [("rice", 0.45), ("banana", 0.20), ("sugarcane", 0.20), ("pulses", 0.15)],
    "Thiruvarur": [("rice", 0.55), ("banana", 0.20), ("sugarcane", 0.15), ("pulses", 0.10)],
    "Nagapattinam": [("rice", 0.50), ("coconut", 0.20), ("banana", 0.15), ("pulses", 0.15)],
    "Kanyakumari": [("coconut", 0.40), ("banana", 0.25), ("rice", 0.20), ("pulses", 0.15)],
    "Nilgiris": [("coffee", 0.45), ("maize", 0.20), ("pulses", 0.20), ("millets", 0.15)],
    "Coimbatore": [("cotton", 0.35), ("maize", 0.25), ("groundnut", 0.20), ("millets", 0.20)],
    "Tiruppur": [("cotton", 0.40), ("maize", 0.25), ("groundnut", 0.20), ("millets", 0.15)],
    "Erode": [("cotton", 0.35), ("banana", 0.20), ("maize", 0.25), ("pulses", 0.20)],
    "Madurai": [("cotton", 0.30), ("millets", 0.25), ("pulses", 0.25), ("maize", 0.20)],
    "Tirunelveli": [("rice", 0.25), ("pulses", 0.30), ("millets", 0.25), ("cotton", 0.20)],
}

SEASONS = [
    ("kuruvai", 0.22),
    ("samba", 0.36),
    ("navarai", 0.18),
    ("sornavari", 0.12),
    ("thaladi", 0.12),
]

SEASON_FACTORS = {
    "kuruvai":   {"temp": 1.01, "hum": 1.00, "rain": 0.95},
    "samba":     {"temp": 0.99, "hum": 1.05, "rain": 1.20},
    "navarai":   {"temp": 1.04, "hum": 0.95, "rain": 0.70},
    "sornavari": {"temp": 1.05, "hum": 0.92, "rain": 0.65},
    "thaladi":   {"temp": 1.00, "hum": 1.02, "rain": 1.05},
}


def choose_weighted(items):
    labels = [x[0] for x in items]
    weights = [x[1] for x in items]
    return random.choices(labels, weights=weights, k=1)[0]


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def sample_feature(r):
    return random.uniform(r[0], r[1])


def generate_row(district_profile):
    district = district_profile["district"]

    crop_options = DISTRICT_CROP_WEIGHTS.get(
        district,
        [("rice", 0.20), ("maize", 0.15), ("cotton", 0.15), ("pulses", 0.15), ("millets", 0.15), ("groundnut", 0.10), ("sugarcane", 0.10)],
    )
    label = choose_weighted(crop_options)
    season = choose_weighted(SEASONS)
    factors = SEASON_FACTORS[season]
    base = CROP_PROFILES[label]

    # crop range + district center pull + season shift + gaussian noise
    N = sample_feature(base["N"]) * 0.75 + district_profile["N"] * 0.25 + random.gauss(0, 3)
    P = sample_feature(base["P"]) * 0.75 + district_profile["P"] * 0.25 + random.gauss(0, 2.2)
    K = sample_feature(base["K"]) * 0.75 + district_profile["K"] * 0.25 + random.gauss(0, 2.5)
    ph = sample_feature(base["ph"]) * 0.70 + district_profile["pH"] * 0.30 + random.gauss(0, 0.08)

    temperature = sample_feature(base["temp"]) * factors["temp"] + random.gauss(0, 0.6)
    humidity = sample_feature(base["hum"]) * factors["hum"] + random.gauss(0, 1.2)
    rainfall = sample_feature(base["rain"]) * factors["rain"] + random.gauss(0, 5)

    return {
        "N": round(clamp(N, 0, 140), 2),
        "P": round(clamp(P, 0, 145), 2),
        "K": round(clamp(K, 0, 210), 2),
        "temperature": round(clamp(temperature, 8, 45), 2),
        "humidity": round(clamp(humidity, 20, 100), 2),
        "ph": round(clamp(ph, 3.5, 10), 2),
        "rainfall": round(clamp(rainfall, 20, 500), 2),
        "label": label,
    }


def build_dataset(total_rows=3500, output_file="tamilnadu_crop_dataset_3500.csv"):
    rows = []
    while len(rows) < total_rows:
        for profile in DISTRICT_PROFILES:
            rows.append(generate_row(profile))
            if len(rows) >= total_rows:
                break

    headers = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall", "label"]
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Generated {len(rows)} rows: {output_file}")


if __name__ == "__main__":
    build_dataset()
