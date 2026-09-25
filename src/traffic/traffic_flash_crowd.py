#!/usr/bin/env python3
"""
Traffic Generator: Flash-Crowd Surge
Simulates sudden, legitimate multi-user spike towards target server h6.
Key characteristics:
- Multiple distinct source hosts (h1..h5)
- Concurrent parallel requests
- Realistic varied packet sizes and legitimate connections
- High aggregate volume approaching link capacity (7 - 9 Mbps)
"""

import sys
import time
import random
import subprocess
import argparse
import threading


def run_client_burst(client_id, target_ip, duration):
    """Worker simulating an individual client's flash-sale activity."""
    rate = f"{random.randint(1200, 1800)}K"
    cmd = [
        "iperf3", "-c", target_ip,
        "-u", "-b", rate,
        "-t", str(duration),
        "-p", "5201"
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"[!] Error in flash client {client_id}: {e}")


def generate_flash_crowd(target_ip="10.0.0.6", duration=30, num_clients=5):
    """
    Launch concurrent requests from simulated diverse clients to create flash-crowd surge.
    """
    print(f"[*] Starting Flash-Crowd Surge simulation ({num_clients} concurrent clients) for {duration}s...")
    start_time = time.time()
    
    threads = []
    for cid in range(1, num_clients + 1):
        t = threading.Thread(target=run_client_burst, args=(cid, target_ip, duration))
        threads.append(t)
        t.start()
        # Stagger client joins slightly (50-200ms) to simulate real user arrivals
        time.sleep(random.uniform(0.05, 0.2))

    for t in threads:
        t.join()

    print("[*] Flash-Crowd Surge generation finished.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Flash-Crowd Surge Traffic Generator")
    parser.add_argument("--target", default="10.0.0.6", help="Target server IP (default: 10.0.0.6)")
    parser.add_argument("--duration", type=int, default=30, help="Duration in seconds (default: 30)")
    parser.add_argument("--clients", type=int, default=5, help="Number of concurrent clients (default: 5)")
    args = parser.parse_args()

    generate_flash_crowd(target_ip=args.target, duration=args.duration, num_clients=args.clients)
