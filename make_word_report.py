#!/usr/bin/env python3
"""
Convert Context-Aware SDN Project Report into a professional Microsoft Word document (.docx).
Applies executive corporate styling:
- Palette: Deep Navy (#0F2942), Sky Blue (#0284C7), Slate Gray (#64748B), Soft Tint (#F8FAFC)
- Typography: Arial / Calibri, clean hierarchies, proper spacing
- Tables: Shaded headers, borders, zebra rows, auto column widths
- Images: Cover image, Block Diagram, Workflow Diagram embedded with captions
- Code blocks: Shaded gray background, Consolas monospace font
- Callouts / Alert boxes: Left-bordered colored callout tables
- Header & Footer: Document title and page numbering
"""

import os
import sys
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    """Apply background color fill to table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    # Remove existing shd if any
    for child in list(tcPr):
        if child.tag.endswith('shd'):
            tcPr.remove(child)
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Set cell internal padding in twips (1/20 of a pt)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def set_table_borders(table, color="D1D5DB", sz="4", val="single"):
    """Set clean subtle borders on table."""
    tblPr = table._tbl.tblPr
    # Remove existing tblBorders
    for child in list(tblPr):
        if child.tag.endswith('tblBorders'):
            tblPr.remove(child)
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:left w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'<w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideV w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def add_header_footer(doc):
    """Add professional running header and footer with page numbers."""
    section = doc.sections[0]
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin = Inches(1.0)
    section.right_margin = Inches(1.0)

    # Header
    header = section.header
    hp = header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    hrun = hp.add_run("Context-Aware SDN: Technical Project Report")
    hrun.font.name = "Arial"
    hrun.font.size = Pt(8.5)
    hrun.font.color.rgb = RGBColor(100, 116, 139)

    # Footer
    footer = section.footer
    fp = footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    frun1 = fp.add_run("Software-Defined Networking & Autonomic Systems  |  Page ")
    frun1.font.name = "Arial"
    frun1.font.size = Pt(9)
    frun1.font.color.rgb = RGBColor(148, 163, 184)

    # Add dynamic PAGE field
    fldSimple1 = OxmlElement('w:fldSimple')
    fldSimple1.set(qn('w:instr'), 'PAGE')
    fp._p.append(fldSimple1)

    frun2 = fp.add_run(" of ")
    frun2.font.name = "Arial"
    frun2.font.size = Pt(9)
    frun2.font.color.rgb = RGBColor(148, 163, 184)

    # Add dynamic NUMPAGES field
    fldSimple2 = OxmlElement('w:fldSimple')
    fldSimple2.set(qn('w:instr'), 'NUMPAGES')
    fp._p.append(fldSimple2)

def add_callout(doc, text, title="KEY ARCHITECTURAL INSIGHT", border_color="0284C7", bg_color="F0F9FF"):
    """Render a styled left-bordered alert callout box."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, bg_color)
    set_cell_margins(cell, top=140, bottom=140, left=200, right=200)

    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:top w:val="none"/>'
        f'<w:left w:val="single" w:sz="24" w:space="0" w:color="{border_color}"/>'
        f'<w:bottom w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(tcBorders)

    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(4)
    run_t = p.add_run(f"📌 {title}\n")
    run_t.font.name = "Arial"
    run_t.font.bold = True
    run_t.font.size = Pt(10)
    run_t.font.color.rgb = RGBColor(2, 132, 199)

    run_body = p.add_run(text)
    run_body.font.name = "Calibri"
    run_body.font.size = Pt(10)
    run_body.font.color.rgb = RGBColor(30, 41, 59)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def add_code_block(doc, code_str, caption=None):
    """Render code or raw configuration in a styled monospace box."""
    if caption:
        cp = doc.add_paragraph()
        cp.paragraph_format.space_before = Pt(6)
        cp.paragraph_format.space_after = Pt(2)
        crun = cp.add_run(f"💻 {caption}")
        crun.font.name = "Arial"
        crun.font.size = Pt(9)
        crun.font.bold = True
        crun.font.color.rgb = RGBColor(71, 85, 105)

    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, "F8FAFC")
    set_cell_margins(cell, top=120, bottom=120, left=180, right=180)

    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="6" w:space="0" w:color="E2E8F0"/>'
        f'<w:left w:val="single" w:sz="18" w:space="0" w:color="3B82F6"/>'
        f'<w:bottom w:val="single" w:sz="6" w:space="0" w:color="E2E8F0"/>'
        f'<w:right w:val="single" w:sz="6" w:space="0" w:color="E2E8F0"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(tcBorders)

    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run(code_str)
    run.font.name = "Consolas"
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(15, 23, 42)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def format_custom_table(table, col_widths, headers, rows_data):
    """Format table with corporate dark header and alternating row tints."""
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table, color="CBD5E1", sz="4")

    # Header Row
    hdr_cells = table.rows[0].cells
    for i, title in enumerate(headers):
        hdr_cells[i].text = title
        set_cell_background(hdr_cells[i], "0F2942")  # Deep Navy
        set_cell_margins(hdr_cells[i], top=140, bottom=140, left=140, right=140)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in p.runs:
            run.font.name = "Arial"
            run.font.bold = True
            run.font.size = Pt(9.5)
            run.font.color.rgb = RGBColor(255, 255, 255)

    # Data Rows
    for r_idx, row_data in enumerate(rows_data):
        row_cells = table.add_row().cells
        bg_col = "F8FAFC" if (r_idx % 2 == 1) else "FFFFFF"
        for c_idx, cell_value in enumerate(row_data):
            row_cells[c_idx].text = str(cell_value)
            set_cell_background(row_cells[c_idx], bg_col)
            set_cell_margins(row_cells[c_idx], top=100, bottom=100, left=120, right=120)
            p = row_cells[c_idx].paragraphs[0]
            # Center alignment for short codes / numbers, left for text
            if len(str(cell_value)) < 15 and ("%" in str(cell_value) or str(cell_value).isdigit() or "UP" in str(cell_value) or "DOWN" in str(cell_value)):
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            for run in p.runs:
                run.font.name = "Calibri"
                run.font.size = Pt(9.5)
                run.font.color.rgb = RGBColor(30, 41, 59)
                if c_idx == 0:
                    run.font.bold = True

    # Set column widths
    for row in table.rows:
        for idx, width in enumerate(col_widths):
            row.cells[idx].width = width

def build_word_document():
    project_root = os.path.abspath(os.path.dirname(__file__))
    output_docx = os.path.join(project_root, "Context_Aware_SDN_Project_Report.docx")
    output_alias = os.path.join(project_root, "PROJECT_REPORT.docx")

    doc = Document()
    add_header_footer(doc)

    # Styles Setup
    styles = doc.styles
    normal_style = styles['Normal']
    normal_style.font.name = 'Calibri'
    normal_style.font.size = Pt(11)
    normal_style.font.color.rgb = RGBColor(30, 41, 59)
    normal_style.paragraph_format.line_spacing = 1.15
    normal_style.paragraph_format.space_after = Pt(6)

    # ========================== COVER PAGE ==========================
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(36)
    p_title.paragraph_format.space_after = Pt(6)
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_title = p_title.add_run("CONTEXT-AWARE SDN")
    r_title.font.name = "Arial"
    r_title.font.bold = True
    r_title.font.size = Pt(28)
    r_title.font.color.rgb = RGBColor(15, 41, 66)

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(18)
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_sub = p_sub.add_run("Unified Multi-Class Network Anomaly Classification &\nDifferentiated Auto-Remediation")
    r_sub.font.name = "Arial"
    r_sub.font.bold = True
    r_sub.font.size = Pt(15)
    r_sub.font.color.rgb = RGBColor(2, 132, 199)

    p_desc = doc.add_paragraph()
    p_desc.paragraph_format.space_before = Pt(0)
    p_desc.paragraph_format.space_after = Pt(24)
    p_desc.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_desc = p_desc.add_run("Technical Project Report & Autonomic Closed-Loop Architecture Specification")
    r_desc.font.name = "Calibri"
    r_desc.font.italic = True
    r_desc.font.size = Pt(11.5)
    r_desc.font.color.rgb = RGBColor(100, 116, 139)

    # Add Cover Image
    cover_img_path = os.path.join(project_root, "Cover_image.png")
    if os.path.exists(cover_img_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_after = Pt(24)
        run_img = p_img.add_run()
        run_img.add_picture(cover_img_path, width=Inches(6.2))

    # Metadata Table
    meta_headers = ["Project Specification", "Implementation Detail"]
    meta_rows = [
        ["Domain / Field", "Computer Networks, Operating Systems, SDN, Autonomic Computing, Machine Learning"],
        ["Controller Architecture", "Ryu SDN Controller (OpenFlow v1.3 Wire Protocol / Event-Driven Async Greenlet)"],
        ["Data Plane Emulation", "Mininet 2.3+ with Open vSwitch 2.17+ (4 Switches, 6 Hosts, Dual 10 Mbps Core Paths)"],
        ["Machine Learning Core", "Champion: Gradient Boosting (92.54% 10-fold CV Accuracy) | Fallback: Random Forest"],
        ["Target Operational States", "Normal Baseline, Flash-Crowd Surge, DDoS Flood, Slow Congestion, Link Failure"],
        ["Southbound Control Protocol", "OpenFlow 1.3 (FlowMods, OFPGT_SELECT Group Tables, PortStatus, Flow/Port Stats)"],
        ["Interactive Dashboards", "Streamlit Live Telemetry App (streamlit_app.py) & D3.js Topology Web GUI"]
    ]
    meta_table = doc.add_table(rows=1, cols=2)
    format_custom_table(meta_table, [Inches(2.2), Inches(4.3)], meta_headers, meta_rows)

    doc.add_page_break()

    # ========================== SECTION 1: EXECUTIVE SUMMARY ==========================
    h1 = doc.add_heading(level=1)
    r = h1.add_run("1. Executive Summary")
    r.font.name = "Arial"
    r.font.color.rgb = RGBColor(15, 41, 66)

    doc.add_paragraph(
        "Modern enterprise networks, cloud data centers, and telecommunications backbones increasingly rely on "
        "Software-Defined Networking (SDN) to achieve centralized visibility, dynamic flow programmability, and agility. "
        "However, traditional SDNs suffer from a critical architectural limitation: coarse, one-size-fits-all reactive policies. "
        "When sudden traffic spikes or anomalies emerge, existing controllers rely on binary thresholds (e.g., aggregate byte counters), "
        "triggering blunt network defense mechanisms. Consequently:"
    )

    p = doc.add_paragraph(style='List Bullet')
    p.add_run("Flash-Crowd Surges ").bold = True
    p.add_run("(legitimate e-commerce flash sales or news spikes) are misclassified as malicious volumetric Distributed Denial of Service (DDoS) attacks and aggressively dropped, causing severe financial loss, brand damage, and Service Level Agreement (SLA) violations.")

    p = doc.add_paragraph(style='List Bullet')
    p.add_run("Slow Buffer Congestion ").bold = True
    p.add_run("is treated with coarse aggregate rerouting only after packet drops occur, inducing route flapping and buffer bloat across redundant core paths.")

    p = doc.add_paragraph(style='List Bullet')
    p.add_run("Physical Link Failures ").bold = True
    p.add_run("and flow-level anomaly detection exist in isolated silos; link failovers often wait for polling timeouts (3.5 to 8.0 seconds), dropping in-flight TCP sessions.")

    add_callout(
        doc,
        "Context-Aware SDN resolves this core flaw by pairing an OpenFlow 1.3 Ryu controller with an embedded multi-class "
        "machine learning engine. By extracting real-time sliding-window telemetry metrics (including Shannon IP entropy, "
        "packet variance, volumetric rates, and hardware port status), the controller diagnoses the exact operational state "
        "among five distinct network conditions and executes surgical, class-specific OpenFlow auto-remediations in real time.",
        title="THE AUTONOMIC PARADIGM SHIFT"
    )

    doc.add_paragraph(
        "Key results achieved by Context-Aware SDN across controlled benchmarks include:\n"
        "• 0.0% Legitimate User Drop Rate during intense flash-crowd surges (compared to 65.4% drop under naive baselines).\n"
        "• 2.7x Higher Goodput achieved via OpenFlow 1.3 OFPGT_SELECT multipath group tables distributing load 50/50.\n"
        "• 100% Core Link Protection by dropping DDoS floods at the edge ingress switch rather than poisoning backup paths.\n"
        "• Sub-48ms Event-Driven Failover during physical cable cuts, preventing TCP session timeouts."
    )

    # ========================== SECTION 2: PROBLEM STATEMENT ==========================
    h2 = doc.add_heading(level=1)
    r = h2.add_run("2. The Core Flaw in Traditional SDNs")
    r.font.name = "Arial"
    r.font.color.rgb = RGBColor(15, 41, 66)

    doc.add_paragraph(
        "In classical network architectures, the data plane (packet forwarding) and the control plane (routing logic) are tightly "
        "coupled inside proprietary hardware switches. SDN revolutionized this paradigm by extracting the control plane into a centralized "
        "software controller. However, current production SDN deployments still make decisions using simplistic threshold-based rules:"
    )

    add_code_block(
        doc,
        "[ Traditional Naive SDN Logic ]\n"
        "Is Aggregate Traffic Volume > Threshold (e.g., 8.0 Mbps)?\n"
        "   ├── YES ──► 'Attack Detected!' ──► Hard Rate-Limit or Drop ALL Flows\n"
        "   └── NO  ──► Do Nothing (Passive Baseline)",
        caption="Traditional Naive SDN Decision Heuristic"
    )

    doc.add_paragraph(
        "This naive heuristic fails catastrophically in multi-tenant cloud and campus networks due to three structural weaknesses:\n\n"
        "1. The Flash-Crowd vs. DDoS Paradox: Both an e-commerce flash sale and a volumetric SYN/UDP flood present identical high aggregate bandwidth. "
        "However, a flash crowd originates from hundreds or thousands of legitimate distinct client IPs requesting valid content, whereas a DDoS flood originates from "
        "spoofed, randomized, or concentrated attack sources transmitting uniform, malformed payloads. A naive SDN cannot differentiate them and drops legitimate buyers.\n\n"
        "2. Reactive vs. Preemptive Congestion Handling: Standard controllers wait until physical interface drop counters increment before reacting. By the time flow rules are updated, hundreds of TCP windows have backed off, leading to severe latency degradation.\n\n"
        "3. Polling Latency in Link Failures: Typical controllers discover downed links by periodic heartbeat polling (e.g., LLDP every 5 seconds). During this dead window, traffic sent across the severed link blackholes completely."
    )

    # ========================== SECTION 3: SYSTEM COMPONENTS TABLE ==========================
    h3 = doc.add_heading(level=1)
    r = h3.add_run("3. Master System Components Table & Deep-Dive Analysis")
    r.font.name = "Arial"
    r.font.color.rgb = RGBColor(15, 41, 66)

    doc.add_paragraph(
        "To provide a complete technical overview of the project, the table below lists every hardware and software component, "
        "outlining its general industry/computer science definition and its specific role in this project:"
    )

    comp_headers = ["Component Name", "Category / Layer", "General Definition", "Specific Role in This Project", "File / Source"]
    comp_rows = [
        ["Mininet Emulator", "Data Plane / Emulation", "A network emulation environment instantiating virtual hosts, switches, and links via Linux namespaces.", "Emulates multi-path network topology with 6 hosts, 4 OVS switches, and link QoS constraints.", "topo_multi_path.py"],
        ["Open vSwitch (OVS)", "Data Plane / Switching", "A production-grade, software-based multi-layer virtual switch compatible with OpenFlow specifications.", "Acts as switches s1, s2, s3, and s4. Executes flow matching, group tables, and drop rules.", "OVS DPIDs 0x01 to 0x04"],
        ["Ryu SDN Controller", "Control Plane / Framework", "A component-based Python SDN framework providing event-driven APIs for OpenFlow network management.", "Acts as central brain. Hosts telemetry poller, ML classifier, and remediation engine.", "multipath_switch.py"],
        ["OpenFlow 1.3 Protocol", "Southbound Protocol", "Standard protocol enabling SDN controllers to manipulate forwarding tables on switches directly.", "Carries FlowStats, PortStats, PacketIn, PortStatus, FlowMod, and GroupMod messages.", "ofproto_v1_3 wire"],
        ["Multi-Path Core Topology", "Network Architecture", "Topology design featuring redundant forwarding paths for fault tolerance and load balancing.", "Implements Path A (s2, 10Mbps, 5ms) and Path B (s3, 10Mbps, 10ms) for failover and ECMP.", "topo_multi_path.py"],
        ["SDN Telemetry Monitor", "Control Plane / Telemetry", "Asynchronous process querying network devices for operational counters at regular intervals.", "Greenlet thread polling FlowStats and PortStats every 2.0s to calculate delta rates.", "sdn_monitor.py"],
        ["Rolling Feature Extractor", "Telemetry / Math Engine", "Signal processing module computing rolling metrics over sliding temporal sample windows.", "Extracts 9-D feature vector: packet rate, byte rate, IP entropy, packet variance, drops.", "remediation_engine.py"],
        ["Shannon Entropy Estimator", "Algorithmic / Math Core", "Formula measuring uncertainty or diversity within a probability distribution across discrete variables.", "Computes H(X) over source IPs to cleanly distinguish flash crowds (>2.5) from DDoS (<0.6).", "remediation_engine.py"],
        ["Scikit-Learn ML Classifier", "Artificial Intelligence / ML", "Machine learning suite utilizing decision tree ensembles for multi-class classification.", "Classifies live telemetry vectors into 5 network conditions in <15ms with 92.54% CV accuracy.", "sdn_classifier.joblib"],
        ["Differentiated Remediation", "Autonomic Policy Engine", "State machine translating high-level classification diagnoses into low-level datapath mutations.", "Dispatches class-specific OpenFlow directives: group tables, drop filters, and reroutes.", "remediation_engine.py"],
        ["OpenFlow 1.3 Group Table", "Advanced OpenFlow Primitive", "Switch mechanism supporting multi-bucket forwarding actions for hash-based multipath load balancing.", "Programs Group 50 with 50/50 dual buckets pointing to Path A and Path B during flash crowds.", "OFPGT_SELECT in engine"],
        ["Scapy Packet Crafter", "Traffic Generation / Security", "Python tool capable of forging, crafting, decoding, and injecting arbitrary network frames.", "Injects volumetric TCP SYN and UDP floods (~1,500 to 2,800 pps) with small 64-byte packets.", "traffic_ddos.py"],
        ["iPerf3 Benchmarking Tool", "Traffic Generation / Utility", "Industry-standard tool for measuring maximum achievable bandwidth, packet loss, and jitter.", "Generates normal baseline traffic, multi-client concurrent bursts, and congestion steps.", "traffic_normal.py, etc."],
        ["Linux tc & iproute2", "OS / Network Kernel Utility", "Linux kernel utilities used for packet scheduling, token bucket filters, and interface state control.", "Emulates physical link cuts (ip link set s1-eth6 down) and configures Mininet link parameters.", "link_failure.sh"],
        ["Scenario Orchestrator", "Test Automation", "Pipeline manager sequentially executing workloads, synchronizing controllers, and logging results.", "Runs automated end-to-end evaluation sweeps across all five traffic conditions.", "scenario_orchestrator.py"],
        ["Streamlit Live Demo", "Presentation / UI", "Python web framework for building interactive data dashboards and real-time ML applications.", "Provides web GUI to simulate traffic, tune telemetry sliders, view live AI inference and actions.", "streamlit_app.py"],
        ["D3.js Topology Visualizer", "Presentation / UI", "JavaScript library for producing dynamic, interactive data visualizations in web browsers.", "Renders animated node-link topology diagram animating packet flows and link states.", "topology_gui.html"],
        ["Telemetry State Logger", "Monitoring / Audit", "Structured storage formats recording system state transitions and temporal telemetry streams.", "Exports live JSON snapshots and audit logs for real-time dashboard updates and evaluation.", "live_remediation_status.json"]
    ]
    comp_table = doc.add_table(rows=1, cols=5)
    format_custom_table(comp_table, [Inches(1.2), Inches(1.1), Inches(1.6), Inches(1.7), Inches(0.9)], comp_headers, comp_rows)

    doc.add_page_break()

    # ========================== SECTION 4: ARCHITECTURE & BLOCK DIAGRAM ==========================
    h4 = doc.add_heading(level=1)
    r = h4.add_run("4. System Architecture & Structural Block Diagram")
    r.font.name = "Arial"
    r.font.color.rgb = RGBColor(15, 41, 66)

    doc.add_paragraph(
        "The system architecture is structured into four distinct, loosely coupled tiers that establish a closed-loop "
        "autonomic feedback cycle: Data Plane, Southbound Control Interface, Ryu SDN Controller & Intelligence Core, "
        "and Management / Presentation Layer."
    )

    bd_img_path = os.path.join(project_root, "block_diagram.png")
    if os.path.exists(bd_img_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(8)
        p_img.paragraph_format.space_after = Pt(4)
        run_img = p_img.add_run()
        run_img.add_picture(bd_img_path, width=Inches(6.5))

        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_after = Pt(12)
        r_cap = p_cap.add_run("Figure 4.1: Context-Aware SDN Multi-Tier Architecture Block Diagram")
        r_cap.font.name = "Arial"
        r_cap.font.bold = True
        r_cap.font.size = Pt(9)
        r_cap.font.color.rgb = RGBColor(71, 85, 105)

    doc.add_paragraph(
        "Architectural Layer Breakdown:\n"
        "1. Tier 1 (Data Plane): 6 hosts (clients h1–h5, server h6) interconnected across 4 Open vSwitches. Redundant dual core paths provide 10 Mbps bottleneck links.\n"
        "2. Tier 2 (Southbound Interface): Standard OpenFlow 1.3 protocol operating over TCP port 6653, transporting telemetry stats and control flow modifications.\n"
        "3. Tier 3 (Ryu Controller Core): Asynchronous greenlet polling engine, rolling Shannon entropy calculator, embedded Scikit-Learn champion model, and autonomic policy dispatcher.\n"
        "4. Tier 4 (Management & GUI): Streamlit live web dashboard, D3.js topology animator, and persistent JSON/log persistence."
    )

    # ========================== SECTION 5: WORKFLOW DIAGRAM ==========================
    h5 = doc.add_heading(level=1)
    r = h5.add_run("5. End-to-End System Workflow & Operational Lifecycle")
    r.font.name = "Arial"
    r.font.color.rgb = RGBColor(15, 41, 66)

    doc.add_paragraph(
        "The system workflow implements an autonomic MAPE-K (Monitor, Analyze, Plan, Execute, Knowledge) closed-loop cycle. "
        "The complete sequence from traffic ingress to surgical remediation and feedback restoration is depicted below:"
    )

    wf_img_path = os.path.join(project_root, "workflow_diagram.png")
    if os.path.exists(wf_img_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(8)
        p_img.paragraph_format.space_after = Pt(4)
        run_img = p_img.add_run()
        run_img.add_picture(wf_img_path, width=Inches(6.5))

        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_after = Pt(12)
        r_cap = p_cap.add_run("Figure 5.1: Context-Aware SDN End-to-End Autonomic Closed-Loop Workflow")
        r_cap.font.name = "Arial"
        r_cap.font.bold = True
        r_cap.font.size = Pt(9)
        r_cap.font.color.rgb = RGBColor(71, 85, 105)

    doc.add_paragraph(
        "Sequential Workflow Phases:\n"
        "• Phase 1 (Ingress): Hosts h1–h5 inject normal, burst, flood, congested, or disrupted traffic streams.\n"
        "• Phase 2 (Telemetry Ingestion): Controller receives periodic stats every 2.0s and catches asynchronous Packet-In and Port-Status interrupts.\n"
        "• Phase 3 (Feature Math): Rolling FIFO buffers compute Shannon IP entropy, packet rates, byte rates, packet size variance, and drop counters.\n"
        "• Phase 4 (AI Classification): Sub-15ms inference via Gradient Boosting ensemble, with physical port status override as a fail-safe.\n"
        "• Phase 5 (Differentiated Remediation): State machine executes tailored OpenFlow actions (SELECT group table, ingress drop, preemptive reroute, sub-50ms failover).\n"
        "• Phase 6 (Closed-Loop Feedback): Controller monitors network stabilization and automatically clears temporary overrides once traffic subsides."
    )

    doc.add_page_break()

    # ========================== SECTION 6: NETWORK TOPOLOGY ==========================
    h6 = doc.add_heading(level=1)
    r = h6.add_run("6. Network Topology & Link Specifications")
    r.font.name = "Arial"
    r.font.color.rgb = RGBColor(15, 41, 66)

    doc.add_paragraph(
        "The network topology is designed to evaluate bottleneck saturation, multi-path ECMP distribution, and hardware failovers "
        "under controlled link bandwidth and propagation delay constraints:"
    )

    add_code_block(
        doc,
        "          [h1]  [h2]  [h3]  [h4]  [h5]   (Clients: 10.0.0.1 - 10.0.0.5)\n"
        "            \\     \\    |    /     /\n"
        "              [ Switch s1 ] (Ingress Switch - DPID 0000000000000001)\n"
        "                 /             \\\n"
        "           Path A               Path B\n"
        "        [ Switch s2 ]        [ Switch s3 ]   (Core Bottlenecks: 10 Mbps, 5ms/10ms)\n"
        "                 \\             /\n"
        "              [ Switch s4 ] (Egress Switch - DPID 0000000000000004)\n"
        "                    |\n"
        "                 [ h6 ] (Destination Server: 10.0.0.6)",
        caption="Mininet Multi-Path Dual-Core Network Topology"
    )

    link_headers = ["Link Segment", "Connected Switch Ports", "Bandwidth", "Delay", "Operational Role"]
    link_rows = [
        ["Clients <-> Switch s1", "h1-h5 to s1 (Ports 1 to 5)", "100 Mbps", "1 ms", "High-speed edge access links simulating local client hosts."],
        ["Switch s1 <-> Switch s2", "s1 (Port 6) to s2 (Port 1)", "10 Mbps", "5 ms", "Core Path A (Primary): Low-latency path for baseline traffic."],
        ["Switch s2 <-> Switch s4", "s2 (Port 2) to s4 (Port 1)", "10 Mbps", "5 ms", "Completes primary Core Path A to egress switch s4."],
        ["Switch s1 <-> Switch s3", "s1 (Port 7) to s3 (Port 1)", "10 Mbps", "10 ms", "Core Path B (Redundant): Backup path for load balancing & failover."],
        ["Switch s3 <-> Switch s4", "s3 (Port 2) to s4 (Port 2)", "10 Mbps", "10 ms", "Completes redundant Core Path B to egress switch s4."],
        ["Switch s4 <-> Server h6", "s4 (Port 3) to h6 (Port 1)", "100 Mbps", "1 ms", "High-speed egress delivery link to destination server."]
    ]
    link_table = doc.add_table(rows=1, cols=5)
    format_custom_table(link_table, [Inches(1.5), Inches(1.4), Inches(0.9), Inches(0.8), Inches(1.9)], link_headers, link_rows)

    # ========================== SECTION 7: 5 OPERATIONAL SCENARIOS ==========================
    h7 = doc.add_heading(level=1)
    r = h7.add_run("7. The 5 Operational Traffic Scenarios")
    r.font.name = "Arial"
    r.font.color.rgb = RGBColor(15, 41, 66)

    doc.add_paragraph(
        "Each operational state produces a distinct mathematical telemetry fingerprint across our feature vector:"
    )

    scen_headers = ["Scenario", "Traffic Generator", "Packet Rate", "Byte Rate", "Shannon Entropy", "Pkt Variance", "Port Drops", "Port State"]
    scen_rows = [
        ["1. Normal Traffic", "traffic_normal.py (iPerf3)", "Low (~120 pps)", "150 KB/s", "Medium (1.80-2.00)", "Medium (~180)", "0", "UP (1)"],
        ["2. Flash-Crowd Surge", "traffic_flash_crowd.py (5 bursts)", "High (~1,450 pps)", "1.85 MB/s", "Very High (>2.50)", "High (~340)", "0 - 15", "UP (1)"],
        ["3. DDoS Flood Attack", "traffic_ddos.py (Scapy SYN/UDP)", "Extremely High (>2,800)", "3.60 MB/s", "Very Low (<0.60)", "Very Low (~12)", "High (>80)", "UP (1)"],
        ["4. Slow Congestion", "traffic_congestion.py (Ramped iPerf3)", "Moderate (~950 pps)", "1.15 MB/s", "Medium (~1.82)", "Medium (~210)", "Rising (>150)", "UP (1)"],
        ["5. Physical Link Failure", "link_failure.sh (ip link set down)", "0 on Path A", "0 on Path A", "0.0", "0", "Accumulating", "DOWN (0)"]
    ]
    scen_table = doc.add_table(rows=1, cols=8)
    format_custom_table(scen_table, [Inches(1.1), Inches(1.2), Inches(0.8), Inches(0.7), Inches(0.8), Inches(0.7), Inches(0.6), Inches(0.6)], scen_headers, scen_rows)

    # ========================== SECTION 8: MATHEMATICAL FEATURE FORMULATION ==========================
    h8 = doc.add_heading(level=1)
    r = h8.add_run("8. Mathematical Formulation & Feature Engineering")
    r.font.name = "Arial"
    r.font.color.rgb = RGBColor(15, 41, 66)

    doc.add_paragraph(
        "To achieve sub-15ms inference latency without memory exhaustion, the feature extractor computes 9 mathematical telemetry primitives:\n\n"
        "1. Shannon Source IP Entropy: Measures the uncertainty and dispersion of incoming source IP addresses:\n"
        "   H(X) = -SUM [ p(x_i) * log2( p(x_i) ) ]\n"
        "   Where p(x_i) = Count(x_i) / N across a sliding window of N=500 sampled packets.\n\n"
        "2. Volumetric Rate Deltas: Measures traffic intensity independent of controller uptime:\n"
        "   Packet Rate = (Packets(t) - Packets(t - dt)) / dt  (packets/sec)\n"
        "   Byte Rate = (Bytes(t) - Bytes(t - dt)) / dt  (bytes/sec)\n\n"
        "3. Packet Size Distribution Moments: Mean (mu) and standard deviation (sigma) of packet sizes:\n"
        "   mu_s = (1/M) * SUM [ s_j ]\n"
        "   sigma_s = SQRT[ (1/M) * SUM [ (s_j - mu_s)^2 ] ]\n"
        "   Malicious flood attacks exhibit uniform payload sizes (sigma < 15 bytes), whereas legitimate traffic exhibits high variance (sigma > 150 bytes).\n\n"
        "4. Interface Health & Drops:\n"
        "   PortStatus in {0, 1} (0 = Down, 1 = Up)\n"
        "   Delta Drops = Delta RX_Dropped + Delta TX_Dropped"
    )

    doc.add_page_break()

    # ========================== SECTION 9: ML ENGINE & EVALUATION ==========================
    h9 = doc.add_heading(level=1)
    r = h9.add_run("9. Machine Learning Engine & Empirical Evaluation")
    r.font.name = "Arial"
    r.font.color.rgb = RGBColor(15, 41, 66)

    doc.add_paragraph(
        "The model was trained on 603 synthesized network telemetry samples across five balanced classes (Normal: 128, DDoS: 123, "
        "Flash-Crowd: 120, Congestion: 120, Link-Failure: 112). Models were evaluated using 10-fold Stratified Cross-Validation:"
    )

    ml_headers = ["Machine Learning Model", "Mean CV Accuracy", "Std Dev (+/-)", "Macro Precision", "Macro Recall", "Macro F1-Score", "95% Confidence Interval"]
    ml_rows = [
        ["Gradient Boosting (Champion)", "92.54%", "+/- 2.89%", "92.85%", "92.50%", "92.49%", "[90.75%, 94.33%]"],
        ["Random Forest", "86.90%", "+/- 4.33%", "87.98%", "86.77%", "86.91%", "[84.22%, 89.58%]"],
        ["Decision Tree", "80.43%", "+/- 3.70%", "84.79%", "80.60%", "81.04%", "[78.14%, 82.72%]"],
        ["K-Nearest Neighbors (KNN)", "77.95%", "+/- 3.72%", "80.48%", "77.59%", "77.80%", "[75.65%, 80.25%]"]
    ]
    ml_table = doc.add_table(rows=1, cols=7)
    format_custom_table(ml_table, [Inches(1.8), Inches(0.8), Inches(0.7), Inches(0.8), Inches(0.8), Inches(0.8), Inches(0.8)], ml_headers, ml_rows)

    doc.add_paragraph(
        "Confusion Matrix (Gradient Boosting Champion Model):\n"
    )

    cm_headers = ["Actual \\ Predicted", "ddos", "flash_crowd", "link_failure", "normal", "slow_congestion"]
    cm_rows = [
        ["ddos", "116", "4", "0", "0", "3"],
        ["flash_crowd", "5", "110", "1", "3", "1"],
        ["link_failure", "0", "0", "102", "7", "3"],
        ["normal", "0", "4", "5", "119", "0"],
        ["slow_congestion", "5", "0", "4", "0", "111"]
    ]
    cm_table = doc.add_table(rows=1, cols=6)
    format_custom_table(cm_table, [Inches(1.7), Inches(0.9), Inches(1.0), Inches(1.0), Inches(0.9), Inches(1.0)], cm_headers, cm_rows)

    # ========================== SECTION 10: DIFFERENTIATED REMEDIATION ==========================
    h10 = doc.add_heading(level=1)
    r = h10.add_run("10. Differentiated Auto-Remediation Mechanisms")
    r.font.name = "Arial"
    r.font.color.rgb = RGBColor(15, 41, 66)

    doc.add_paragraph(
        "Unlike naive controllers that apply indiscriminate rate-limiting, Context-Aware SDN executes surgical OpenFlow actions:"
    )

    add_code_block(
        doc,
        "# Flash-Crowd: OpenFlow 1.3 SELECT group table multi-path load balancing\n"
        "bucket_a = parser.OFPBucket(weight=50, watch_port=6, actions=[parser.OFPActionOutput(6)])\n"
        "bucket_b = parser.OFPBucket(weight=50, watch_port=7, actions=[parser.OFPActionOutput(7)])\n"
        "group_mod = parser.OFPGroupMod(dp, command=OFPGC_ADD, type_=OFPGT_SELECT, group_id=50, buckets=[bucket_a, bucket_b])\n"
        "dp.send_msg(group_mod)\n\n"
        "# DDoS Flood: High-priority ingress drop rule matched on attacker source IP\n"
        "match_drop = parser.OFPMatch(eth_type=0x0800, ipv4_src=attacker_ip, ipv4_dst='10.0.0.6')\n"
        "mod_drop = parser.OFPFlowMod(dp, priority=150, match=match_drop, instructions=[OFPInstructionActions(OFPIT_APPLY_ACTIONS, [])])\n"
        "dp.send_msg(mod_drop)\n\n"
        "# Slow Congestion: Preemptive bulk traffic diversion to Path B before queue drop\n"
        "match_bulk = parser.OFPMatch(eth_type=0x0800, ipv4_src='10.0.0.2', ipv4_dst='10.0.0.6')\n"
        "mod_divert = parser.OFPFlowMod(dp, priority=80, match=match_bulk, actions=[parser.OFPActionOutput(7)])\n"
        "dp.send_msg(mod_divert)\n\n"
        "# Link Failure: Hardware event-triggered failover to Path B in <48ms\n"
        "match_fail = parser.OFPMatch(eth_type=0x0800, ipv4_dst='10.0.0.6')\n"
        "mod_fail = parser.OFPFlowMod(dp, priority=120, match=match_fail, actions=[parser.OFPActionOutput(7)])\n"
        "dp.send_msg(mod_fail)",
        caption="Core OpenFlow 1.3 Remediation Rules Dispatched by the Controller"
    )

    # ========================== SECTION 11: BENCHMARK ==========================
    h11 = doc.add_heading(level=1)
    r = h11.add_run("11. Controlled Benchmark: Differentiated vs. Naive Baseline")
    r.font.name = "Arial"
    r.font.color.rgb = RGBColor(15, 41, 66)

    doc.add_paragraph(
        "A controlled evaluation demonstrates the profound performance advantage of differentiated remediation over standard SDN defense mechanisms:"
    )

    bench_headers = ["Metric / Scenario", "Naive Generic Baseline", "Context-Aware SDN (Ours)", "Quantifiable Improvement"]
    bench_rows = [
        ["Flash-Crowd Legitimate Drop Rate", "65.4% (throttled as DDoS)", "0.0% (multipath distributed)", "100% preservation of legitimate traffic"],
        ["Flash-Crowd Effective Goodput", "3.4 Mbps (severely throttled)", "9.2 Mbps (approaching link cap)", "2.7x higher goodput"],
        ["DDoS Attack Defense", "Reroutes dirty traffic to Path B", "Surgically filters attacker at s1", "Backup core path protected from attack"],
        ["Congestion Handling", "Reacts after packet drops occur", "Preemptively reroutes at 85% cap", "Zero buffer queue drop loss"],
        ["Link Failure Recovery Latency", "3.5 - 8.0 seconds (polling timeout)", "< 48 ms (hardware interrupt)", "Sub-second failover; zero session drops"],
        ["Classification Accuracy", "50.0% (binary threshold heuristic)", "92.54% (multi-class ensemble)", "+42.5% classification accuracy"]
    ]
    bench_table = doc.add_table(rows=1, cols=4)
    format_custom_table(bench_table, [Inches(1.8), Inches(1.7), Inches(1.7), Inches(1.3)], bench_headers, bench_rows)

    doc.add_page_break()

    # ========================== SECTION 12: EXECUTION GUIDE ==========================
    h12 = doc.add_heading(level=1)
    r = h12.add_run("12. Reproduction & Execution Guide")
    r.font.name = "Arial"
    r.font.color.rgb = RGBColor(15, 41, 66)

    doc.add_paragraph(
        "To reproduce and evaluate the system, follow these execution steps in an Ubuntu Linux environment:"
    )

    add_code_block(
        doc,
        "# Step 1: Start Ryu Controller with Differentiated Remediation Engine\n"
        "source ~/ryu-env/bin/activate\n"
        "ryu-manager --ofp-tcp-listen-port 6653 src/controller/remediation_engine.py\n\n"
        "# Step 2: In a second terminal, launch Mininet Multi-Path Network\n"
        "sudo python3 src/topology/topo_multi_path.py --controller-ip 127.0.0.1 --controller-port 6653\n\n"
        "# Step 3: Run Automated Traffic Scenarios\n"
        "python3 src/traffic/scenario_orchestrator.py\n\n"
        "# Step 4: Run Machine Learning Cross-Validation Benchmark\n"
        "python3 src/ml/train_classifier.py\n"
        "python3 src/ml/cross_validate.py\n\n"
        "# Step 5: Launch Interactive Streamlit Demonstration Dashboard\n"
        "pip install -r requirements.txt\n"
        "streamlit run streamlit_app.py",
        caption="Step-by-Step Terminal Execution Commands"
    )

    # ========================== SECTION 13: CONCLUSION ==========================
    h13 = doc.add_heading(level=1)
    r = h13.add_run("13. Conclusion & Future Work")
    r.font.name = "Arial"
    r.font.color.rgb = RGBColor(15, 41, 66)

    doc.add_paragraph(
        "Context-Aware SDN represents a paradigm shift from traditional, rigid, binary threshold SDN defense mechanisms "
        "to an autonomic, context-aware closed loop. By unifying 9-dimensional rolling telemetry metrics with an embedded "
        "Gradient Boosting ensemble classifier, the system reliably differentiates flash-crowd surges from volumetric DDoS attacks, "
        "detects early buffer queue buildup, and catches physical link cuts via hardware interrupts.\n\n"
        "The resulting differentiated remediation actions eliminate collateral damage to legitimate traffic, achieve 0% drop rates "
        "during flash crowds with a 2.7x goodput boost, protect backup links from toxic floods, and recover from hardware cuts in under 48ms.\n\n"
        "Future enhancements include migrating telemetry calculations directly into hardware pipelines using P4 programmable switches, "
        "and employing Deep Reinforcement Learning (DRL) for dynamic continuous group table bucket weight tuning."
    )

    doc.save(output_docx)
    doc.save(output_alias)
    print(f"[OK] Saved Word Document to: {output_docx}")
    print(f"[OK] Saved Word Document alias to: {output_alias}")

if __name__ == '__main__':
    build_word_document()
