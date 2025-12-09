#!/usr/bin/env python3
from mininet.net import Mininet
from mininet.node import OVSKernelSwitch, RemoteController
from mininet.link import TCLink
from mininet.log import setLogLevel, info
import time
import os
import sys

# Add the Code directory to the Python path
code_dir = os.path.expanduser('~/Fat-Tree-Data-Center-Topology/Code')
sys.path.append(code_dir)

# Try to import with absolute path if needed
if not os.path.exists(os.path.join(code_dir, 'fat_tree.py')):
    info(f"Fat tree module not found in {code_dir}\n")
    sys.exit(1)
else:
    info(f"Found fat_tree.py in {code_dir}\n")

# Import the topology
from fat_tree import MyTopo

def test_fattree_bandwidth(bw_mbit):
    """Test bandwidth in a fat-tree topology with specified core bandwidth"""
    topo = MyTopo(k=4)
    net = Mininet(topo=topo, 
                  controller=RemoteController, 
                  switch=OVSKernelSwitch, 
                  link=TCLink,
                  autoSetMacs=True,
                  autoStaticArp=True)
    
    net.start()
    info(f"*** Fat-tree (k=4) up with {len(net.hosts)} hosts\n")
    
    # Wait for controller to set up paths
    info("*** Waiting for controller to establish paths (10s)...\n")
    time.sleep(10)
    
    # Apply bandwidth limiting only on core-to-aggregation links
    info(f"*** Applying {bw_mbit}Mbit bandwidth limit to core links\n")
    for link in net.links:
        n1, n2 = link.intf1.node, link.intf2.node
        if n1.name.startswith('a') and n2.name.startswith('c'):
            n1.cmd(f"tc qdisc replace dev {link.intf1.name} "
                  f"root tbf rate {bw_mbit}mbit burst 100kb limit 200kb")
            info(f"Applied limit on {n1.name} -> {n2.name}\n")
        elif n2.name.startswith('a') and n1.name.startswith('c'):
            n2.cmd(f"tc qdisc replace dev {link.intf2.name} "
                  f"root tbf rate {bw_mbit}mbit burst 100kb limit 200kb")
            info(f"Applied limit on {n2.name} -> {n1.name}\n")
    
    # Get hosts for testing
    h1 = net.get('h1')
    h16 = net.get('h16')
    
    # Test connectivity
    info(f"*** Testing connectivity from {h1.name} to {h16.name}\n")
    result = h1.cmd(f"ping -c 3 -W 1 {h16.IP()}")
    info(result)
    
    # Run iperf test
    info(f"*** Running iperf test between {h1.name} and {h16.name}\n")
    h16.cmd("iperf -s &")
    time.sleep(1)
    
    # Run iperf client with a longer duration
    result = h1.cmd(f"iperf -c {h16.IP()} -t 30")
    info(f"*** Iperf result:\n{result}\n")
    
    # Save result to file
    with open(f"fattree_bw_{bw_mbit}m_test.txt", "w") as f:
        f.write(result)
    
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    # Test with 20Mbit
    test_fattree_bandwidth(20) 