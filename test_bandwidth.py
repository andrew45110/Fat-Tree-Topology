#!/usr/bin/env python3
from mininet.net import Mininet
from mininet.node import Controller, OVSKernelSwitch
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel, info
import time
import os

def test_bandwidth(bw):
    """Create a simple network and test bandwidth with iperf"""
    net = Mininet(controller=Controller, switch=OVSKernelSwitch, link=TCLink, autoSetMacs=True)
    
    info('*** Adding controller\n')
    net.addController('c0')
    
    info('*** Adding hosts\n')
    h1 = net.addHost('h1')
    h2 = net.addHost('h2')
    
    info('*** Adding switch\n')
    s1 = net.addSwitch('s1')
    
    info(f'*** Creating links with {bw} Mbps bandwidth\n')
    net.addLink(h1, s1, bw=bw, delay='1ms')
    net.addLink(h2, s1, bw=bw, delay='1ms')
    
    info('*** Starting network\n')
    net.start()
    
    info('*** Testing connectivity\n')
    net.pingAll()
    
    info('*** Running iperf test\n')
    # Start iperf server
    h2.cmd('iperf -s &')
    time.sleep(1)
    
    # Run iperf client
    result = h1.cmd(f'iperf -c {h2.IP()} -t 10')
    info(f'*** Iperf result:\n{result}\n')
    
    # Extract bandwidth from result
    for line in result.split('\n'):
        if 'Mbits/sec' in line:
            info(f'*** {line.strip()}\n')
            break
    
    info('*** Stopping network\n')
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    for bw in [5, 10, 20]:
        info(f'\n*** Testing {bw} Mbps bandwidth\n')
        test_bandwidth(bw)
        time.sleep(2) 