#!/usr/bin/env python3
"""
Phase 2 Test Runner: Automated Verification of all 5 Traffic Scenarios
Runs inside the Mininet environment and executes:
1. Normal Baseline Traffic
2. Flash-Crowd Surge
3. DDoS Attack (Scapy SYN/UDP flood)
4. Slow Congestion Buildup
5. Link Failure Simulation
"""

import sys
import os
import time
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.link import TCLink
from mininet.log import setLogLevel, info

# Import our custom multi-path topology
sys.path.append(os.path.join(os.path.dirname(__file__), 'topology'))
from topo_multi_path import MultiPathTopo


def test_traffic_generators():
    setLogLevel('info')
    info("=== 1. Starting Mininet Multi-Path Network ===\n")
    topo = MultiPathTopo()
    net = Mininet(
        topo=topo,
        switch=OVSSwitch,
        controller=None,
        link=TCLink,
        autoSetMacs=True,
        autoStaticArp=True
    )
    net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6653)
    net.start()

    time.sleep(2)
    h1, h2, h3, h4, h5, h6 = net.get('h1', 'h2', 'h3', 'h4', 'h5', 'h6')
    traffic_dir = os.path.join(os.path.dirname(__file__), 'traffic')

    info("=== 2. Starting iperf3 Server Daemon on h6 ===\n")
    h6.cmd("pkill iperf3 || true")
    time.sleep(0.5)
    h6.cmd("iperf3 -s -D")
    time.sleep(1)

    results = {}

    # Test 1: Normal Traffic
    info("\n--- Testing Class 1: Normal Baseline Traffic ---\n")
    out = h1.cmd(f"python3 {traffic_dir}/traffic_normal.py --target 10.0.0.6 --duration 5")
    print(out)
    results["Normal Traffic"] = "finished" in out

    # Test 2: Flash Crowd Surge
    info("\n--- Testing Class 2: Flash-Crowd Surge ---\n")
    out = h1.cmd(f"python3 {traffic_dir}/traffic_flash_crowd.py --target 10.0.0.6 --duration 5 --clients 3")
    print(out)
    results["Flash Crowd"] = "finished" in out

    # Test 3: DDoS Attack
    info("\n--- Testing Class 3: DDoS Attack (Scapy) ---\n")
    out = h2.cmd(f"python3 {traffic_dir}/traffic_ddos.py --target 10.0.0.6 --duration 5 --pps 300")
    print(out)
    results["DDoS Attack"] = "finished" in out

    # Test 4: Slow Congestion Buildup
    info("\n--- Testing Class 4: Slow Congestion Buildup ---\n")
    out = h3.cmd(f"python3 {traffic_dir}/traffic_congestion.py --target 10.0.0.6 --duration 5 --steps 3")
    print(out)
    results["Slow Congestion"] = "finished" in out

    # Test 5: Link Failure
    info("\n--- Testing Class 5: Link Failure Simulation ---\n")
    out = os.popen(f"bash {traffic_dir}/link_failure.sh s1-eth6 3").read()
    print(out)
    results["Link Failure"] = "restored" in out

    info("\n=== 3. Stopping Mininet Network ===\n")
    h6.cmd("pkill iperf3 || true")
    net.stop()

    info("\n=========================================\n")
    info("       PHASE 2 VERIFICATION SUMMARY       \n")
    info("=========================================\n")
    all_passed = True
    for test, passed in results.items():
        status = "PASSED [OK]" if passed else "FAILED [X]"
        info(f" - {test:25s}: {status}\n")
        if not passed:
            all_passed = False

    return all_passed


if __name__ == "__main__":
    success = test_traffic_generators()
    sys.exit(0 if success else 1)
