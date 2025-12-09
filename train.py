#!/home/mininet/torch-env/bin/python
"""
train.py: Distributed CIFAR-10 training using PyTorch DDP over Mininet
Reverted to real CIFAR-10 + ResNet
"""
import os
import time
import argparse
import torch
import torch.distributed as dist
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torch.utils.data.distributed import DistributedSampler
from torchvision import datasets, transforms, models

def main():
    parser = argparse.ArgumentParser(
        description="Distributed CIFAR-10 Training with DDP"
    )
    parser.add_argument('--rank',        type=int,   required=True, help='Rank of this process')
    parser.add_argument('--world_size',  type=int,   required=True, help='Total number of processes')
    parser.add_argument('--master_addr', type=str,   required=True, help='IP of rank 0 (master)')
    parser.add_argument('--master_port', type=int,   required=True, help='Port for initialization')
    parser.add_argument('--epochs',      type=int,   default=5,    help='Number of epochs')
    parser.add_argument('--batch_size',  type=int,   default=64,   help='Batch size per process')
    args = parser.parse_args()

    # Debug: received arguments
    print(
        f"DEBUG: rank={args.rank}, world_size={args.world_size}, "
        f"master_addr={args.master_addr}, master_port={args.master_port}",
        flush=True
    )

    # Set environment variables for Gloo
    os.environ['MASTER_ADDR'] = args.master_addr
    os.environ['MASTER_PORT'] = str(args.master_port)
    os.environ['GLOO_SOCKET_IFNAME'] = f"h{args.rank+1}-eth0"

    # Initialize process group
    init_method = f"tcp://{args.master_addr}:{args.master_port}"
    dist.init_process_group(
        backend='gloo',
        init_method=init_method,
        rank=args.rank,
        world_size=args.world_size
    )

    if args.rank == 0:
        print("Rank 0 initialized; training starting...", flush=True)
        print(
            f">>> Entering training loop for {args.epochs} epochs", flush=True
        )

    # Data transforms and dataset
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465),
                             (0.2023, 0.1994, 0.2010)),
    ])
    train_dataset = datasets.CIFAR10(
        root='/home/mininet/data',
        train=True,
        download=False,
        transform=transform
    )
    sampler = DistributedSampler(
        train_dataset, num_replicas=args.world_size, rank=args.rank
    )
    loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        sampler=sampler,
        num_workers=2,
        pin_memory=True
    )

    # Model, criterion, optimizer
    model = models.resnet18(num_classes=10)
    model = nn.parallel.DistributedDataParallel(model)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(
        model.parameters(), lr=0.01, momentum=0.9
    )

    # Training loop
    start_time = time.time()
    for epoch in range(args.epochs):
        if args.rank == 0:
            print(f"--- Starting epoch {epoch+1}/{args.epochs}", flush=True)
        sampler.set_epoch(epoch)
        total_loss = 0.0
        for inputs, targets in loader:
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        if args.rank == 0:
            avg_loss = total_loss / len(loader)
            print(f"Epoch {epoch+1}, Avg Loss: {avg_loss:.4f}", flush=True)

    # Synchronize and finalize
    dist.barrier()
    if args.rank == 0:
        elapsed = time.time() - start_time
        print(f"All done! Total training time: {elapsed:.2f}s", flush=True)
    dist.destroy_process_group()

if __name__ == '__main__':
    main()
