#!/usr/bin/env python3
"""
Phase 4: Automated Dataset Generation & Labeling Engine
Orchestrates automated multi-scenario runs in Mininet, collecting and labeling
flow-level and port-level feature vectors across all 5 network classes:
1. normal
2. flash_crowd
3. ddos
4. slow_congestion
5. link_failure
"""

import sys
import os
import time
import subprocess
import pandas as pd

from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.link import TCLink
from mininet.log import setLogLevel, info

# Path setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(BASE_DIR, 'topology'))
from topo_multi_path import MultiPathTopo


def set_active_label(label):
    """Dynamically set the ground-truth label read by SDNMonitorController."""
    with open("/tmp/active_label.txt", "w") as f:
        f.write(label + "\n")
    info(f"\n=======================================================\n")
    info(f"[DATASET] Set active ground-truth label -> {label.upper()}\n")
    info(f"=======================================================\n")


def generate_dataset(rounds=2, scenario_duration=25):
    """
    Generate balanced dataset by running repeated iterations of all scenarios.
    """
    setLogLevel('info')
    dataset_file = os.path.expanduser("~/sdn_project/data/sdn_dataset.csv")
    traffic_dir = os.path.join(BASE_DIR, 'traffic')

    info("=== Step 1: Cleaning previous state & starting Ryu Controller ===\n")
    os.system("killall -9 ryu-manager 2>/dev/null || true")
    os.system("sudo mn -c > /dev/null 2>&1")
    time.sleep(1)

    # Launch Ryu SDNMonitorController in background
    ryu_cmd = (
        "screen -dmS ryu_dataset /home/deeepo/ryu-env/bin/ryu-manager "
        "--ofp-tcp-listen-port 6653 --wsapi-port 8080 "
        f"{BASE_DIR}/controller/sdn_monitor.py"
    )
    os.system(ryu_cmd)
    time.sleep(2)

    info("=== Step 2: Initializing Mininet Multi-Path Network ===\n")
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

    info("=== Step 3: Starting iperf3 Server on Target h6 ===\n")
    h6.cmd("pkill iperf3 || true")
    time.sleep(0.5)
    h6.cmd("iperf3 -s -D")
    time.sleep(1)

    scenarios = ["normal", "flash_crowd", "ddos", "slow_congestion", "link_failure"]

    for r in range(1, rounds + 1):
        info(f"\n>>>>>>>>>>>> STARTING DATASET COLLECTION ROUND {r}/{rounds} <<<<<<<<<<<<\n")

        for sc in scenarios:
            set_active_label(sc)
            time.sleep(2)  # Settle time

            if sc == "normal":
                info(f"[*] Running Normal traffic for {scenario_duration}s...\n")
                h1.cmd(f"python3 {traffic_dir}/traffic_normal.py --target 10.0.0.6 --duration {scenario_duration}")

            elif sc == "flash_crowd":
                info(f"[*] Running Flash-Crowd surge from h1..h5 for {scenario_duration}s...\n")
                h1.cmd(f"python3 {traffic_dir}/traffic_flash_crowd.py --target 10.0.0.6 --duration {scenario_duration} --clients 5")

            elif sc == "ddos":
                info(f"[*] Launching DDoS attack from h2 for {scenario_duration}s...\n")
                h2.cmd(f"python3 {traffic_dir}/traffic_ddos.py --target 10.0.0.6 --duration {scenario_duration} --pps 600")

            elif sc == "slow_congestion":
                info(f"[*] Injecting Slow Congestion buildup from h3 for {scenario_duration}s...\n")
                h3.cmd(f"python3 {traffic_dir}/traffic_congestion.py --target 10.0.0.6 --duration {scenario_duration} --steps 5")

            elif sc == "link_failure":
                info(f"[*] Simulating Link Failure for {scenario_duration}s...\n")
                # Run background normal traffic
                h1.cmd(f"python3 {traffic_dir}/traffic_normal.py --target 10.0.0.6 --duration {scenario_duration} &")
                time.sleep(5)
                # Cut link for 12 seconds
                os.system(f"bash {traffic_dir}/link_failure.sh s1-eth6 12")
                time.sleep(max(1, scenario_duration - 17))

            time.sleep(3)  # Cooldown between scenarios

    info("\n=== Step 4: Stopping Mininet & Ryu ===\n")
    h6.cmd("pkill iperf3 || true")
    net.stop()
    os.system("killall -9 ryu-manager 2>/dev/null || true")

    info("\n=== Step 5: Dataset Summary & Validation ===\n")
    if os.path.exists(dataset_file):
        df = pd.read_csv(dataset_file)
        info(f"Total samples collected: {len(df)}\n")
        info("Class distribution:\n")
        info(str(df['label'].value_counts()) + "\n")
        info("\nDataset successfully generated at: " + dataset_file + "\n")
        return True
    else:
        info("[ERROR] Dataset file not found!\n")
        return False


if __name__ == "__main__":
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 25
    rounds = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    success = generate_dataset(rounds=rounds, scenario_duration=duration)
    sys.exit(0 if success else 1)
