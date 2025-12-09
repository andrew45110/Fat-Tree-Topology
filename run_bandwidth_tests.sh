#!/bin/bash

# Function to run a single bandwidth test
run_bw_test() {
    BW=$1
    echo "=================================================="
    echo "Running test with bandwidth: $BW Mbps"
    echo "=================================================="
    
    # Clean up Mininet
    sudo mn -c
    
    # Create results directory
    RESULT_DIR="results/bw_${BW}mbit_new"
    mkdir -p $RESULT_DIR
    
    # Run simulation with appropriate bandwidth
    sudo PYTHONPATH=$HOME/mininet python3 run_sim_fat_tree.py \
      --k 4 \
      --ps-host h16 \
      --worker-host h1 \
      --csv /home/mininet/cifar_traffic_profile.csv \
      --port 5000 \
      --iperf-port 5001 \
      --iperf-duration 10 \
      --core-bw ${BW}mbit \
      --debug \
      --result-dir $RESULT_DIR
    
    # Process latency data if not done automatically
    if [ ! -f "$RESULT_DIR/latencies.csv" ] || [ ! -s "$RESULT_DIR/latencies.csv" ]; then
        echo "Processing latency data..."
        sudo python3 parse_latency.py
        [ -f "latencies.csv" ] && sudo cp latencies.csv $RESULT_DIR/
    fi
    
    # Create throughput.csv if not done automatically
    if [ ! -f "$RESULT_DIR/throughput.csv" ] || [ ! -s "$RESULT_DIR/throughput.csv" ]; then
        echo "Creating throughput data..."
        if [ -f "iperf_client.log" ]; then
            MBPS=$(grep "Mbits/sec" iperf_client.log | awk '{print $7}')
            if [ ! -z "$MBPS" ]; then
                echo "metric,value" > $RESULT_DIR/throughput.csv
                echo "throughput_mbps,$MBPS" >> $RESULT_DIR/throughput.csv
            fi
        fi
    fi
    
    # Copy any remaining logs
    for f in h1_client.log h16_server.log iperf_client.log iperf_server.log ping.log; do
        if [ -f "$f" ]; then
            sudo cp $f $RESULT_DIR/
        fi
    done
    
    echo "Test completed for $BW Mbps. Results in $RESULT_DIR"
    echo ""
}

# Run tests with different bandwidths
run_bw_test 5
sleep 5
run_bw_test 10
sleep 5
run_bw_test 20

echo "All bandwidth tests completed!" 