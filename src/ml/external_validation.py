#!/usr/bin/env python3
"""
External Validation Script for SDN Anomaly Classifier
1. Collects a completely new, independent dataset (sdn_dataset_external.csv)
   using fresh network traffic configurations not used during training:
   - Unseen attack packet rates (e.g. 650 pps SYN, 950 pps UDP)
   - Different client concurrency (4 and 5 clients)
   - Unseen normal background rates (750K, 1400K)
   - Distinct congestion step profiles and cut durations (11s, 14s)
2. Loads the pre-trained champion Gradient Boosting model (models/sdn_classifier.joblib)
3. Evaluates external generalization:
   - External Validation Accuracy
   - Macro Precision, Recall, F1-Score
   - Per-Class Metrics and Confusion Matrix
4. Saves external validation results to models/external_validation_report.json
"""

import os
import sys
import time
import json
import numpy as np
import pandas as pd
from collections import Counter
import joblib
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, precision_recall_fscore_support

from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.link import TCLink
from mininet.log import setLogLevel, info

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))
sys.path.append(os.path.join(BASE_DIR, 'topology'))
from topo_multi_path import MultiPathTopo

FEATURE_COLS = [
    "packet_rate", "byte_rate", "flow_duration_sec", "ip_src_count",
    "ip_src_entropy", "avg_packet_size", "std_packet_size",
    "port_status", "rx_dropped", "tx_dropped"
]


def set_active_label(label):
    with open("/tmp/active_label.txt", "w") as f:
        f.write(label + "\n")
    info(f"\n[EXTERNAL DATASET] Active Scenario Ground-Truth -> {label.upper()}\n")


def collect_external_dataset(rounds=2, scenario_duration=22):
    """Generate a completely fresh, independent dataset for external validation."""
    dataset_file = os.path.join(PROJECT_DIR, 'data', 'sdn_dataset_external.csv')
    traffic_dir = os.path.join(BASE_DIR, 'traffic')

    if os.path.exists(dataset_file):
        os.remove(dataset_file)
    if os.path.exists("/tmp/active_label.txt"):
        os.remove("/tmp/active_label.txt")

    info("=== Step 1: Clearing previous state & starting Ryu Controller ===\n")
    os.system("killall -9 ryu-manager 2>/dev/null || true")
    os.system("sudo mn -c > /dev/null 2>&1")
    set_active_label("normal")
    time.sleep(1)

    # Launch Ryu monitor configured to write to external dataset CSV
    ryu_cmd = (
        f"SDN_INTERVAL=1.0 SDN_DATASET_FILE={dataset_file} "
        "screen -dmS ryu_ext /home/deeepo/ryu-env/bin/ryu-manager "
        "--ofp-tcp-listen-port 6653 --wsapi-port 8080 "
        f"{BASE_DIR}/controller/sdn_monitor.py"
    )
    os.system(ryu_cmd)
    time.sleep(2)

    info("=== Step 2: Initializing Mininet Topology ===\n")
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

    # Fresh, unseen parameter configurations
    configs = [
        {"round": 1, "clients": 4, "pps": 650, "attack": "syn", "cong_steps": 4, "cut_time": 11, "norm_host": h3, "norm_rate": "750K"},
        {"round": 2, "clients": 5, "pps": 950, "attack": "udp", "cong_steps": 6, "cut_time": 14, "norm_host": h5, "norm_rate": "1400K"}
    ]

    scenarios = ["normal", "flash_crowd", "ddos", "slow_congestion", "link_failure"]

    for cfg in configs[:rounds]:
        r = cfg["round"]
        info(f"\n=======================================================================\n")
        info(f" >>> RUNNING EXTERNAL VALIDATION ROUND {r}/{rounds} <<<\n")
        info(f" Config: PPS={cfg['pps']} ({cfg['attack']}) | Clients={cfg['clients']} | NormHost={cfg['norm_host'].name} | CutTime={cfg['cut_time']}s\n")
        info(f"=======================================================================\n")

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

    info("\n=== Step 4: Finalizing External Dataset Collection ===\n")
    net.stop()
    os.system("killall -9 ryu-manager 2>/dev/null || true")
    os.system("sudo mn -c > /dev/null 2>&1")
    time.sleep(1)

    return dataset_file


def run_external_validation(dataset_file=None):
    """Evaluate pre-trained model on the external validation dataset."""
    if dataset_file is None:
        dataset_file = os.path.join(PROJECT_DIR, 'data', 'sdn_dataset_external.csv')

    model_file = os.path.join(PROJECT_DIR, 'models', 'sdn_classifier.joblib')

    print(f"\n=======================================================")
    print(f"       EXTERNAL VALIDATION ON UNSEEN DATASET          ")
    print(f"=======================================================")
    print(f"Loading external dataset from: {dataset_file}")
    print(f"Loading trained champion model from: {model_file}")

    if not os.path.exists(dataset_file):
        raise FileNotFoundError(f"External dataset not found: {dataset_file}")
    if not os.path.exists(model_file):
        raise FileNotFoundError(f"Champion model not found: {model_file}")

    df = pd.read_csv(dataset_file)
    print(f"\nExternal Dataset Loaded: {len(df)} total samples.")
    print("Class distribution:")
    for lbl, count in df['label'].value_counts().items():
        print(f"  - {lbl:16s}: {count:3d} samples ({count/len(df)*100:4.1f}%)")

    # Clean numeric features
    for col in FEATURE_COLS:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    X_ext = df[FEATURE_COLS]
    y_ext = df['label']

    # Load model
    model = joblib.load(model_file)

    meta_path = os.path.join(PROJECT_DIR, 'models', 'model_metadata.json')
    if os.path.exists(meta_path):
        with open(meta_path, 'r') as f:
            classes = json.load(f).get('classes', ['ddos', 'flash_crowd', 'link_failure', 'normal', 'slow_congestion'])
    else:
        classes = ['ddos', 'flash_crowd', 'link_failure', 'normal', 'slow_congestion']

    # Run predictions
    y_pred = model.predict(X_ext)
    y_proba = model.predict_proba(X_ext)

    # Map predictions to string labels if model outputs integer class indices
    if isinstance(y_pred[0], (int, np.integer)):
        y_pred = np.array([classes[idx] for idx in y_pred])

    # Compute metrics
    acc = accuracy_score(y_ext, y_pred)
    prec, rec, f1, _ = precision_recall_fscore_support(y_ext, y_pred, average='macro', zero_division=0)
    
    rep_dict = classification_report(y_ext, y_pred, labels=classes, output_dict=True, zero_division=0)
    rep_text = classification_report(y_ext, y_pred, labels=classes, zero_division=0)
    cm = confusion_matrix(y_ext, y_pred, labels=classes)

    print("\n" + "=" * 65)
    print(f"   EXTERNAL VALIDATION ACCURACY: {acc * 100:.2f}%")
    print(f"   EXTERNAL MACRO F1-SCORE:      {f1 * 100:.2f}%")
    print(f"   EXTERNAL MACRO PRECISION:     {prec * 100:.2f}%")
    print(f"   EXTERNAL MACRO RECALL:        {rec * 100:.2f}%")
    print("=" * 65)
    print("\nDetailed Per-Class Performance:")
    print(rep_text)

    print("\nExternal Validation Confusion Matrix:")
    header = f"{'':18s}" + "".join(f"{c[:10]:>12s}" for c in classes)
    print(header)
    for i, row_class in enumerate(classes):
        row_str = f"{row_class:18s}" + "".join(f"{cm[i][j]:12d}" for j in range(len(classes)))
        print(row_str)

    # Export report
    report = {
        "validation_type": "External Independent Validation",
        "dataset_file": os.path.basename(dataset_file),
        "total_samples": len(df),
        "class_distribution": df['label'].value_counts().to_dict(),
        "external_accuracy": float(acc),
        "external_macro_f1": float(f1),
        "external_macro_precision": float(prec),
        "external_macro_recall": float(rec),
        "classes": classes,
        "confusion_matrix": cm.tolist(),
        "per_class_report": rep_dict
    }

    report_path = os.path.join(PROJECT_DIR, 'models', 'external_validation_report.json')
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n[OK] External validation report saved to: {report_path}")

    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="External Validation Suite")
    parser.add_argument("--collect-only", action="store_true", help="Only collect external dataset")
    parser.add_argument("--eval-only", action="store_true", help="Only evaluate existing external dataset")
    parser.add_argument("--rounds", type=int, default=2, help="Number of diverse rounds to simulate (default: 2)")
    parser.add_argument("--duration", type=int, default=22, help="Duration per scenario in seconds (default: 22)")
    args = parser.parse_args()

    if args.eval_only:
        run_external_validation()
    elif args.collect_only:
        collect_external_dataset(rounds=args.rounds, scenario_duration=args.duration)
    else:
        info(">>> Starting Full External Validation (Collection + Inference) <<<\n")
        ext_file = collect_external_dataset(rounds=args.rounds, scenario_duration=args.duration)
        run_external_validation(ext_file)
