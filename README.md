# SoilSense (Tamil Nadu Crop Recommendation)

## What was fixed
- Added **district-wise defaults for 39 Tamil Nadu districts** (instead of only 4 broad regions).
- Added input validation so unrealistic values do not produce meaningless predictions.
- Fixed model loading to support both old and new model file naming.
- Fixed training script so it correctly exports both model and label encoder.

## Train your model
```bash
python XGBClassifier.py --dataset crop_recommendation.csv
```

## Real dataset sources (for 3000-4000 rows)
To build a stronger dataset, combine records from these public sources:
1. Kaggle Crop Recommendation dataset (base NPK/pH/temp/humidity/rainfall + crop label)
2. ICAR / Soil Health Card district data (Tamil Nadu NPK/pH statistics)
3. Open-Meteo historical weather (district-wise rainfall, temp, humidity)
4. India data.gov.in district agriculture statistics (crop suitability/yield)

> Recommended target: 39 districts × 80-100 records each = **3120-3900 rows**.

## Run app
```bash
python app.py
```


## Generate 3500-row Tamil Nadu dataset CSV
```bash
python generate_tn_dataset.py
```
This creates:
- `tamilnadu_crop_dataset_3500.csv` (exactly 3500 rows, ready for model training)
