import os

root_path = r"C:\Users"

print("Scanning Started...")

file_count = 0

for foldername, subfolders, filenames in os.walk(root_path):
    file_count += len(filenames)

print(f"Total Files Found: {file_count}")