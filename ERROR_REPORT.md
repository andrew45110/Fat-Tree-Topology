# Fat-Tree Data Center Network Simulation Project
## Error Report and Rectification Summary

This document details all the errors, issues, and challenges encountered during the preparation of the Fat-Tree Data Center Network Simulation project for distribution, along with the solutions implemented.

---

## Table of Contents
1. [Unnecessary Large Files Included in Initial Zip](#1-unnecessary-large-files-included-in-initial-zip)
2. [Missing RYU Virtual Environment Activation Step](#2-missing-ryu-virtual-environment-activation-step)
3. [Missing Mininet Cleanup Instructions](#3-missing-mininet-cleanup-instructions)
4. [Multiple RYU Controller Instances Conflict](#4-multiple-ryu-controller-instances-conflict)
5. [Zip Process Appeared to Hang](#5-zip-process-appeared-to-hang)
6. [Missing README Documentation in Zip File](#6-missing-readme-documentation-in-zip-file)
7. [Missing Helper Scripts in Zip File](#7-missing-helper-scripts-in-zip-file)
8. [Hardcoded File Paths in Scripts](#8-hardcoded-file-paths-in-scripts)
9. [Missing TCP vs DCTCP Comparison Script](#9-missing-tcp-vs-dctcp-comparison-script)
10. [Unclear Experiment Results Location](#10-unclear-experiment-results-location)

---

## 1. Unnecessary Large Files Included in Initial Zip

### Problem
The initial attempt to zip the entire mininet home directory included the PyTorch virtual environment (`torch-env/`) which was approximately **5.1 GB** in size. This was unnecessary because:
- The project had transitioned from actual AI training to traffic simulation using `traffic_replay.py`
- The traffic simulation only requires the `cifar_traffic_profile.csv` file, not the actual PyTorch installation or CIFAR-10 dataset

### Files That Were Unnecessarily Large
| File/Directory | Size | Purpose |
|----------------|------|---------|
| `torch-env/` | 5.1 GB | PyTorch virtual environment |
| `data/cifar-10-python.tar.gz` | 170 MB | CIFAR-10 dataset archive |
| `mininet_home_backup.zip` | 113 MB | Old backup file |

### Solution
Removed the unnecessary files to free up approximately 5.4 GB of disk space:
```bash
rm -rf torch-env/ data/cifar-10-python.tar.gz mininet_home_backup.zip
```

### Verification
After removal, disk usage dropped significantly:
```bash
df -h .
# Result: 51GB available (previously much less)
```

---

## 2. Missing RYU Virtual Environment Activation Step

### Problem
The initial documentation did not include the critical step of activating the RYU virtual environment before starting the controller. Without this step, users would encounter import errors when trying to run the RYU controller.

### Error Scenario
If a user tried to run the RYU controller without activating the virtual environment:
```bash
cd ryu
./run_ryu.py ryu.app.simple_switch_13
# Would fail with ModuleNotFoundError for eventlet or ryu modules
```

### Solution
Updated the README-SETUP.md to include the virtual environment activation step:
```bash
# First, activate the RYU virtual environment:
source ~/ryu/venv/bin/activate

# Then start the RYU controller:
cd ryu
./run_ryu.py ryu.app.simple_switch_13
```

---

## 3. Missing Mininet Cleanup Instructions

### Problem
If a user ran `run_sim_fat_tree.py` and then tried to run it again without cleaning up, they would encounter errors because:
- Previous Mininet instances might still be running
- Network interfaces from the previous run might still exist
- Open vSwitch might have stale configurations

### Error Scenario
```bash
# Running simulation without cleanup
sudo python3 run_sim_fat_tree.py ...
# Error: RTNETLINK answers: File exists
# Error: could not find host interface
```

### Solution
Added instructions to always run cleanup before starting a new simulation:
```bash
sudo mn -c
```

This command:
- Removes all Mininet-created network interfaces
- Cleans up Open vSwitch configurations
- Kills any lingering Mininet processes

---

## 4. Multiple RYU Controller Instances Conflict

### Problem
If multiple RYU controller instances are running simultaneously, they compete for the same OpenFlow port (6653), causing:
- Connection failures
- Unpredictable behavior
- Switches connecting to the wrong controller

### Error Scenario
```bash
# Second RYU instance fails to bind to port
OSError: [Errno 98] Address already in use
```

### Solution
Added instructions to check for and kill existing RYU processes before starting a new one:

```bash
# Check for running RYU processes
ps aux | grep ryu

# Kill existing RYU processes if found
sudo kill $(ps aux | grep ryu | grep -v grep | awk '{print $2}')

# Alternatively, check if port 6653 is in use
sudo lsof -i :6653
```

---

## 5. Zip Process Appeared to Hang

### Problem
When creating the zip file, the process appeared to "hang" or stop mid-execution. The terminal output was truncated, making it seem like the zip command had failed.

### Initial Concern
```bash
cd mininet_fat_tree_project && zip -r ../mininet_fat_tree_minimal.zip *
# Output stopped after showing partial file list
# Command appeared interrupted
```

### Investigation
Checked if the zip process was still running:
```bash
ps aux | grep -i zip
# No active zip process found
```

Checked if the system killed the process due to memory issues:
```bash
dmesg | grep -i -e killed -e oom | tail -10
# No OOM killer messages found
```

### Actual Cause
The zip process had actually **completed successfully**. The apparent "hang" was due to:
1. The large number of files being processed generated extensive output
2. The terminal output was truncated for display purposes
3. The zip file was successfully created

### Verification
```bash
ls -lah mininet_fat_tree_minimal.zip
# Result: 41M - file exists and has proper size

unzip -t mininet_fat_tree_minimal.zip | tail
# Result: "No errors detected in compressed data"
```

### Lesson Learned
Always verify zip file creation by:
1. Checking if the file exists and has a reasonable size
2. Running `unzip -t <file>` to test integrity

---

## 6. Missing README Documentation in Zip File

### Problem
The comprehensive README-SETUP.md that was created with all the setup and troubleshooting instructions was not included in the initial zip file.

### Discovery
```bash
unzip -l mininet_project_essential.zip | grep -i readme
# Only showed READMEs from subdirectories, not the main setup README
```

### Solution
Added the README to the zip file in two forms:
```bash
# Add as README-SETUP.md
zip -u mininet_project_essential.zip README-SETUP.md

# Also add as README.md for visibility
cp README-SETUP.md README.md
zip -u mininet_project_essential.zip README.md
rm README.md
```

---

## 7. Missing Helper Scripts in Zip File

### Problem
The `fix_paths.sh` and `setup.sh` helper scripts were created but not included in the initial `mininet_project_essential.zip` file.

### Scripts and Their Purposes
| Script | Purpose |
|--------|---------|
| `fix_paths.sh` | Updates hardcoded paths to match installation location |
| `setup.sh` | Creates RYU virtual environment and installs dependencies |

### Solution
Added both scripts to the zip file:
```bash
# Extract, add scripts, and update zip
mkdir -p test_extract && cd test_extract
unzip -q ../mininet_project_essential.zip
cp ../mininet_fat_tree_project/fix_paths.sh .
cp ../mininet_fat_tree_project/setup.sh .
chmod +x fix_paths.sh setup.sh
zip -u ../mininet_project_essential.zip fix_paths.sh setup.sh
```

---

## 8. Hardcoded File Paths in Scripts

### Problem
Several scripts contained hardcoded paths that assumed the project was installed in `/home/mininet/`. This would cause failures when users installed the project in different locations.

### Affected Files and Hardcoded Paths
| File | Hardcoded Path |
|------|----------------|
| `run_bandwidth_tests.sh` | `/home/mininet/cifar_traffic_profile.csv` |
| `run_tcp_dctcp_compare.sh` | `/home/mininet/cifar_traffic_profile.csv` |
| `visualize_cifar_profile.py` | `/home/mininet/cifar_traffic_profile.csv` |

### Error Scenario
```bash
./run_bandwidth_tests.sh
# Error: FileNotFoundError: /home/mininet/cifar_traffic_profile.csv not found
```

### Solution
Created `fix_paths.sh` script that automatically updates paths based on installation location:

```bash
#!/bin/bash
echo "Fixing paths in project files..."
CURR_DIR=$(pwd)

# Fix paths in run_bandwidth_tests.sh
sed -i "s|/home/mininet/cifar_traffic_profile.csv|$CURR_DIR/cifar_traffic_profile.csv|g" run_bandwidth_tests.sh

# Fix paths in run_tcp_dctcp_compare.sh
sed -i "s|/home/mininet/cifar_traffic_profile.csv|$CURR_DIR/cifar_traffic_profile.csv|g" run_tcp_dctcp_compare.sh

# Fix paths in visualize_cifar_profile.py
sed -i "s|/home/mininet/cifar_traffic_profile.csv|$CURR_DIR/cifar_traffic_profile.csv|g" visualize_cifar_profile.py

echo "Path fixing complete!"
```

---

## 9. Missing TCP vs DCTCP Comparison Script

### Problem
The `run_tcp_dctcp_compare.sh` script, which is essential for comparing TCP and DCTCP performance, was not included in the zip file.

### Discovery
```bash
unzip -l mininet_project_essential.zip | grep -E "(run_tcp_dctcp_compare|run_bandwidth_tests).sh"
# Only showed run_bandwidth_tests.sh, missing run_tcp_dctcp_compare.sh
```

### Complication
The script was located in an unusual path due to a tilde character in the directory name:
```bash
# Incorrect path (didn't work)
~/Fat-Tree-Data-Center-Topology/Code/run_tcp_dctcp_compare.sh

# Correct path (note the escaped tilde)
~/~/Fat-Tree-Data-Center-Topology/Code/run_tcp_dctcp_compare.sh
```

### Solution
```bash
cp ~/\~/Fat-Tree-Data-Center-Topology/Code/run_tcp_dctcp_compare.sh .
chmod +x run_tcp_dctcp_compare.sh
zip -u mininet_project_essential.zip run_tcp_dctcp_compare.sh
```

---

## 10. Unclear Experiment Results Location

### Problem
The initial documentation did not clearly explain where experiment results were stored and which files contained meaningful data versus which were empty or incomplete.

### Issue
Some result directories contained files with minimal or no data:
```bash
ls -lh Fat-Tree-Data-Center-Topology/Code/results/bw_*/latencies.csv
# Some files were only 17 bytes (just headers, no data)
# Others were 1.4K (actual data)
```

### Solution
Updated README-SETUP.md with detailed explanation of:

1. **Results Directory Structure:**
```
Fat-Tree-Data-Center-Topology/Code/results/
├── bw_5mbit_new/      # Results for 5Mbps bandwidth test
│   ├── latencies.csv  # Contains batch number and latency in seconds
│   ├── throughput.csv # Contains throughput measurements in Mbps
│   └── various log files
├── tcp_10mbit/        # Results for TCP with 10Mbps bandwidth
├── dctcp_10mbit/      # Results for DCTCP with 10Mbps bandwidth
└── plots/             # Generated visualization plots
    ├── latency_stats.csv    # Summary statistics
    └── throughput_stats.csv # Throughput summary
```

2. **Which directories contain complete data:**
   - `bw_5mbit_new/`
   - `tcp_10mbit/`
   - `dctcp_10mbit/`

3. **How visualization script uses these files:**
   - Explained that `visualize_results.py` reads from specific directories
   - Pointed users to the `plots/` directory for summary statistics

---

## Summary of All Files Added to Final Zip

| File | Purpose | Status |
|------|---------|--------|
| `README.md` | Main documentation | Added |
| `README-SETUP.md` | Detailed setup guide | Added |
| `fix_paths.sh` | Path configuration script | Added |
| `setup.sh` | Environment setup script | Added |
| `run_bandwidth_tests.sh` | Bandwidth experiment script | Already present |
| `run_tcp_dctcp_compare.sh` | TCP/DCTCP comparison script | Added |
| `cifar_traffic_profile.csv` | Traffic pattern data | Already present |
| `cifar_profile.json` | Profile data | Already present |
| `visualize_results.py` | Results visualization | Already present |
| `visualize_cifar_profile.py` | CIFAR profile visualization | Already present |
| `Fat-Tree-Data-Center-Topology/` | Main project code | Already present |
| `ryu/` | RYU controller | Already present |

---

## Final Verification Checklist

Before distribution, the following checks were performed:

- [x] Zip file integrity verified with `unzip -t`
- [x] All essential scripts included
- [x] README documentation included
- [x] Helper scripts (fix_paths.sh, setup.sh) included
- [x] TCP/DCTCP comparison script included
- [x] Unnecessary large files (torch-env, CIFAR dataset) removed
- [x] All scripts have execute permissions

---

## Installation Instructions for End Users

1. Extract the zip file in the Mininet VM's home directory:
   ```bash
   cd ~
   unzip mininet_project_essential.zip
   ```

2. Run the path fixing script:
   ```bash
   ./fix_paths.sh
   ```

3. Run the setup script:
   ```bash
   ./setup.sh
   ```

4. Follow the instructions in README.md to run experiments

---

*Report generated during project preparation session*
*Date: April 30, 2025*

