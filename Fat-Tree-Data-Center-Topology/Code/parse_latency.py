#!/usr/bin/env python3
import re
import csv
import sys
import os

# Names of the client/server log files
CLIENT_LOG = "h1_client.log"
SERVER_LOG = "h16_server.log"
OUTPUT_CSV = "latencies.csv"

def extract_timestamps(logfile, pattern):
    """Scan logfile line by line, return list of float timestamps matching pattern."""
    ts = []
    prog = re.compile(pattern)
    
    # Check if file exists and has content
    if not os.path.exists(logfile) or os.path.getsize(logfile) == 0:
        print(f"Warning: {logfile} is empty or missing", file=sys.stderr)
        return ts
        
    try:
        with open(logfile, 'r') as f:
            for line in f:
                m = prog.search(line)
                if m:
                    ts.append(float(m.group(1)))
    except Exception as e:
        print(f"Error reading {logfile}: {e}", file=sys.stderr)
    
    return ts

def main():
    # 1) Extract send times from the client log
    sends = extract_timestamps(
        CLIENT_LOG,
        r"Sent .* at ([0-9]+\.[0-9]+)"
    )

    # 2) Extract receive‑complete times from the server log
    recvs = extract_timestamps(
        SERVER_LOG,
        r"Completed receiving .* at ([0-9]+\.[0-9]+)"
    )

    if len(sends) == 0 and len(recvs) == 0:
        print(f"Error: No timestamps found in logs. Traffic may not be flowing correctly.", file=sys.stderr)
        # Create an empty but valid CSV to avoid downstream errors
        with open(OUTPUT_CSV, 'w', newline='') as out:
            writer = csv.writer(out)
            writer.writerow(["batch", "latency_s"])
        print(f"Created empty {OUTPUT_CSV} file")
        return
        
    if len(sends) != len(recvs):
        print(f"Warning: {len(sends)} sends vs {len(recvs)} receives", file=sys.stderr)

    # 3) Pair them up and write CSV
    with open(OUTPUT_CSV, 'w', newline='') as out:
        writer = csv.writer(out)
        writer.writerow(["batch", "latency_s"])
        for i, (s, r) in enumerate(zip(sends, recvs)):
            writer.writerow([i, r - s])

    print(f"Wrote {min(len(sends), len(recvs))} latency records to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
