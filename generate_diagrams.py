#!/usr/bin/env python3
"""
Diagrams Generator for Context-Aware SDN Project
Generates:
1. block_diagram.svg & block_diagram.png (Multi-tier architectural block diagram)
2. workflow_diagram.svg & workflow_diagram.png (End-to-end autonomic workflow diagram)
Saves in both the root folder and the diagrams/ directory.
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ArrowStyle

def create_block_diagram_png(output_path):
    fig = plt.figure(figsize=(16, 12), dpi=300)
    ax = fig.add_subplot(111)
    ax.set_xlim(0, 160)
    ax.set_ylim(0, 120)
    ax.axis('off')

    # Color palette
    c_bg = "#0f172a"
    c_box_bg = "#1e293b"
    c_blue = "#38bdf8"
    c_indigo = "#818cf8"
    c_emerald = "#34d399"
    c_amber = "#fbbf24"
    c_rose = "#f43f5e"
    c_purple = "#c084fc"
    c_text = "#f8fafc"
    c_subtext = "#94a3b8"

    fig.patch.set_facecolor(c_bg)

    # Title Banner
    ax.text(80, 115, "CONTEXT-AWARE SDN: SYSTEM ARCHITECTURE BLOCK DIAGRAM", 
            ha='center', va='center', fontsize=18, fontweight='bold', color='#38bdf8')
    ax.text(80, 111.5, "Unified Multi-Class Network Anomaly Classification & Differentiated Auto-Remediation", 
            ha='center', va='center', fontsize=11, color=c_subtext)

    # ------------------ LAYER 1: DATA PLANE ------------------
    # Data plane bounding box
    rect1 = FancyBboxPatch((4, 4), 152, 28, boxstyle="round,pad=1,rounding_size=2",
                           facecolor="#111c33", edgecolor="#1e3a8a", linewidth=2, linestyle='--')
    ax.add_patch(rect1)
    ax.text(8, 30, "DATA PLANE (Mininet & Open vSwitch 2.17+ / OpenFlow 1.3)", 
            fontsize=11, fontweight='bold', color="#60a5fa")

    # Hosts h1-h5
    for i in range(5):
        x = 10 + i * 11
        h_box = FancyBboxPatch((x, 16), 9, 8, boxstyle="round,pad=0.5,rounding_size=1",
                               facecolor="#1e293b", edgecolor="#38bdf8", linewidth=1.5)
        ax.add_patch(h_box)
        ax.text(x+4.5, 21.5, f"Client h{i+1}", ha='center', va='center', fontsize=8.5, fontweight='bold', color=c_text)
        ax.text(x+4.5, 18, f"10.0.0.{i+1}", ha='center', va='center', fontsize=7, color=c_subtext)

    # Ingress Switch s1
    s1_box = FancyBboxPatch((68, 16), 18, 9, boxstyle="round,pad=0.5,rounding_size=1.5",
                            facecolor="#1e293b", edgecolor="#fbbf24", linewidth=2)
    ax.add_patch(s1_box)
    ax.text(77, 22, "Ingress Switch s1", ha='center', va='center', fontsize=9.5, fontweight='bold', color=c_amber)
    ax.text(77, 18, "OVS DPID: 0x01", ha='center', va='center', fontsize=7.5, color=c_subtext)

    # Core Switch s2 (Path A)
    s2_box = FancyBboxPatch((94, 22), 22, 8, boxstyle="round,pad=0.5,rounding_size=1",
                            facecolor="#1e293b", edgecolor="#34d399", linewidth=1.5)
    ax.add_patch(s2_box)
    ax.text(105, 27, "Path A: Switch s2", ha='center', va='center', fontsize=8.5, fontweight='bold', color=c_emerald)
    ax.text(105, 24, "Core: 10 Mbps, 5ms", ha='center', va='center', fontsize=7, color=c_subtext)

    # Core Switch s3 (Path B)
    s3_box = FancyBboxPatch((94, 9), 22, 8, boxstyle="round,pad=0.5,rounding_size=1",
                            facecolor="#1e293b", edgecolor="#818cf8", linewidth=1.5)
    ax.add_patch(s3_box)
    ax.text(105, 14, "Path B: Switch s3", ha='center', va='center', fontsize=8.5, fontweight='bold', color=c_indigo)
    ax.text(105, 11, "Core: 10 Mbps, 10ms", ha='center', va='center', fontsize=7, color=c_subtext)

    # Egress Switch s4
    s4_box = FancyBboxPatch((124, 16), 15, 9, boxstyle="round,pad=0.5,rounding_size=1.5",
                            facecolor="#1e293b", edgecolor="#fbbf24", linewidth=2)
    ax.add_patch(s4_box)
    ax.text(131.5, 22, "Egress s4", ha='center', va='center', fontsize=9.5, fontweight='bold', color=c_amber)
    ax.text(131.5, 18, "OVS DPID: 0x04", ha='center', va='center', fontsize=7.5, color=c_subtext)

    # Destination Server h6
    h6_box = FancyBboxPatch((145, 16), 9, 8, boxstyle="round,pad=0.5,rounding_size=1",
                            facecolor="#1e293b", edgecolor="#f43f5e", linewidth=1.5)
    ax.add_patch(h6_box)
    ax.text(149.5, 21.5, "Server h6", ha='center', va='center', fontsize=8.5, fontweight='bold', color=c_text)
    ax.text(149.5, 18, "10.0.0.6", ha='center', va='center', fontsize=7, color=c_subtext)

    # Connecting lines in data plane
    for i in range(5):
        ax.annotate('', xy=(68, 20.5), xytext=(19 + i*11, 20),
                    arrowprops=dict(arrowstyle="->", color="#38bdf8", lw=1.2))
    ax.annotate('', xy=(94, 26), xytext=(86, 22), arrowprops=dict(arrowstyle="<->", color="#34d399", lw=1.5))
    ax.annotate('', xy=(94, 13), xytext=(86, 18), arrowprops=dict(arrowstyle="<->", color="#818cf8", lw=1.5))
    ax.annotate('', xy=(124, 22), xytext=(116, 26), arrowprops=dict(arrowstyle="<->", color="#34d399", lw=1.5))
    ax.annotate('', xy=(124, 18), xytext=(116, 13), arrowprops=dict(arrowstyle="<->", color="#818cf8", lw=1.5))
    ax.annotate('', xy=(145, 20), xytext=(139, 20), arrowprops=dict(arrowstyle="<->", color="#f43f5e", lw=1.5))

    # ------------------ LAYER 2: SOUTHBOUND INTERFACE ------------------
    sb_box = FancyBboxPatch((4, 36), 152, 10, boxstyle="round,pad=1,rounding_size=1.5",
                            facecolor="#1e293b", edgecolor="#38bdf8", linewidth=1.5)
    ax.add_patch(sb_box)
    ax.text(80, 42.5, "SOUTHBOUND CONTROL INTERFACE: OPENFLOW 1.3 PROTOCOL (TCP Port 6653)", 
            ha='center', va='center', fontsize=10.5, fontweight='bold', color="#38bdf8")
    ax.text(80, 39, "Telemetry: OFPFlowStatsReply, OFPPortStatsReply, PacketIn, PortStatus  |  Control: OFPFlowMod, OFPGroupMod (OFPGT_SELECT)", 
            ha='center', va='center', fontsize=8, color="#94a3b8")

    # Arrows between Data Plane and Southbound
    ax.annotate('', xy=(40, 36), xytext=(40, 32), arrowprops=dict(arrowstyle="<->", color="#38bdf8", lw=2))
    ax.annotate('', xy=(80, 36), xytext=(80, 32), arrowprops=dict(arrowstyle="<->", color="#fbbf24", lw=2))
    ax.annotate('', xy=(120, 36), xytext=(120, 32), arrowprops=dict(arrowstyle="<->", color="#38bdf8", lw=2))

    # ------------------ LAYER 3: RYU SDN CONTROLLER & INTELLIGENCE CORE ------------------
    ryu_bg = FancyBboxPatch((4, 50), 152, 44, boxstyle="round,pad=1,rounding_size=2",
                            facecolor="#132238", edgecolor="#6366f1", linewidth=2.2)
    ax.add_patch(ryu_bg)
    ax.text(8, 92, "RYU SDN CONTROLLER & AUTONOMIC CLOSED-LOOP ENGINE (Control Plane)", 
            fontsize=12, fontweight='bold', color="#818cf8")

    # 3.1 Base Forwarding & Topology Discovery
    m1 = FancyBboxPatch((8, 54), 32, 34, boxstyle="round,pad=0.8,rounding_size=1.5",
                        facecolor="#1e293b", edgecolor="#38bdf8", linewidth=1.5)
    ax.add_patch(m1)
    ax.text(24, 84, "Base Forwarding & Telemetry", ha='center', va='center', fontsize=9.5, fontweight='bold', color="#38bdf8")
    ax.text(24, 79, "* multipath_switch.py\n* sdn_monitor.py\n* 2.0s Periodic Stats Poller\n* OFPFlowStatsRequest\n* OFPPortStatsRequest\n* EventOFPPortStatus\n* EventOFPPacketIn", 
            ha='center', va='center', fontsize=7.5, color="#cbd5e1")

    # 3.2 Feature Engineering
    m2 = FancyBboxPatch((44, 54), 32, 34, boxstyle="round,pad=0.8,rounding_size=1.5",
                        facecolor="#1e293b", edgecolor="#fbbf24", linewidth=1.5)
    ax.add_patch(m2)
    ax.text(60, 84, "Rolling Feature Extraction", ha='center', va='center', fontsize=9.5, fontweight='bold', color="#fbbf24")
    ax.text(60, 78, "* Shannon IP Entropy (H)\n* Packet Rate (pps)\n* Byte Rate (Bps)\n* Unique Source IPs Count\n* Mean Packet Size\n* Std Dev Packet Size\n* Physical Port State (0/1)\n* RX / TX Dropped Counters", 
            ha='center', va='center', fontsize=7.5, color="#cbd5e1")

    # 3.3 ML Classification Subsystem
    m3 = FancyBboxPatch((80, 54), 34, 34, boxstyle="round,pad=0.8,rounding_size=1.5",
                        facecolor="#1e293b", edgecolor="#34d399", linewidth=1.5)
    ax.add_patch(m3)
    ax.text(97, 84, "ML Classifier Engine", ha='center', va='center', fontsize=9.5, fontweight='bold', color="#34d399")
    ax.text(97, 78, "* Champion: Gradient Boosting\n* 10-Fold CV: 92.54% Accuracy\n* Fallback: Random Forest (86.9%)\n* Sub-15ms Live Inference\n* Target Classes:\n  - Normal Baseline\n  - Flash-Crowd Surge\n  - Volumetric DDoS Flood\n  - Slow Buffer Congestion\n  - Physical Link Failure", 
            ha='center', va='center', fontsize=7.2, color="#cbd5e1")

    # 3.4 Autonomic Remediation Engine
    m4 = FancyBboxPatch((118, 54), 34, 34, boxstyle="round,pad=0.8,rounding_size=1.5",
                        facecolor="#1e293b", edgecolor="#f43f5e", linewidth=1.5)
    ax.add_patch(m4)
    ax.text(135, 84, "Differentiated Remediation", ha='center', va='center', fontsize=9.5, fontweight='bold', color="#f43f5e")
    ax.text(135, 78, "* remediation_engine.py\n* Flash-Crowd:\n  OFPGT_SELECT Multipath\n* DDoS Attack:\n  Priority 150 Surgical Drop\n* Slow Congestion:\n  Priority 80 Preemptive Route\n* Link Failure:\n  Priority 120 Failover (<50ms)\n* Normal: Clear Overrides", 
            ha='center', va='center', fontsize=7.2, color="#cbd5e1")

    # Arrows inside Ryu Engine
    ax.annotate('', xy=(44, 71), xytext=(40, 71), arrowprops=dict(arrowstyle="->", color="#fbbf24", lw=2))
    ax.annotate('', xy=(80, 71), xytext=(76, 71), arrowprops=dict(arrowstyle="->", color="#34d399", lw=2))
    ax.annotate('', xy=(118, 71), xytext=(114, 71), arrowprops=dict(arrowstyle="->", color="#f43f5e", lw=2))

    # Control loop down to Southbound
    ax.annotate('', xy=(135, 46), xytext=(135, 54), arrowprops=dict(arrowstyle="->", color="#f43f5e", lw=2.2))
    ax.annotate('', xy=(24, 54), xytext=(24, 46), arrowprops=dict(arrowstyle="->", color="#38bdf8", lw=2.2))

    # ------------------ LAYER 4: ORCHESTRATION & PRESENTATION ------------------
    orch_bg = FancyBboxPatch((4, 98), 152, 12, boxstyle="round,pad=1,rounding_size=1.5",
                             facecolor="#172554", edgecolor="#38bdf8", linewidth=1.5)
    ax.add_patch(orch_bg)
    ax.text(8, 107.5, "MANAGEMENT, EVALUATION & USER PRESENTATION LAYER", 
            fontsize=10.5, fontweight='bold', color="#38bdf8")

    # 4 sub-boxes
    app_boxes = [
        ("Traffic Generation Suite", "iPerf3, Scapy, TC, Bash Scripts", 10, 32, "#38bdf8"),
        ("Live Streamlit Dashboard", "streamlit_app.py Interactive Web UI", 46, 32, "#34d399"),
        ("Telemetry & Event Persistence", "live_remediation_status.json / logs", 82, 34, "#fbbf24"),
        ("D3.js GUI & Report Decks", "topology_gui.html, PDF/PPTX Reports", 120, 32, "#c084fc")
    ]
    for title, desc, x, w, col in app_boxes:
        ab = FancyBboxPatch((x, 99.5), w, 6.5, boxstyle="round,pad=0.4,rounding_size=0.8",
                            facecolor="#1e293b", edgecolor=col, linewidth=1.2)
        ax.add_patch(ab)
        ax.text(x + w/2, 104, title, ha='center', va='center', fontsize=8, fontweight='bold', color=col)
        ax.text(x + w/2, 101.5, desc, ha='center', va='center', fontsize=6.8, color=c_subtext)

    # Connections between Ryu and Presentation
    ax.annotate('', xy=(99, 99.5), xytext=(99, 94), arrowprops=dict(arrowstyle="<->", color="#fbbf24", lw=1.5))
    ax.annotate('', xy=(62, 99.5), xytext=(62, 94), arrowprops=dict(arrowstyle="<->", color="#34d399", lw=1.5))

    plt.tight_layout()
    fig.savefig(output_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
    plt.close(fig)
    print(f"[OK] Saved Block Diagram PNG to: {output_path}")

def create_workflow_diagram_png(output_path):
    fig = plt.figure(figsize=(16, 13), dpi=300)
    ax = fig.add_subplot(111)
    ax.set_xlim(0, 160)
    ax.set_ylim(0, 130)
    ax.axis('off')

    c_bg = "#0f172a"
    c_subtext = "#94a3b8"
    fig.patch.set_facecolor(c_bg)

    # Title
    ax.text(80, 125, "CONTEXT-AWARE SDN: END-TO-END AUTONOMIC WORKFLOW", 
            ha='center', va='center', fontsize=18, fontweight='bold', color='#38bdf8')
    ax.text(80, 121.5, "Closed-Loop Cycle: Ingress -> Dual Telemetry -> Sliding Feature Math -> ML Inference -> Differentiated Remediation", 
            ha='center', va='center', fontsize=10.5, color=c_subtext)

    steps = [
        # (title, desc, x, y, w, h, border_color)
        ("1. TRAFFIC GENERATION & INGRESS", 
         "Hosts h1-h5 generate traffic toward h6:\n* Normal Baseline (web/file transfer)\n* Flash-Crowd (5 client burst)\n* DDoS Flood (SYN/UDP flood via Scapy)\n* Slow Congestion (ramping load)\n* Physical Link Down (s1-eth6)", 
         10, 95, 38, 22, "#38bdf8"),

        ("2. DUAL-CHANNEL TELEMETRY INGESTION", 
         "Ryu SDN Controller collects telemetry:\n* Channel A (Periodic): 2.0s polling for\n  OFPFlowStatsRequest & PortStats\n* Channel B (Event-Driven): PacketIn for\n  packet sizing & PortStatus for link cuts", 
         61, 95, 38, 22, "#fbbf24"),

        ("3. SLIDING-WINDOW FEATURE EXTRACTION", 
         "Calculates 9 pure telemetry metrics:\n* Delta Packet & Byte Rates (pps, Bps)\n* Shannon IP Entropy: -SUM(p * log2(p))\n* IP Diversity Count & Pkt Size Mean/Std\n* Port Status (1/0) & Dropped Packet Counts", 
         112, 95, 38, 22, "#34d399"),

        ("4. ML INFERENCE & HARDWARE OVERRIDE", 
         "Multi-Class Model (Gradient Boosting / RF):\n* Sub-15ms live feature evaluation\n* Check Port Status: If 0 -> Link Failure override\n* Predicts class C in {Normal, Flash, DDoS, Congest, LinkFail}\n* Computes classification confidence score", 
         112, 60, 38, 22, "#818cf8"),
    ]

    for title, desc, x, y, w, h, col in steps:
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.8,rounding_size=1.5",
                             facecolor="#1e293b", edgecolor=col, linewidth=2)
        ax.add_patch(box)
        ax.text(x + w/2, y + h - 3, title, ha='center', va='center', fontsize=9, fontweight='bold', color=col)
        ax.text(x + 2, y + (h/2) - 2.5, desc, ha='left', va='center', fontsize=7.2, color="#f1f5f9")

    # Arrows between top steps
    ax.annotate('', xy=(61, 106), xytext=(48, 106), arrowprops=dict(arrowstyle="->", color="#38bdf8", lw=2.5))
    ax.annotate('', xy=(112, 106), xytext=(99, 106), arrowprops=dict(arrowstyle="->", color="#fbbf24", lw=2.5))
    ax.annotate('', xy=(131, 82), xytext=(131, 95), arrowprops=dict(arrowstyle="->", color="#34d399", lw=2.5))

    # Arrow from Step 4 to Decision Box
    ax.annotate('', xy=(85, 71), xytext=(112, 71), arrowprops=dict(arrowstyle="->", color="#818cf8", lw=2.5))

    # STEP 5: Remediation Decision Hub
    dec_box = FancyBboxPatch((20, 60), 65, 22, boxstyle="round,pad=0.8,rounding_size=1.5",
                             facecolor="#1e1e38", edgecolor="#f43f5e", linewidth=2.2)
    ax.add_patch(dec_box)
    ax.text(52.5, 79, "5. AUTONOMIC DIFFERENTIATED REMEDIATION ENGINE", ha='center', va='center', fontsize=10, fontweight='bold', color="#f43f5e")
    ax.text(52.5, 70, "Evaluates Predicted Class & Dispatches Surgical OpenFlow Directives:\nMatches condition to exact network optimization or mitigation strategy,\neliminating collateral damage to legitimate users and core backup paths.", 
            ha='center', va='center', fontsize=7.8, color="#cbd5e1")

    # 5 Branch Action Boxes below Step 5
    branches = [
        ("BRANCH 1: NORMAL", "Action: Passive Baseline\n* Retain Path A routing\n* Clear temporary overrides\n* Restore primary flows", 8, 22, 26, 26, "#38bdf8"),
        ("BRANCH 2: FLASH-CROWD", "Action: OFPGT_SELECT\n* OpenFlow 1.3 Group Table\n* 50/50 dual-path distribution\n* Zero legitimate drop rate", 38, 22, 26, 26, "#34d399"),
        ("BRANCH 3: DDOS FLOOD", "Action: Surgical Ingress Drop\n* High-priority (150) FlowMod\n* Drop attacker source at s1\n* Path A/B preserved clean", 68, 22, 26, 26, "#f43f5e"),
        ("BRANCH 4: CONGESTION", "Action: Preemptive Diversion\n* Divert bulk flows to Path B\n* Priority 80 routing rule\n* Prevents queue overflow", 98, 22, 26, 26, "#fbbf24"),
        ("BRANCH 5: LINK FAILURE", "Action: Sub-50ms Failover\n* Hardware interrupt trigger\n* Instant switchover to Path B\n* Zero TCP session loss", 128, 22, 26, 26, "#c084fc"),
    ]

    for title, desc, x, y, w, h, col in branches:
        bb = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6,rounding_size=1.2",
                            facecolor="#1e293b", edgecolor=col, linewidth=1.8)
        ax.add_patch(bb)
        ax.text(x + w/2, y + h - 3, title, ha='center', va='center', fontsize=7.8, fontweight='bold', color=col)
        ax.text(x + 2, y + (h/2) - 1.5, desc, ha='left', va='center', fontsize=7, color="#f8fafc")
        # Arrow from Decision Hub to each Branch
        ax.annotate('', xy=(x + w/2, y + h), xytext=(52.5, 60),
                    arrowprops=dict(arrowstyle="->", color=col, lw=1.5, connectionstyle="angle,angleA=0,angleB=90,rad=5"))

    # STEP 6: Closed-Loop Verification & Live State Persistence (Bottom banner)
    verif_box = FancyBboxPatch((8, 4), 146, 12, boxstyle="round,pad=0.6,rounding_size=1.2",
                               facecolor="#064e3b", edgecolor="#34d399", linewidth=1.5)
    ax.add_patch(verif_box)
    ax.text(81, 12.5, "6. CLOSED-LOOP SLA VERIFICATION, TELEMETRY PERSISTENCE & AUTO-RESTORATION", 
            ha='center', va='center', fontsize=9.5, fontweight='bold', color="#a7f3d0")
    ax.text(81, 7.5, "Writes state to data/live_remediation_status.json | Appends to remediation_events.log | Live updates in Streamlit UI\nNext polling epoch continuously reassesses datapath. When traffic subsides, controller restores default baseline.", 
            ha='center', va='center', fontsize=7.5, color="#e2e8f0")

    # Feedback loop arrows
    for x in [21, 51, 81, 111, 141]:
        ax.annotate('', xy=(x, 16), xytext=(x, 22), arrowprops=dict(arrowstyle="->", color="#34d399", lw=1.2))

    # Return loop back to Step 1/2
    ax.annotate('', xy=(10, 106), xytext=(8, 10),
                arrowprops=dict(arrowstyle="->", color="#38bdf8", lw=1.8, connectionstyle="angle,angleA=180,angleB=90,rad=5"))

    plt.tight_layout()
    fig.savefig(output_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
    plt.close(fig)
    print(f"[OK] Saved Workflow Diagram PNG to: {output_path}")

def create_svg_block_diagram(output_path):
    svg_code = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 900" width="100%" height="100%" style="background:#0f172a; font-family:'Segoe UI', system-ui, -apple-system, sans-serif;">
  <defs>
    <filter id="shadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#000" flood-opacity="0.4"/>
    </filter>
    <linearGradient id="blueGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0284c7"/>
      <stop offset="100%" stop-color="#0369a1"/>
    </linearGradient>
    <linearGradient id="purpleGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#6366f1"/>
      <stop offset="100%" stop-color="#4f46e5"/>
    </linearGradient>
    <linearGradient id="emeraldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#10b981"/>
      <stop offset="100%" stop-color="#059669"/>
    </linearGradient>
    <linearGradient id="amberGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#f59e0b"/>
      <stop offset="100%" stop-color="#d97706"/>
    </linearGradient>
    <linearGradient id="roseGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#f43f5e"/>
      <stop offset="100%" stop-color="#e11d48"/>
    </linearGradient>
    <marker id="arrowBlue" markerWidth="10" markerHeight="10" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L9,3 z" fill="#38bdf8"/>
    </marker>
    <marker id="arrowGreen" markerWidth="10" markerHeight="10" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L9,3 z" fill="#34d399"/>
    </marker>
    <marker id="arrowAmber" markerWidth="10" markerHeight="10" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L9,3 z" fill="#fbbf24"/>
    </marker>
    <marker id="arrowRose" markerWidth="10" markerHeight="10" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L9,3 z" fill="#f43f5e"/>
    </marker>
  </defs>

  <!-- Title -->
  <text x="600" y="45" text-anchor="middle" fill="#38bdf8" font-size="24" font-weight="bold" letter-spacing="1">CONTEXT-AWARE SDN: SYSTEM ARCHITECTURE BLOCK DIAGRAM</text>
  <text x="600" y="70" text-anchor="middle" fill="#94a3b8" font-size="13">Unified Multi-Class Network Anomaly Classification &amp; Differentiated Auto-Remediation</text>

  <!-- LAYER 4: ORCHESTRATION & DASHBOARD (TOP) -->
  <rect x="40" y="90" width="1120" height="90" rx="12" fill="#1e293b" stroke="#38bdf8" stroke-width="1.5" filter="url(#shadow)"/>
  <text x="60" y="115" fill="#38bdf8" font-size="13" font-weight="bold">MANAGEMENT, EVALUATION &amp; USER INTERACTION LAYER</text>
  
  <rect x="60" y="125" width="250" height="42" rx="6" fill="#0f172a" stroke="#0284c7" stroke-width="1"/>
  <text x="185" y="143" text-anchor="middle" fill="#f8fafc" font-size="11" font-weight="bold">Traffic Generation Suite</text>
  <text x="185" y="158" text-anchor="middle" fill="#94a3b8" font-size="9.5">Normal, Flash, DDoS, Congestion, Cut</text>

  <rect x="330" y="125" width="250" height="42" rx="6" fill="#0f172a" stroke="#10b981" stroke-width="1"/>
  <text x="455" y="143" text-anchor="middle" fill="#f8fafc" font-size="11" font-weight="bold">Streamlit Live Dashboard</text>
  <text x="455" y="158" text-anchor="middle" fill="#94a3b8" font-size="9.5">streamlit_app.py Interactive Web UI</text>

  <rect x="600" y="125" width="260" height="42" rx="6" fill="#0f172a" stroke="#f59e0b" stroke-width="1"/>
  <text x="730" y="143" text-anchor="middle" fill="#f8fafc" font-size="11" font-weight="bold">Telemetry &amp; Event Persistence</text>
  <text x="730" y="158" text-anchor="middle" fill="#94a3b8" font-size="9.5">live_remediation_status.json / logs</text>

  <rect x="880" y="125" width="260" height="42" rx="6" fill="#0f172a" stroke="#c084fc" stroke-width="1"/>
  <text x="1010" y="143" text-anchor="middle" fill="#f8fafc" font-size="11" font-weight="bold">Topology Visualizer &amp; Reports</text>
  <text x="1010" y="158" text-anchor="middle" fill="#94a3b8" font-size="9.5">D3.js GUI &amp; 14-Slide PDF/PPTX Decks</text>

  <!-- LAYER 3: RYU SDN CONTROLLER (MIDDLE) -->
  <rect x="40" y="210" width="1120" height="320" rx="16" fill="#132238" stroke="#6366f1" stroke-width="2.5" filter="url(#shadow)"/>
  <text x="60" y="240" fill="#818cf8" font-size="15" font-weight="bold">RYU SDN CONTROLLER &amp; AUTONOMIC CLOSED-LOOP ENGINE (Control Plane)</text>

  <!-- Module 1: Base Forwarding -->
  <rect x="60" y="255" width="250" height="255" rx="10" fill="#1e293b" stroke="#38bdf8" stroke-width="1.5"/>
  <text x="185" y="282" text-anchor="middle" fill="#38bdf8" font-size="13" font-weight="bold">Base Forwarding &amp; Poller</text>
  <text x="75" y="310" fill="#cbd5e1" font-size="10.5">File: multipath_switch.py</text>
  <text x="75" y="328" fill="#cbd5e1" font-size="10.5">File: sdn_monitor.py</text>
  <text x="75" y="355" fill="#94a3b8" font-size="10">• 2.0s Periodic Stats Loop</text>
  <text x="75" y="375" fill="#94a3b8" font-size="10">• OFPFlowStatsRequest</text>
  <text x="75" y="395" fill="#94a3b8" font-size="10">• OFPPortStatsRequest</text>
  <text x="75" y="415" fill="#94a3b8" font-size="10">• EventOFPPacketIn Hook</text>
  <text x="75" y="435" fill="#94a3b8" font-size="10">• EventOFPPortStatus Handler</text>
  <text x="75" y="465" fill="#38bdf8" font-size="9.5">Dual-Channel Telemetry Stream</text>

  <!-- Module 2: Feature Engineering -->
  <rect x="330" y="255" width="250" height="255" rx="10" fill="#1e293b" stroke="#fbbf24" stroke-width="1.5"/>
  <text x="455" y="282" text-anchor="middle" fill="#fbbf24" font-size="13" font-weight="bold">Sliding Feature Math</text>
  <text x="345" y="310" fill="#cbd5e1" font-size="10.5">Mathematical Telemetry Formulation</text>
  <text x="345" y="335" fill="#94a3b8" font-size="10">• Shannon IP Entropy H(X)</text>
  <text x="345" y="355" fill="#94a3b8" font-size="10">• Packet Rate ΔP / Δt (pps)</text>
  <text x="345" y="375" fill="#94a3b8" font-size="10">• Byte Rate ΔB / Δt (Bps)</text>
  <text x="345" y="395" fill="#94a3b8" font-size="10">• Unique Source IPs Count</text>
  <text x="345" y="415" fill="#94a3b8" font-size="10">• Packet Size Mean (μ) &amp; Std (σ)</text>
  <text x="345" y="435" fill="#94a3b8" font-size="10">• Core Port Status (UP=1 / DOWN=0)</text>
  <text x="345" y="455" fill="#94a3b8" font-size="10">• RX/TX Dropped Counter Deltas</text>
  <text x="345" y="485" fill="#fbbf24" font-size="9.5">9-Dimensional Feature Vector</text>

  <!-- Module 3: ML Inference -->
  <rect x="600" y="255" width="260" height="255" rx="10" fill="#1e293b" stroke="#34d399" stroke-width="1.5"/>
  <text x="730" y="282" text-anchor="middle" fill="#34d399" font-size="13" font-weight="bold">ML Classifier Engine</text>
  <text x="615" y="310" fill="#cbd5e1" font-size="10.5">Model: sdn_classifier.joblib</text>
  <text x="615" y="335" fill="#94a3b8" font-size="10">• Champion: Gradient Boosting</text>
  <text x="615" y="355" fill="#94a3b8" font-size="10">• 10-Fold CV: 92.54% Accuracy</text>
  <text x="615" y="375" fill="#94a3b8" font-size="10">• Live Inference Latency: &lt; 15 ms</text>
  <text x="615" y="400" fill="#34d399" font-size="10.5" font-weight="bold">Multi-Class Predictions:</text>
  <text x="615" y="420" fill="#94a3b8" font-size="9.5">1. Normal Baseline</text>
  <text x="615" y="438" fill="#94a3b8" font-size="9.5">2. Flash-Crowd Surge</text>
  <text x="615" y="456" fill="#94a3b8" font-size="9.5">3. DDoS Flood Attack</text>
  <text x="615" y="474" fill="#94a3b8" font-size="9.5">4. Slow Buffer Congestion</text>
  <text x="615" y="492" fill="#94a3b8" font-size="9.5">5. Physical Link Failure</text>

  <!-- Module 4: Differentiated Remediation -->
  <rect x="880" y="255" width="260" height="255" rx="10" fill="#1e293b" stroke="#f43f5e" stroke-width="1.5"/>
  <text x="1010" y="282" text-anchor="middle" fill="#f43f5e" font-size="13" font-weight="bold">Differentiated Remediation</text>
  <text x="895" y="310" fill="#cbd5e1" font-size="10.5">File: remediation_engine.py</text>
  <text x="895" y="335" fill="#94a3b8" font-size="9.5"><tspan font-weight="bold" fill="#34d399">Flash-Crowd:</tspan> OFPGT_SELECT Group</text>
  <text x="895" y="350" fill="#64748b" font-size="9">50/50 Dual Core Load Balance (0% drop)</text>
  <text x="895" y="370" fill="#94a3b8" font-size="9.5"><tspan font-weight="bold" fill="#f43f5e">DDoS Flood:</tspan> Priority 150 FlowMod</text>
  <text x="895" y="385" fill="#64748b" font-size="9">Surgical drop of attacker at Ingress s1</text>
  <text x="895" y="405" fill="#94a3b8" font-size="9.5"><tspan font-weight="bold" fill="#fbbf24">Congestion:</tspan> Priority 80 FlowMod</text>
  <text x="895" y="420" fill="#64748b" font-size="9">Preemptive bulk shift to Path B</text>
  <text x="895" y="440" fill="#94a3b8" font-size="9.5"><tspan font-weight="bold" fill="#c084fc">Link Failure:</tspan> Priority 120 FlowMod</text>
  <text x="895" y="455" fill="#64748b" font-size="9">Sub-50ms instant failover to Path B</text>
  <text x="895" y="475" fill="#94a3b8" font-size="9.5"><tspan font-weight="bold" fill="#38bdf8">Normal:</tspan> Clear override rules</text>

  <!-- Arrows in Controller -->
  <line x1="310" y1="380" x2="326" y2="380" stroke="#fbbf24" stroke-width="2.5" marker-end="url(#arrowAmber)"/>
  <line x1="580" y1="380" x2="596" y2="380" stroke="#34d399" stroke-width="2.5" marker-end="url(#arrowGreen)"/>
  <line x1="860" y1="380" x2="876" y2="380" stroke="#f43f5e" stroke-width="2.5" marker-end="url(#arrowRose)"/>

  <!-- SOUTHBOUND PROTOCOL BAR -->
  <rect x="40" y="555" width="1120" height="45" rx="8" fill="#1e293b" stroke="#38bdf8" stroke-width="1.5"/>
  <text x="600" y="575" text-anchor="middle" fill="#38bdf8" font-size="12" font-weight="bold">SOUTHBOUND CONTROL INTERFACE: OPENFLOW 1.3 PROTOCOL (TCP Port 6653)</text>
  <text x="600" y="591" text-anchor="middle" fill="#94a3b8" font-size="9.5">Stats Replies, Port-Status Alerts, Packet-In ◄════════════════════► Flow-Mod Rules, Group-Mod (SELECT) Tables, Packet-Out</text>

  <!-- Connecting Southbound Arrows -->
  <line x1="185" y1="510" x2="185" y2="550" stroke="#38bdf8" stroke-width="2" marker-end="url(#arrowBlue)"/>
  <line x1="1010" y1="510" x2="1010" y2="550" stroke="#f43f5e" stroke-width="2.5" marker-end="url(#arrowRose)"/>

  <!-- LAYER 1: DATA PLANE (BOTTOM) -->
  <rect x="40" y="625" width="1120" height="240" rx="16" fill="#111c33" stroke="#1e3a8a" stroke-width="2" stroke-dasharray="6,4" filter="url(#shadow)"/>
  <text x="60" y="652" fill="#60a5fa" font-size="14" font-weight="bold">DATA PLANE: MININET MULTI-PATH TOPOLOGY &amp; OPEN vSWITCHES</text>

  <!-- Client hosts h1-h5 -->
  <g transform="translate(60, 680)">
    <rect x="0" y="0" width="60" height="50" rx="6" fill="#1e293b" stroke="#38bdf8" stroke-width="1.5"/>
    <text x="30" y="22" text-anchor="middle" fill="#f8fafc" font-size="11" font-weight="bold">Client h1</text>
    <text x="30" y="38" text-anchor="middle" fill="#94a3b8" font-size="9">10.0.0.1</text>

    <rect x="75" y="0" width="60" height="50" rx="6" fill="#1e293b" stroke="#38bdf8" stroke-width="1.5"/>
    <text x="105" y="22" text-anchor="middle" fill="#f8fafc" font-size="11" font-weight="bold">Client h2</text>
    <text x="105" y="38" text-anchor="middle" fill="#94a3b8" font-size="9">10.0.0.2</text>

    <rect x="150" y="0" width="60" height="50" rx="6" fill="#1e293b" stroke="#38bdf8" stroke-width="1.5"/>
    <text x="180" y="22" text-anchor="middle" fill="#f8fafc" font-size="11" font-weight="bold">Client h3</text>
    <text x="180" y="38" text-anchor="middle" fill="#94a3b8" font-size="9">10.0.0.3</text>

    <rect x="225" y="0" width="60" height="50" rx="6" fill="#1e293b" stroke="#38bdf8" stroke-width="1.5"/>
    <text x="255" y="22" text-anchor="middle" fill="#f8fafc" font-size="11" font-weight="bold">Client h4</text>
    <text x="255" y="38" text-anchor="middle" fill="#94a3b8" font-size="9">10.0.0.4</text>

    <rect x="300" y="0" width="60" height="50" rx="6" fill="#1e293b" stroke="#38bdf8" stroke-width="1.5"/>
    <text x="330" y="22" text-anchor="middle" fill="#f8fafc" font-size="11" font-weight="bold">Client h5</text>
    <text x="330" y="38" text-anchor="middle" fill="#94a3b8" font-size="9">10.0.0.5</text>
    <text x="180" y="70" text-anchor="middle" fill="#38bdf8" font-size="9.5">Access Links: 100 Mbps, 1ms delay</text>
  </g>

  <!-- Ingress Switch s1 -->
  <rect x="460" y="705" width="130" height="65" rx="8" fill="#1e293b" stroke="#fbbf24" stroke-width="2"/>
  <text x="525" y="732" text-anchor="middle" fill="#fbbf24" font-size="12" font-weight="bold">Ingress Switch s1</text>
  <text x="525" y="750" text-anchor="middle" fill="#94a3b8" font-size="10">OVS DPID: 0x01</text>

  <!-- Path A Switch s2 -->
  <rect x="650" y="660" width="150" height="60" rx="8" fill="#1e293b" stroke="#34d399" stroke-width="1.5"/>
  <text x="725" y="684" text-anchor="middle" fill="#34d399" font-size="11" font-weight="bold">Path A: Switch s2</text>
  <text x="725" y="702" text-anchor="middle" fill="#94a3b8" font-size="9.5">Core: 10 Mbps, 5ms delay</text>

  <!-- Path B Switch s3 -->
  <rect x="650" y="755" width="150" height="60" rx="8" fill="#1e293b" stroke="#818cf8" stroke-width="1.5"/>
  <text x="725" y="779" text-anchor="middle" fill="#818cf8" font-size="11" font-weight="bold">Path B: Switch s3</text>
  <text x="725" y="797" text-anchor="middle" fill="#94a3b8" font-size="9.5">Core: 10 Mbps, 10ms delay</text>

  <!-- Egress Switch s4 -->
  <rect x="850" y="705" width="120" height="65" rx="8" fill="#1e293b" stroke="#fbbf24" stroke-width="2"/>
  <text x="910" y="732" text-anchor="middle" fill="#fbbf24" font-size="12" font-weight="bold">Egress Switch s4</text>
  <text x="910" y="750" text-anchor="middle" fill="#94a3b8" font-size="10">OVS DPID: 0x04</text>

  <!-- Target Server h6 -->
  <rect x="1020" y="705" width="110" height="65" rx="8" fill="#1e293b" stroke="#f43f5e" stroke-width="2"/>
  <text x="1075" y="732" text-anchor="middle" fill="#f43f5e" font-size="12" font-weight="bold">Server h6</text>
  <text x="1075" y="750" text-anchor="middle" fill="#cbd5e1" font-size="10">10.0.0.6</text>
  <text x="1075" y="763" text-anchor="middle" fill="#94a3b8" font-size="8.5">HTTP / iPerf3</text>

  <!-- Internal Lines in Data Plane -->
  <line x1="420" y1="737" x2="455" y2="737" stroke="#38bdf8" stroke-width="2" marker-end="url(#arrowBlue)"/>
  <line x1="590" y1="725" x2="645" y2="690" stroke="#34d399" stroke-width="2" marker-end="url(#arrowGreen)"/>
  <line x1="590" y1="750" x2="645" y2="785" stroke="#818cf8" stroke-width="2" marker-end="url(#arrowBlue)"/>
  <line x1="800" y1="690" x2="845" y2="725" stroke="#34d399" stroke-width="2" marker-end="url(#arrowGreen)"/>
  <line x1="800" y1="785" x2="845" y2="750" stroke="#818cf8" stroke-width="2" marker-end="url(#arrowBlue)"/>
  <line x1="970" y1="737" x2="1015" y2="737" stroke="#f43f5e" stroke-width="2" marker-end="url(#arrowRose)"/>

  <!-- Protocol connection between Southbound and Data Plane -->
  <line x1="525" y1="600" x2="525" y2="700" stroke="#fbbf24" stroke-width="2" stroke-dasharray="4,3" marker-end="url(#arrowAmber)"/>
  <line x1="910" y1="600" x2="910" y2="700" stroke="#fbbf24" stroke-width="2" stroke-dasharray="4,3" marker-end="url(#arrowAmber)"/>
</svg>'''
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(svg_code)
    print(f"[OK] Saved Block Diagram SVG to: {output_path}")

def create_svg_workflow_diagram(output_path):
    svg_code = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 950" width="100%" height="100%" style="background:#0f172a; font-family:'Segoe UI', system-ui, -apple-system, sans-serif;">
  <defs>
    <filter id="shadowWf" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#000" flood-opacity="0.4"/>
    </filter>
    <marker id="arrB" markerWidth="10" markerHeight="10" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L9,3 z" fill="#38bdf8"/>
    </marker>
    <marker id="arrG" markerWidth="10" markerHeight="10" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L9,3 z" fill="#34d399"/>
    </marker>
    <marker id="arrY" markerWidth="10" markerHeight="10" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L9,3 z" fill="#fbbf24"/>
    </marker>
    <marker id="arrR" markerWidth="10" markerHeight="10" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L9,3 z" fill="#f43f5e"/>
    </marker>
    <marker id="arrP" markerWidth="10" markerHeight="10" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L9,3 z" fill="#c084fc"/>
    </marker>
  </defs>

  <!-- Title -->
  <text x="600" y="45" text-anchor="middle" fill="#38bdf8" font-size="24" font-weight="bold" letter-spacing="1">CONTEXT-AWARE SDN: END-TO-END AUTONOMIC WORKFLOW</text>
  <text x="600" y="70" text-anchor="middle" fill="#94a3b8" font-size="13">Closed-Loop Process: Telemetry Collection ➔ Sliding Feature Math ➔ AI Inference ➔ Differentiated Action ➔ Feedback</text>

  <!-- STEP 1 -->
  <rect x="40" y="100" width="250" height="150" rx="10" fill="#1e293b" stroke="#38bdf8" stroke-width="1.8" filter="url(#shadowWf)"/>
  <rect x="40" y="100" width="250" height="32" rx="10" fill="#0284c7"/>
  <text x="165" y="122" text-anchor="middle" fill="#fff" font-size="11.5" font-weight="bold">1. TRAFFIC INGRESS</text>
  <text x="55" y="152" fill="#cbd5e1" font-size="10">• Hosts h1-h5 transmit toward h6</text>
  <text x="55" y="172" fill="#cbd5e1" font-size="10">• Normal traffic (web/file transfer)</text>
  <text x="55" y="192" fill="#cbd5e1" font-size="10">• Flash-Crowd (5 client burst)</text>
  <text x="55" y="212" fill="#cbd5e1" font-size="10">• DDoS flood (SYN/UDP flood)</text>
  <text x="55" y="232" fill="#cbd5e1" font-size="10">• Congestion ramp or Link Cut</text>

  <!-- Arrow 1 -> 2 -->
  <line x1="290" y1="175" x2="325" y2="175" stroke="#38bdf8" stroke-width="3" marker-end="url(#arrB)"/>

  <!-- STEP 2 -->
  <rect x="330" y="100" width="260" height="150" rx="10" fill="#1e293b" stroke="#fbbf24" stroke-width="1.8" filter="url(#shadowWf)"/>
  <rect x="330" y="100" width="260" height="32" rx="10" fill="#d97706"/>
  <text x="460" y="122" text-anchor="middle" fill="#fff" font-size="11.5" font-weight="bold">2. TELEMETRY INGESTION</text>
  <text x="345" y="152" fill="#cbd5e1" font-size="10">• Periodic Polling (every 2.0s):</text>
  <text x="360" y="170" fill="#94a3b8" font-size="9.5">OFPFlowStats &amp; OFPPortStats</text>
  <text x="345" y="192" fill="#cbd5e1" font-size="10">• Event-Driven Telemetry:</text>
  <text x="360" y="210" fill="#94a3b8" font-size="9.5">Packet-In (entropy &amp; sizes)</text>
  <text x="360" y="228" fill="#94a3b8" font-size="9.5">Port-Status (link cut interrupt)</text>

  <!-- Arrow 2 -> 3 -->
  <line x1="590" y1="175" x2="625" y2="175" stroke="#fbbf24" stroke-width="3" marker-end="url(#arrY)"/>

  <!-- STEP 3 -->
  <rect x="630" y="100" width="260" height="150" rx="10" fill="#1e293b" stroke="#34d399" stroke-width="1.8" filter="url(#shadowWf)"/>
  <rect x="630" y="100" width="260" height="32" rx="10" fill="#059669"/>
  <text x="760" y="122" text-anchor="middle" fill="#fff" font-size="11.5" font-weight="bold">3. FEATURE EXTRACTION</text>
  <text x="645" y="150" fill="#cbd5e1" font-size="9.5">• Shannon Entropy: H = -Σ p log₂(p)</text>
  <text x="645" y="170" fill="#cbd5e1" font-size="9.5">• Δ Packet Rate (pps) &amp; Δ Byte Rate</text>
  <text x="645" y="190" fill="#cbd5e1" font-size="9.5">• Unique Source IPs count</text>
  <text x="645" y="210" fill="#cbd5e1" font-size="9.5">• Packet Size Mean &amp; Std Deviation</text>
  <text x="645" y="230" fill="#cbd5e1" font-size="9.5">• Port status (1/0) &amp; Dropped counters</text>

  <!-- Arrow 3 -> 4 -->
  <line x1="890" y1="175" x2="925" y2="175" stroke="#34d399" stroke-width="3" marker-end="url(#arrG)"/>

  <!-- STEP 4 -->
  <rect x="930" y="100" width="230" height="150" rx="10" fill="#1e293b" stroke="#818cf8" stroke-width="1.8" filter="url(#shadowWf)"/>
  <rect x="930" y="100" width="230" height="32" rx="10" fill="#4f46e5"/>
  <text x="1045" y="122" text-anchor="middle" fill="#fff" font-size="11.5" font-weight="bold">4. AI CLASSIFICATION</text>
  <text x="945" y="152" fill="#cbd5e1" font-size="10">• 9-D Feature Vector Input</text>
  <text x="945" y="172" fill="#cbd5e1" font-size="10">• Model: Gradient Boosting / RF</text>
  <text x="945" y="192" fill="#cbd5e1" font-size="10">• Sub-15ms live inference</text>
  <text x="945" y="212" fill="#cbd5e1" font-size="10">• Output: Class + Confidence %</text>
  <text x="945" y="232" fill="#818cf8" font-size="9.5">Fail-Safe: HW Port=0 ➔ LinkCut</text>

  <!-- Downward Arrow from Step 4 to Step 5 -->
  <path d="M 1045,250 L 1045,290 L 600,290 L 600,325" fill="none" stroke="#818cf8" stroke-width="3" marker-end="url(#arrP)"/>

  <!-- STEP 5: AUTONOMIC DECISION ENGINE -->
  <rect x="150" y="335" width="900" height="80" rx="12" fill="#172554" stroke="#f43f5e" stroke-width="2.5" filter="url(#shadowWf)"/>
  <text x="600" y="365" text-anchor="middle" fill="#f43f5e" font-size="15" font-weight="bold">5. AUTONOMIC DIFFERENTIATED REMEDIATION ENGINE (State Machine)</text>
  <text x="600" y="390" text-anchor="middle" fill="#cbd5e1" font-size="11.5">Evaluates predicted condition and triggers surgical, class-specific OpenFlow datapath reprogramming,</text>
  <text x="600" y="405" text-anchor="middle" fill="#94a3b8" font-size="10.5">guaranteeing zero collateral damage to legitimate traffic and protecting backup core links.</text>

  <!-- 5 BRANCHES OF DIFFERENTIATED REMEDIATION -->
  
  <!-- Branch 1: Normal -->
  <rect x="40" y="470" width="210" height="230" rx="10" fill="#1e293b" stroke="#38bdf8" stroke-width="1.8" filter="url(#shadowWf)"/>
  <rect x="40" y="470" width="210" height="32" rx="10" fill="#0284c7"/>
  <text x="145" y="492" text-anchor="middle" fill="#fff" font-size="11" font-weight="bold">BRANCH 1: NORMAL</text>
  <text x="55" y="525" fill="#38bdf8" font-size="10.5" font-weight="bold">Status: Baseline</text>
  <text x="55" y="548" fill="#cbd5e1" font-size="9.5">• Primary Path A active</text>
  <text x="55" y="570" fill="#cbd5e1" font-size="9.5">• Passive 2.0s monitoring</text>
  <text x="55" y="592" fill="#cbd5e1" font-size="9.5">• Clear temporary rules</text>
  <text x="55" y="614" fill="#cbd5e1" font-size="9.5">• Priority 0/1 baseline</text>
  <text x="55" y="645" fill="#94a3b8" font-size="9">Path B kept on hot standby for immediate failover.</text>

  <!-- Branch 2: Flash Crowd -->
  <rect x="270" y="470" width="210" height="230" rx="10" fill="#1e293b" stroke="#34d399" stroke-width="1.8" filter="url(#shadowWf)"/>
  <rect x="270" y="470" width="210" height="32" rx="10" fill="#059669"/>
  <text x="375" y="492" text-anchor="middle" fill="#fff" font-size="11" font-weight="bold">BRANCH 2: FLASH-CROWD</text>
  <text x="285" y="525" fill="#34d399" font-size="10.5" font-weight="bold">Action: Group Table SELECT</text>
  <text x="285" y="548" fill="#cbd5e1" font-size="9.5">• OpenFlow 1.3 OFPGT_SELECT</text>
  <text x="285" y="570" fill="#cbd5e1" font-size="9.5">• 50/50 dual path load balance</text>
  <text x="285" y="592" fill="#cbd5e1" font-size="9.5">• Priority 100 flow instruction</text>
  <text x="285" y="614" fill="#34d399" font-size="9.5" font-weight="bold">• 0.0% Legitimate User Loss</text>
  <text x="285" y="636" fill="#cbd5e1" font-size="9.5">• 2.7x higher goodput</text>
  <text x="285" y="660" fill="#94a3b8" font-size="8.5">Both Path A and Path B utilized simultaneously.</text>

  <!-- Branch 3: DDoS Attack -->
  <rect x="500" y="470" width="210" height="230" rx="10" fill="#1e293b" stroke="#f43f5e" stroke-width="1.8" filter="url(#shadowWf)"/>
  <rect x="500" y="470" width="210" height="32" rx="10" fill="#e11d48"/>
  <text x="605" y="492" text-anchor="middle" fill="#fff" font-size="11" font-weight="bold">BRANCH 3: DDOS FLOOD</text>
  <text x="515" y="525" fill="#f43f5e" font-size="10.5" font-weight="bold">Action: Surgical Ingress Drop</text>
  <text x="515" y="548" fill="#cbd5e1" font-size="9.5">• Identifies malicious IP source</text>
  <text x="515" y="570" fill="#cbd5e1" font-size="9.5">• Priority 150 OFPFlowMod drop</text>
  <text x="515" y="592" fill="#cbd5e1" font-size="9.5">• Blocks attack at Ingress s1</text>
  <text x="515" y="614" fill="#34d399" font-size="9.5" font-weight="bold">• Core paths remain 100% clean</text>
  <text x="515" y="636" fill="#cbd5e1" font-size="9.5">• Legitimate flows preserved</text>
  <text x="515" y="660" fill="#94a3b8" font-size="8.5">Avoids toxic aggregate rerouting to backup.</text>

  <!-- Branch 4: Slow Congestion -->
  <rect x="730" y="470" width="210" height="230" rx="10" fill="#1e293b" stroke="#fbbf24" stroke-width="1.8" filter="url(#shadowWf)"/>
  <rect x="730" y="470" width="210" height="32" rx="10" fill="#d97706"/>
  <text x="835" y="492" text-anchor="middle" fill="#fff" font-size="11" font-weight="bold">BRANCH 4: CONGESTION</text>
  <text x="745" y="525" fill="#fbbf24" font-size="10.5" font-weight="bold">Action: Preemptive Diversion</text>
  <text x="745" y="548" fill="#cbd5e1" font-size="9.5">• Detects early queue escalation</text>
  <text x="745" y="570" fill="#cbd5e1" font-size="9.5">• Priority 80 FlowMod installed</text>
  <text x="745" y="592" fill="#cbd5e1" font-size="9.5">• Moves bulk flows to Path B</text>
  <text x="745" y="614" fill="#34d399" font-size="9.5" font-weight="bold">• Prevents buffer queue drop</text>
  <text x="745" y="636" fill="#cbd5e1" font-size="9.5">• Smooth latency transition</text>
  <text x="745" y="660" fill="#94a3b8" font-size="8.5">Engages at 85% capacity before saturation.</text>

  <!-- Branch 5: Link Failure -->
  <rect x="960" y="470" width="200" height="230" rx="10" fill="#1e293b" stroke="#c084fc" stroke-width="1.8" filter="url(#shadowWf)"/>
  <rect x="960" y="470" width="200" height="32" rx="10" fill="#7e22ce"/>
  <text x="1060" y="492" text-anchor="middle" fill="#fff" font-size="11" font-weight="bold">BRANCH 5: LINK FAILURE</text>
  <text x="975" y="525" fill="#c084fc" font-size="10.5" font-weight="bold">Action: Fast Port Failover</text>
  <text x="975" y="548" fill="#cbd5e1" font-size="9.5">• EventOFPPortStatus interrupt</text>
  <text x="975" y="570" fill="#cbd5e1" font-size="9.5">• Priority 120 override rules</text>
  <text x="975" y="592" fill="#cbd5e1" font-size="9.5">• Diverts 100% traffic to Path B</text>
  <text x="975" y="614" fill="#34d399" font-size="9.5" font-weight="bold">• Failover latency: &lt; 48 ms</text>
  <text x="975" y="636" fill="#cbd5e1" font-size="9.5">• Zero TCP session drops</text>
  <text x="975" y="660" fill="#94a3b8" font-size="8.5">Event-driven, eliminates 5-8s poll timeout.</text>

  <!-- Connectors from Engine to 5 Branches -->
  <path d="M 600,415 L 600,440 L 145,440 L 145,470" fill="none" stroke="#38bdf8" stroke-width="2" marker-end="url(#arrB)"/>
  <path d="M 600,415 L 600,440 L 375,440 L 375,470" fill="none" stroke="#34d399" stroke-width="2" marker-end="url(#arrG)"/>
  <path d="M 600,415 L 600,470" fill="none" stroke="#f43f5e" stroke-width="2" marker-end="url(#arrR)"/>
  <path d="M 600,415 L 600,440 L 835,440 L 835,470" fill="none" stroke="#fbbf24" stroke-width="2" marker-end="url(#arrY)"/>
  <path d="M 600,415 L 600,440 L 1060,440 L 1060,470" fill="none" stroke="#c084fc" stroke-width="2" marker-end="url(#arrP)"/>

  <!-- STEP 6: CLOSED-LOOP FEEDBACK & TELEMETRY LOGGING (BOTTOM) -->
  <rect x="40" y="740" width="1120" height="110" rx="12" fill="#064e3b" stroke="#34d399" stroke-width="2" filter="url(#shadowWf)"/>
  <text x="600" y="770" text-anchor="middle" fill="#a7f3d0" font-size="13.5" font-weight="bold">6. CLOSED-LOOP TELEMETRY PERSISTENCE, SLA MONITORING &amp; AUTO-RESTORATION</text>
  <text x="600" y="795" text-anchor="middle" fill="#e2e8f0" font-size="10.5">• Real-time state serialized to data/live_remediation_status.json for live Streamlit &amp; D3.js GUIs.</text>
  <text x="600" y="815" text-anchor="middle" fill="#e2e8f0" font-size="10.5">• Persistent event logging in data/remediation_events.log for audit trails and comparative benchmarking.</text>
  <text x="600" y="835" text-anchor="middle" fill="#e2e8f0" font-size="10.5">• Continuous autonomic polling loop: As soon as traffic stabilizes, the controller automatically clears overrides and restores Path A.</text>

  <!-- Connectors from branches to bottom -->
  <line x1="145" y1="700" x2="145" y2="738" stroke="#34d399" stroke-width="1.8" marker-end="url(#arrG)"/>
  <line x1="375" y1="700" x2="375" y2="738" stroke="#34d399" stroke-width="1.8" marker-end="url(#arrG)"/>
  <line x1="605" y1="700" x2="605" y2="738" stroke="#34d399" stroke-width="1.8" marker-end="url(#arrG)"/>
  <line x1="835" y1="700" x2="835" y2="738" stroke="#34d399" stroke-width="1.8" marker-end="url(#arrG)"/>
  <line x1="1060" y1="700" x2="1060" y2="738" stroke="#34d399" stroke-width="1.8" marker-end="url(#arrG)"/>

  <!-- Long feedback loop arrow from bottom back to Step 2 -->
  <path d="M 40,795 L 20,795 L 20,175 L 35,175" fill="none" stroke="#38bdf8" stroke-width="2.5" stroke-dasharray="6,4" marker-end="url(#arrB)"/>
  <text x="25" y="460" transform="rotate(-90 25,460)" fill="#38bdf8" font-size="10" font-weight="bold" letter-spacing="1">CONTINUOUS CLOSED-LOOP FEEDBACK</text>
</svg>'''
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(svg_code)
    print(f"[OK] Saved Workflow Diagram SVG to: {output_path}")

if __name__ == '__main__':
    project_root = os.path.abspath(os.path.dirname(__file__))
    diagrams_dir = os.path.join(project_root, "diagrams")
    os.makedirs(diagrams_dir, exist_ok=True)

    # 1. Block Diagram files
    bd_png_root = os.path.join(project_root, "block_diagram.png")
    bd_png_diag = os.path.join(diagrams_dir, "block_diagram.png")
    bd_svg_root = os.path.join(project_root, "block_diagram.svg")
    bd_svg_diag = os.path.join(diagrams_dir, "block_diagram.svg")

    create_block_diagram_png(bd_png_root)
    create_block_diagram_png(bd_png_diag)
    create_svg_block_diagram(bd_svg_root)
    create_svg_block_diagram(bd_svg_diag)

    # 2. Workflow Diagram files
    wf_png_root = os.path.join(project_root, "workflow_diagram.png")
    wf_png_diag = os.path.join(diagrams_dir, "workflow_diagram.png")
    wf_svg_root = os.path.join(project_root, "workflow_diagram.svg")
    wf_svg_diag = os.path.join(diagrams_dir, "workflow_diagram.svg")

    create_workflow_diagram_png(wf_png_root)
    create_workflow_diagram_png(wf_png_diag)
    create_svg_workflow_diagram(wf_svg_root)
    create_svg_workflow_diagram(wf_svg_diag)

    print("[SUCCESS] All Block and Workflow Diagrams generated in both SVG and high-res PNG formats!")
