import os

root_path = r"C:\Users"

largest_files = []

print("Scanning for large files...")

for foldername, subfolders, filenames in os.walk(root_path):
    for filename in filenames:
        try:
            file_path = os.path.join(foldername, filename)
            size = os.path.getsize(file_path)

            largest_files.append((size, file_path))

        except Exception:
            pass

largest_files.sort(reverse=True)

print("\n=== TOP 10 LARGEST FILES ===\n")

for size, path in largest_files[:10]:
    print(f"{size/(1024**3):.2f} GB | {path}")