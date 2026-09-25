#!/usr/bin/env python3
"""
Enhanced Large Dataset Generator for Comprehensive Cross-Validation
Executes 4 diverse simulation rounds with randomized and varied traffic parameters:
- Varying client concurrency (3 to 5 hosts)
- Varying attack vectors (TCP SYN flood & UDP flood, 500 to 1200 pps)
- Diverse traffic intensities (300K to 2M for normal, 2M to 10M for congestion)
- Varied link cut durations (8s to 14s)
- High-frequency 1.0-second telemetry polling

Target output: ~500 to 700 diverse, labeled feature rows in data/sdn_dataset_large.csv
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

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(BASE_DIR, 'topology'))
from topo_multi_path import MultiPathTopo


def set_active_label(label):
    """Set active ground-truth label for the controller."""
    with open("/tmp/active_label.txt", "w") as f:
        f.write(label + "\n")
    info(f"\n=======================================================\n")
    info(f"[DATASET] Set active ground-truth label -> {label.upper()}\n")
    info(f"=======================================================\n")


def generate_large_dataset(rounds=4, scenario_duration=28):
    setLogLevel('info')
    dataset_file = os.path.expanduser("~/sdn_project/data/sdn_dataset_large.csv")
    traffic_dir = os.path.join(BASE_DIR, 'traffic')

    # Remove previous large dataset if exists to start fresh
    if os.path.exists(dataset_file):
        os.remove(dataset_file)

    info("=== Step 1: Cleaning previous state & starting Ryu Controller ===\n")
    os.system("killall -9 ryu-manager 2>/dev/null || true")
    os.system("sudo mn -c > /dev/null 2>&1")
    time.sleep(1)

    # Launch Ryu with high-frequency 1.0s interval
    ryu_cmd = (
        "SDN_INTERVAL=1.0 "
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

    # Round parameter configurations
    configs = [
        {"round": 1, "clients": 4, "pps": 500, "attack": "syn", "cong_steps": 5, "cut_time": 10, "norm_host": h1, "norm_rate": "800K"},
        {"round": 2, "clients": 5, "pps": 800, "attack": "udp", "cong_steps": 6, "cut_time": 12, "norm_host": h4, "norm_rate": "1500K"},
        {"round": 3, "clients": 3, "pps": 1000, "attack": "syn", "cong_steps": 4, "cut_time": 9, "norm_host": h2, "norm_rate": "1000K"},
        {"round": 4, "clients": 5, "pps": 1200, "attack": "udp", "cong_steps": 5, "cut_time": 13, "norm_host": h5, "norm_rate": "1200K"}
    ]

    scenarios = ["normal", "flash_crowd", "ddos", "slow_congestion", "link_failure"]

    for cfg in configs[:rounds]:
        r = cfg["round"]
        info(f"\n>>>>>>>>>>>> STARTING DIVERSE ROUND {r}/{rounds} <<<<<<<<<<<<\n")
        info(f"Config: PPS={cfg['pps']} ({cfg['attack']}) | Clients={cfg['clients']} | NormHost={cfg['norm_host'].name} | CutTime={cfg['cut_time']}s\n")

        for sc in scenarios:
            set_active_label(sc)
            time.sleep(1.5)

            if sc == "normal":
                info(f"[*] [Round {r}] Normal traffic from {cfg['norm_host'].name} ({cfg['norm_rate']}) for {scenario_duration}s...\n")
                cfg['norm_host'].cmd(f"python3 {traffic_dir}/traffic_normal.py --target 10.0.0.6 --duration {scenario_duration} --rate {cfg['norm_rate']}")

            elif sc == "flash_crowd":
                info(f"[*] [Round {r}] Flash-Crowd surge ({cfg['clients']} clients) for {scenario_duration}s...\n")
                h1.cmd(f"python3 {traffic_dir}/traffic_flash_crowd.py --target 10.0.0.6 --duration {scenario_duration} --clients {cfg['clients']}")

            elif sc == "ddos":
                info(f"[*] [Round {r}] DDoS {cfg['attack'].upper()} attack ({cfg['pps']} pps) for {scenario_duration}s...\n")
                h2.cmd(f"python3 {traffic_dir}/traffic_ddos.py --target 10.0.0.6 --duration {scenario_duration} --pps {cfg['pps']} --type {cfg['attack']}")

            elif sc == "slow_congestion":
                info(f"[*] [Round {r}] Slow Congestion ({cfg['cong_steps']} steps) for {scenario_duration}s...\n")
                h3.cmd(f"python3 {traffic_dir}/traffic_congestion.py --target 10.0.0.6 --duration {scenario_duration} --steps {cfg['cong_steps']}")

            elif sc == "link_failure":
                info(f"[*] [Round {r}] Link Failure (cut duration {cfg['cut_time']}s) for {scenario_duration}s...\n")
                h1.cmd(f"python3 {traffic_dir}/traffic_normal.py --target 10.0.0.6 --duration {scenario_duration} &")
                time.sleep(4)
                os.system(f"bash {traffic_dir}/link_failure.sh s1-eth6 {cfg['cut_time']}")
                time.sleep(max(1, scenario_duration - cfg['cut_time'] - 5))

            time.sleep(2)  # Cooldown

    info("\n=== Step 4: Stopping Mininet & Ryu ===\n")
    h6.cmd("pkill iperf3 || true")
    net.stop()
    os.system("killall -9 ryu-manager 2>/dev/null || true")

    # Rename dataset file to sdn_dataset_large.csv
    src_data = os.path.expanduser("~/sdn_project/data/sdn_dataset.csv")
    if os.path.exists(src_data):
        import shutil
        shutil.copyfile(src_data, dataset_file)

    info("\n=== Step 5: Large Dataset Summary & Validation ===\n")
    if os.path.exists(dataset_file):
        df = pd.read_csv(dataset_file)
        info(f"Total samples collected: {len(df)}\n")
        info("Class distribution:\n")
        info(str(df['label'].value_counts()) + "\n")
        info(f"Dataset successfully created at: {dataset_file}\n")
        return True
    return False


if __name__ == "__main__":
    generate_large_dataset(rounds=4, scenario_duration=20)
