#!/usr/bin/env python3
"""
traffic_replay.py

A combined server/client for replaying gradient-exchange traffic in Mininet.

Usage:
  Server mode (run on h2):
    python3 traffic_replay.py --mode server --port 5000

  Client mode (run on h1):
    python3 traffic_replay.py --mode client \
      --host <server_ip> --port 5000 \
      --csv /home/mininet/Code/cifar_traffic_profile.csv
"""

import argparse
import socket
import csv
import time
import struct
import sys
import os


def run_server(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(('0.0.0.0', port))
        s.listen(1)
        print(f"[Server] Listening on port {port}...")
        
        # Set a timeout for the accept call so we don't block forever
        s.settimeout(300)  # 5 minutes timeout
        
        try:
            conn, addr = s.accept()
            print(f"[Server] Connection from {addr}")
            conn.settimeout(60)  # Set a timeout on data reception
            try:
                while True:
                    hdr = conn.recv(8)
                    if not hdr or len(hdr) < 8:
                        if not hdr:
                            print("[Server] Connection closed by client")
                        else:
                            print(f"[Server] Received incomplete header: {len(hdr)} bytes")
                        break
                    
                    size = struct.unpack('>Q', hdr)[0]
                    t_recv = time.time()
                    print(f"[Server] Received header for {size} bytes at {t_recv:.6f}")
                    
                    remaining = size
                    chunks_received = 0
                    while remaining > 0:
                        try:
                            chunk = conn.recv(min(65536, remaining))
                            chunks_received += 1
                            if not chunk:
                                print("[Server] Connection broken while receiving data")
                                break
                            remaining -= len(chunk)
                        except socket.timeout:
                            print(f"[Server] Timeout while receiving data, {remaining} bytes left")
                            break
                    
                    t_complete = time.time()
                    print(f"[Server] Completed receiving {size-remaining} bytes (in {chunks_received} chunks) at {t_complete:.6f}")
            finally:
                conn.close()
        except socket.timeout:
            print("[Server] Timeout waiting for client connection")
        except Exception as e:
            print(f"[Server] Error during connection: {e}")
    except OSError as e:
        print(f"[Server] Could not bind to port {port}: {e}", file=sys.stderr)
    finally:
        s.close()
    print("[Server] Shut down")


def run_client(host, port, csv_file):
    print(f"[Client] Connecting to {host}:{port}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Set a timeout for connection attempts
    sock.settimeout(30)
    
    try:
        sock.connect((host, port))
        print("[Client] Connected")
        
        # Verify CSV file exists and has content
        if not os.path.exists(csv_file):
            print(f"[Client] Error: CSV file {csv_file} not found", file=sys.stderr)
            sock.close()
            return
            
        row_count = 0
        try:
            with open(csv_file, newline='') as f:
                reader = csv.DictReader(f)
                for idx, row in enumerate(reader):
                    try:
                        interval = float(row['interval_s'])
                        size = int(row['grad_bytes'])
                        
                        print(f"[Client] [{idx}] Sleeping {interval:.4f}s before sending {size} bytes")
                        time.sleep(interval)
                        
                        # send 8-byte header then payload
                        sock.sendall(struct.pack('>Q', size))
                        sock.sendall(b'\x00' * size)
                        t_send = time.time()
                        print(f"[Client] [{idx}] Sent {size} bytes at {t_send:.6f}")
                        row_count += 1
                    except (ValueError, KeyError) as e:
                        print(f"[Client] Error parsing row {idx}: {e}", file=sys.stderr)
                    except socket.error as e:
                        print(f"[Client] Socket error at row {idx}: {e}", file=sys.stderr)
                        break
        except Exception as e:
            print(f"[Client] Error reading CSV: {e}", file=sys.stderr)
        
        print(f"[Client] Processed {row_count} gradient exchanges")
    except socket.timeout:
        print(f"[Client] Timeout connecting to {host}:{port}", file=sys.stderr)
    except socket.error as e:
        print(f"[Client] Connection error: {e}", file=sys.stderr)
    finally:
        sock.close()
    print("[Client] Done sending")


def main():
    parser = argparse.ArgumentParser(description="Mininet gradient-exchange traffic replay")
    parser.add_argument('--mode', choices=['server','client'], required=True)
    parser.add_argument('--host', type=str, help="Server IP (for client mode)")
    parser.add_argument('--port', type=int, default=5000, help="Port to use")
    parser.add_argument('--csv', type=str, help="Path to traffic CSV (for client mode)")
    args = parser.parse_args()

    if args.mode == 'server':
        run_server(args.port)
    elif args.mode == 'client':
        if not args.host or not args.csv:
            print("[Error] --host and --csv are required in client mode", file=sys.stderr)
            sys.exit(1)
        run_client(args.host, args.port, args.csv)

if __name__ == '__main__':
    main()
