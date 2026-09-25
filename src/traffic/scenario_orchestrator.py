#!/usr/bin/env python3
"""
Unified Traffic Scenario Orchestrator
Executes specific traffic scenarios inside Mininet host namespaces.
Scenarios:
- normal: Baseline browsing traffic
- flash_crowd: Legitimate multi-client surge
- ddos: High-rate malicious packet flood
- congestion: Slow progressive bandwidth ramp
- link_failure: Physical link down toggle
"""

import sys
import os
import time
import subprocess
import argparse


def run_command(cmd, wait=True):
    """Helper to run system command."""
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if wait:
        stdout, stderr = proc.communicate()
        return proc.returncode, stdout, stderr
    return 0, "", ""


def get_mininet_pid(host_name):
    """Find the process ID of a Mininet host."""
    code, out, _ = run_command(f"ps ax | grep 'mininet:{host_name}' | grep -v grep | awk '{{print $1}}'")
    pids = out.strip().split()
    return pids[0] if pids else None


def exec_in_host(host_name, command, background=False):
    """Execute command inside the network namespace of a Mininet host."""
    pid = get_mininet_pid(host_name)
    if not pid:
        # Fallback using mnexec directly
        full_cmd = f"sudo mnexec -a $(cat /tmp/mn-{host_name}.pid 2>/dev/null || pgrep -f 'mininet:{host_name}') {command}"
    else:
        full_cmd = f"sudo mnexec -a {pid} {command}"

    if background:
        full_cmd += " > /dev/null 2>&1 &"
        return run_command(full_cmd, wait=False)
    else:
        return run_command(full_cmd, wait=True)


def ensure_server_running():
    """Ensure iperf3 server is running on server h6."""
    print("[*] Ensuring iperf3 server daemon is active on h6...")
    exec_in_host("h6", "pkill iperf3 || true")
    time.sleep(0.5)
    exec_in_host("h6", "iperf3 -s -D", background=False)
    time.sleep(0.5)


def run_scenario(scenario_name, duration=30):
    """Execute designated scenario."""
    print(f"\n=======================================================")
    print(f"[*] EXECUTING SCENARIO: {scenario_name.upper()} ({duration}s)")
    print(f"=======================================================")

    ensure_server_running()

    traffic_dir = os.path.dirname(os.path.abspath(__file__))

    if scenario_name == "normal":
        print("[*] Running normal baseline traffic from h1...")
        cmd = f"python3 {traffic_dir}/traffic_normal.py --target 10.0.0.6 --duration {duration}"
        exec_in_host("h1", cmd, background=False)

    elif scenario_name == "flash_crowd":
        print("[*] Running flash crowd surge from h1..h5 simultaneously...")
        cmd = f"python3 {traffic_dir}/traffic_flash_crowd.py --target 10.0.0.6 --duration {duration} --clients 5"
        exec_in_host("h1", cmd, background=False)

    elif scenario_name == "ddos":
        print("[*] Launching high-rate DDoS attack from h2...")
        cmd = f"python3 {traffic_dir}/traffic_ddos.py --target 10.0.0.6 --duration {duration} --pps 800"
        exec_in_host("h2", cmd, background=False)

    elif scenario_name == "congestion":
        print("[*] Injecting progressive slow congestion from h3...")
        cmd = f"python3 {traffic_dir}/traffic_congestion.py --target 10.0.0.6 --duration {duration} --steps 5"
        exec_in_host("h3", cmd, background=False)

    elif scenario_name == "link_failure":
        print("[*] Simulating background traffic with mid-run link failure...")
        # Start background traffic
        cmd_traffic = f"python3 {traffic_dir}/traffic_normal.py --target 10.0.0.6 --duration {duration}"
        exec_in_host("h1", cmd_traffic, background=True)

        # Trigger link failure at midpoint
        half_time = max(5, int(duration / 2))
        print(f"[*] Waiting {half_time}s before triggering link cut...")
        time.sleep(half_time)

        fail_time = min(10, duration - half_time)
        cmd_fail = f"bash {traffic_dir}/link_failure.sh s1-eth6 {fail_time}"
        run_command(cmd_fail, wait=True)

    else:
        print(f"[!] Unknown scenario: {scenario_name}")
        sys.exit(1)

    print(f"[*] Scenario {scenario_name} finished successfully.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SDN Scenario Orchestrator")
    parser.add_argument("--scenario", required=True, choices=["normal", "flash_crowd", "ddos", "congestion", "link_failure"], help="Scenario to execute")
    parser.add_argument("--duration", type=int, default=20, help="Scenario duration in seconds (default: 20)")
    args = parser.parse_args()

    run_scenario(args.scenario, duration=args.duration)
