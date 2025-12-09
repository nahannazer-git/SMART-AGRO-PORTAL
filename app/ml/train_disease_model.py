"""
Disease Prediction Model Training Script
Classification model that accepts dropdown-based categorical inputs
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, MultiLabelBinarizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib
import os
from pathlib import Path

# Define categorical features (dropdown values)
CROP_TYPES = ['Rice', 'Wheat', 'Corn', 'Tomato', 'Potato', 'Cotton', 'Sugarcane']
SYMPTOMS = [
    'Yellowing leaves', 'Brown spots', 'Wilting', 'Stunted growth',
    'Leaf curling', 'White powdery substance', 'Black spots',
    'Holes in leaves', 'Discolored stems', 'Root rot', 'Fruit drop',
    'Flower drop', 'Mosaic pattern', 'Necrosis', 'Chlorosis'
]
LOCATIONS = ['Kerala', 'Tamil Nadu', 'Karnataka', 'Andhra Pradesh', 'Maharashtra', 'Punjab', 'Haryana']
SEASONS = ['Kharif', 'Rabi', 'Summer', 'Monsoon']

# Disease labels
DISEASES = {
    'Rice': ['Blast', 'Brown Spot', 'Sheath Blight', 'Bacterial Leaf Blight', 'Tungro'],
    'Wheat': ['Rust', 'Powdery Mildew', 'Fusarium Head Blight', 'Leaf Blight'],
    'Corn': ['Northern Corn Leaf Blight', 'Common Rust', 'Gray Leaf Spot', 'Ear Rot'],
    'Tomato': ['Early Blight', 'Late Blight', 'Bacterial Spot', 'Septoria Leaf Spot', 'Fusarium Wilt'],
    'Potato': ['Late Blight', 'Early Blight', 'Blackleg', 'Bacterial Wilt'],
    'Cotton': ['Boll Rot', 'Leaf Curl', 'Bacterial Blight', 'Fusarium Wilt'],
    'Sugarcane': ['Red Rot', 'Smut', 'Ratoon Stunting', 'Leaf Scald']
}

# Recommended actions for each disease
DISEASE_ACTIONS = {
    'Blast': ['Apply Tricyclazole fungicide', 'Ensure proper drainage', 'Use resistant varieties'],
    'Brown Spot': ['Apply Mancozeb', 'Improve soil fertility', 'Remove infected plants'],
    'Sheath Blight': ['Apply Propiconazole', 'Maintain proper spacing', 'Avoid excess nitrogen'],
    'Bacterial Leaf Blight': ['Apply Copper-based bactericide', 'Use disease-free seeds', 'Practice crop rotation'],
    'Tungro': ['Control leafhoppers', 'Use resistant varieties', 'Remove infected plants'],
    'Rust': ['Apply Propiconazole', 'Use resistant varieties', 'Practice crop rotation'],
    'Powdery Mildew': ['Apply Sulfur-based fungicide', 'Improve air circulation', 'Reduce humidity'],
    'Fusarium Head Blight': ['Apply Tebuconazole', 'Use resistant varieties', 'Avoid planting in infected fields'],
    'Leaf Blight': ['Apply Mancozeb', 'Practice crop rotation', 'Remove crop debris'],
    'Northern Corn Leaf Blight': ['Apply Azoxystrobin', 'Use resistant hybrids', 'Practice crop rotation'],
    'Common Rust': ['Apply Propiconazole', 'Use resistant varieties', 'Early planting'],
    'Gray Leaf Spot': ['Apply Azoxystrobin', 'Practice crop rotation', 'Remove infected leaves'],
    'Ear Rot': ['Apply Propiconazole', 'Control insects', 'Harvest early'],
    'Early Blight': ['Apply Chlorothalonil', 'Practice crop rotation', 'Remove infected leaves'],
    'Late Blight': ['Apply Metalaxyl', 'Improve air circulation', 'Remove infected plants'],
    'Bacterial Spot': ['Apply Copper-based bactericide', 'Use disease-free seeds', 'Avoid overhead irrigation'],
    'Septoria Leaf Spot': ['Apply Mancozeb', 'Remove infected leaves', 'Improve air circulation'],
    'Fusarium Wilt': ['Use resistant varieties', 'Practice crop rotation', 'Improve soil drainage'],
    'Blackleg': ['Use certified seed', 'Practice crop rotation', 'Remove infected plants'],
    'Bacterial Wilt': ['Use resistant varieties', 'Practice crop rotation', 'Control insects'],
    'Boll Rot': ['Apply Carbendazim', 'Control insects', 'Improve air circulation'],
    'Leaf Curl': ['Control whiteflies', 'Use resistant varieties', 'Remove infected plants'],
    'Bacterial Blight': ['Apply Copper-based bactericide', 'Use disease-free seeds', 'Practice crop rotation'],
    'Red Rot': ['Use disease-free setts', 'Practice crop rotation', 'Remove infected plants'],
    'Smut': ['Use disease-free setts', 'Hot water treatment', 'Practice crop rotation'],
    'Ratoon Stunting': ['Use disease-free setts', 'Practice crop rotation', 'Remove infected plants'],
    'Leaf Scald': ['Apply Copper-based fungicide', 'Use resistant varieties', 'Practice crop rotation']
}

def generate_training_data(n_samples=5000):
    """Generate synthetic training data based on categorical features"""
    np.random.seed(42)
    data = []
    
    for _ in range(n_samples):
        crop_type = np.random.choice(CROP_TYPES)
        location = np.random.choice(LOCATIONS)
        season = np.random.choice(SEASONS)
        
        # Select 2-5 random symptoms
        num_symptoms = np.random.randint(2, 6)
        selected_symptoms = np.random.choice(SYMPTOMS, size=num_symptoms, replace=False).tolist()
        
        # Determine disease based on crop type and symptoms
        possible_diseases = DISEASES.get(crop_type, ['Unknown Disease'])
        disease = np.random.choice(possible_diseases)
        
        # Create feature vector
        row = {
            'crop_type': crop_type,
            'location': location,
            'season': season,
            'symptoms': selected_symptoms,
            'disease': disease
        }
        data.append(row)
    
    return pd.DataFrame(data)

def encode_features(df):
    """Encode categorical features for model training"""
    # Encode single-value categorical features
    le_crop = LabelEncoder()
    le_location = LabelEncoder()
    le_season = LabelEncoder()
    le_disease = LabelEncoder()
    
    df['crop_type_encoded'] = le_crop.fit_transform(df['crop_type'])
    df['location_encoded'] = le_location.fit_transform(df['location'])
    df['season_encoded'] = le_season.fit_transform(df['season'])
    df['disease_encoded'] = le_disease.fit_transform(df['disease'])
    
    # Encode multi-label symptoms
    mlb = MultiLabelBinarizer()
    symptoms_encoded = mlb.fit_transform(df['symptoms'])
    symptoms_df = pd.DataFrame(symptoms_encoded, columns=mlb.classes_)
    
    # Combine all features
    X = pd.concat([
        df[['crop_type_encoded', 'location_encoded', 'season_encoded']],
        symptoms_df
    ], axis=1)
    
    y = df['disease_encoded']
    
    return X, y, {
        'crop_encoder': le_crop,
        'location_encoder': le_location,
        'season_encoder': le_season,
        'disease_encoder': le_disease,
        'symptoms_encoder': mlb
    }

def train_model():
    """Train the disease prediction model"""
    print("Generating training data...")
    df = generate_training_data(n_samples=5000)
    
    print("Encoding features...")
    X, y, encoders = encode_features(df)
    
    print("Splitting data...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print("Training Random Forest Classifier...")
    model = RandomForestClassifier(
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
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Model Accuracy: {accuracy:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=encoders['disease_encoder'].classes_))
    
    # Save model and encoders
    model_dir = Path(__file__).parent / 'models'
    model_dir.mkdir(exist_ok=True)
    
    model_path = model_dir / 'disease_model.pkl'
    encoders_path = model_dir / 'disease_encoders.pkl'
    
    joblib.dump(model, model_path)
    joblib.dump(encoders, encoders_path)
    
    print(f"\nModel saved to: {model_path}")
    print(f"Encoders saved to: {encoders_path}")
    
    return model, encoders

if __name__ == '__main__':
    train_model()

