#!/usr/bin/env python3
"""
run_sim_fat_tree.py

Launch a k‑pod fat‑tree, apply network knobs, run a 2‑node PS workload,
and collect:
  - per‑iteration sync latency
  - aggregate throughput via iperf
  - ping RTTs
  - core switch port stats before/after

New flag:
  --auto-exit    : skip the CLI and auto‑tear down once replay is done
"""

import argparse
import csv
import os
import time
import subprocess
import shutil
from mininet.net      import Mininet
from mininet.node     import OVSKernelSwitch, RemoteController
from mininet.link     import TCLink
from mininet.cli      import CLI
from fat_tree         import MyTopo

def apply_core_rate(net, rate, tbf_limit="200kb", burst="100kb"):
    for link in net.links:
        n1, n2 = link.intf1.node, link.intf2.node
        if n1.name.startswith('a') and n2.name.startswith('c'):
            n1.cmd(f"tc qdisc replace dev {link.intf1.name} "
                   f"root tbf rate {rate} burst {burst} limit {tbf_limit}")
        elif n2.name.startswith('a') and n1.name.startswith('c'):
            n2.cmd(f"tc qdisc replace dev {link.intf2.name} "
                   f"root tbf rate {rate} burst {burst} limit {tbf_limit}")

def apply_netem(net, netem_args):
    for link in net.links:
        n1, n2 = link.intf1.node, link.intf2.node
        if n1.name.startswith('a') and n2.name.startswith('c'):
            n1.cmd(f"tc qdisc replace dev {link.intf1.name} "
                   f"root netem {netem_args}")
        elif n2.name.startswith('a') and n1.name.startswith('c'):
            n2.cmd(f"tc qdisc replace dev {link.intf2.name} "
                   f"root netem {netem_args}")

def compute_total_runtime(csv_path, margin=5.0):
    """Sum up all interval_s in the CSV, plus a safety margin (seconds)."""
    total = 0.0
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += float(row['interval_s'])
    return total + margin

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--k',             type=int,   default=4)
    p.add_argument('--csv',           type=str,   required=True)
    p.add_argument('--ps-host',       type=str,   default='h16')
    p.add_argument('--worker-host',   type=str,   default='h1')
    p.add_argument('--port',          type=int,   default=5000)
    p.add_argument('--iperf-port',    type=int,   default=5001)
    p.add_argument('--iperf-duration',type=int,   default=10)
    p.add_argument('--core-bw',       type=str,   default=None)
    p.add_argument('--qdisc',         choices=['fifo','tbf','netem','dctcp'],
                   default='fifo')
    p.add_argument('--netem-args',    type=str,   default=None)
    p.add_argument('--ecn',           action='store_true')
    p.add_argument('--auto-exit',     action='store_true',
                   help='Skip CLI and auto‑tear down after replay')
    p.add_argument('--result-dir',    type=str,   default=None,
                   help='Directory to store results')
    p.add_argument('--debug',         action='store_true',
                   help='Enable verbose debugging output')
    args = p.parse_args()

    # Create result directory based on bandwidth if not specified
    if args.result_dir is None:
        if args.core_bw:
            args.result_dir = f"results/bw_{args.core_bw.replace('mbit', 'mbit').replace('Mbit', 'mbit')}"
        else:
            args.result_dir = "results/default"
    
    # Create the result directory if it doesn't exist
    os.makedirs(args.result_dir, exist_ok=True)
    
    # Save command parameters to a log file
    with open(os.path.join(args.result_dir, "sim.log"), "w") as f:
        f.write(f"Simulation parameters:\n")
        f.write(f"  k: {args.k}\n")
        f.write(f"  csv: {args.csv}\n")
        f.write(f"  ps-host: {args.ps_host}\n")
        f.write(f"  worker-host: {args.worker_host}\n")
        f.write(f"  core-bw: {args.core_bw}\n")
        f.write(f"  qdisc: {args.qdisc}\n")
        f.write(f"  ecn: {args.ecn}\n")
        f.write(f"  netem-args: {args.netem_args}\n")
        f.write(f"  auto-exit: {args.auto_exit}\n")
        f.write(f"  debug: {args.debug}\n")

    topo = MyTopo(k=args.k)
    net  = Mininet(topo=topo,
                   controller=RemoteController,
                   switch=OVSKernelSwitch,
                   link=TCLink,
                   autoSetMacs=True,
                   autoStaticArp=True)
    net.start()
    print(f"*** Fat-tree (k={args.k}) up with {len(net.hosts)} hosts")

    # Wait for the controller to set up paths (important!)
    print("*** Waiting for controller to establish paths (10s)...")
    time.sleep(10)
    
    # Debug: Run pingall to verify connectivity
    if args.debug:
        print("*** Running pingall to verify connectivity")
        net.pingAll()
    
    # ECN / DCTCP
    if args.ecn or args.qdisc == 'dctcp':
        print("*** Enabling ECN/DCTCP")
        os.system("ovs-vsctl set Open_vSwitch . other_config:ecn=true")
        for node in (net.get(args.ps_host), net.get(args.worker_host)):
            node.cmd("sysctl -w net.ipv4.tcp_ecn=1")
            node.cmd("sysctl -w net.ipv4.tcp_congestion_control=dctcp")

    # Core rate‑limit
    if args.qdisc in ('tbf','fifo') and args.core_bw:
        print(f"*** Applying TBF rate={args.core_bw}")
        apply_core_rate(net, args.core_bw)

    # Netem
    if args.qdisc == 'netem' and args.netem_args:
        print(f"*** Applying netem ({args.netem_args})")
        apply_netem(net, args.netem_args)

    # Get host references
    ps = net.get(args.ps_host)
    w = net.get(args.worker_host)
    ps_ip = ps.IP()
    
    # Debug: Verify connectivity between worker and PS
    print(f"*** Testing connectivity from {args.worker_host} to {args.ps_host}")
    ping_result = w.cmd(f"ping -c 3 -W 1 {ps_ip}")
    with open(os.path.join(args.result_dir, "pre_ping.log"), "w") as f:
        f.write(ping_result)
    
    if "0% packet loss" not in ping_result:
        print(f"WARNING: Ping test failed between {args.worker_host} and {args.ps_host}")
        print("*** Trying to fix connectivity issues...")
        
        # Attempt to fix connectivity by pinging all hosts
        print("*** Pinging all hosts to establish flows")
        net.pingAll()
        
        # Check again
        ping_result = w.cmd(f"ping -c 3 -W 1 {ps_ip}")
        if "0% packet loss" not in ping_result:
            print(f"ERROR: Still cannot ping between {args.worker_host} and {args.ps_host}")
            print("*** Consider checking your controller or network configuration")
            # Continue anyway to see if other parts work
        else:
            print("*** Connectivity fixed!")

    # Start PS server - adding extra debugging
    print(f"*** Starting PS on {args.ps_host} at {ps_ip}:{args.port}")
    ps.cmd(f"python3 traffic_replay.py --mode server --port {args.port} "
           f"> {args.ps_host}_server.log 2>&1 &")
    
    # Debug: Give the server a moment to start
    time.sleep(2)
    
    # Verify server is running
    ps_listening = ps.cmd(f"netstat -tuln | grep {args.port}")
    if str(args.port) not in ps_listening:
        print(f"WARNING: Server not listening on port {args.port}")
        print("*** Server process status:")
        print(ps.cmd("ps aux | grep traffic_replay"))
    else:
        print(f"*** Server confirmed listening on port {args.port}")

    # Start worker client with debug logging
    print(f"*** Launching worker {args.worker_host} -> PS {ps_ip}:{args.port}")
    w.cmd(f"python3 traffic_replay.py --mode client "
          f"--host {ps_ip} --port {args.port} --csv {args.csv} "
          f"> {args.worker_host}_client.log 2>&1 &")

    # Iperf
    print(f"*** Starting iperf on {args.ps_host}:{args.iperf_port}")
    ps.cmd(f"iperf -s -p {args.iperf_port} > iperf_server.log 2>&1 &")
    print(f"*** Running iperf client on {args.worker_host}")
    w.cmd(f"iperf -c {ps_ip} -p {args.iperf_port} "
          f"-t {args.iperf_duration} > iperf_client.log 2>&1 &")

    # Core stats before
    print("*** Dumping core stats (before)")
    for sw in net.switches:
        if sw.name.startswith('c'):
            data = sw.cmd(f"ovs-ofctl dump-ports {sw.name}")
            with open(f"{sw.name}_stats_before.log","w") as f:
                f.write(data)

    if args.auto_exit:
        # compute how long to wait for the traffic replay to finish
        wait = compute_total_runtime(args.csv)
        print(f"*** Auto‑exit mode: sleeping {wait:.1f}s…")
        time.sleep(wait)
    else:
        print("*** Network is ready. Enter 'exit' when done.")
        CLI(net)

    # Check if client process completed successfully
    print("*** Checking client/server status")
    client_status = w.cmd("ps aux | grep traffic_replay | grep -v grep")
    if client_status:
        print("*** Client is still running, checking logs")
    else:
        print("*** Client process has finished")
    
    server_status = ps.cmd("ps aux | grep traffic_replay | grep -v grep")
    if server_status:
        print("*** Server is still running")
    else:
        print("*** Server process has finished")
    
    # Core stats after
    print("*** Dumping core stats (after)")
    for sw in net.switches:
        if sw.name.startswith('c'):
            data = sw.cmd(f"ovs-ofctl dump-ports {sw.name}")
            with open(f"{sw.name}_stats_after.log","w") as f:
                f.write(data)

    # Ping
    print(f"*** Pinging from {args.worker_host} to PS {ps_ip}")
    ping_out = w.cmd(f"ping -c 20 {ps_ip}")
    with open("ping.log","w") as f:
        f.write(ping_out)

    # Parse latency data
    print("*** Parsing latency data")
    if os.path.exists(f"{args.worker_host}_client.log") and os.path.getsize(f"{args.worker_host}_client.log") > 0:
        try:
            subprocess.run(["python3", "parse_latency.py"], check=True)
            print("*** Latency data processed successfully")
        except subprocess.CalledProcessError:
            print("*** Error processing latency data")
    else:
        print("*** Client log is empty or missing, cannot process latency data")
        # Create an empty latencies.csv to avoid errors later
        with open("latencies.csv", "w") as f:
            f.write("batch,latency_s\n")

    # Parse iperf for throughput
    print("*** Extracting throughput from iperf")
    with open("throughput.csv", "w") as out:
        out.write("metric,value\n")
        if os.path.exists("iperf_client.log") and os.path.getsize("iperf_client.log") > 0:
            try:
                with open("iperf_client.log", "r") as f:
                    for line in f:
                        if "Bandwidth" in line:
                            parts = line.split()
                            mbps = [p for p in parts if "Mbits/sec" in p]
                            if mbps:
                                out.write(f"throughput_mbps,{mbps[0].split()[0]}\n")
                                break
            except Exception as e:
                print(f"*** Error parsing iperf data: {e}")
                out.write(f"throughput_mbps,error\n")
        else:
            print("*** Iperf client log is empty or missing")
            out.write(f"throughput_mbps,missing\n")

    # Move all log files to the result directory
    print(f"*** Moving logs to {args.result_dir}")
    log_files = [
        f"{args.worker_host}_client.log", 
        f"{args.ps_host}_server.log",
        "iperf_client.log", 
        "iperf_server.log", 
        "ping.log", 
        "latencies.csv",
        "throughput.csv",
        "pre_ping.log"
    ]
    
    # Add core switch stats logs
    for sw in net.switches:
        if sw.name.startswith('c'):
            log_files.append(f"{sw.name}_stats_before.log")
            log_files.append(f"{sw.name}_stats_after.log")
    
    # Move files that exist
    for file in log_files:
        if os.path.exists(file):
            shutil.copy2(file, os.path.join(args.result_dir, file))
        else:
            print(f"Warning: {file} not found")

    net.stop()
    print(f"*** Done; logs saved to {args.result_dir}.")

if __name__ == '__main__':
    main()
