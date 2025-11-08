import cv2
import numpy as np
from sklearn.cluster import KMeans

def analyze_skin(image_path, face_image):
    """
    Analyze skin conditions: acne, dark circles, oiliness, dryness, redness
    Returns: Dictionary with analysis results
    """
    if face_image is None:
        return {}
    
    # Convert to different color spaces for analysis
    hsv = cv2.cvtColor(face_image, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(face_image, cv2.COLOR_BGR2LAB)
    
    # Analyze different skin conditions
    analysis = {
        'acne_spots': detect_acne(face_image, hsv),
        'dark_circles': detect_dark_circles(face_image, lab),
        'redness': detect_redness(face_image, hsv),
        'oiliness': detect_oiliness(face_image),
        'dryness': detect_dryness(face_image),
        'uneven_tone': detect_uneven_tone(face_image, lab),
        'texture': analyze_texture(face_image)
    }
    
    return analysis

def detect_acne(image, hsv):
    """Detect acne spots using color and texture analysis"""
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Detect dark spots (potential acne)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filter small dark spots
    acne_count = 0
    total_area = 0
    
    for contour in contours:
        area = cv2.contourArea(contour)
        if 10 < area < 500:  # Filter by size
            acne_count += 1
            total_area += area
    
    # Calculate acne severity (0-100)
    image_area = image.shape[0] * image.shape[1]
    severity = min(100, (total_area / image_area) * 1000)
    
    return {
        'count': acne_count,
        'severity': round(severity, 2),
        'level': 'low' if severity < 10 else 'medium' if severity < 30 else 'high'
    }

def detect_dark_circles(image, lab):
    """Detect dark circles around eyes using LAB color space"""
    # Extract L channel (lightness)
    l_channel = lab[:, :, 0]
    
    # Focus on lower half of face (eye region approximation)
    height = image.shape[0]
    eye_region = l_channel[:height//2, :]
    
    # Calculate average lightness in eye region
    avg_lightness = np.mean(eye_region)
    
    # Detect dark regions
    dark_threshold = avg_lightness * 0.7
    dark_pixels = np.sum(eye_region < dark_threshold)
    total_pixels = eye_region.size
    
    darkness_percentage = (dark_pixels / total_pixels) * 100
    
    return {
        'severity': round(darkness_percentage, 2),
        'level': 'low' if darkness_percentage < 15 else 'medium' if darkness_percentage < 30 else 'high'
    }

def detect_redness(image, hsv):
    """Detect redness in skin using HSV color space"""
    # Red color range in HSV
    lower_red1 = np.array([0, 50, 50])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 50, 50])
    upper_red2 = np.array([180, 255, 255])
    
    # Create masks for red regions
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    red_mask = mask1 + mask2
    
    # Calculate redness percentage
    red_pixels = np.sum(red_mask > 0)
    total_pixels = image.shape[0] * image.shape[1]
    redness_percentage = (red_pixels / total_pixels) * 100
    
    return {
        'severity': round(redness_percentage, 2),
        'level': 'low' if redness_percentage < 10 else 'medium' if redness_percentage < 25 else 'high'
    }

def detect_oiliness(image):
    """Detect oily skin by analyzing skin shine/reflection"""
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Calculate variance in pixel intensities (oily skin has more variation due to shine)
    variance = np.var(gray)
    
    # Normalize variance (0-100 scale)
    # This is a simplified approach - in production, use ML model
    oiliness_score = min(100, (variance / 1000) * 100)
    
    return {
        'score': round(oiliness_score, 2),
        'level': 'low' if oiliness_score < 30 else 'medium' if oiliness_score < 60 else 'high'
    }

def detect_dryness(image):
    """Detect dry skin by analyzing texture and flakiness"""
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply Laplacian to detect edges (dry skin has more visible texture)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    variance = np.var(laplacian)
    
    # Higher variance indicates more texture (potential dryness)
    dryness_score = min(100, (variance / 500) * 100)
    
    return {
        'score': round(dryness_score, 2),
        'level': 'low' if dryness_score < 20 else 'medium' if dryness_score < 50 else 'high'
    }

def detect_uneven_tone(image, lab):
    """Detect uneven skin tone using LAB color space"""
    # Extract A and B channels (color information)
    a_channel = lab[:, :, 1]
    b_channel = lab[:, :, 2]
    
    # Calculate standard deviation (higher = more uneven)
    a_std = np.std(a_channel)
    b_std = np.std(b_channel)
    
    # Combine both channels
    unevenness_score = ((a_std + b_std) / 2) * 2
    
    return {
        'score': round(unevenness_score, 2),
        'level': 'low' if unevenness_score < 15 else 'medium' if unevenness_score < 30 else 'high'
    }

def analyze_texture(image):
    """Analyze skin texture using Local Binary Patterns (simplified)"""
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Calculate texture using gradient magnitude
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    gradient_magnitude = np.sqrt(sobelx**2 + sobely**2)
    
    texture_score = np.mean(gradient_magnitude)
    
    return {
        'score': round(texture_score, 2),
        'smoothness': 'smooth' if texture_score < 20 else 'moderate' if texture_score < 40 else 'rough'
    }

def calculate_skin_health_score(analysis):
    """
    Calculate overall skin health score (0-100)
    Higher score = better skin health
    """
    if not analysis:
        return 0
    
    base_score = 100
    
    # Deduct points for issues
    acne_penalty = min(30, analysis.get('acne_spots', {}).get('severity', 0) * 0.3)
    dark_circles_penalty = min(20, analysis.get('dark_circles', {}).get('severity', 0) * 0.2)
    redness_penalty = min(15, analysis.get('redness', {}).get('severity', 0) * 0.15)
    uneven_tone_penalty = min(15, analysis.get('uneven_tone', {}).get('score', 0) * 0.15)
    
    # Oiliness and dryness balance
    oiliness = analysis.get('oiliness', {}).get('score', 50)
    dryness = analysis.get('dryness', {}).get('score', 50)
    balance_penalty = abs(oiliness - dryness) * 0.1
    
    # Calculate final score
    health_score = base_score - acne_penalty - dark_circles_penalty - redness_penalty - uneven_tone_penalty - balance_penalty
    
    return max(0, min(100, round(health_score, 2)))

