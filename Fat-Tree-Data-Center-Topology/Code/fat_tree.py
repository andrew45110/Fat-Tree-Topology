from mininet.topo import Topo
from mininet.link import TCLink
from mininet.node import OVSKernelSwitch, RemoteController

# Global DPIDs counter for unique switch IDs
def new_dpid():
    if not hasattr(new_dpid, 'counter'):
        new_dpid.counter = 0x100
    new_dpid.counter += 1
    return f'{new_dpid.counter:016x}'

class MyTopo(Topo):
    """
    Parameterized k-ary fat-tree topology.

    Attributes:
        k (int): number of pods
        L1, L2, L3 (int): number of switches in core, aggregation, and edge layers respectively
    """
    def __init__(self, k=4):
        super(MyTopo, self).__init__()
        self.k = k
        pods = self.k

        # Number of switches per layer
        L1 = (pods // 2) ** 2
        L2 = pods * (pods // 2)
        L3 = L2

        # Lists to hold switch references
        core_switches = []
        agg_switches  = []
        edge_switches = []

        # Core layer: c1…cL1
        for i in range(L1):
            name = f'c{i+1}'
            sw = self.addSwitch(name, dpid=new_dpid(), protocols='OpenFlow13')
            core_switches.append(sw)

        # Aggregation layer: a{L1+1}…a{L1+L2}
        for i in range(L2):
            name = f'a{L1 + i + 1}'
            sw = self.addSwitch(name, dpid=new_dpid(), protocols='OpenFlow13')
            agg_switches.append(sw)

        # Edge layer: e{L1+L2+1}…e{L1+L2+L3}
        for i in range(L3):
            name = f'e{L1 + L2 + i + 1}'
            sw = self.addSwitch(name, dpid=new_dpid(), protocols='OpenFlow13')
            edge_switches.append(sw)

        # Links: core → aggregation
        for i, c_sw in enumerate(core_switches):
            start = i % (pods // 2)
            for j in range(pods):
                a_idx = start + j * (pods // 2)
                self.addLink(c_sw, agg_switches[a_idx], bw=10)

        # Links: aggregation → edge
        for i, a_sw in enumerate(agg_switches):
            group = i // (pods // 2)
            for j in range(pods // 2):
                e_idx = group * (pods // 2) + j
                self.addLink(a_sw, edge_switches[e_idx], bw=10)

        # Links: edge → hosts (2 hosts per edge switch)
        host_id = 1
        for e_sw in edge_switches:
            for _ in range(2):
                h_name = f'h{host_id}'
                host = self.addHost(h_name)
                self.addLink(e_sw, host, bw=10)
                host_id += 1

# Allow `mn --custom fat_tree.py --topo=mytopo,k=8` style usage
topos = {'mytopo': (lambda k=4: MyTopo(k))}

