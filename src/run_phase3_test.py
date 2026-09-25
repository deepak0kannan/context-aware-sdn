#!/usr/bin/env python3
"""
Phase 3 Verification Script: Live SDN Monitoring & Feature Extraction
Tests Ryu SDNMonitorController in real-time under traffic:
- Launches Ryu controller with sdn_monitor.py
- Launches Mininet network
- Generates traffic from h1 to h6
- Verifies feature extraction output in CSV and console
"""

import sys
import os
import time
import subprocess
import csv

from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.link import TCLink
from mininet.log import setLogLevel, info

sys.path.append(os.path.join(os.path.dirname(__file__), 'topology'))
from topo_multi_path import MultiPathTopo


def run_phase3_verification():
    setLogLevel('info')
    data_file = os.path.expanduser("~/sdn_project/data/sdn_features.csv")

    info("=== 1. Cleaning Previous Controller & Feature Log ===\n")
    os.system("killall -9 ryu-manager 2>/dev/null || true")
    if os.path.exists(data_file):
        os.remove(data_file)
    time.sleep(1)

    info("=== 2. Starting Ryu SDNMonitorController on port 6653 ===\n")
    ryu_cmd = (
        "screen -dmS ryu_monitor /home/deeepo/ryu-env/bin/ryu-manager "
        "--ofp-tcp-listen-port 6653 --wsapi-port 8080 "
        "/home/deeepo/sdn_project/src/controller/sdn_monitor.py"
    )
    os.system(ryu_cmd)
    time.sleep(2)

    info("=== 3. Starting Mininet Multi-Path Network ===\n")
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

    h1, h6 = net.get('h1', 'h6')

    info("=== 4. Starting iperf3 Server on h6 ===\n")
    h6.cmd("pkill iperf3 || true")
    time.sleep(0.5)
    h6.cmd("iperf3 -s -D")
    time.sleep(1)

    info("=== 5. Injecting Active Traffic from h1 to h6 (10s) ===\n")
    # Send moderate UDP traffic to generate observable flow counters
    h1.cmd("iperf3 -c 10.0.0.6 -u -b 3M -t 8 &")
    
    # Wait for monitoring cycles to capture statistics
    for i in range(5):
        time.sleep(2)
        info(f"[*] Polling stats cycle {i+1}/5...\n")

    info("=== 6. Stopping Mininet Network ===\n")
    h6.cmd("pkill iperf3 || true")
    net.stop()

    info("=== 7. Validating Feature Extraction CSV Output ===\n")
    if not os.path.exists(data_file):
        info("[ERROR] Feature CSV file was not created!\n")
        return False

    with open(data_file, mode="r") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if len(rows) <= 1:
        info("[ERROR] Feature CSV has no data rows!\n")
        return False

    info(f"[OK] Successfully collected {len(rows)-1} feature sample rows.\n")
    info("\n--- Sample Extracted Feature Vectors ---\n")
    header = rows[0]
    for idx, row in enumerate(rows[1:5]):
        info(f"Sample {idx+1}:\n")
        for col_name, val in zip(header, row):
            info(f"  {col_name:18s}: {val}\n")
        info("-" * 35 + "\n")

    info("\n=========================================\n")
    info("       PHASE 3 VERIFICATION: PASSED       \n")
    info("=========================================\n")
    return True


if __name__ == "__main__":
    success = run_phase3_verification()
    sys.exit(0 if success else 1)
