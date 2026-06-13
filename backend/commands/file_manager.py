import os
import logging
import subprocess

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ASTRA.FileManager")

def get_user_profile():
    return os.environ.get("USERPROFILE", "C:\\")

def open_downloads():
    path = os.path.join(get_user_profile(), "Downloads")
    if os.path.exists(path):
        os.startfile(path)
        return "Opening Downloads folder."
    return "Downloads folder not found."

def open_documents():
    path = os.path.join(get_user_profile(), "Documents")
    if os.path.exists(path):
        os.startfile(path)
        return "Opening Documents folder."
    return "Documents folder not found."

def open_desktop():
    path = os.path.join(get_user_profile(), "Desktop")
    if os.path.exists(path):
        os.startfile(path)
        return "Opening Desktop folder."
    return "Desktop folder not found."

def search_files(name_query, max_results=5):
    """
    Searches for files matching name_query in the user's home directory.
    To ensure speed, it prioritizes Desktop, Documents, and Downloads first.
    """
    user_home = get_user_profile()
    priority_dirs = [
        os.path.join(user_home, "Desktop"),
        os.path.join(user_home, "Documents"),
        os.path.join(user_home, "Downloads")
    ]
    
    matches = []
    
    # 1. Search priority directories first
    for directory in priority_dirs:
        if not os.path.exists(directory):
            continue
        for root, dirs, files in os.walk(directory):
            for file in files:
                if name_query.lower() in file.lower():
                    matches.append(os.path.join(root, file))
                    if len(matches) >= max_results:
                        return matches
                        
    # 2. Fallback to general home directory (excluding AppData or hidden folders to keep it fast)
    for root, dirs, files in os.walk(user_home):
        # Skip hidden and system/app directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['AppData', 'Local Settings', 'Application Data', 'Saved Games', 'Searches']]
        
        # Don't re-scan priority dirs
        if any(root.startswith(p_dir) for p_dir in priority_dirs):
            continue
            
        for file in files:
            if name_query.lower() in file.lower():
                matches.append(os.path.join(root, file))
                if len(matches) >= max_results:
                    return matches
                    
    return matches

def open_file_by_name(filename):
    """
    Attempts to search for a file and open it.
    Specially handles common extensions if not specified.
    """
    logger.info(f"Requested to open file: {filename}")
    
    # 1. Try if it is already an absolute/relative path
    if os.path.exists(filename) and os.path.isfile(filename):
        try:
            os.startfile(filename)
            return f"Opening file at {filename}"
        except Exception as e:
            return f"Failed to open file: {str(e)}"
            
    # 2. Search for the file in the home directory
    matches = search_files(filename)
    
    if not matches:
        # If no extension was provided, try adding common ones and search again
        if not os.path.splitext(filename)[1]:
            extensions = ['.pdf', '.zip', '.docx', '.pptx', '.txt', '.xlsx']
            for ext in extensions:
                matches = search_files(filename + ext)
                if matches:
                    break
                    
    if not matches:
        return f"Sorry, I couldn't find any file named '{filename}'."
        
    # Open the first match
    target_file = matches[0]
    try:
        os.startfile(target_file)
        return f"Found and opening: {os.path.basename(target_file)}"
    except Exception as e:
        return f"Found file {os.path.basename(target_file)} but failed to open: {str(e)}"

def open_folder_by_name(folder_name):
    """
    Searches for a folder/directory and opens it in Explorer.
    """
    logger.info(f"Requested to open folder: {folder_name}")
    user_home = get_user_profile()
    
    # Check shortcuts first
    shortcuts = {
        "downloads": open_downloads,
        "documents": open_documents,
        "desktop": open_desktop,
        "home": lambda: os.startfile(user_home) or "Opening home folder."
    }
    
    clean_name = folder_name.lower().strip()
    if clean_name in shortcuts:
        return shortcuts[clean_name]()
        
    # Otherwise search directories in User profile
    for root, dirs, files in os.walk(user_home):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['AppData', 'Local Settings']]
        for d in dirs:
            if clean_name == d.lower() or clean_name in d.lower():
                target_path = os.path.join(root, d)
                try:
                    os.startfile(target_path)
                    return f"Opening folder: {d}"
                except Exception as e:
                    return f"Found folder {d} but failed to open: {str(e)}"
                    
    return f"Sorry, I couldn't find any folder named '{folder_name}'."
