import os
import cv2
import numpy as np
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ASTRA.Vision")

MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(MODEL_DIR, "face_model.yml")
CASCADE_PATH = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'

def register_user(name="Sanjeev", sample_count=30):
    """
    Captures face samples from the webcam, trains the LBPH recognizer,
    and saves the trained model to face_model.yml.
    """
    logger.info(f"Starting face registration for {name}...")
    face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
    
    # Check if cascade file is loaded correctly
    if face_cascade.empty():
        logger.error("Failed to load Haar Cascade XML file.")
        return False
        
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logger.error("Webcam could not be opened. Registration aborted.")
        return False
        
    print("\n--- ASTRA Face Registration ---")
    print("Please look at the camera. Capturing face samples...")
    
    faces = []
    labels = []
    count = 0
    
    while count < sample_count:
        ret, frame = cap.read()
        if not ret:
            logger.warning("Failed to grab frame from webcam.")
            continue
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        detected_faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        for (x, y, w, h) in detected_faces:
            face_roi = gray[y:y+h, x:x+w]
            face_roi_resized = cv2.resize(face_roi, (200, 200))
            faces.append(face_roi_resized)
            labels.append(1) # Label 1 for Sanjeev
            count += 1
            
            # Draw rectangle on frame and show progress
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, f"Captured: {count}/{sample_count}", (x, y-10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
        cv2.imshow("ASTRA Face Registration", frame)
        
        # Break on 'q' key or Esc
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()
    
    if len(faces) < 10:
        logger.error("Not enough face samples captured. Training failed.")
        return False
        
    try:
        # Create LBPH face recognizer
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.train(faces, np.array(labels))
        recognizer.save(MODEL_PATH)
        logger.info(f"Face registration complete. Model saved at {MODEL_PATH}")
        print(f"Success: Registered face for {name}!")
        return True
    except AttributeError:
        logger.error("LBPHFaceRecognizer is not available. Please install opencv-contrib-python.")
        return False
    except Exception as e:
        logger.error(f"Error during training: {str(e)}")
        return False

def verify_user(timeout_seconds=5, required_confidence=105):
    """
    Opens the webcam and checks if the authorized user ('Sanjeev') is present.
    Returns (True, name) if verified, (False, 'Unknown') otherwise.
    """
    if not os.path.exists(MODEL_PATH):
        logger.warning(f"Face model file {MODEL_PATH} not found. Face verification skipped.")
        return False, "Model Missing"
        
    face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
    if face_cascade.empty():
        logger.error("Failed to load Haar Cascade XML file.")
        return False, "Cascade Missing"
        
    try:
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.read(MODEL_PATH)
    except AttributeError:
        logger.error("LBPHFaceRecognizer is not available.")
        return False, "Recognizer Missing"
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        return False, "Model Error"

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logger.error("Webcam could not be opened for verification.")
        return False, "Camera Error"

    import time
    start_time = time.time()
    verified = False
    user_name = "Unknown"
    
    logger.info("Starting face verification...")
    
    while time.time() - start_time < timeout_seconds:
        ret, frame = cap.read()
        if not ret:
            continue
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        detected_faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        for (x, y, w, h) in detected_faces:
            face_roi = gray[y:y+h, x:x+w]
            face_roi_resized = cv2.resize(face_roi, (200, 200))
            
            label, confidence = recognizer.predict(face_roi_resized)
            
            # LBPH confidence is a distance. Lower values mean higher match/confidence.
            logger.info(f"Predicted label: {label}, confidence/distance: {confidence:.2f}")
            
            if label == 1 and confidence < required_confidence:
                verified = True
                user_name = "Sanjeev"
                
                # Draw feedback
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, f"Verified: {user_name}", (x, y-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                break
            else:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                cv2.putText(frame, "Unknown Person", (x, y-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                            
        cv2.imshow("ASTRA Face Verification", frame)
        if cv2.waitKey(1) & 0xFF == ord('q') or verified:
            break
            
    cap.release()
    cv2.destroyAllWindows()
    return verified, user_name

if __name__ == "__main__":
    # If run directly, offer face registration
    print("ASTRA Face Recognition Utility")
    print("1. Register Face")
    print("2. Test Verification")
    choice = input("Enter choice: ")
    if choice == "1":
        register_user()
    elif choice == "2":
        verified, user = verify_user()
        print(f"Verified: {verified}, User: {user}")
