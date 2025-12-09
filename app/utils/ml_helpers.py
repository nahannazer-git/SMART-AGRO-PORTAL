# ML Helper Functions for AI Predictions
import json
from app.ml.prediction import predict_disease as ml_predict_disease, predict_yield as ml_predict_yield

def predict_disease(image_path, symptoms, crop_type):
    """
    AI disease prediction function using trained ML model.
    Falls back to mock prediction if model not available.
    
    Args:
        image_path: Image path (not used in dropdown-based model, kept for compatibility)
        symptoms: List of symptoms (dropdown selections)
        crop_type: Crop type (dropdown selection)
    
    Returns:
        JSON string with prediction results
    """
    # Convert symptoms to list if it's a string
    if isinstance(symptoms, str):
        try:
            symptoms = json.loads(symptoms)
        except:
            symptoms = [symptoms] if symptoms else []
    elif not isinstance(symptoms, list):
        symptoms = [symptoms] if symptoms else []
    
    # Use ML model for prediction
    try:
        result = ml_predict_disease(
            crop_type=crop_type,
            symptoms=symptoms,
            location=None,  # Can be added from form
            season=None     # Can be added from form
        )
        
        prediction = {
            'disease_name': result['disease_name'],
            'confidence': result['confidence'],
            'severity': 'High' if result['confidence'] > 0.9 else 'Medium' if result['confidence'] > 0.75 else 'Low',
            'recommendations': result['recommended_actions'],
            'treatment_options': result['recommended_actions'][:3] if len(result['recommended_actions']) >= 3 else result['recommended_actions']
        }
    except Exception as e:
        # Fallback to mock if ML model fails
        from app.ml.prediction import _mock_disease_prediction
        result = _mock_disease_prediction(crop_type, symptoms)
        prediction = {
            'disease_name': result['disease_name'],
            'confidence': result['confidence'],
            'severity': 'Medium',
            'recommendations': result['recommended_actions'],
            'treatment_options': result['recommended_actions']
        }
    
    return json.dumps(prediction)

def predict_yield(crop_type, soil_type, irrigation_type, fertilizer_type, 
                  temperature, rainfall, farm_size, location):
    """
    AI yield prediction function using trained ML model.
    Falls back to mock prediction if model not available.
    
    Args:
        crop_type: Crop type (dropdown)
        soil_type: Soil type (dropdown)
        irrigation_type: Irrigation type (dropdown)
        fertilizer_type: Fertilizer type (dropdown)
        temperature: Temperature value
        rainfall: Rainfall value
        farm_size: Farm size in acres
        location: Location (optional dropdown)
    
    Returns:
        Dictionary with prediction results
    """
    # Use ML model for prediction
    try:
        result = ml_predict_yield(
            crop_type=crop_type,
            soil_type=soil_type,
            irrigation_type=irrigation_type,
            fertilizer_type=fertilizer_type,
            temperature=temperature,
            rainfall=rainfall,
            farm_size=farm_size,
            location=location,
            season=None  # Can be added from form
        )
        
        prediction = {
            'predicted_yield_per_acre': result['yield_per_acre'],
            'total_predicted_yield': result['total_yield'],
            'confidence_score': result['confidence_score'],
            'unit': 'tons',
            'factors_considered': {
                'crop_type': crop_type,
                'soil_type': soil_type,
                'irrigation': irrigation_type,
                'fertilizer': fertilizer_type,
                'temperature': temperature,
                'rainfall': rainfall
            },
            'recommendations': [
                f'Expected yield: {result["total_yield"]} tons for {farm_size} acres',
                'Ensure proper irrigation management',
                'Monitor soil nutrients regularly',
                'Follow recommended crop protection measures'
            ]
        }
    except Exception as e:
        # Fallback to mock if ML model fails
        from app.ml.prediction import _mock_yield_prediction
        result = _mock_yield_prediction(
            crop_type, soil_type, irrigation_type, fertilizer_type,
            temperature, rainfall, farm_size
        )
        prediction = {
            'predicted_yield_per_acre': result['yield_per_acre'],
            'total_predicted_yield': result['total_yield'],
            'confidence_score': result['confidence_score'],
            'unit': 'tons',
            'factors_considered': {
                'crop_type': crop_type,
                'soil_type': soil_type,
                'irrigation': irrigation_type,
                'fertilizer': fertilizer_type,
                'temperature': temperature,
                'rainfall': rainfall
            },
            'recommendations': [
                f'Expected yield: {result["total_yield"]} tons for {farm_size} acres',
                'Ensure proper irrigation management',
                'Monitor soil nutrients regularly',
                'Follow recommended crop protection measures'
            ]
        }
    
    return prediction

