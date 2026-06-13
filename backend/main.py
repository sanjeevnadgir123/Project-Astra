import os
import time
import psutil
import logging
import threading
import tempfile
import asyncio
from fastapi import FastAPI, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ASTRA.DashboardAPI")

app = FastAPI(
    title="ASTRA Dashboard API",
    description="Backend API and WebSocket services for ASTRA",
    version="1.0.0"
)

# Enable CORS for frontend dashboard connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared in-memory ASTRA state
class AstraState:
    def __init__(self):
        self.voice_status = "SLEEPING" # SLEEPING, ACTIVE, LISTENING, PROCESSING
        self.last_transcript = ""
        self.last_response = ""
        self.face_status = "UNKNOWN" # UNKNOWN, VERIFYING, VERIFIED, LOCKDOWN
        self.two_claps_detected = False
        self.events = [
            {"time": time.strftime("%H:%M:%S"), "type": "SYSTEM", "message": "ASTRA Core Booted."}
        ]
        
    def add_event(self, event_type, message):
        self.events.append({
            "time": time.strftime("%H:%M:%S"),
            "type": event_type,
            "message": message
        })
        # Keep last 50 events
        if len(self.events) > 50:
            self.events.pop(0)

# Global instances
astra_state = AstraState()

# Global cache for heavy storage scans
class StorageCache:
    def __init__(self):
        self.junk_count = 0
        self.junk_size_mb = 0.0
        self.largest_files = []
        self.total_files = 0
        self.drive_info = []
        self.is_scanning = False
        self.last_scanned = 0.0

storage_cache = StorageCache()

def perform_storage_scan():
    """Heavy background task to scan drives, large files, and junk."""
    logger.info("Storage background scan started...")
    storage_cache.is_scanning = True
    astra_state.add_event("SYSTEM", "Storage scan started.")
    
    # 1. Junk Scan (Temp folder)
    temp_folder = tempfile.gettempdir()
    junk_count = 0
    total_junk_size = 0
    try:
        for root, dirs, files in os.walk(temp_folder):
            for file in files:
                try:
                    file_path = os.path.join(root, file)
                    total_junk_size += os.path.getsize(file_path)
                    junk_count += 1
                except Exception:
                    pass
    except Exception as e:
        logger.error(f"Junk scan error: {str(e)}")
        
    storage_cache.junk_count = junk_count
    storage_cache.junk_size_mb = total_junk_size / (1024**2)

    # 2. Drive Scan
    drive_info = []
    try:
        partitions = psutil.disk_partitions()
        for partition in partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                drive_info.append({
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                    "total_gb": round(usage.total / (1024**3), 2),
                    "used_gb": round(usage.used / (1024**3), 2),
                    "free_gb": round(usage.free / (1024**3), 2),
                    "percent": usage.percent
                })
            except PermissionError:
                continue
    except Exception as e:
        logger.error(f"Drive partition scan error: {str(e)}")
    storage_cache.drive_info = drive_info

    # 3. Largest Files and Total Files Scan (Limited to user home for speed)
    user_home = os.environ.get("USERPROFILE", "C:\\")
    largest_files = []
    total_files = 0
    
    try:
        for root, dirs, files in os.walk(user_home):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['AppData', 'Local Settings', 'Application Data']]
            total_files += len(files)
            
            for file in files:
                try:
                    file_path = os.path.join(root, file)
                    size = os.path.getsize(file_path)
                    largest_files.append((size, file_path))
                except Exception:
                    pass
    except Exception as e:
        logger.error(f"File system walking error: {str(e)}")

    # Sort largest files
    largest_files.sort(reverse=True, key=lambda x: x[0])
    formatted_largest = [
        {"path": path, "size_gb": round(size / (1024**3), 3)}
        for size, path in largest_files[:10]
    ]

    storage_cache.largest_files = formatted_largest
    storage_cache.total_files = total_files
    storage_cache.last_scanned = time.time()
    storage_cache.is_scanning = False
    astra_state.add_event("SYSTEM", "Storage scan completed.")
    logger.info("Storage background scan completed successfully.")

@app.get("/")
def get_root():
    return {
        "status": "online",
        "system": "ASTRA (Advanced Smart Task and Response Assistant)",
        "message": "Dashboard backend services are fully operational."
    }

@app.get("/api/metrics")
def get_realtime_metrics():
    """Returns quick real-time CPU, RAM, and main drive disk metrics."""
    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory().percent
    try:
        disk = psutil.disk_usage("C:\\").percent
    except Exception:
        disk = 0.0
        
    return {
        "cpu_percent": cpu,
        "ram_percent": ram,
        "disk_percent": disk,
        "timestamp": time.time()
    }

@app.get("/api/processes")
def get_processes():
    """Returns total running process count and process details."""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
            
    processes.sort(key=lambda x: x.get('cpu_percent') or 0, reverse=True)
    
    return {
        "total_processes": len(processes),
        "processes": processes[:20]
    }

@app.get("/api/storage/summary")
def get_storage_summary(background_tasks: BackgroundTasks):
    """Returns storage metrics. Triggers a background scan if never run."""
    if storage_cache.last_scanned == 0.0 and not storage_cache.is_scanning:
        background_tasks.add_task(perform_storage_scan)
        return {
            "message": "Storage scan initiated. Please check back in a few seconds.",
            "is_scanning": True,
            "last_scanned": 0
        }
        
    return {
        "is_scanning": storage_cache.is_scanning,
        "last_scanned_timestamp": storage_cache.last_scanned,
        "total_files": storage_cache.total_files,
        "junk_files_found": storage_cache.junk_count,
        "junk_storage_mb": round(storage_cache.junk_size_mb, 2),
        "drives": storage_cache.drive_info,
        "top_largest_files": storage_cache.largest_files
    }

@app.post("/api/storage/scan")
def trigger_storage_scan(background_tasks: BackgroundTasks):
    """Explicitly triggers a re-scan of the storage system in the background."""
    if storage_cache.is_scanning:
        return {"status": "scanning_already_in_progress", "is_scanning": True}
        
    background_tasks.add_task(perform_storage_scan)
    return {"status": "scan_initiated", "is_scanning": True}

@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint to stream system metrics and ASTRA status in real-time."""
    await websocket.accept()
    logger.info("WebSocket connection established with client dashboard.")
    try:
        while True:
            # Gather quick metrics
            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory().percent
            try:
                disk = psutil.disk_usage("C:\\").percent
            except Exception:
                disk = 0.0

            # Gather process details (top 10 for compactness)
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except Exception:
                    pass
            processes.sort(key=lambda x: x.get('cpu_percent') or 0, reverse=True)

            payload = {
                "metrics": {
                    "cpu_percent": cpu,
                    "ram_percent": ram,
                    "disk_percent": disk,
                    "uptime_sec": int(time.time() - psutil.boot_time())
                },
                "processes": processes[:10],
                "astra": {
                    "voice_status": astra_state.voice_status,
                    "last_transcript": astra_state.last_transcript,
                    "last_response": astra_state.last_response,
                    "face_status": astra_state.face_status,
                    "two_claps_detected": astra_state.two_claps_detected
                },
                "events": astra_state.events,
                "storage": {
                    "is_scanning": storage_cache.is_scanning,
                    "total_files": storage_cache.total_files,
                    "junk_count": storage_cache.junk_count,
                    "junk_size_mb": round(storage_cache.junk_size_mb, 2),
                    "drives": storage_cache.drive_info,
                    "largest_files": storage_cache.largest_files
                }
            }
            await websocket.send_json(payload)
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        logger.info("WebSocket connection disconnected.")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")

from pydantic import BaseModel

class CommandRequest(BaseModel):
    command: str

@app.post("/api/command")
async def run_command_endpoint(req: CommandRequest, background_tasks: BackgroundTasks):
    """Executes a command from the dashboard console or quick actions instantly in the background."""
    command = req.command
    logger.info(f"Dashboard Command: {command}")
    
    # Add event to logs immediately
    astra_state.add_event("USER", f"Console command: {command}")
    
    cmd_lower = command.lower()
    
    # Import necessary routing elements
    from commands.command_engine import execute_command
    from voice.astra_chat import speak, speak_non_blocking, listen, handle_file_deletion, handle_file_move, run_system_query
    from security.security_layer import confirm_sensitive_action
    
    def process_command():
        # 0. Check for face registration/training
        if "register face" in cmd_lower or "train face" in cmd_lower or "face registration" in cmd_lower:
            from vision.face_recognizer import register_user
            astra_state.add_event("SECURITY", "Face registration window opened.")
            speak_non_blocking("Opening face registration window. Please look directly at the camera.")
            success = register_user("Sanjeev")
            if success:
                reply = "Face registration complete. Face database updated."
                astra_state.add_event("SECURITY", reply)
                astra_state.last_response = reply
                speak_non_blocking(reply)
            else:
                reply = "Face registration failed. Please ensure your camera is connected."
                astra_state.add_event("SECURITY", reply)
                astra_state.last_response = reply
                speak_non_blocking(reply)
            return

        # 1. Check for specific dashboard cleanup trigger first
        if "system cleanup" in cmd_lower or "cleanup" in cmd_lower or "clean junk" in cmd_lower:
            # Ask user for confirmation (voice + face check)
            confirmed = confirm_sensitive_action("perform a system temp files cleanup", speak_non_blocking, listen, require_face=True)
            if confirmed:
                from storage.junk_scanner import clean_junk_files
                del_count, freed = clean_junk_files()
                # Update cache so the UI reflects the cleanup immediately!
                storage_cache.junk_count = 0
                storage_cache.junk_size_mb = 0.0
                
                reply = f"System cleanup completed. Deleted {del_count} files, freeing {freed / (1024**2):.2f} MB of temporary storage."
                astra_state.add_event("SYSTEM", reply)
                astra_state.last_response = reply
                speak_non_blocking(reply)
            else:
                astra_state.add_event("SECURITY", "Cleanup aborted by user or face verification failed.")
                astra_state.last_response = "Cleanup aborted."
            return

        # 2. Check for file deletion
        elif "delete file " in cmd_lower or "remove file " in cmd_lower:
            filename = cmd_lower.replace("delete file ", "").replace("remove file ", "").strip()
            confirmed = confirm_sensitive_action(f"delete the file '{filename}'", speak_non_blocking, listen, require_face=True)
            if confirmed:
                reply = handle_file_deletion(filename)
                astra_state.add_event("ASTRA", reply)
                astra_state.last_response = reply
                speak_non_blocking(reply)
            else:
                astra_state.add_event("SECURITY", f"Deletion of '{filename}' cancelled or verification failed.")
                astra_state.last_response = "Action cancelled."
            return
                
        # 3. Check for file move
        elif "move file " in cmd_lower or "transfer file " in cmd_lower:
            clean_cmd = cmd_lower.replace("move file ", "").replace("transfer file ", "")
            if " to " in clean_cmd:
                src, dest = clean_cmd.split(" to ", 1)
                src = src.strip()
                dest = dest.strip()
                confirmed = confirm_sensitive_action(f"move '{src}' to '{dest}'", speak_non_blocking, listen, require_face=True)
                if confirmed:
                    reply = handle_file_move(src, dest)
                    astra_state.add_event("ASTRA", reply)
                    astra_state.last_response = reply
                    speak_non_blocking(reply)
                else:
                    astra_state.add_event("SECURITY", f"Moving '{src}' cancelled or verification failed.")
                    astra_state.last_response = "Action cancelled."
            else:
                reply = "Please specify both source and destination using: move file [name] to [folder]"
                astra_state.add_event("ASTRA", reply)
                astra_state.last_response = reply
            return
                
        # 4. Check for PC Shutdown
        elif any(p in cmd_lower for p in ["shutdown pc", "shutdown computer", "turn off computer"]):
            confirmed = confirm_sensitive_action("shutdown your computer", speak_non_blocking, listen, require_face=True)
            if confirmed:
                reply = "Shutting down the system. Goodbye."
                astra_state.add_event("SYSTEM", reply)
                astra_state.last_response = reply
                speak_non_blocking(reply)
                
                import os
                import time
                time.sleep(2)
                os.system("shutdown /s /t 1")
            else:
                astra_state.add_event("SECURITY", "Shutdown cancelled or verification failed.")
                astra_state.last_response = "Action cancelled."
            return

        # 5. Check for real-time system metrics query
        sys_reply = run_system_query(command)
        if sys_reply:
            astra_state.add_event("ASTRA", sys_reply)
            astra_state.last_response = sys_reply
            speak_non_blocking(sys_reply)
            return

        # 6. Execute general command (website, local app, path etc)
        reply = execute_command(command)
        if reply:
            astra_state.add_event("ASTRA", reply)
            astra_state.last_response = reply
            speak_non_blocking(reply)
            return

        # 7. Fallback to LLM chat brain
        from ai.brain import ask_astra
        reply = ask_astra(command)
        astra_state.add_event("ASTRA", reply)
        astra_state.last_response = reply
        speak_non_blocking(reply)

    # Dispatch task to background thread execution
    background_tasks.add_task(process_command)
    
    return {"status": "success", "reply": "Command received."}

# Self-contained startup routine if main.py is run directly
if __name__ == "__main__":
    print("=== STARTING ASTRA DASHBOARD BACKEND SERVICES ===")
    
    # Pre-run storage scan in separate thread on startup to populate cache immediately
    startup_scan = threading.Thread(target=perform_storage_scan, daemon=True)
    startup_scan.start()

    # Start ASTRA Voice Assistant thread
    try:
        from voice.astra_chat import start_assistant
        assistant_thread = threading.Thread(target=start_assistant, daemon=True)
        assistant_thread.start()
        logger.info("ASTRA Voice Assistant background thread initialized.")
    except Exception as e:
        logger.error(f"Failed to start ASTRA Voice Assistant thread: {str(e)}")
    
    # Launch uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)