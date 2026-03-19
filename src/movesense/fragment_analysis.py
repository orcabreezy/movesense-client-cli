import sys
from datetime import datetime
from os import path
from pathlib import Path

import pandas as pd

if __name__ == "__main__":
    path_str = sys.argv[1]

    # Path to your data folder
    data_folder = Path(path_str)  # <-- change this

    # Collect all CSV files matching the expected name format
    csv_files = list(data_folder.glob("*.csv"))

    # Parse datetime from filename stem: YYYYMMDD_HHMMSS
    def parse_timestamp(file_path: Path):
        try:
            return datetime.strptime(file_path.stem, "%Y%m%d_%H%M%S")
        except ValueError:
            return None  # Skip files that don't match the expected format

    # Keep only valid files
    valid_files = [(f, parse_timestamp(f)) for f in csv_files]
    valid_files = [(f, ts) for f, ts in valid_files if ts is not None]

    # Sort by timestamp descending (most recent first)
    valid_files.sort(key=lambda x: x[1], reverse=True)

    # Get top 3 most recent
    top_3 = [f.name for f, _ in valid_files[:3]]

    print("Three most recent CSV files:")

    for name in top_3:
        print(name)

    before = pd.read_csv(f"{path_str}/{top_3[2]}")
    after = pd.read_csv(f"{path_str}/{top_3[1]}")
    buffered = pd.read_csv(f"{path_str}/{top_3[0]}")

    break_off_time = list(before["timestamp"])[-1]
    begin_log_time = list(buffered["timestamp"])[0]
    end_log_time = list(buffered["timestamp"])[-1]
    begin_continue_time = list(after["timestamp"])[0]

    lost_time_on_start = begin_log_time - break_off_time
    lost_time_on_end = begin_continue_time - end_log_time

    print()
    print(f"lost time: {lost_time_on_start} ms")
    print(f"lost time on end: {lost_time_on_end} ms")
    print("-----")
    print(f"Break off time: {break_off_time}")
    print(f"Begin log time: {begin_log_time}")
    print(f"End log time  : {end_log_time}")
    print(f"continue time : {begin_continue_time}")
