#!/usr/bin/env python3
"""
Traffic Generator: Slow Congestion Buildup
Simulates progressive bandwidth saturation (e.g. ISP evening peak load).
Key characteristics:
- Gradual utilization increase over time (ramping step-by-step from 2 Mbps to 9.5 Mbps)
- Legitimate packet composition and normal packet sizes
- Steady queue delay escalation leading to buffer fullness before packet drops
"""

import sys
import time
import subprocess
import argparse


def generate_slow_congestion(target_ip="10.0.0.6", duration=30, steps=5):
    """
    Ramp up traffic linearly across multiple stages to simulate gradual network congestion.
    """
    print(f"[*] Starting Slow Congestion Buildup towards {target_ip} for {duration}s across {steps} ramp stages...")
    start_time = time.time()
    step_duration = max(1, int(duration / steps))
    
    # Ramp from 2 Mbps up to 9.5 Mbps (approaching the 10 Mbps core bottleneck)
    rates = ["2M", "4M", "6M", "8M", "9.5M"]
    
    for i, rate in enumerate(rates[:steps]):
        if time.time() - start_time >= duration:
            break
            
        print(f"[Congestion Stage {i+1}/{steps}] Injected load rate: {rate} for {step_duration}s")
        cmd = [
            "iperf3", "-c", target_ip,
            "-u", "-b", rate,
            "-t", str(step_duration),
            "-p", "5201"
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"[!] Error injecting congestion stage {i+1}: {e}")

    print("[*] Slow Congestion Buildup simulation finished.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Slow Congestion Buildup Traffic Generator")
    parser.add_argument("--target", default="10.0.0.6", help="Target server IP (default: 10.0.0.6)")
    parser.add_argument("--duration", type=int, default=30, help="Total duration in seconds (default: 30)")
    parser.add_argument("--steps", type=int, default=5, help="Number of ramp stages (default: 5)")
    args = parser.parse_args()

    generate_slow_congestion(target_ip=args.target, duration=args.duration, steps=args.steps)
