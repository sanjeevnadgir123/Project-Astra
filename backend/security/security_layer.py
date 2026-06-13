import logging
from vision.face_recognizer import verify_user

logger = logging.getLogger("ASTRA.Security")

def confirm_sensitive_action(action_name, speak_fn, listen_fn, require_face=True):
    """
    Prompts the user for confirmation before performing a sensitive action.
    Optionally performs face verification to authenticate the user.
    
    - action_name: Description of the action (e.g., "delete the system log file")
    - speak_fn: A function to speak text to the user (e.g., speak(text))
    - listen_fn: A function to listen and return user speech (e.g., listen())
    - require_face: If True, triggers face recognition after verbal confirmation
    """
    logger.info(f"Security check initiated for action: {action_name}")
    
    # 1. Ask for verbal confirmation
    speak_fn(f"Are you sure you want to {action_name}?")
    
    # Listen for verbal response (we can retry once if they don't answer clearly)
    response = ""
    for attempt in range(2):
        try:
            print("Listening for confirmation (yes/no)...")
            response = listen_fn().lower()
            break
        except Exception:
            speak_fn("I didn't hear you clearly. Please say yes or no.")
            
    # Check if user confirmed
    confirm_words = ["yes", "confirm", "sure", "yep", "do it"]
    if not any(word in response for word in confirm_words):
        logger.info(f"Action '{action_name}' cancelled verbally by user.")
        speak_fn("Action cancelled.")
        return False
        
    # 2. If verbal confirmation is yes, perform face verification (if enabled)
    if require_face:
        speak_fn("Face verification required. Please look at your camera.")
        logger.info("Triggering face verification for security check...")
        
        verified, user_name = verify_user(timeout_seconds=5)
        
        if verified and user_name == "Sanjeev":
            logger.info("Face verified. Access granted.")
            speak_fn("User verified. Proceeding with action.")
            return True
        else:
            logger.warning(f"Face verification failed. Result: Verified={verified}, User={user_name}")
            speak_fn("Face verification failed. Access denied. Action aborted.")
            return False
            
    # If face recognition is not required, just verbal confirmation is enough
    logger.info("Verbal confirmation accepted. Proceeding.")
    return True
