#!/bin/bash
# Phase 1 Test Runner: Multi-Path Mininet Topology + Ryu OpenFlow 1.3 Controller

echo "=== 1. Cleaning previous Mininet & Ryu state ==="
sudo mn -c > /dev/null 2>&1
killall -9 ryu-manager 2> /dev/null || true
sleep 1

echo "=== 2. Starting Ryu OpenFlow 1.3 Controller ==="
/home/deeepo/ryu-env/bin/ryu-manager \
    --ofp-tcp-listen-port 6653 \
    --wsapi-port 8080 \
    --observe-links \
    /home/deeepo/sdn_project/src/controller/multipath_switch.py \
    ryu.app.gui_topology.gui_topology > /tmp/ryu.log 2>&1 &

RYU_PID=$!
sleep 2

# Verify Ryu is listening
if ss -tulpn | grep -q 6653; then
    echo "[OK] Ryu Controller is listening on port 6653 (PID: $RYU_PID)"
else
    echo "[ERROR] Ryu Controller failed to start. Logs:"
    cat /tmp/ryu.log
    exit 1
fi

echo "=== 3. Running Mininet Multi-Path Connectivity Test (pingall) ==="
sudo python3 /home/deeepo/sdn_project/src/topology/topo_multi_path.py --test

echo "=== 4. Checking Ryu Switch & Flow Status ==="
python3 -c "import urllib.request, json; print(json.dumps(json.loads(urllib.request.urlopen('http://127.0.0.1:8080/v1.0/topology/switches').read()), indent=2))" || true
echo ""
echo "=== Phase 1 Test Complete ==="
