#!/usr/bin/env bash
declare -A COREBW=( [baseline]=10 [core20]=20 [dctcp]=10 [smallbuf]=10 [compress]=10 )
declare -A QDISC=( [baseline]=fifo [core20]=fifo [dctcp]=dctcp [smallbuf]=tbf [compress]=fifo )
declare -A ECN=( [baseline]=off [core20]=off [dctcp]=on [smallbuf]=off [compress]=off )
declare -A COMP=( [baseline]=none [core20]=none [dctcp]=none [smallbuf]=none [compress]=4x )

mkdir -p results
for cfg in baseline core20 dctcp smallbuf compress; do
  echo "=== $cfg ==="
  sudo mn -c

  # Start fat‑tree with run_sim_fat_tree.py, passing in flags
  # (Assume run_sim_fat_tree.py reads env vars or cmdline flags for core bw, qdisc, ecn, comp)
  CORE_BW=${COREBW[$cfg]} QDISC=${QDISC[$cfg]} ECN=${ECN[$cfg]} COMP_RATIO=${COMP[$cfg]} \
  sudo python3 run_sim_fat_tree.py \
    --k 4 \
    --ps-host h16 \
    --worker-host h1 \
    --csv /home/mininet/cifar_traffic_profile${COMP_RATIO}.csv \
    --port 5000 \
    --iperf-port 5001 \
    --iperf-duration 10 \
    --core-bw $CORE_BW \
    --qdisc $QDISC \
    --ecn $ECN \
    > results/${cfg}.log 2>&1

  # Move all generated CSVs/logs into subfolder
  mv latencies.csv throughput.csv ping_stats.csv link_stats.csv results/${cfg}/
done
