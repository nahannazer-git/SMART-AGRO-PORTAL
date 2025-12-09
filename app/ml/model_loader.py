"""
Model Loading Helper
Loads trained models and encoders for predictions
"""
import joblib
from pathlib import Path
import os

# Model directory
MODEL_DIR = Path(__file__).parent / 'models'

# Model paths
DISEASE_MODEL_PATH = MODEL_DIR / 'disease_model.pkl'
DISEASE_ENCODERS_PATH = MODEL_DIR / 'disease_encoders.pkl'
YIELD_MODEL_PATH = MODEL_DIR / 'yield_model.pkl'
YIELD_ENCODERS_PATH = MODEL_DIR / 'yield_encoders.pkl'

# Cache for loaded models
_loaded_models = {
    'disease_model': None,
    'disease_encoders': None,
    'yield_model': None,
    'yield_encoders': None
}

def load_disease_model():
    """Load disease prediction model and encoders"""
    if _loaded_models['disease_model'] is None:
        if not DISEASE_MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Disease model not found at {DISEASE_MODEL_PATH}. "
                "Please run train_disease_model.py first."
            )
        _loaded_models['disease_model'] = joblib.load(DISEASE_MODEL_PATH)
        _loaded_models['disease_encoders'] = joblib.load(DISEASE_ENCODERS_PATH)
    
    return _loaded_models['disease_model'], _loaded_models['disease_encoders']

def load_yield_model():
    """Load yield prediction model and encoders"""
    if _loaded_models['yield_model'] is None:
        if not YIELD_MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Yield model not found at {YIELD_MODEL_PATH}. "
                "Please run train_yield_model.py first."
            )
        _loaded_models['yield_model'] = joblib.load(YIELD_MODEL_PATH)
        _loaded_models['yield_encoders'] = joblib.load(YIELD_ENCODERS_PATH)
    
    return _loaded_models['yield_model'], _loaded_models['yield_encoders']

def reload_models():
    """Force reload of all models (useful after retraining)"""
    _loaded_models['disease_model'] = None
    _loaded_models['disease_encoders'] = None
    _loaded_models['yield_model'] = None
    _loaded_models['yield_encoders'] = None

def check_models_exist():
    """Check if model files exist"""
    return {
        'disease_model': DISEASE_MODEL_PATH.exists(),
        'yield_model': YIELD_MODEL_PATH.exists()
    }

