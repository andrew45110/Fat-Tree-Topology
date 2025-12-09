#!/bin/bash

# Run TCP test
echo "==================================================="
echo "Running standard TCP test with 10 Mbps bandwidth"
echo "==================================================="

# Clean up Mininet
sudo mn -c

# Create results directory
TCP_DIR="results/tcp_10mbit"
mkdir -p $TCP_DIR

# Run simulation with TCP
sudo PYTHONPATH=$HOME/mininet python3 run_sim_fat_tree.py \
  --k 4 \
  --ps-host h16 \
  --worker-host h1 \
  --csv /home/mininet/cifar_traffic_profile.csv \
  --port 5000 \
  --iperf-port 5001 \
  --iperf-duration 10 \
  --core-bw 10mbit \
  --debug \
  --result-dir $TCP_DIR

# Process latency data
sudo python3 parse_latency.py
[ -f "latencies.csv" ] && sudo cp latencies.csv $TCP_DIR/

# Create throughput.csv if needed
if [ -f "iperf_client.log" ]; then
    MBPS=$(grep "Mbits/sec" iperf_client.log | awk '{print $7}')
    if [ ! -z "$MBPS" ]; then
        echo "metric,value" > $TCP_DIR/throughput.csv
        echo "throughput_mbps,$MBPS" >> $TCP_DIR/throughput.csv
    fi
fi

# Copy logs
for f in h1_client.log h16_server.log iperf_client.log iperf_server.log ping.log; do
    if [ -f "$f" ]; then
        sudo cp $f $TCP_DIR/
    fi
done

echo "TCP test completed. Results in $TCP_DIR"
echo ""

# Wait before running next test
sleep 5

# Run DCTCP test
echo "==================================================="
echo "Running DCTCP test with 10 Mbps bandwidth"
echo "==================================================="

# Clean up Mininet
sudo mn -c

# Create results directory
DCTCP_DIR="results/dctcp_10mbit"
mkdir -p $DCTCP_DIR

# Run simulation with DCTCP
sudo PYTHONPATH=$HOME/mininet python3 run_sim_fat_tree.py \
  --k 4 \
  --ps-host h16 \
  --worker-host h1 \
  --csv /home/mininet/cifar_traffic_profile.csv \
  --port 5000 \
  --iperf-port 5001 \
  --iperf-duration 10 \
  --core-bw 10mbit \
  --qdisc dctcp \
  --ecn \
  --debug \
  --result-dir $DCTCP_DIR

# Process latency data
sudo python3 parse_latency.py
[ -f "latencies.csv" ] && sudo cp latencies.csv $DCTCP_DIR/

# Create throughput.csv if needed
if [ -f "iperf_client.log" ]; then
    MBPS=$(grep "Mbits/sec" iperf_client.log | awk '{print $7}')
    if [ ! -z "$MBPS" ]; then
        echo "metric,value" > $DCTCP_DIR/throughput.csv
        echo "throughput_mbps,$MBPS" >> $DCTCP_DIR/throughput.csv
    fi
fi

# Copy logs
for f in h1_client.log h16_server.log iperf_client.log iperf_server.log ping.log; do
    if [ -f "$f" ]; then
        sudo cp $f $DCTCP_DIR/
    fi
done

echo "DCTCP test completed. Results in $DCTCP_DIR"
echo ""

echo "All tests completed!" 