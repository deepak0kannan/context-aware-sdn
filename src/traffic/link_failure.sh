#!/bin/bash
# Link Failure Simulation Script
# Disables the core primary link (s1 <-> s2) to simulate hardware link cut

INTERFACE=${1:-"s1-eth6"}
DURATION=${2:-10}

echo "[*] Simulating Hardware Link Failure on interface: $INTERFACE"
echo "[*] Disabling $INTERFACE (bringing link DOWN)..."
sudo ip link set "$INTERFACE" down

echo "[*] Link is DOWN for ${DURATION}s. Triggering OpenFlow port-down event..."
sleep "$DURATION"

echo "[*] Restoring link: bringing $INTERFACE back UP..."
sudo ip link set "$INTERFACE" up
echo "[*] Link $INTERFACE restored to UP state."
