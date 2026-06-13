import psutil

print("\n=== ASTRA DRIVE SCANNER ===\n")

partitions = psutil.disk_partitions()

for partition in partitions:
    try:
        usage = psutil.disk_usage(partition.mountpoint)

        print(f"Drive       : {partition.device}")
        print(f"Mount Point : {partition.mountpoint}")
        print(f"File System : {partition.fstype}")
        print(f"Total Space : {usage.total / (1024**3):.2f} GB")
        print(f"Used Space  : {usage.used / (1024**3):.2f} GB")
        print(f"Free Space  : {usage.free / (1024**3):.2f} GB")
        print(f"Usage       : {usage.percent}%")
        print("-" * 50)

    except PermissionError:
        continue