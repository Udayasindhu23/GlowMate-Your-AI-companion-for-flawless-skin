import cv2
import numpy as np

def detect_face(image_path):
    """
    Detect face in the image using OpenCV's Haar Cascade or DNN face detector
    Returns: (face_detected: bool, face_image: numpy array)
    """
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        return False, None
    
    # Convert to grayscale for face detection
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Load face cascade classifier
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    # Detect faces
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(100, 100)
    )
    
    if len(faces) == 0:
        # Try DNN face detector as fallback
        return detect_face_dnn(image_path)
    
    # Get the largest face (assuming it's the main subject)
    largest_face = max(faces, key=lambda rect: rect[2] * rect[3])
    x, y, w, h = largest_face
    
    # Extract face region with some padding
    padding = 20
    x = max(0, x - padding)
    y = max(0, y - padding)
    w = min(image.shape[1] - x, w + 2 * padding)
    h = min(image.shape[0] - y, h + 2 * padding)
    
    face_image = image[y:y+h, x:x+w]
    
    return True, face_image

def detect_face_dnn(image_path):
    """
    Detect face using DNN face detector (more accurate but slower)
    """
    try:
        # Load DNN model files (you may need to download these)
        prototxt_path = "models/deploy.prototxt"
        model_path = "models/res10_300x300_ssd_iter_140000.caffemodel"
        
        # Try to load DNN model
        net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)
        
        image = cv2.imread(image_path)
        if image is None:
            return False, None
        
        (h, w) = image.shape[:2]
        
        # Create blob from image
        blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
        
        # Pass blob through network
        net.setInput(blob)
        detections = net.forward()
        
        # Find the face with highest confidence
        max_confidence = 0
        best_face = None
        
        for i in range(0, detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            
            if confidence > 0.5 and confidence > max_confidence:
                max_confidence = confidence
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (x, y, x1, y1) = box.astype("int")
                
                # Ensure coordinates are within image bounds
                x = max(0, x)
                y = max(0, y)
                x1 = min(w, x1)
                y1 = min(h, y1)
                
                best_face = (x, y, x1 - x, y1 - y)
        
        if best_face:
            x, y, w, h = best_face
            padding = 20
            x = max(0, x - padding)
            y = max(0, y - padding)
            w = min(image.shape[1] - x, w + 2 * padding)
            h = min(image.shape[0] - y, h + 2 * padding)
            
            face_image = image[y:y+h, x:x+w]
            return True, face_image
        
        return False, None
    
    except:
        # If DNN fails, return False
        return False, None

