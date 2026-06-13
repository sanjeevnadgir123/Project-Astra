import psutil

print("\n=== ASTRA PROCESS SCANNER ===\n")

for process in psutil.process_iter(['pid', 'name']):
    try:
        print(
            f"PID: {process.info['pid']} | "
            f"Process: {process.info['name']}"
        )
    except:
        pass