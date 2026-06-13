import os
import tempfile
import logging

logger = logging.getLogger("ASTRA.JunkScanner")

def scan_junk_files():
    """Scans the system's temporary directory and returns (file_count, total_bytes)."""
    temp_folder = tempfile.gettempdir()
    total_size = 0
    file_count = 0

    try:
        for root, dirs, files in os.walk(temp_folder):
            for file in files:
                try:
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
                    file_count += 1
                except Exception:
                    pass
    except Exception as e:
        logger.error(f"Error scanning junk files: {str(e)}")
        
    return file_count, total_size

def clean_junk_files():
    """
    Deletes files in the system's temporary folder and returns (deleted_count, freed_bytes).
    """
    temp_folder = tempfile.gettempdir()
    deleted_count = 0
    freed_bytes = 0
    
    logger.info(f"Starting cleanup of temp folder: {temp_folder}")
    
    for root, dirs, files in os.walk(temp_folder, topdown=False):
        for file in files:
            try:
                file_path = os.path.join(root, file)
                size = os.path.getsize(file_path)
                os.remove(file_path)
                deleted_count += 1
                freed_bytes += size
            except Exception:
                pass
        for directory in dirs:
            try:
                dir_path = os.path.join(root, directory)
                os.rmdir(dir_path)
            except Exception:
                pass
                
    logger.info(f"Cleanup complete. Deleted {deleted_count} files, freed {freed_bytes / (1024**2):.2f} MB.")
    return deleted_count, freed_bytes

if __name__ == "__main__":
    print("=== ASTRA JUNK SCANNER ===")
    count, size = scan_junk_files()
    print(f"Junk Files: {count}")
    print(f"Total Size: {size / (1024**2):.2f} MB")
    
    confirm = input("Clean junk files now? (y/n): ")
    if confirm.lower() == 'y':
        del_count, freed = clean_junk_files()
        print(f"Freed: {freed / (1024**2):.2f} MB (Deleted {del_count} files)")