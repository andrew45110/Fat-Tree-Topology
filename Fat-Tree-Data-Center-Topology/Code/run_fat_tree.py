#!/usr/bin/env python3
"""
run_fat_tree.py: Launch a k‑ary fat‑tree and run train.py on every host.
"""
import argparse
from mininet.net import Mininet
from mininet.node import OVSKernelSwitch, RemoteController
from mininet.link import TCLink
from mininet.cli  import CLI
from fat_tree    import MyTopo

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--k',          type=int, default=2,     help='pods in fat-tree (2→2 hosts)')
    p.add_argument('--master_port',type=int, default=12345, help='port for rank 0')
    p.add_argument('--epochs',     type=int, default=2,     help='epochs (smoke‑test)')
    p.add_argument('--batch_size', type=int, default=32,    help='batch size')
    args = p.parse_args()

    world_size = args.k**3 // 4   # for k=2 → 2 hosts
    topo       = MyTopo(k=args.k)
    net        = Mininet(topo=topo,
                         controller=RemoteController,
                         switch=OVSKernelSwitch,
                         link=TCLink,
                         autoSetMacs=True,
                         autoStaticArp=True)
    net.start()

    print(f"Iperf h1<->h2 on k={args.k} fat-tree")
    net.iperf((net.hosts[0], net.hosts[1]))

    master_ip = net.get('h1').IP()
    for rank in range(world_size):
        host = f'h{rank+1}'
        cmd  = (
            f"/home/mininet/torch-env/bin/python /home/mininet/train.py "
            f"--rank {rank} --world_size {world_size} "
            f"--master_addr {master_ip} --master_port {args.master_port} "
            f"--epochs {args.epochs} --batch_size {args.batch_size} "
            f"> /home/mininet/{host}.log 2>&1 &"
        )
        print(f"Launching rank={rank} on {host}")
        net.get(host).cmd(cmd)

    CLI(net)
    net.stop()

if __name__ == '__main__':
    main()
