"""
Yield Prediction Model Training Script
Regression model that accepts dropdown-based categorical inputs
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib
from pathlib import Path

# Define categorical features (dropdown values)
CROP_TYPES = ['Rice', 'Wheat', 'Corn', 'Tomato', 'Potato', 'Cotton', 'Sugarcane']
SOIL_TYPES = ['Loamy', 'Clay', 'Sandy', 'Silt', 'Red Soil', 'Black Soil']
IRRIGATION_TYPES = ['Drip', 'Sprinkler', 'Flood', 'Rainfed', 'Furrow']
FERTILIZER_TYPES = ['Organic', 'Chemical', 'Mixed', 'None', 'Bio-fertilizer']
LOCATIONS = ['Kerala', 'Tamil Nadu', 'Karnataka', 'Andhra Pradesh', 'Maharashtra', 'Punjab', 'Haryana']
SEASONS = ['Kharif', 'Rabi', 'Summer', 'Monsoon']

# Base yield per acre (in tons) for different crops
BASE_YIELDS = {
    'Rice': 3.5,
    'Wheat': 2.8,
    'Corn': 4.2,
    'Tomato': 25.0,
    'Potato': 20.0,
    'Cotton': 0.5,
    'Sugarcane': 70.0
}

# Yield multipliers based on conditions
SOIL_MULTIPLIERS = {
    'Loamy': 1.15,
    'Clay': 1.05,
    'Sandy': 0.85,
    'Silt': 1.10,
    'Red Soil': 0.95,
    'Black Soil': 1.20
}

IRRIGATION_MULTIPLIERS = {
    'Drip': 1.20,
    'Sprinkler': 1.10,
    'Flood': 1.0,
    'Rainfed': 0.75,
    'Furrow': 0.95
}

FERTILIZER_MULTIPLIERS = {
    'Organic': 0.95,
    'Chemical': 1.15,
    'Mixed': 1.10,
    'None': 0.70,
    'Bio-fertilizer': 1.05
}

def generate_training_data(n_samples=5000):
    """Generate synthetic training data based on categorical features"""
    np.random.seed(42)
    data = []
    
    for _ in range(n_samples):
        crop_type = np.random.choice(CROP_TYPES)
        soil_type = np.random.choice(SOIL_TYPES)
        irrigation_type = np.random.choice(IRRIGATION_TYPES)
        fertilizer_type = np.random.choice(FERTILIZER_TYPES)
        location = np.random.choice(LOCATIONS)
        season = np.random.choice(SEASONS)
        
        # Generate realistic temperature and rainfall based on season and location
        if season == 'Monsoon':
            temperature = np.random.uniform(25, 30)
            rainfall = np.random.uniform(150, 300)
        elif season == 'Summer':
            temperature = np.random.uniform(30, 40)
            rainfall = np.random.uniform(0, 50)
        elif season == 'Kharif':
            temperature = np.random.uniform(25, 35)
            rainfall = np.random.uniform(100, 200)
        else:  # Rabi
            temperature = np.random.uniform(15, 25)
            rainfall = np.random.uniform(20, 100)
        
        farm_size = np.random.uniform(0.5, 50.0)  # acres
        
        # Calculate yield based on multipliers
        base_yield = BASE_YIELDS.get(crop_type, 3.0)
        soil_mult = SOIL_MULTIPLIERS.get(soil_type, 1.0)
        irrigation_mult = IRRIGATION_MULTIPLIERS.get(irrigation_type, 1.0)
        fertilizer_mult = FERTILIZER_MULTIPLIERS.get(fertilizer_type, 1.0)
        
        # Temperature adjustment (optimal 25-30°C)
        if 25 <= temperature <= 30:
            temp_mult = 1.0
        elif 20 <= temperature < 25 or 30 < temperature <= 35:
            temp_mult = 0.95
        else:
            temp_mult = 0.85
        
        # Rainfall adjustment (optimal 100-150mm)
        if 100 <= rainfall <= 150:
            rain_mult = 1.0
        elif 50 <= rainfall < 100 or 150 < rainfall <= 200:
            rain_mult = 0.95
        else:
            rain_mult = 0.90
        
        predicted_yield = base_yield * soil_mult * irrigation_mult * fertilizer_mult * temp_mult * rain_mult
        
        # Add some noise
        predicted_yield *= np.random.uniform(0.90, 1.10)
        
        row = {
            'crop_type': crop_type,
            'soil_type': soil_type,
            'irrigation_type': irrigation_type,
            'fertilizer_type': fertilizer_type,
            'location': location,
            'season': season,
            'temperature': temperature,
            'rainfall': rainfall,
            'farm_size': farm_size,
            'yield_per_acre': predicted_yield
        }
        data.append(row)
    
    return pd.DataFrame(data)

def encode_features(df):
    """Encode categorical features for model training"""
    le_crop = LabelEncoder()
    le_soil = LabelEncoder()
    le_irrigation = LabelEncoder()
    le_fertilizer = LabelEncoder()
    le_location = LabelEncoder()
    le_season = LabelEncoder()
    
    df['crop_type_encoded'] = le_crop.fit_transform(df['crop_type'])
    df['soil_type_encoded'] = le_soil.fit_transform(df['soil_type'])
    df['irrigation_type_encoded'] = le_irrigation.fit_transform(df['irrigation_type'])
    df['fertilizer_type_encoded'] = le_fertilizer.fit_transform(df['fertilizer_type'])
    df['location_encoded'] = le_location.fit_transform(df['location'])
    df['season_encoded'] = le_season.fit_transform(df['season'])
    
    # Combine all features
    X = df[[
        'crop_type_encoded', 'soil_type_encoded', 'irrigation_type_encoded',
        'fertilizer_type_encoded', 'location_encoded', 'season_encoded',
        'temperature', 'rainfall', 'farm_size'
    ]]
    
    y = df['yield_per_acre']
    
    return X, y, {
        'crop_encoder': le_crop,
        'soil_encoder': le_soil,
        'irrigation_encoder': le_irrigation,
        'fertilizer_encoder': le_fertilizer,
        'location_encoder': le_location,
        'season_encoder': le_season
    }

def train_model():
    """Train the yield prediction model"""
    print("Generating training data...")
    df = generate_training_data(n_samples=5000)
    
    print("Encoding features...")
    X, y, encoders = encode_features(df)
    
    print("Splitting data...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print("Training Random Forest Regressor...")
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=20,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    print("Evaluating model...")
    y_pred = model.predict(X_test)
    
    mse = mean_squared_error(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mse)
    
    print(f"R² Score: {r2:.4f}")
    print(f"RMSE: {rmse:.4f} tons/acre")
    print(f"MAE: {mae:.4f} tons/acre")
    
    # Save model and encoders
    model_dir = Path(__file__).parent / 'models'
    model_dir.mkdir(exist_ok=True)
    
    model_path = model_dir / 'yield_model.pkl'
    encoders_path = model_dir / 'yield_encoders.pkl'
    
    joblib.dump(model, model_path)
    joblib.dump(encoders, encoders_path)
    
    print(f"\nModel saved to: {model_path}")
    print(f"Encoders saved to: {encoders_path}")
    
    return model, encoders

if __name__ == '__main__':
    train_model()

