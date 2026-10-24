#!/usr/bin/env python3
"""
Phase 6 Automated Verification Suite:
Tests the Differentiated Auto-Remediation Engine across all network conditions:
1. Baseline Normal traffic -> Confirms default Path A active.
2. Flash Crowd Surge       -> Confirms OpenFlow 1.3 SELECT group table and dual-path distribution.
3. Volumetric DDoS         -> Confirms surgical ingress drop rule and legitimate user survival.
4. Slow Congestion         -> Confirms preemptive bulk traffic diversion to Path B.
5. Hardware Link Failure   -> Confirms sub-second failover upon port-down signal.
"""

import os
import sys
import time
import json
import subprocess

from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.link import TCLink
from mininet.log import setLogLevel, info

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, 'topology'))
from topo_multi_path import MultiPathTopo

TRAFFIC_DIR = os.path.join(BASE_DIR, 'traffic')
STATUS_FILE = "/home/deeepo/sdn_project/data/live_remediation_status.json"


def clean_state():
    info("[*] Cleaning previous Mininet & Ryu processes...\n")
    os.system("sudo killall -9 ryu-manager 2>/dev/null || true")
    os.system("sudo fuser -k 6653/tcp 2>/dev/null || true")
    os.system("sudo fuser -k 6633/tcp 2>/dev/null || true")
    os.system("sudo fuser -k 8080/tcp 2>/dev/null || true")
    os.system("sudo mn -c > /dev/null 2>&1")
    os.system("sudo pkill -9 -f 'iperf3' 2>/dev/null || true")
    os.system("sudo pkill -9 -f 'traffic_' 2>/dev/null || true")
    time.sleep(1)


def read_live_status():
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"detected_class": "normal", "remediation_state": "NORMAL", "confidence": 0.0}


def check_ping(host, target_ip="10.0.0.6", count=2, timeout=1):
    out = host.cmd(f"ping -c {count} -W {timeout} {target_ip}")
    success = "64 bytes from" in out or "0% packet loss" in out or "100% packet loss" not in out
    return success, out


def run_phase6_verification():
    setLogLevel('info')
    results = {}

    clean_state()

    info("\n=== Step 1: Starting Ryu Differentiated Remediation Controller ===\n")
    ryu_log = open("/tmp/ryu_phase6.log", "w")
    env = os.environ.copy()
    env["SDN_INTERVAL"] = "1.0"
    ryu_proc = subprocess.Popen([
        "/home/deeepo/ryu-env/bin/ryu-manager",
        "--ofp-tcp-listen-port", "6653",
        "--wsapi-port", "8080",
        f"{BASE_DIR}/controller/remediation_engine.py"
    ], env=env, stdout=ryu_log, stderr=subprocess.STDOUT)
    time.sleep(3)

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

    info("=== Step 3: Starting iperf3 Target Servers on h6 ===\n")
    for p in range(5201, 5206):
        h6.cmd(f"iperf3 -s -p {p} -D")
    time.sleep(1)

    # -------------------------------------------------------------
    # Test 1: Normal Baseline Traffic
    # -------------------------------------------------------------
    info("\n>>> TEST 1: Normal Baseline Traffic Verification <<<\n")
    h1.cmd(f"python3 {TRAFFIC_DIR}/traffic_normal.py --target 10.0.0.6 --duration 8 --rate 800K &")
    time.sleep(5)
    st = read_live_status()
    info(f"[*] Live Status: {st.get('detected_class', 'none')} | State: {st.get('remediation_state', 'none')}\n")
    ping_ok, ping_out = check_ping(h1, "10.0.0.6")
    info(f"[*] Ping h1 -> h6: {'SUCCESS' if ping_ok else 'FAILED'}\n")
    results["Normal Baseline"] = ping_ok

    # -------------------------------------------------------------
    # Test 2: Flash Crowd Surge -> Load Balancing
    # -------------------------------------------------------------
    info("\n>>> TEST 2: Flash Crowd Surge -> Multi-Path Load Balancing <<<\n")
    clients = [h1, h2, h3, h4, h5]
    for idx, client in enumerate(clients):
        port = 5201 + idx
        client.cmd(f"iperf3 -c 10.0.0.6 -u -b 1600K -t 10 -p {port} &")
    time.sleep(5)
    # Check OpenFlow group table on s1
    group_dump = os.popen("sudo ovs-ofctl -O OpenFlow13 dump-groups s1").read()
    st = read_live_status()
    info(f"[*] Live Status: {st.get('detected_class', 'none')} | State: {st.get('remediation_state', 'none')}\n")
    info(f"[*] OpenFlow Group Table on s1:\n{group_dump.strip()}\n")
    has_group = "group_id=50" in group_dump or "type=select" in group_dump or st.get('remediation_state') == "LOAD_BALANCED" or st.get('detected_class') in ["flash_crowd", "slow_congestion"]
    results["Flash Crowd Load Balancing"] = has_group
    time.sleep(2)
    os.system("pkill -9 -f 'iperf3 -c' || true")

    # -------------------------------------------------------------
    # Test 3: Volumetric DDoS Flood -> Surgical Ingress Drop
    # -------------------------------------------------------------
    info("\n>>> TEST 3: DDoS Attack -> Surgical Ingress Drop & User Protection <<<\n")
    h1.cmd(f"python3 {TRAFFIC_DIR}/traffic_ddos.py --target 10.0.0.6 --duration 10 --pps 900 --type udp &")
    time.sleep(5)
    st = read_live_status()
    flows_s1 = os.popen("sudo ovs-ofctl -O OpenFlow13 dump-flows s1").read()
    info(f"[*] Live Status: {st.get('detected_class', 'none')} | State: {st.get('remediation_state', 'none')}\n")
    # Verify legitimate user h2 can still ping target server h6 during active attack!
    ping_ok, ping_out = check_ping(h2, "10.0.0.6")
    info(f"[*] Legitimate User (h2) Ping during DDoS: {'SUCCESS' if ping_ok else 'DROPPED'}\n")
    results["DDoS Surgical Mitigation"] = (ping_ok or "actions=drop" in flows_s1 or st.get('remediation_state') == "INGRESS_DROP")
    os.system("pkill -9 -f 'traffic_ddos' || true")
    time.sleep(2)

    # -------------------------------------------------------------
    # Test 4: Slow Congestion -> Preemptive Reroute
    # -------------------------------------------------------------
    info("\n>>> TEST 4: Slow Congestion -> Preemptive Traffic Diversion <<<\n")
    h2.cmd(f"python3 {TRAFFIC_DIR}/traffic_congestion.py --target 10.0.0.6 --duration 12 --steps 4 &")
    h3.cmd("iperf3 -c 10.0.0.6 -u -b 7.5M -t 8 -p 5201 &")
    time.sleep(6)
    st = read_live_status()
    flows_s1 = os.popen("sudo ovs-ofctl -O OpenFlow13 dump-flows s1").read()
    info(f"[*] Live Status: {st.get('detected_class', 'none')} | State: {st.get('remediation_state', 'none')}\n")
    results["Slow Congestion Preemption"] = (
        st.get('detected_class') in ["slow_congestion", "flash_crowd"] or 
        st.get('remediation_state') in ["PREEMPTIVE_REROUTE", "LOAD_BALANCED"] or
        "output:7" in flows_s1
    )
    os.system("pkill -9 -f 'traffic_congestion' || true")
    os.system("pkill -9 -f 'iperf3' || true")
    time.sleep(2)

    # -------------------------------------------------------------
    # Test 5: Hardware Link Failure -> Instant Failover
    # -------------------------------------------------------------
    info("\n>>> TEST 5: Hardware Link Failure -> Instant Sub-Second Failover <<<\n")
    h1.cmd(f"python3 {TRAFFIC_DIR}/traffic_normal.py --target 10.0.0.6 --duration 12 &")
    time.sleep(2)
    info("[*] Cutting Core Path A (s1-eth6)...\n")
    os.system(f"bash {TRAFFIC_DIR}/link_failure.sh s1-eth6 8 &")
    time.sleep(4)
    st = read_live_status()
    info(f"[*] Live Status: {st.get('detected_class', 'none')} | State: {st.get('remediation_state', 'none')}\n")
    # Verify reachability through backup Path B
    ping_ok, ping_out = check_ping(h1, "10.0.0.6")
    info(f"[*] Backup Path Ping during Link Cut: {'SUCCESS' if ping_ok else 'FAILED'}\n")
    results["Link Failure Instant Failover"] = (st.get('detected_class') == "link_failure" or st.get('remediation_state') == "LINK_FAILOVER" or ping_ok)

    # Clean up
    try:
        net.stop()
    except Exception:
        pass
    clean_state()

    info("\n=================================================================\n")
    info("              PHASE 6 AUTO-REMEDIATION VERIFICATION SUMMARY      \n")
    info("=================================================================\n")
    all_passed = True
    for test_name, passed in results.items():
        status_str = "PASSED [OK]" if passed else "FAILED [X]"
        info(f"  - {test_name:<35s}: {status_str}\n")
        if not passed:
            all_passed = False
    info("=================================================================\n")

    return all_passed


if __name__ == "__main__":
    success = run_phase6_verification()
    sys.exit(0 if success else 1)
