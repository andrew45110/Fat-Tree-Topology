#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Load the CIFAR-10 gradient profile data
csv_path = '/home/mininet/cifar_traffic_profile.csv'
df = pd.read_csv(csv_path)

# Create output directory for plots
plots_dir = "cifar_profile_plots"
os.makedirs(plots_dir, exist_ok=True)

# Print basic statistics about the profile
total_records = len(df)
total_epochs = df['epoch'].max()
total_batches = df['batch'].max() + 1  # zero-indexed
mean_interval = df['interval_s'].mean()
mean_grad_size = df['grad_bytes'].mean() / 1024  # KB
median_grad_size = df['grad_bytes'].median() / 1024  # KB
min_grad_size = df['grad_bytes'].min() / 1024  # KB
max_grad_size = df['grad_bytes'].max() / 1024  # KB
total_duration = df['interval_s'].sum()

# Print summary statistics
print(f"CIFAR-10 Gradient Profile Analysis")
print(f"==================================")
print(f"Total records: {total_records}")
print(f"Epochs: {total_epochs}")
print(f"Batches per epoch: {total_batches}")
print(f"Mean interval between exchanges: {mean_interval:.6f} seconds")
print(f"Mean gradient size: {mean_grad_size:.2f} KB")
print(f"Median gradient size: {median_grad_size:.2f} KB")
print(f"Gradient size range: {min_grad_size:.2f} KB to {max_grad_size:.2f} KB")
print(f"Total profile duration: {total_duration:.2f} seconds")
print()

# 1. Gradient Size Distribution
plt.figure(figsize=(10, 6))
plt.hist(df['grad_bytes']/1024, bins=20, alpha=0.7, color='blue')
plt.xlabel('Gradient Size (KB)')
plt.ylabel('Frequency')
plt.title('Distribution of Gradient Sizes in CIFAR-10 Training')
plt.grid(True, linestyle='--', alpha=0.7)
plt.savefig(os.path.join(plots_dir, "gradient_size_distribution.png"))
print(f"Saved gradient size distribution to {os.path.join(plots_dir, 'gradient_size_distribution.png')}")

# 2. Intervals Between Gradient Exchanges
plt.figure(figsize=(10, 6))
plt.hist(df['interval_s'], bins=30, alpha=0.7, color='green')
plt.xlabel('Interval (seconds)')
plt.ylabel('Frequency')
plt.title('Distribution of Intervals Between Gradient Exchanges')
plt.grid(True, linestyle='--', alpha=0.7)
plt.savefig(os.path.join(plots_dir, "interval_distribution.png"))
print(f"Saved interval distribution to {os.path.join(plots_dir, 'interval_distribution.png')}")

# 3. Temporal Pattern of Gradient Exchanges
cumulative_time = df['interval_s'].cumsum()
plt.figure(figsize=(12, 6))
plt.scatter(cumulative_time, df['grad_bytes']/1024, alpha=0.5, s=10, c='purple')
plt.plot(cumulative_time, df['grad_bytes']/1024, alpha=0.3, linewidth=1, color='purple')
plt.xlabel('Cumulative Time (s)')
plt.ylabel('Gradient Size (KB)')
plt.title('Temporal Pattern of Gradient Exchanges in CIFAR-10 Training')
plt.grid(True, linestyle='--', alpha=0.7)
plt.savefig(os.path.join(plots_dir, "gradient_temporal_pattern.png"))
print(f"Saved temporal pattern to {os.path.join(plots_dir, 'gradient_temporal_pattern.png')}")

# 4. Gradient Size by Epoch/Batch
plt.figure(figsize=(12, 6))
for epoch in sorted(df['epoch'].unique()):
    epoch_data = df[df['epoch'] == epoch]
    plt.plot(epoch_data['batch'], epoch_data['grad_bytes']/1024, label=f'Epoch {epoch}')

plt.xlabel('Batch Number')
plt.ylabel('Gradient Size (KB)')
plt.title('Gradient Size by Batch and Epoch')
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend()
plt.savefig(os.path.join(plots_dir, "gradient_size_by_epoch.png"))
print(f"Saved gradient size by epoch to {os.path.join(plots_dir, 'gradient_size_by_epoch.png')}")

# 5. Moving Average of Gradient Size
window_size = 10
plt.figure(figsize=(12, 6))
rolling_mean = df['grad_bytes'].rolling(window=window_size).mean()/1024
plt.plot(rolling_mean, color='red')
plt.xlabel('Gradient Exchange Number')
plt.ylabel('Moving Average Gradient Size (KB)')
plt.title(f'Moving Average of Gradient Size (Window Size: {window_size})')
plt.grid(True, linestyle='--', alpha=0.7)
plt.savefig(os.path.join(plots_dir, "gradient_moving_average.png"))
print(f"Saved moving average to {os.path.join(plots_dir, 'gradient_moving_average.png')}")

print(f"\nAll visualizations saved to {plots_dir}/")
print(f"To view images in the HTTP server, visit: http://192.168.56.1:8000/{plots_dir}/") 