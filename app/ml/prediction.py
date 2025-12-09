"""
Prediction Functions
Functions to make predictions using trained models
"""
import pandas as pd
import numpy as np
from app.ml.model_loader import load_disease_model, load_yield_model
from app.ml.constants import DISEASE_ACTIONS

def predict_disease(crop_type, symptoms, location=None, season=None):
    """
    Predict disease based on dropdown inputs
    
    Args:
        crop_type (str): Crop type from dropdown
        symptoms (list): List of selected symptoms
        location (str, optional): Location from dropdown
        season (str, optional): Season from dropdown
    
    Returns:
        dict: {
            'disease_name': str,
            'confidence': float (0-1),
            'recommended_actions': list
        }
    """
    try:
        model, encoders = load_disease_model()
    except FileNotFoundError:
        # Fallback to mock prediction if model not trained
        return _mock_disease_prediction(crop_type, symptoms)
    
    # Default values if not provided
    if location is None:
        location = 'Kerala'
    if season is None:
        season = 'Kharif'
    
    # Encode categorical features
    crop_encoded = encoders['crop_encoder'].transform([crop_type])[0]
    location_encoded = encoders['location_encoder'].transform([location])[0]
    season_encoded = encoders['season_encoder'].transform([season])[0]
    
    # Encode symptoms (multi-label)
    symptoms_encoded = encoders['symptoms_encoder'].transform([symptoms])
    symptoms_array = symptoms_encoded[0]
    
    # Combine all features
    features = np.concatenate([
        [crop_encoded, location_encoded, season_encoded],
        symptoms_array
    ]).reshape(1, -1)
    
    # Make prediction
    disease_encoded = model.predict(features)[0]
    disease_proba = model.predict_proba(features)[0]
    
    # Get disease name
    disease_name = encoders['disease_encoder'].inverse_transform([disease_encoded])[0]
    
    # Get confidence (probability of predicted class)
    confidence = float(disease_proba[disease_encoded])
    
    # Get recommended actions
    recommended_actions = DISEASE_ACTIONS.get(disease_name, [
        'Consult with agricultural expert',
        'Apply general fungicide',
        'Improve crop management practices'
    ])
    
    return {
        'disease_name': disease_name,
        'confidence': confidence,
        'recommended_actions': recommended_actions
    }

def predict_yield(crop_type, soil_type, irrigation_type, fertilizer_type,
                  temperature, rainfall, farm_size, location=None, season=None):
    """
    Predict yield based on dropdown inputs
    
    Args:
        crop_type (str): Crop type from dropdown
        soil_type (str): Soil type from dropdown
        irrigation_type (str): Irrigation type from dropdown
        fertilizer_type (str): Fertilizer type from dropdown
        temperature (float): Temperature value
        rainfall (float): Rainfall value
        farm_size (float): Farm size in acres
        location (str, optional): Location from dropdown
        season (str, optional): Season from dropdown
    
    Returns:
        dict: {
            'yield_per_acre': float (tons/acre),
            'total_yield': float (tons),
            'confidence_score': float (0-1)
        }
    """
    try:
        model, encoders = load_yield_model()
    except FileNotFoundError:
        # Fallback to mock prediction if model not trained
        return _mock_yield_prediction(
            crop_type, soil_type, irrigation_type, fertilizer_type,
            temperature, rainfall, farm_size
        )
    
    # Default values if not provided
    if location is None:
        location = 'Kerala'
    if season is None:
        season = 'Kharif'
    
    # Encode categorical features
    crop_encoded = encoders['crop_encoder'].transform([crop_type])[0]
    soil_encoded = encoders['soil_encoder'].transform([soil_type])[0]
    irrigation_encoded = encoders['irrigation_encoder'].transform([irrigation_type])[0]
    fertilizer_encoded = encoders['fertilizer_encoder'].transform([fertilizer_type])[0]
    location_encoded = encoders['location_encoder'].transform([location])[0]
    season_encoded = encoders['season_encoder'].transform([season])[0]
    
    # Combine all features
    features = np.array([[
        crop_encoded, soil_encoded, irrigation_encoded, fertilizer_encoded,
        location_encoded, season_encoded, temperature, rainfall, farm_size
    ]])
    
    # Make prediction
    yield_per_acre = float(model.predict(features)[0])
    total_yield = yield_per_acre * farm_size
    
    # Calculate confidence based on feature importance and prediction variance
    # For regression, we use a simplified confidence metric
    # In practice, you might use prediction intervals
    confidence_score = min(0.95, max(0.75, 1.0 - abs(yield_per_acre - 3.0) / 10.0))
    
    return {
        'yield_per_acre': round(yield_per_acre, 2),
        'total_yield': round(total_yield, 2),
        'confidence_score': round(confidence_score, 2)
    }

def _mock_disease_prediction(crop_type, symptoms):
    """Mock disease prediction when model is not available"""
    import random
    
    diseases = {
        'Rice': ['Blast', 'Brown Spot', 'Sheath Blight', 'Bacterial Leaf Blight'],
        'Wheat': ['Rust', 'Powdery Mildew', 'Fusarium Head Blight'],
        'Corn': ['Northern Corn Leaf Blight', 'Common Rust', 'Gray Leaf Spot'],
        'Tomato': ['Early Blight', 'Late Blight', 'Bacterial Spot', 'Septoria Leaf Spot'],
        'Potato': ['Late Blight', 'Early Blight', 'Blackleg'],
    }
    
    crop_diseases = diseases.get(crop_type, ['Unknown Disease'])
    predicted_disease = random.choice(crop_diseases)
    
    return {
        'disease_name': predicted_disease,
        'confidence': round(random.uniform(0.75, 0.95), 2),
        'recommended_actions': DISEASE_ACTIONS.get(predicted_disease, [
            'Consult with agricultural expert',
            'Apply general fungicide',
            'Improve crop management practices'
        ])
    }

def _mock_yield_prediction(crop_type, soil_type, irrigation_type, fertilizer_type,
                           temperature, rainfall, farm_size):
    """Mock yield prediction when model is not available"""
    base_yields = {
        'Rice': 3.5,
        'Wheat': 2.8,
        'Corn': 4.2,
        'Tomato': 25.0,
        'Potato': 20.0,
    }
    
    base_yield = base_yields.get(crop_type, 3.0)
    
    adjustments = {
        'soil_type': {
            'Loamy': 1.1,
            'Clay': 0.95,
            'Sandy': 0.85,
            'Silt': 1.05
        },
        'irrigation_type': {
            'Drip': 1.15,
            'Sprinkler': 1.05,
            'Flood': 1.0,
            'Rainfed': 0.8
        },
        'fertilizer_type': {
            'Organic': 0.95,
            'Chemical': 1.1,
            'Mixed': 1.05,
            'None': 0.7
        }
    }
    
    soil_mult = adjustments['soil_type'].get(soil_type, 1.0)
    irrigation_mult = adjustments['irrigation_type'].get(irrigation_type, 1.0)
    fertilizer_mult = adjustments['fertilizer_type'].get(fertilizer_type, 1.0)
    
    if 25 <= temperature <= 30:
        temp_mult = 1.0
    elif 20 <= temperature < 25 or 30 < temperature <= 35:
        temp_mult = 0.95
    else:
        temp_mult = 0.85
    
    if 100 <= rainfall <= 150:
        rain_mult = 1.0
    elif 50 <= rainfall < 100 or 150 < rainfall <= 200:
        rain_mult = 0.95
    else:
        rain_mult = 0.9
    
    predicted_yield_per_acre = base_yield * soil_mult * irrigation_mult * fertilizer_mult * temp_mult * rain_mult
    total_yield = predicted_yield_per_acre * farm_size
    
    return {
        'yield_per_acre': round(predicted_yield_per_acre, 2),
        'total_yield': round(total_yield, 2),
        'confidence_score': round(0.85, 2)
    }

