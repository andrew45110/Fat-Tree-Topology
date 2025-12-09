# Fat-Tree Data Center Network Simulation

This project simulates a Fat-Tree data center topology in Mininet, using a traffic replay mechanism to simulate CIFAR-10 gradient exchange traffic patterns.

## Prerequisites

- Ubuntu (tested on Ubuntu 18.04/20.04)
- Mininet
- RYU controller
- Python 3.x

## Quick Start

### 1. Clean Up Previous Mininet Instances

Before starting a new simulation, always clean up any previous Mininet instances:

```bash
sudo mn -c
```

### 2. Ensure Only One RYU Controller is Running

Check if any RYU controllers are already running:

```bash
ps aux | grep ryu
```

If there are existing RYU processes, kill them:

```bash
sudo kill $(ps aux | grep ryu | grep -v grep | awk '{print $2}')
```

Or check if port 6653 (OpenFlow) is already in use:

```bash
sudo lsof -i :6653
```

### 3. Start the RYU Controller

First, activate the RYU virtual environment:

```bash
source ~/ryu/venv/bin/activate
```

Then start the RYU controller with the simple_switch_13 app:

```bash
cd ryu
./run_ryu.py ryu.app.simple_switch_13
```

Or if you want to use the spanning tree protocol:

```bash
cd ryu
./run_ryu.py ryu.app.simple_switch_stp_13
```

Leave this terminal open with the controller running.

## Experiment Scripts

### 1. Bandwidth Tests

The `run_bandwidth_tests.sh` script runs experiments with different bandwidth constraints (5Mbps, 10Mbps, 20Mbps) to collect throughput and latency data for each setting. This helps analyze how bandwidth affects gradient exchange performance.

```bash
./run_bandwidth_tests.sh
```

This script:
- Runs tests sequentially with 5, 10, and 20 Mbps bandwidth limits
- Measures the latency of each gradient exchange
- Measures throughput using iperf
- Collects results in separate directories for each bandwidth setting

### 2. TCP vs DCTCP Comparison

The project also includes a script to compare regular TCP with Data Center TCP (DCTCP) performance:

```bash
./Fat-Tree-Data-Center-Topology/Code/run_tcp_dctcp_compare.sh
```

This script:
- Runs a simulation using standard TCP and collects performance data
- Runs an identical simulation using DCTCP with ECN (Explicit Congestion Notification)
- Stores results in separate directories for comparison
- Allows analysis of how DCTCP's congestion control affects gradient exchange in data centers

### 3. Running Individual Tests

To run a single test with specific parameters:

```bash
sudo PYTHONPATH=$HOME/mininet python3 Fat-Tree-Data-Center-Topology/Code/run_sim_fat_tree.py \
  --k 4 \
  --ps-host h16 \
  --worker-host h1 \
  --csv cifar_traffic_profile.csv \
  --port 5000 \
  --iperf-port 5001 \
  --iperf-duration 10 \
  --core-bw 10mbit \
  --debug \
  --result-dir results/my_custom_test
```

### 4. Visualize Results

After running tests, you can visualize the results:

```bash
python3 visualize_results.py --result-dir results/
```

For CIFAR profile visualization:

```bash
python3 visualize_cifar_profile.py
```

## Project Structure

- `Fat-Tree-Data-Center-Topology/`: Main project code
  - `Code/`: Contains the simulation code
    - `fat_tree.py`: Fat-tree topology implementation
    - `run_sim_fat_tree.py`: Main simulation script
    - `traffic_replay.py`: Traffic replay client/server
    - `run_tcp_dctcp_compare.sh`: Script to compare TCP and DCTCP performance
- `ryu/`: RYU OpenFlow controller
- `mininet/`: Mininet network emulator
- `cifar_traffic_profile.csv`: Traffic pattern data based on CIFAR-10 training
- `run_bandwidth_tests.sh`: Script to run bandwidth experiments
- `visualize_results.py`: Script to visualize experiment results

## Troubleshooting

1. **Controller Connection Issues**: If hosts can't ping each other, make sure the RYU controller is running and accessible.

2. **Permission Issues**: Many commands require sudo privileges due to network operations.

3. **Path Issues**: If you get import errors, ensure PYTHONPATH includes the mininet directory:
   ```bash
   export PYTHONPATH=$HOME/mininet:$PYTHONPATH
   ```

4. **Clean Up**: If Mininet doesn't exit cleanly, run:
   ```bash
   sudo mn -c
   ```

5. **Multiple Controllers**: If you experience connectivity issues, check if multiple RYU controllers are running simultaneously and causing conflicts.

## Experiment Results

The experiment results are stored in specific locations:

### Results Directory Structure

```
Fat-Tree-Data-Center-Topology/Code/results/
├── bw_5mbit_new/      # Results for 5Mbps bandwidth test
│   ├── latencies.csv  # Contains batch number and latency in seconds
│   ├── throughput.csv # Contains throughput measurements in Mbps
│   └── various log files
├── bw_10mbit_new/     # Results for 10Mbps bandwidth test
├── bw_20mbit_new/     # Results for 20Mbps bandwidth test
├── tcp_10mbit/        # Results for TCP with 10Mbps bandwidth
├── dctcp_10mbit/      # Results for DCTCP with 10Mbps bandwidth
└── plots/             # Generated visualization plots and summary statistics
    ├── bandwidth_vs_latency.png
    ├── bandwidth_vs_throughput.png
    ├── tcp_vs_dctcp_latency_boxplot.png
    ├── tcp_vs_dctcp_latency_cdf.png
    ├── tcp_vs_dctcp_throughput.png
    ├── latency_stats.csv    # Summary statistics for latency
    └── throughput_stats.csv # Summary statistics for throughput
```

### Key Data Files

1. **Latency Data**: 
   - Each experiment directory contains a `latencies.csv` file with columns for batch number and latency in seconds
   - The most complete data is in the `bw_5mbit_new/`, `tcp_10mbit/`, and `dctcp_10mbit/` directories

2. **Throughput Data**:
   - Each experiment directory contains a `throughput.csv` file with measurements from iperf
   - Format: `metric,value` where the value is in Mbps

3. **Summary Statistics**:
   - `plots/latency_stats.csv`: Contains mean, median, std dev, min, max, and 95th percentile for latency measurements
   - `plots/throughput_stats.csv`: Contains average throughput for each test configuration

The visualization script (`visualize_results.py`) reads these data files directly from the results directory, processes them, and generates plots in the `plots/` subdirectory. When running the visualization script, it will tell you exactly which files it is using and where it's saving the output. 