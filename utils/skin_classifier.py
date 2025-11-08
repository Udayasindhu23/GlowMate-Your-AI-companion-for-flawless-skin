import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

def classify_skin_type(analysis):
    """
    Classify skin type based on analysis results
    Returns: 'Dry', 'Oily', 'Combination', 'Normal'
    """
    if not analysis:
        return 'Normal'
    
    # Extract features
    oiliness_score = analysis.get('oiliness', {}).get('score', 50)
    dryness_score = analysis.get('dryness', {}).get('score', 50)
    acne_severity = analysis.get('acne_spots', {}).get('severity', 0)
    redness_severity = analysis.get('redness', {}).get('severity', 0)
    
    # Rule-based classification (can be replaced with ML model)
    # Simple rule-based approach
    oil_dry_diff = oiliness_score - dryness_score
    
    if oil_dry_diff > 20 and acne_severity > 15:
        return 'Oily'
    elif oil_dry_diff < -20 and dryness_score > 40:
        return 'Dry'
    elif abs(oil_dry_diff) < 15 and oiliness_score < 40 and dryness_score < 40:
        return 'Normal'
    else:
        return 'Combination'

def train_skin_classifier():
    """
    Train a ML model for skin type classification
    This is a placeholder - in production, use real labeled data
    """
    # Generate synthetic training data (replace with real data)
    np.random.seed(42)
    n_samples = 1000
    
    # Feature matrix: [oiliness, dryness, acne_severity, redness_severity]
    X = np.random.rand(n_samples, 4) * 100
    
    # Labels based on rules
    y = []
    for i in range(n_samples):
        oil_dry_diff = X[i, 0] - X[i, 1]
        if oil_dry_diff > 20 and X[i, 2] > 15:
            y.append('Oily')
        elif oil_dry_diff < -20 and X[i, 1] > 40:
            y.append('Dry')
        elif abs(oil_dry_diff) < 15 and X[i, 0] < 40 and X[i, 1] < 40:
            y.append('Normal')
        else:
            y.append('Combination')
    
    # Train model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    # Save model
    os.makedirs('models', exist_ok=True)
    joblib.dump(model, 'models/skin_classifier.pkl')
    
    return model

def load_skin_classifier():
    """Load trained skin classifier model"""
    model_path = 'models/skin_classifier.pkl'
    
    if os.path.exists(model_path):
        return joblib.load(model_path)
    else:
        # Train and save if not exists
        return train_skin_classifier()

def classify_with_model(analysis):
    """
    Classify skin type using trained ML model
    """
    try:
        model = load_skin_classifier()
        
        # Extract features
        features = np.array([[
            analysis.get('oiliness', {}).get('score', 50),
            analysis.get('dryness', {}).get('score', 50),
            analysis.get('acne_spots', {}).get('severity', 0),
            analysis.get('redness', {}).get('severity', 0)
        ]])
        
        prediction = model.predict(features)[0]
        return prediction
    except:
        # Fallback to rule-based
        return classify_skin_type(analysis)

