import webbrowser
import subprocess
import os
from commands.file_manager import open_file_by_name, open_folder_by_name

# Mapping of popular websites to their correct URLs
POPULAR_WEBSITES = {
    "chatgpt": "https://chatgpt.com",
    "youtube": "https://youtube.com",
    "google": "https://google.com",
    "github": "https://github.com",
    "whatsapp": "https://web.whatsapp.com",
    "facebook": "https://facebook.com",
    "instagram": "https://instagram.com",
    "twitter": "https://twitter.com",
    "x": "https://x.com",
    "linkedin": "https://linkedin.com",
    "reddit": "https://reddit.com",
    "wikipedia": "https://wikipedia.org",
    "netflix": "https://netflix.com",
    "amazon": "https://amazon.com",
    "yahoo": "https://yahoo.com",
    "outlook": "https://outlook.live.com",
    "gmail": "https://mail.google.com",
    "zoom": "https://zoom.us"
}

# Mapping of popular apps to their executable names
POPULAR_APPS = {
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "notepad": "notepad.exe",
    "paint": "mspaint.exe",
    "mspaint": "mspaint.exe",
    "cmd": "cmd.exe",
    "command prompt": "cmd.exe",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "task manager": "taskmgr.exe",
    "taskmgr": "taskmgr.exe",
    "chrome": "chrome.exe",
    "google chrome": "chrome.exe",
    "vs code": "code",
    "vscode": "code",
    "code": "code"
}

def get_chrome_path():
    possible_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    ]
    user_profile = os.environ.get("USERPROFILE")
    if user_profile:
        possible_paths.append(os.path.join(user_profile, r"AppData\Local\Google\Chrome\Application\chrome.exe"))
        
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

def open_in_chrome(url):
    chrome_path = get_chrome_path()
    if chrome_path:
        try:
            webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(chrome_path))
            webbrowser.get('chrome').open(url)
            return
        except Exception:
            pass
    webbrowser.open(url)

def clean_target(target):
    target = target.strip().lower()
    
    # Remove leading articles, pronouns, and redundant verbs
    prefixes = ["the ", "my ", "local ", "a ", "an ", "open "]
    changed = True
    while changed:
        changed = False
        for prefix in prefixes:
            if target.startswith(prefix):
                target = target[len(prefix):].strip()
                changed = True
                
    # Remove trailing nouns and classifiers
    suffixes = [" folder", " directory", " drive"]
    changed = True
    while changed:
        changed = False
        for suffix in suffixes:
            if target.endswith(suffix):
                target = target[:-len(suffix)].strip()
                changed = True
                
    return target

def execute_command(command):
    command = command.strip().lower()

    # Intercept explicit file/folder actions first
    if command.startswith("open folder "):
        folder = command[len("open folder "):].strip()
        return open_folder_by_name(folder)
    elif command.startswith("open the folder "):
        folder = command[len("open the folder "):].strip()
        return open_folder_by_name(folder)
    elif command.startswith("open file "):
        file = command[len("open file "):].strip()
        return open_file_by_name(file)
    elif command.startswith("open the file "):
        file = command[len("open the file "):].strip()
        return open_file_by_name(file)

    # Handle Search Queries
    if command.startswith("search for "):
        query = command[len("search for "):].strip()
        open_in_chrome(f"https://www.google.com/search?q={query}")
        return f"Searching Google for: {query}"
    
    elif command.startswith("search "):
        query = command[len("search "):].strip()
        open_in_chrome(f"https://www.google.com/search?q={query}")
        return f"Searching Google for: {query}"

    # Extract target if command starts with "open " or "go to "
    target_raw = None
    if command.startswith("open "):
        target_raw = command[len("open "):].strip()
    elif command.startswith("go to "):
        target_raw = command[len("go to "):].strip()
    else:
        target_raw = command

    if not target_raw:
        return None

    target = clean_target(target_raw)

    # 1. Check if target is a single-letter drive (e.g., "c", "d")
    if len(target) == 1 and target.isalpha():
        drive_path = f"{target.upper()}:\\"
        if os.path.exists(drive_path):
            try:
                os.startfile(drive_path)
                return f"Opening drive {drive_path}"
            except Exception as e:
                pass

    # 2. Check if target is an absolute or valid relative path/directory on the disk
    if os.path.isdir(target):
        try:
            os.startfile(target)
            return f"Opening path: {target}"
        except Exception:
            pass

    # 3. Check if target is a system folder shortcut
    user_profile = os.environ.get("USERPROFILE", "")
    system_folders = {
        "downloads": os.path.join(user_profile, "Downloads"),
        "documents": os.path.join(user_profile, "Documents"),
        "desktop": os.path.join(user_profile, "Desktop"),
        "pictures": os.path.join(user_profile, "Pictures"),
        "music": os.path.join(user_profile, "Music"),
        "videos": os.path.join(user_profile, "Videos"),
        "user profile": user_profile,
        "profile": user_profile,
        "user folder": user_profile
    }

    if target in system_folders:
        folder_path = system_folders[target]
        if os.path.exists(folder_path):
            try:
                os.startfile(folder_path)
                return f"Opening {target.capitalize()}"
            except Exception as e:
                pass

    # 4. Check if target is a known popular website
    if target in POPULAR_WEBSITES:
        url = POPULAR_WEBSITES[target]
        open_in_chrome(url)
        return f"Opening {target.capitalize()}"

    # 5. Check if target is a file (ends in common file extension)
    _, ext = os.path.splitext(target)
    if ext in ['.pdf', '.zip', '.docx', '.pptx', '.txt', '.xlsx', '.png', '.jpg', '.jpeg', '.mp3', '.mp4']:
        return open_file_by_name(target)

    # 6. Check if target is a URL/domain name (contains '.' or starts with http)
    if "." in target or target.startswith("http"):
        url = target if target.startswith("http") else "https://" + target
        open_in_chrome(url)
        return f"Opening website: {target}"

    # 7. Check if target is Google Chrome (ensure absolute path is tried first)
    if target in ["chrome", "google chrome"]:
        chrome_path = get_chrome_path()
        if chrome_path:
            try:
                subprocess.Popen(chrome_path)
                return "Opening Google Chrome"
            except Exception:
                pass

    # 8. Check if target is a known popular application
    if target in POPULAR_APPS:
        app_exe = POPULAR_APPS[target]
        try:
            subprocess.Popen(app_exe, shell=True)
            return f"Opening {target.capitalize()}"
        except Exception as e:
            return f"Failed to open application {target}: {str(e)}"

    # 9. Try running it as a generic local system command/executable
    try:
        subprocess.Popen(target)
        return f"Opening {target}"
    except Exception:
        # 10. Fallback: treat as a website name (e.g., "open chatgpt" -> https://www.chatgpt.com)
        url = f"https://www.{target}.com"
        open_in_chrome(url)
        return f"Opening {target}.com in Chrome"
