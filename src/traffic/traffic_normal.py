#!/usr/bin/env python3
"""
Traffic Generator: Normal Baseline Traffic
Simulates standard user browsing and intermittent API calls between hosts and server h6.
"""

import sys
import time
import random
import subprocess
import argparse


def generate_normal_traffic(target_ip="10.0.0.6", duration=30, rate="1M"):
    """
    Run intermittent iperf3 client traffic simulating realistic baseline traffic.
    """
    print(f"[*] Starting Normal Traffic generator towards {target_ip} for {duration}s...")
    start_time = time.time()
    
    while time.time() - start_time < duration:
        # Pick random duration between 3 and 7 seconds
        session_time = min(random.randint(3, 7), int(duration - (time.time() - start_time)))
        if session_time <= 0:
            break
            
        # Vary rate slightly around baseline (0.5M to 1.5M)
        actual_rate = f"{random.randint(500, 1500)}K"
        print(f"[Normal] Sending burst: {actual_rate} for {session_time}s")
        
        cmd = [
            "iperf3", "-c", target_ip,
            "-u", "-b", actual_rate,
            "-t", str(session_time),
            "-p", "5201"
        ]
        
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"[!] Error running normal traffic burst: {e}")
            
        # Idle pause between bursts (1 to 3 seconds)
        pause = random.uniform(1.0, 3.0)
        time.sleep(pause)

    print("[*] Normal Traffic generation finished.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Normal Baseline Traffic Generator")
    parser.add_argument("--target", default="10.0.0.6", help="Target server IP (default: 10.0.0.6)")
    parser.add_argument("--duration", type=int, default=30, help="Duration in seconds (default: 30)")
    parser.add_argument("--rate", default="1M", help="Target bandwidth rate")
    args = parser.parse_args()

    generate_normal_traffic(target_ip=args.target, duration=args.duration, rate=args.rate)
