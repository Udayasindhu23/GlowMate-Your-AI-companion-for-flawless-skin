import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

def classify_skin_type(analysis):
    """
    Classify skin type based on analysis results
    Returns: 'Dry', 'Oily', 'Combination', 'Normal', 'Sensitive'
    """
    if not analysis:
        return 'Normal'
    
    # Extract features with defaults
    oiliness_score = analysis.get('oiliness', {}).get('score', 50)
    dryness_score = analysis.get('dryness', {}).get('score', 50)
    acne_severity = analysis.get('acne_spots', {}).get('severity', 0)
    redness_severity = analysis.get('redness', {}).get('severity', 0)
    uneven_tone_score = analysis.get('uneven_tone', {}).get('score', 0)
    texture_score = analysis.get('texture', {}).get('score', 0)
    
    # Calculate differences and ratios
    oil_dry_diff = oiliness_score - dryness_score
    oil_dry_ratio = oiliness_score / max(dryness_score, 1)  # Avoid division by zero
    
    # Priority 1: Check for Sensitive Skin
    # Sensitive skin is characterized by high redness, irritation, and often uneven tone
    sensitivity_score = (redness_severity * 0.5) + (uneven_tone_score * 0.3) + (acne_severity * 0.2)
    if redness_severity > 25 or (redness_severity > 15 and uneven_tone_score > 20):
        return 'Sensitive'
    
    # Priority 2: Check for Oily Skin
    # Oily skin: high oiliness, low dryness, often with acne
    if oiliness_score > 65:
        if oil_dry_diff > 30:  # Significantly more oily than dry
            return 'Oily'
        elif oiliness_score > 70 and acne_severity > 10:
            return 'Oily'
    
    # Priority 3: Check for Dry Skin
    # Dry skin: high dryness, low oiliness, often with texture issues
    if dryness_score > 60:
        if oil_dry_diff < -25:  # Significantly more dry than oily
            return 'Dry'
        elif dryness_score > 65 and texture_score > 30:
            return 'Dry'
    
    # Priority 4: Check for Normal Skin
    # Normal skin: balanced oiliness and dryness, low issues
    if (30 <= oiliness_score <= 55 and 
        30 <= dryness_score <= 55 and 
        abs(oil_dry_diff) <= 15 and
        acne_severity < 15 and
        redness_severity < 15):
        return 'Normal'
    
    # Priority 5: Check for Combination Skin
    # Combination: moderate oiliness and dryness, or mixed characteristics
    # T-zone (forehead, nose) tends to be oily, cheeks tend to be dry/normal
    if (oiliness_score > 45 and dryness_score > 35) or \
       (40 <= oiliness_score <= 65 and 35 <= dryness_score <= 60 and abs(oil_dry_diff) < 30):
        # Additional check: if there's significant variation, it's combination
        if abs(oil_dry_diff) < 25 and (oiliness_score > 50 or dryness_score > 50):
            return 'Combination'
    
    # Fallback classification based on dominant characteristic
    if oil_dry_diff > 25:
        return 'Oily'
    elif oil_dry_diff < -25:
        return 'Dry'
    elif abs(oil_dry_diff) <= 20:
        # Balanced - check if it's normal or combination
        if oiliness_score < 50 and dryness_score < 50:
            return 'Normal'
        else:
            return 'Combination'
    else:
        # Default to combination for ambiguous cases
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
    
    # Labels based on improved rules
    y = []
    for i in range(n_samples):
        oiliness = X[i, 0]
        dryness = X[i, 1]
        acne = X[i, 2]
        redness = X[i, 3]
        oil_dry_diff = oiliness - dryness
        
        # Sensitive skin
        if redness > 25 or (redness > 15 and X[i, 0] > 20):  # uneven_tone proxy
            y.append('Sensitive')
        # Oily skin
        elif oiliness > 65 and oil_dry_diff > 30:
            y.append('Oily')
        # Dry skin
        elif dryness > 60 and oil_dry_diff < -25:
            y.append('Dry')
        # Normal skin
        elif (30 <= oiliness <= 55 and 30 <= dryness <= 55 and 
              abs(oil_dry_diff) <= 15 and acne < 15 and redness < 15):
            y.append('Normal')
        # Combination skin
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
        
        # Extract features (model uses 4 features: oiliness, dryness, acne, redness)
        features = np.array([[
            analysis.get('oiliness', {}).get('score', 50),
            analysis.get('dryness', {}).get('score', 50),
            analysis.get('acne_spots', {}).get('severity', 0),
            analysis.get('redness', {}).get('severity', 0)
        ]])
        
        prediction = model.predict(features)[0]
        return prediction
    except Exception as e:
        # Fallback to improved rule-based classification
        print(f"Model classification failed, using rule-based: {e}")
        return classify_skin_type(analysis)

