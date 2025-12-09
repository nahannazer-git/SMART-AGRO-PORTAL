# ML Models for Smart Agriculture Support System

This directory contains machine learning models for disease prediction and yield prediction.

## Models

### 1. Disease Prediction Model (Classification)
- **File**: `train_disease_model.py`
- **Type**: Random Forest Classifier
- **Inputs**: Crop type, symptoms (multi-select), location, season (all dropdown-based)
- **Output**: Disease name, confidence score, recommended actions

### 2. Yield Prediction Model (Regression)
- **File**: `train_yield_model.py`
- **Type**: Random Forest Regressor
- **Inputs**: Crop type, soil type, irrigation type, fertilizer type, temperature, rainfall, farm size, location, season (all dropdown-based)
- **Output**: Yield per acre (tons), total yield, confidence score

## Training the Models

### Prerequisites
```bash
pip install scikit-learn pandas numpy joblib
```

### Train Disease Model
```bash
cd app/ml
python train_disease_model.py
```

This will:
- Generate synthetic training data (5000 samples)
- Train a Random Forest Classifier
- Save model to `models/disease_model.pkl`
- Save encoders to `models/disease_encoders.pkl`
- Display accuracy and classification report

### Train Yield Model
```bash
cd app/ml
python train_yield_model.py
```

This will:
- Generate synthetic training data (5000 samples)
- Train a Random Forest Regressor
- Save model to `models/yield_model.pkl`
- Save encoders to `models/yield_encoders.pkl`
- Display R² score, RMSE, and MAE

## Using the Models

### In Python Code
```python
from app.ml.prediction import predict_disease, predict_yield

# Disease prediction
result = predict_disease(
    crop_type='Rice',
    symptoms=['Yellowing leaves', 'Brown spots'],
    location='Kerala',
    season='Kharif'
)
# Returns: {'disease_name': 'Blast', 'confidence': 0.85, 'recommended_actions': [...]}

# Yield prediction
result = predict_yield(
    crop_type='Rice',
    soil_type='Loamy',
    irrigation_type='Drip',
    fertilizer_type='Chemical',
    temperature=28.5,
    rainfall=120.0,
    farm_size=5.0,
    location='Kerala',
    season='Kharif'
)
# Returns: {'yield_per_acre': 4.2, 'total_yield': 21.0, 'confidence_score': 0.88}
```

### Model Loading
```python
from app.ml.model_loader import load_disease_model, load_yield_model, check_models_exist

# Check if models exist
status = check_models_exist()
print(status)  # {'disease_model': True, 'yield_model': True}

# Load models (cached after first load)
disease_model, encoders = load_disease_model()
yield_model, encoders = load_yield_model()
```

## Model Features

### Disease Model Inputs
- **Crop Type**: Rice, Wheat, Corn, Tomato, Potato, Cotton, Sugarcane
- **Symptoms**: Multi-select from 15 common symptoms
- **Location**: 7 Indian states
- **Season**: Kharif, Rabi, Summer, Monsoon

### Yield Model Inputs
- **Crop Type**: Rice, Wheat, Corn, Tomato, Potato, Cotton, Sugarcane
- **Soil Type**: Loamy, Clay, Sandy, Silt, Red Soil, Black Soil
- **Irrigation Type**: Drip, Sprinkler, Flood, Rainfed, Furrow
- **Fertilizer Type**: Organic, Chemical, Mixed, None, Bio-fertilizer
- **Location**: 7 Indian states
- **Season**: Kharif, Rabi, Summer, Monsoon
- **Temperature**: Numeric value (°C)
- **Rainfall**: Numeric value (mm)
- **Farm Size**: Numeric value (acres)

## Model Outputs

### Disease Prediction
```json
{
    "disease_name": "Blast",
    "confidence": 0.85,
    "recommended_actions": [
        "Apply Tricyclazole fungicide",
        "Ensure proper drainage",
        "Use resistant varieties"
    ]
}
```

### Yield Prediction
```json
{
    "yield_per_acre": 4.2,
    "total_yield": 21.0,
    "confidence_score": 0.88
}
```

## Notes

- Models use synthetic data for training. Replace with real agricultural data for production.
- Models are cached in memory after first load for performance.
- Fallback mock predictions are available if models are not trained.
- All inputs are dropdown-based categorical values (no free text).

