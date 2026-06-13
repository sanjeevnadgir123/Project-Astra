import sys
import os
import time
import psutil
import logging
import shutil
import speech_recognition as sr
import pyttsx3

# Add backend directory to sys.path to resolve module imports properly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.brain import brain, ask_astra
from commands.command_engine import execute_command
from voice.wake_word import wait_for_wake_word
from voice.clap_detector import wait_for_claps
from vision.face_recognizer import verify_user, register_user, MODEL_PATH
from security.security_layer import confirm_sensitive_action
from commands.file_manager import search_files, get_user_profile

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ASTRA.Orchestrator")

engine = pyttsx3.init()

def speak(text):
    print(f"\nASTRA: {text}")
    update_state(voice_status="PROCESSING", response=text, event=("ASTRA", f"ASTRA: {text}"))
    engine.say(text)
    engine.runAndWait()

def speak_non_blocking(text):
    """Speaks text in a separate thread to avoid blocking FastAPI or causing COM deadlocks."""
    import threading
    
    print(f"\nASTRA: {text}")
    update_state(voice_status="PROCESSING", response=text, event=("ASTRA", f"ASTRA: {text}"))
    
    def worker():
        try:
            import pythoncom
            import pyttsx3
            pythoncom.CoInitialize()
            local_engine = pyttsx3.init()
            local_engine.say(text)
            local_engine.runAndWait()
        except Exception as e:
            logger.error(f"Non-blocking speak failed: {str(e)}")
            
    threading.Thread(target=worker, daemon=True).start()

def listen_raw():
    """Listens to speech from the user and returns the recognized text."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.8)
        update_state(voice_status="LISTENING")
        audio = recognizer.listen(source, timeout=8, phrase_time_limit=5)
    
    text = recognizer.recognize_google(audio)
    print(f"You: {text}")
    update_state(voice_status="PROCESSING", transcript=text, event=("USER", f"You: {text}"))
    return text

def listen():
    """Wrapper that catches recognition errors and logs them."""
    try:
        return listen_raw()
    except sr.WaitTimeoutError:
        return ""
    except sr.UnknownValueError:
        return ""
    except Exception as e:
        logger.error(f"Speech recognition failed: {str(e)}")
        return ""

def update_state(voice_status=None, face_status=None, claps=None, transcript=None, response=None, event=None):
    """Helper to update global state in main.py without circular dependency."""
    try:
        from main import astra_state
        if voice_status:
            astra_state.voice_status = voice_status
        if face_status:
            astra_state.face_status = face_status
        if claps is not None:
            astra_state.two_claps_detected = claps
        if transcript:
            astra_state.last_transcript = transcript
        if response:
            astra_state.last_response = response
        if event:
            astra_state.add_event(event[0], event[1])
    except Exception as e:
        pass

def handle_file_deletion(filename):
    matches = search_files(filename)
    if not matches:
        return f"I couldn't find any file named '{filename}'."
    target_file = matches[0]
    try:
        os.remove(target_file)
        update_state(event=("SYSTEM", f"Deleted file: {os.path.basename(target_file)}"))
        return f"File '{os.path.basename(target_file)}' has been deleted successfully."
    except Exception as e:
        return f"Failed to delete file: {str(e)}"

def handle_file_move(src_query, dest_query):
    matches = search_files(src_query)
    if not matches:
        return f"Source file '{src_query}' not found."
    src_file = matches[0]
    
    user_home = get_user_profile()
    shortcuts = {
        "downloads": os.path.join(user_home, "Downloads"),
        "documents": os.path.join(user_home, "Documents"),
        "desktop": os.path.join(user_home, "Desktop")
    }
    
    dest_path = shortcuts.get(dest_query.lower().strip())
    if not dest_path:
        test_path = os.path.join(user_home, dest_query)
        if os.path.isdir(test_path):
            dest_path = test_path
        else:
            dest_path = os.path.join(user_home, "Documents")
            
    try:
        shutil.move(src_file, dest_path)
        update_state(event=("SYSTEM", f"Moved file '{os.path.basename(src_file)}' to '{os.path.basename(dest_path)}'"))
        return f"Successfully moved '{os.path.basename(src_file)}' to '{os.path.basename(dest_path)}'."
    except Exception as e:
        return f"Failed to move file: {str(e)}"

def run_system_query(command):
    """Answers real-time system metrics directly without LLM latency."""
    cmd = command.lower()
    if "cpu" in cmd:
        cpu = psutil.cpu_percent(interval=0.05)
        return f"Current CPU usage is at {cpu} percent."
        
    elif "ram" in cmd or "memory" in cmd:
        ram = psutil.virtual_memory().percent
        return f"Current memory usage is at {ram} percent."
        
    elif "disk" in cmd or "storage usage" in cmd:
        disk = psutil.disk_usage("C:\\").percent
        return f"Primary disk usage is at {disk} percent."
        
    elif "process" in cmd:
        process_count = len(list(psutil.process_iter()))
        return f"There are currently {process_count} active processes running on your system."
        
    elif "drive" in cmd:
        partitions = psutil.disk_partitions()
        drives = []
        for partition in partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                drives.append(f"Drive {partition.device} is {usage.percent} percent full.")
            except Exception:
                pass
        return " ".join(drives) if drives else "I could not retrieve drive metrics."
        
    return None

def wait_for_clap_or_wake_word(wake_word="jarvis"):
    """
    Listens for either a double-clap or the wake word 'Jarvis'.
    Returns 'CLAP' if double-clap is detected, 'WAKE_WORD' if wake-word is detected, or None.
    """
    # 1. Listen for claps for 3 seconds
    try:
        if wait_for_claps(timeout=3.0):
            return "CLAP"
    except Exception as e:
        logger.error(f"Error in clap check: {e}")
        
    # 2. Listen for wake word for 3 seconds
    try:
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=3.0, phrase_time_limit=2.5)
        text = recognizer.recognize_google(audio).lower()
        if wake_word in text:
            return "WAKE_WORD"
    except sr.WaitTimeoutError:
        pass
    except sr.UnknownValueError:
        pass
    except Exception as e:
        logger.error(f"Error in wake-word check: {e}")
        time.sleep(0.5)
        
    return None

def start_assistant():
    """Main lifecycle state machine for ASTRA."""
    update_state(voice_status="SLEEPING", event=("SYSTEM", "ASTRA Core Initialized."))
    speak("ASTRA is booting up.")
    
    while True:
        update_state(voice_status="SLEEPING", event=("SYSTEM", "Waiting for double clap or 'Jarvis' wake word..."))
        speak("ASTRA is sleeping. Say Jarvis or double clap to wake me up.")
        
        trigger = wait_for_clap_or_wake_word("jarvis")
        if not trigger:
            continue
            
        if trigger == "CLAP":
            update_state(claps=True, voice_status="ACTIVE")
            
            # Face Verification
            if not os.path.exists(MODEL_PATH):
                update_state(face_status="UNKNOWN", event=("SECURITY", "No face database found. Registering face."))
                speak("No face recognition model found. Starting face registration for Sanjeev. Please look at the camera.")
                success = register_user("Sanjeev")
                if not success:
                    speak("Face registration failed. Running ASTRA in standard mode.")
                    # Fallthrough
                else:
                    speak("Face registration successful. Welcome Sanjeev. Jarvis is activated.")
            else:
                update_state(face_status="VERIFYING", event=("SECURITY", "Face verification requested."))
                speak("Clap detected. Verifying your face.")
                verified, user_name = verify_user(timeout_seconds=5)
                if verified and user_name == "Sanjeev":
                    update_state(face_status="VERIFIED", event=("SECURITY", "Access granted. Face verified: Sanjeev."))
                    speak("Welcome Sanjeev. Jarvis is activated.")
                else:
                    update_state(face_status="LOCKDOWN", event=("SECURITY", "Access denied. Face verification failed."))
                    speak("Unknown user detected. Security lockdown active.")
                    time.sleep(2)
                    continue # Go back to waiting loop

        elif trigger == "WAKE_WORD":
            update_state(voice_status="ACTIVE", event=("SYSTEM", "Wake word 'Jarvis' detected."))
            speak("Yes Sanjeev, Jarvis is activated. How can I help you?")

        # Active conversation command loop
        last_interaction_time = time.time()
        while True:
            # Sleep if idle for more than 25 seconds
            if time.time() - last_interaction_time > 25:
                speak("Going to sleep. Say Jarvis or double clap to wake me up.")
                break
                
            try:
                print("\nListening for command...")
                command = listen()
                if not command:
                    continue
                    
                last_interaction_time = time.time()
                
                # Check for exit commands
                if any(exit_phrase in command.lower() for exit_phrase in ["exit", "stop", "goodbye", "shutdown astra"]):
                    update_state(event=("SYSTEM", "ASTRA shutdown requested."))
                    speak("Goodbye Sanjeev. Shutting down.")
                    sys.exit(0)
                    
                # Check for conversation history clear
                if "clear memory" in command.lower() or "clear history" in command.lower():
                    brain.clear_memory()
                    speak("Conversational history cleared.")
                    continue

                # Face Registration Trigger
                elif "register face" in command.lower() or "train face" in command.lower() or "face registration" in command.lower():
                    speak("Opening face registration window. Please look directly at the camera.")
                    success = register_user("Sanjeev")
                    if success:
                        speak("Face registration successful. Face database updated.")
                    else:
                        speak("Face registration failed. Please check your webcam connection.")
                    continue

                # 4. Check for Security-Sensitive Tasks
                # a) File Deletion
                if "delete file " in command.lower() or "remove file " in command.lower():
                    filename = command.lower().replace("delete file ", "").replace("remove file ", "").strip()
                    confirmed = confirm_sensitive_action(f"delete the file '{filename}'", speak, listen, require_face=True)
                    if confirmed:
                        reply = handle_file_deletion(filename)
                        speak(reply)
                    continue
                    
                # b) File Moving
                elif "move file " in command.lower() or "transfer file " in command.lower():
                    clean_cmd = command.lower().replace("move file ", "").replace("transfer file ", "")
                    if " to " in clean_cmd:
                        src, dest = clean_cmd.split(" to ", 1)
                        src = src.strip()
                        dest = dest.strip()
                        confirmed = confirm_sensitive_action(f"move '{src}' to '{dest}'", speak, listen, require_face=True)
                        if confirmed:
                            reply = handle_file_move(src, dest)
                            speak(reply)
                    else:
                        speak("Please specify both the source file and destination directory using the format: move file [name] to [folder]")
                    continue
                    
                # c) PC Shutdown
                elif any(shutdown_phrase in command.lower() for shutdown_phrase in ["shutdown pc", "shutdown computer", "turn off computer"]):
                    confirmed = confirm_sensitive_action("shutdown your computer", speak, listen, require_face=True)
                    if confirmed:
                        speak("Shutting down the system. Goodbye.")
                        os.system("shutdown /s /t 1")
                    continue

                # 5. Check for System Information Queries
                sys_reply = run_system_query(command)
                if sys_reply:
                    speak(sys_reply)
                    continue

                # 6. Check for Command Engine / Local Tasks (Websites, Apps, Folder Shortcuts)
                cmd_reply = execute_command(command)
                if cmd_reply:
                    speak(cmd_reply)
                    continue

                # 7. Fallback to LLM Chat Brain (Groq Llama-3)
                ai_reply = ask_astra(command)
                speak(ai_reply)
                
            except Exception as e:
                logger.error(f"Error in conversation loop: {str(e)}")
                speak("I encountered an error. Please try again.")

if __name__ == "__main__":
    start_assistant()
