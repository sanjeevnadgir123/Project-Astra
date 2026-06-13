import speech_recognition as sr
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ASTRA.WakeWord")

def wait_for_wake_word(wake_word="jarvis", timeout=None):
    """
    Listens continuously via the microphone until the specified wake word is detected.
    Returns True when the wake word is spoken.
    """
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    logger.info(f"Wake word listener initialized. Listening for: '{wake_word}'")
    
    try:
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
    except Exception as e:
        logger.error(f"Failed to adjust for ambient noise: {str(e)}")
        # Continue anyway
        
    while True:
        try:
            with microphone as source:
                print(f"Listening for wake word '{wake_word}'...")
                # We set a phrase time limit of 3 seconds to keep checking quickly
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=3)
                
            text = recognizer.recognize_google(audio).lower()
            logger.info(f"Heard: '{text}'")
            
            if wake_word in text:
                logger.info(f"Wake word '{wake_word}' detected successfully.")
                return True
        except sr.WaitTimeoutError:
            # Normal timeout, continue listening
            pass
        except sr.UnknownValueError:
            # Could not understand audio, continue listening
            pass
        except Exception as e:
            logger.error(f"Error in wake word detector loop: {str(e)}")
            # Avoid tight loop on constant failure (e.g. mic unplugged)
            import time
            time.sleep(2)

if __name__ == "__main__":
    print("Testing wake word detection...")
    wait_for_wake_word()
