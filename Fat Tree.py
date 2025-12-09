from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel

class FatTreeTopo(Topo):
    def __init__(self, k=4):
        super(FatTreeTopo, self).__init__()
        self.k = k
        self.pod = k
        self.core_switches = []
        self.agg_switches = []
        self.edge_switches = []
        self.host_list = []  # Avoid conflict with Topo.hosts()

        self.build_topology()

    def build_topology(self):
        # Core Layer
        core_count = (self.k // 2) ** 2
        for i in range(core_count):
            sw = self.addSwitch(f'c{i+1}', protocols='OpenFlow13')
            self.core_switches.append(sw)

        # Pods (Aggregation + Edge)
        for pod in range(self.pod):
            # Aggregation switches
            agg_switches = []
            for i in range(self.k // 2):
                sw_id = len(self.core_switches) + pod * (self.k // 2) + i + 1
                sw = self.addSwitch(f'a{sw_id}', protocols='OpenFlow13')
                self.agg_switches.append(sw)
                agg_switches.append(sw)

            # Edge switches
            edge_switches = []
            for i in range(self.k // 2):
                sw_id = len(self.core_switches) + len(self.agg_switches) + pod * (self.k // 2) + i + 1
                sw = self.addSwitch(f'e{sw_id}', protocols='OpenFlow13')
                self.edge_switches.append(sw)
                edge_switches.append(sw)

            # Aggregation ↔ Edge links
            for agg in agg_switches:
                for edge in edge_switches:
                    self.addLink(agg, edge, bw=10)

            # Core ↔ Aggregation links (connect to all pods)
            for i, core_sw in enumerate(self.core_switches):
                pod_offset = (i // (self.k // 2)) % (self.k // 2)
                agg_sw = agg_switches[pod_offset]
                self.addLink(core_sw, agg_sw, bw=10)

        # Hosts (2 per edge switch)
        for i, edge_sw in enumerate(self.edge_switches):
            for j in range(2):
                host = self.addHost(f'h{i*2 + j + 1}')
                self.host_list.append(host)
                self.addLink(edge_sw, host, bw=10)

def run_fat_tree():
    topo = FatTreeTopo(k=4)
    net = Mininet(
        topo=topo,
        controller=lambda name: RemoteController(name, ip='127.0.0.1', port=6633),
        link=TCLink,
        autoSetMacs=True
    )
    net.start()
    print("Fat-Tree network started!")
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run_fat_tree()
