#!/usr/bin/env python3
"""
Context-Aware SDN: Differentiated Auto-Remediation Engine
Ryu OpenFlow 1.3 Controller with Embedded ML Classifier

Features:
1. Real-time telemetry extraction (Packet/Byte rate, IP entropy, packet stats, port drops).
2. Embedded inference via serialized Scikit-Learn champion model (sdn_classifier.joblib).
3. Class-specific autonomic differentiated remediation:
   - FLASH CROWD    -> Dynamic Multi-Path Load Balancing (OpenFlow 1.3 OFPGT_SELECT Group Table).
   - DDOS ATTACK    -> Surgical Ingress Rate-Limiting & Flow Drop (OFPFlowMod priority=150, drop).
   - SLOW CONGESTION-> Preemptive Traffic Diversion (Proactively shifts bulk traffic to Path B).
   - LINK FAILURE   -> Sub-Second Port-Down Failover (Instant cutover to Path B upon hardware event).
   - NORMAL         -> Continuous passive telemetry polling; primary Path A active.
4. Live JSON state & event logging for visualization dashboard and comparative benchmarking.
"""

import os
import sys
import time
import math
import json
import csv
import numpy as np
from collections import Counter, defaultdict

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ipv4, arp, ether_types
from ryu.lib import hub

import joblib

# Import base multi-path controller
from multipath_switch import MultiPathSwitch


class DifferentiatedRemediationController(MultiPathSwitch):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(DifferentiatedRemediationController, self).__init__(*args, **kwargs)
        self.name = "DifferentiatedRemediationEngine"

        # Telemetry polling interval (seconds)
        self.monitor_interval = float(os.environ.get("SDN_INTERVAL", "1.0"))

        # Base paths
        self.project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.model_path = os.path.join(self.project_dir, "models", "sdn_classifier.joblib")
        self.metadata_path = os.path.join(self.project_dir, "models", "model_metadata.json")
        self.live_state_file = os.path.join(self.project_dir, "data", "live_remediation_status.json")
        self.event_log_file = os.path.join(self.project_dir, "data", "remediation_events.log")

        # Load trained champion model
        self.model = None
        self.class_names = ["ddos", "flash_crowd", "link_failure", "normal", "slow_congestion"]
        self.load_classifier()

        # Telemetry tracking state
        self.prev_flow_stats = defaultdict(dict)
        self.port_status = defaultdict(lambda: 1)
        self.port_drops = defaultdict(lambda: (0, 0))
        self.sampled_src_ips = defaultdict(list)
        self.sampled_pkt_sizes = defaultdict(list)
        self.max_samples = 500

        # Remediation state tracking
        self.current_state = "NORMAL"
        self.last_predicted_class = "normal"
        self.consecutive_class_counts = defaultdict(int)
        self.group_installed = False
        self.group_id = 50

        # Action statistics counters (for benchmarking evaluation)
        self.action_counts = {
            "load_balance": 0,
            "ddos_drop": 0,
            "preemptive_reroute": 0,
            "link_failover": 0,
            "normal_restore": 0
        }

        # Export initial baseline state
        self.export_live_state("normal", 1.0, "INITIAL_BASELINE", "Primary Path A active", [0.0] * 9)

        # Spawn periodic monitoring and autonomic remediation greenlet
        self.monitor_thread = hub.spawn(self._monitor_and_remediate_loop)
        self.logger.info("==================================================================")
        self.logger.info("[REMEDIATION ENGINE] Initialized with 5-Class Differentiated Autonomics")
        self.logger.info("==================================================================")

    def load_classifier(self):
        """Load trained Scikit-Learn champion model and metadata."""
        try:
            if os.path.exists(self.metadata_path):
                with open(self.metadata_path, "r") as f:
                    meta = json.load(f)
                    self.class_names = meta.get("classes", self.class_names)
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                self.logger.info("[ML MODEL] Successfully loaded champion classifier: %s", type(self.model).__name__)
                self.logger.info("[ML MODEL] Classes: %s", self.class_names)
            else:
                self.logger.error("[ML MODEL] Model file not found at: %s", self.model_path)
        except Exception as e:
            self.logger.error("[ML MODEL] Error loading model: %s", e)

    def _monitor_and_remediate_loop(self):
        """Periodic loop requesting stats and executing real-time remediation."""
        while True:
            for dp in list(self.datapaths.values()):
                self._request_stats(dp)
            hub.sleep(self.monitor_interval)

    def _request_stats(self, datapath):
        """Send OpenFlow stats requests to connected switches."""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        # Flow stats
        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)
        # Port stats
        port_req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(port_req)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        """Intercept packet-in events to capture entropy and packet sizes."""
        super(DifferentiatedRemediationController, self).packet_in_handler(ev)
        msg = ev.msg
        dpid = msg.datapath.id
        pkt = packet.Packet(msg.data)
        ip_pkt = pkt.get_protocol(ipv4.ipv4)

        if ip_pkt:
            src_ip = ip_pkt.src
            pkt_size = len(msg.data)
            src_list = self.sampled_src_ips[dpid]
            size_list = self.sampled_pkt_sizes[dpid]

            src_list.append(src_ip)
            size_list.append(pkt_size)

            if len(src_list) > self.max_samples:
                src_list.pop(0)
            if len(size_list) > self.max_samples:
                size_list.pop(0)

    @set_ev_cls(ofp_event.EventOFPPortStatus, MAIN_DISPATCHER)
    def port_status_handler(self, ev):
        """Immediate hardware-level link change detection (Sub-second failover trigger)."""
        msg = ev.msg
        reason = msg.reason
        port_no = msg.desc.port_no
        dpid = msg.datapath.id
        ofproto = msg.datapath.ofproto

        is_link_down = (msg.desc.state & ofproto.OFPPS_LINK_DOWN) != 0 or reason == ofproto.OFPPR_DELETE
        status = 0 if is_link_down else 1
        self.port_status[(dpid, port_no)] = status

        self.logger.warning(
            "[PORT_STATUS] Switch s%d Port %d link changed: %s",
            dpid, port_no, "DOWN" if status == 0 else "UP"
        )

        # Instant sub-second failover if core Path A port goes down on Ingress Switch s1
        if dpid == 1 and port_no == 6 and status == 0:
            self.logger.critical("[FAST-FAILOVER] Hardware Port-Down on core Path A! Triggering instant failover to Path B...")
            self.apply_link_failure_remediation(trigger_type="HARDWARE_INTERRUPT")

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def port_stats_reply_handler(self, ev):
        """Process port statistics."""
        dpid = ev.msg.datapath.id
        for stat in ev.msg.body:
            self.port_drops[(dpid, stat.port_no)] = (stat.rx_dropped, stat.tx_dropped)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def flow_stats_reply_handler(self, ev):
        """Process flow statistics, calculate features, run inference, and trigger remediation."""
        body = ev.msg.body
        dpid = ev.msg.datapath.id
        now = time.time()

        # We focus feature calculation and autonomic remediation primarily on Ingress Switch s1
        if dpid != 1:
            return

        total_packets = 0
        total_bytes = 0
        matched_src_ips = list(self.sampled_src_ips[dpid])
        computed_pkt_sizes = list(self.sampled_pkt_sizes[dpid])

        # Track active high-rate source IPs for targeted DDoS mitigation
        flow_rates_by_src = defaultdict(int)

        for stat in body:
            if stat.priority == 0:
                continue
            total_packets += stat.packet_count
            total_bytes += stat.byte_count

            src_ip = stat.match.get('ipv4_src') or stat.match.get('arp_spa')
            if src_ip:
                matched_src_ips.append(str(src_ip))
                flow_rates_by_src[str(src_ip)] += stat.packet_count

            if stat.packet_count > 0:
                computed_pkt_sizes.append(stat.byte_count / stat.packet_count)

        # Delta rates
        prev = self.prev_flow_stats[dpid].get("totals", {"packets": 0, "bytes": 0, "time": now})
        time_delta = max(0.5, now - prev["time"])
        packet_delta = max(0, total_packets - prev["packets"])
        byte_delta = max(0, total_bytes - prev["bytes"])

        packet_rate = packet_delta / time_delta
        byte_rate = byte_delta / time_delta

        self.prev_flow_stats[dpid]["totals"] = {
            "packets": total_packets,
            "bytes": total_bytes,
            "time": now
        }

        # Shannon Entropy of Source IPs
        src_ips = matched_src_ips
        ip_count = len(set(src_ips))
        entropy = 0.0
        if src_ips:
            total_ips = len(src_ips)
            counts = Counter(src_ips)
            for cnt in counts.values():
                p = cnt / total_ips
                entropy -= p * math.log2(p)

        # Packet Size Mean & Std Dev
        if packet_delta > 0:
            computed_pkt_sizes.append(byte_delta / packet_delta)

        pkt_sizes = computed_pkt_sizes[-50:] if computed_pkt_sizes else []
        if pkt_sizes:
            avg_size = sum(pkt_sizes) / len(pkt_sizes)
            variance = sum((x - avg_size) ** 2 for x in pkt_sizes) / len(pkt_sizes)
            std_size = math.sqrt(variance)
        else:
            avg_size = 0.0
            std_size = 0.0

        # Core port status (s1-eth6: port 6)
        core_port_status = self.port_status.get((dpid, 6), 1)
        rx_drop, tx_drop = self.port_drops.get((dpid, 6), (0, 0))

        # Build feature vector: 9 pure telemetry features
        # [packet_rate, byte_rate, ip_src_count, ip_src_entropy, avg_packet_size, std_packet_size, port_status, rx_dropped, tx_dropped]
        feature_vector = [
            float(packet_rate),
            float(byte_rate),
            float(ip_count),
            float(entropy),
            float(avg_size),
            float(std_size),
            float(core_port_status),
            float(rx_drop),
            float(tx_drop)
        ]

        # Run ML Classification
        predicted_class = "normal"
        confidence = 0.95

        if self.model is not None:
            try:
                features_arr = np.array([feature_vector])
                pred_idx = self.model.predict(features_arr)[0]
                if isinstance(pred_idx, (int, np.integer)):
                    predicted_class = self.class_names[pred_idx]
                else:
                    predicted_class = str(pred_idx)

                if hasattr(self.model, "predict_proba"):
                    proba = self.model.predict_proba(features_arr)[0]
                    confidence = float(np.max(proba))
            except Exception as e:
                self.logger.error("[INFERENCE ERROR] %s", e)

        # Hardware override: if port is physically down, force link_failure
        if core_port_status == 0:
            predicted_class = "link_failure"
            confidence = 1.0

        self.last_predicted_class = predicted_class

        # Log periodic inference
        self.logger.info(
            "[AI INFERENCE] s1 | Pred: %-15s (Conf: %5.1f%%) | PktRate: %6.1f pps | ByteRate: %8.1f Bps | Entropy: %5.3f | IPs: %2d | Link: %s",
            predicted_class.upper(), confidence * 100, packet_rate, byte_rate, entropy, ip_count,
            "UP" if core_port_status == 1 else "DOWN"
        )

        # Execute Differentiated Remediation based on predicted condition
        self.execute_remediation(predicted_class, confidence, feature_vector, flow_rates_by_src)

    def execute_remediation(self, predicted_class, confidence, features, flow_rates):
        """State machine that routes network conditions to specific OpenFlow actions."""
        now = time.time()
        datapath_s1 = self.datapaths.get(1)
        datapath_s4 = self.datapaths.get(4)

        if not datapath_s1 or not datapath_s4:
            return

        action_taken = "NONE"
        action_desc = ""

        # 1. LINK FAILURE
        if predicted_class == "link_failure":
            if self.current_state != "LINK_FAILOVER":
                self.apply_link_failure_remediation(trigger_type="AI_PREDICTION")
                action_taken = "FAILOVER_PATH_B"
                action_desc = "Instant failover to Path B (s3) installed"
                self.action_counts["link_failover"] += 1

        # 2. FLASH CROWD SURGE
        elif predicted_class == "flash_crowd":
            if self.current_state != "LOAD_BALANCED":
                self.apply_flash_crowd_remediation()
                action_taken = "OFPGT_SELECT_MULTIPATH"
                action_desc = "Dual-path 50/50 load-balancing active"
                self.action_counts["load_balance"] += 1

        # 3. DDOS ATTACK
        elif predicted_class == "ddos":
            if self.current_state != "INGRESS_DROP":
                self.apply_ddos_remediation(flow_rates)
                action_taken = "SURGICAL_INGRESS_DROP"
                action_desc = "Targeted drop rule on attacker traffic installed"
                self.action_counts["ddos_drop"] += 1

        # 4. SLOW CONGESTION
        elif predicted_class == "slow_congestion":
            if self.current_state != "PREEMPTIVE_REROUTE":
                self.apply_congestion_remediation()
                action_taken = "PREEMPTIVE_REROUTE"
                action_desc = "Bulk traffic preemptively diverted to Path B"
                self.action_counts["preemptive_reroute"] += 1

        # 5. NORMAL BASELINE
        elif predicted_class == "normal":
            if self.current_state != "NORMAL":
                self.restore_normal_routing()
                action_taken = "RESTORE_NORMAL"
                action_desc = "Default primary Path A routing restored"
                self.action_counts["normal_restore"] += 1

        # Export live state for real-time dashboard and benchmarks
        self.export_live_state(predicted_class, confidence, action_taken, action_desc, features)

    def apply_link_failure_remediation(self, trigger_type="AI_PREDICTION"):
        """Instant failover: shifts all traffic from failed Path A to backup Path B."""
        dp1 = self.datapaths.get(1)
        dp4 = self.datapaths.get(4)
        if not dp1 or not dp4:
            return

        parser1 = dp1.ofproto_parser
        parser4 = dp4.ofproto_parser

        # Override route on s1 to port 7 (s3, Path B) with high priority=120
        match_ip = parser1.OFPMatch(eth_type=0x0800, ipv4_dst="10.0.0.6")
        self.add_flow(dp1, priority=120, match=match_ip, actions=[parser1.OFPActionOutput(7)])

        match_arp = parser1.OFPMatch(eth_type=0x0806, arp_tpa="10.0.0.6")
        self.add_flow(dp1, priority=120, match=match_arp, actions=[parser1.OFPActionOutput(7)])

        # Override return route on s4 to port 2 (s3, Path B) with high priority=120
        match_ret_ip = parser4.OFPMatch(in_port=3, eth_type=0x0800)
        self.add_flow(dp4, priority=120, match=match_ret_ip, actions=[parser4.OFPActionOutput(2)])

        self.current_state = "LINK_FAILOVER"
        self.logger.warning(
            "[ACTION: LINK FAILURE] Core link failover completed (%s). All traffic rerouted to Path B.",
            trigger_type
        )
        self.log_event("LINK_FAILURE", "FAILOVER_PATH_B", f"Triggered by {trigger_type}. Switched to Path B.")

    def apply_flash_crowd_remediation(self):
        """Dynamic load balancing: installs OpenFlow 1.3 SELECT group table (50/50 dual path)."""
        dp1 = self.datapaths.get(1)
        dp4 = self.datapaths.get(4)
        if not dp1 or not dp4:
            return

        ofproto1 = dp1.ofproto
        parser1 = dp1.ofproto_parser
        parser4 = dp4.ofproto_parser

        # Install/update OpenFlow 1.3 SELECT group table on s1
        actions_a = [parser1.OFPActionOutput(6)]  # Path A
        actions_b = [parser1.OFPActionOutput(7)]  # Path B

        bucket_a = parser1.OFPBucket(weight=50, watch_port=6, actions=actions_a)
        bucket_b = parser1.OFPBucket(weight=50, watch_port=7, actions=actions_b)

        cmd = ofproto1.OFPGC_MODIFY if self.group_installed else ofproto1.OFPGC_ADD
        group_mod = parser1.OFPGroupMod(
            datapath=dp1, command=cmd,
            type_=ofproto1.OFPGT_SELECT,
            group_id=self.group_id,
            buckets=[bucket_a, bucket_b]
        )
        dp1.send_msg(group_mod)
        self.group_installed = True

        # Direct client traffic to group table with priority=100
        match_ip = parser1.OFPMatch(eth_type=0x0800, ipv4_dst="10.0.0.6")
        inst = [parser1.OFPInstructionActions(ofproto1.OFPIT_APPLY_ACTIONS, [parser1.OFPActionGroup(self.group_id)])]
        mod = parser1.OFPFlowMod(datapath=dp1, priority=100, match=match_ip, instructions=inst)
        dp1.send_msg(mod)

        # Allow return traffic from s4 via both Path A (port 1) and Path B (port 2)
        # s4 already forwards packet-in based on destination IP to client hosts
        self.current_state = "LOAD_BALANCED"
        self.logger.info("[ACTION: FLASH CROWD] Programmed OpenFlow 1.3 OFPGT_SELECT Group 50. Traffic distributed 50/50 across Path A & Path B.")
        self.log_event("FLASH_CROWD", "LOAD_BALANCED", "50/50 SELECT group table programmed across Path A and Path B.")

    def apply_ddos_remediation(self, flow_rates):
        """Surgical drop: installs high-priority drop rules against malicious flood sources."""
        dp1 = self.datapaths.get(1)
        if not dp1:
            return

        ofproto = dp1.ofproto
        parser = dp1.ofproto_parser

        # Identify attacker IP from highest packet rate or install targeted drop on flood vector
        attacker_ip = None
        if flow_rates:
            attacker_ip = max(flow_rates.items(), key=lambda x: x[1])[0]

        if attacker_ip and attacker_ip != "10.0.0.6":
            # Match specifically on attacker source IP
            match_drop = parser.OFPMatch(eth_type=0x0800, ipv4_src=attacker_ip, ipv4_dst="10.0.0.6")
            self.logger.warning("[ACTION: DDOS] Surgical drop rule installed for malicious attacker IP: %s", attacker_ip)
            desc = f"Hard-drop rule installed on attacker source {attacker_ip}."
        else:
            # Drop UDP/SYN flood targeting server port 80 / 5201 with priority=150
            match_drop = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.0.0.6", ip_proto=17)
            desc = "Ingress flood drop installed on destination server port."

        inst_drop = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, [])]
        mod = parser.OFPFlowMod(
            datapath=dp1, priority=150, match=match_drop,
            instructions=inst_drop, idle_timeout=20, hard_timeout=40
        )
        dp1.send_msg(mod)

        self.current_state = "INGRESS_DROP"
        self.logger.warning("[ACTION: DDOS] High-priority drop rule installed on s1. Legitimate traffic preserved on Path A.")
        self.log_event("DDOS", "SURGICAL_INGRESS_DROP", desc)

    def apply_congestion_remediation(self):
        """Preemptive diversion: moves bulk flows to alternate Path B before queue drop occurs."""
        dp1 = self.datapaths.get(1)
        dp4 = self.datapaths.get(4)
        if not dp1 or not dp4:
            return

        parser1 = dp1.ofproto_parser
        parser4 = dp4.ofproto_parser

        # Preemptively reroute secondary hosts (e.g. h2/h3) or UDP bulk flows to Path B (port 7)
        match_bulk = parser1.OFPMatch(eth_type=0x0800, ipv4_src="10.0.0.2", ipv4_dst="10.0.0.6")
        self.add_flow(dp1, priority=80, match=match_bulk, actions=[parser1.OFPActionOutput(7)], idle_timeout=30)

        match_bulk2 = parser1.OFPMatch(eth_type=0x0800, ipv4_src="10.0.0.3", ipv4_dst="10.0.0.6")
        self.add_flow(dp1, priority=80, match=match_bulk2, actions=[parser1.OFPActionOutput(7)], idle_timeout=30)

        self.current_state = "PREEMPTIVE_REROUTE"
        self.logger.info("[ACTION: CONGESTION] Preemptive rerouting engaged. Heavy bulk flows diverted to Path B. Core Path A protected.")
        self.log_event("SLOW_CONGESTION", "PREEMPTIVE_REROUTE", "Bulk streams diverted to Path B before queue drop.")

    def restore_normal_routing(self):
        """Cleans override rules and returns network to primary baseline state."""
        dp1 = self.datapaths.get(1)
        dp4 = self.datapaths.get(4)
        if not dp1 or not dp4:
            return

        ofproto1 = dp1.ofproto
        parser1 = dp1.ofproto_parser
        ofproto4 = dp4.ofproto_parser
        parser4 = dp4.ofproto_parser

        # Delete high priority override flows (priorities 80, 100, 120, 150)
        for prio in [80, 100, 120, 150]:
            match_any = parser1.OFPMatch(eth_type=0x0800)
            mod1 = parser1.OFPFlowMod(
                datapath=dp1, command=ofproto1.OFPFC_DELETE,
                out_port=ofproto1.OFPP_ANY, out_group=ofproto1.OFPG_ANY,
                priority=prio, match=match_any
            )
            dp1.send_msg(mod1)

            mod4 = parser4.OFPFlowMod(
                datapath=dp4, command=ofproto4.OFPFC_DELETE,
                out_port=ofproto4.OFPP_ANY, out_group=ofproto4.OFPG_ANY,
                priority=prio, match=match_any
            )
            dp4.send_msg(mod4)

        self.current_state = "NORMAL"
        self.logger.info("[ACTION: NORMAL] Network stabilized. Cleared overrides, primary Path A restored.")
        self.log_event("NORMAL", "RESTORE_NORMAL", "Primary Path A baseline routing active.")

    def log_event(self, condition, action, description):
        """Append remediation action to persistent log."""
        os.makedirs(os.path.dirname(self.event_log_file), exist_ok=True)
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(self.event_log_file, "a") as f:
            f.write(f"[{now_str}] CONDITION: {condition:<15s} | ACTION: {action:<22s} | {description}\n")

    def export_live_state(self, predicted_class, confidence, action, action_desc, features):
        """Export JSON state for live GUI and comparative benchmark readers."""
        state = {
            "timestamp": time.time(),
            "formatted_time": time.strftime("%H:%M:%S"),
            "detected_class": predicted_class,
            "confidence": float(confidence),
            "remediation_state": self.current_state,
            "last_action": action,
            "action_description": action_desc,
            "telemetry": {
                "packet_rate": features[0],
                "byte_rate": features[1],
                "unique_ips": int(features[2]),
                "entropy": features[3],
                "avg_packet_size": features[4],
                "std_packet_size": features[5],
                "port_status": int(features[6]),
                "rx_dropped": int(features[7]),
                "tx_dropped": int(features[8])
            },
            "cumulative_actions": self.action_counts
        }
        os.makedirs(os.path.dirname(self.live_state_file), exist_ok=True)
        try:
            with open(self.live_state_file, "w") as f:
                json.dump(state, f, indent=2)
        except Exception:
            pass
