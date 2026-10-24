#!/usr/bin/env python3
"""
Phase 7: Naive Reactive Baseline Controller
Implements the generic, non-context-aware SDN baseline for empirical comparison.
Characteristics of the Naive Baseline:
1. No Machine Learning classification: treats all disturbances indiscriminately.
2. Generic Reaction:
   - Upon any high volume surge (threshold > 100 pps): applies indiscriminate rate-limiting / drop that throttles ALL incoming ports, causing high collateral damage to legitimate users.
   - Upon congestion: waits until queue overflow occurs before taking action.
   - Upon link cut: reactive slow timeout-based rerouting rather than fast proactive failover.
"""

import os
import sys
import time
import json
import logging
from collections import defaultdict

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ether_types, ipv4
from ryu.lib import hub

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
sys.path.append(os.path.join(PROJECT_DIR, "src", "controller"))
from multipath_switch import MultiPathSwitch


class NaiveBaselineController(MultiPathSwitch):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(NaiveBaselineController, self).__init__(*args, **kwargs)
        self.logger.setLevel(logging.INFO)
        
        self.project_dir = PROJECT_DIR
        self.status_file = os.path.join(self.project_dir, "data", "naive_status.json")
        self.event_log = os.path.join(self.project_dir, "data", "naive_events.log")
        
        self.threshold_pps = 100.0
        self.prev_stats = defaultdict(lambda: {"packets": 0, "bytes": 0, "time": time.time()})
        self.current_state = "NORMAL"
        self.action_counts = {
            "indiscriminate_throttle": 0,
            "reactive_reroute": 0,
            "normal": 0
        }
        
        self.export_status("NORMAL", "NONE", "Primary Path A default routing", 0.0, 0.0)
        self.monitor_thread = hub.spawn(self._monitor_loop)
        self.logger.info("==================================================================")
        self.logger.info("[NAIVE CONTROLLER] Initialized: Generic Threshold Baseline")
        self.logger.info("==================================================================")

    def _monitor_loop(self):
        while True:
            for dp in list(self.datapaths.values()):
                parser = dp.ofproto_parser
                ofproto = dp.ofproto
                req = parser.OFPFlowStatsRequest(dp)
                dp.send_msg(req)
                port_req = parser.OFPPortStatsRequest(dp, 0, ofproto.OFPP_ANY)
                dp.send_msg(port_req)
            hub.sleep(1.0)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def flow_stats_reply_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        dpid = dp.id
        if dpid != 1:
            return

        now = time.time()
        body = msg.body
        total_packets = sum(s.packet_count for s in body if s.priority > 0)
        total_bytes = sum(s.byte_count for s in body if s.priority > 0)

        prev = self.prev_stats[dpid]
        dt = max(0.5, now - prev["time"])
        pkt_rate = max(0, total_packets - prev["packets"]) / dt
        byte_rate = max(0, total_bytes - prev["bytes"]) / dt

        self.prev_stats[dpid] = {"packets": total_packets, "bytes": total_bytes, "time": now}

        # Naive Threshold Logic: If packet rate exceeds threshold, blindly throttle all traffic
        if pkt_rate > self.threshold_pps:
            if self.current_state != "THROTTLED":
                self.apply_naive_throttling(dp)
                self.current_state = "THROTTLED"
                self.action_counts["indiscriminate_throttle"] += 1
                self.export_status("THROTTLED", "BLIND_DROP_PRIORITY_90", 
                                   "Generic rate limit applied to ALL ingress ports", pkt_rate, byte_rate)
        else:
            if self.current_state == "THROTTLED":
                self.restore_naive(dp)
                self.current_state = "NORMAL"
                self.action_counts["normal"] += 1
                self.export_status("NORMAL", "RESTORE_NORMAL", "Baseline traffic restored", pkt_rate, byte_rate)
            else:
                self.export_status("NORMAL", "NONE", "Normal forwarding active", pkt_rate, byte_rate)

    def apply_naive_throttling(self, dp):
        """Naive blind response: Installs generic drop flow that indiscriminately drops traffic to target server."""
        parser = dp.ofproto_parser
        ofproto = dp.ofproto
        self.logger.warning("[NAIVE ACTION] High volume detected! Applying blind generic drop rule...")
        # Blindly drops 50% or all traffic towards 10.0.0.6 with priority=90
        match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.0.0.6")
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, [])]
        mod = parser.OFPFlowMod(datapath=dp, priority=90, match=match, instructions=inst, idle_timeout=15)
        dp.send_msg(mod)

    def restore_naive(self, dp):
        parser = dp.ofproto_parser
        ofproto = dp.ofproto
        match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.0.0.6")
        mod = parser.OFPFlowMod(datapath=dp, command=ofproto.OFPFC_DELETE, priority=90,
                                out_port=ofproto.OFPP_ANY, out_group=ofproto.OFPG_ANY, match=match)
        dp.send_msg(mod)
        self.logger.info("[NAIVE ACTION] High volume subsided. Throttling removed.")

    def export_status(self, state, action, desc, pps, bps):
        data = {
            "timestamp": time.time(),
            "formatted_time": time.strftime("%H:%M:%S"),
            "controller_type": "NAIVE_BASELINE",
            "state": state,
            "action": action,
            "description": desc,
            "packet_rate": round(pps, 2),
            "byte_rate": round(bps, 2),
            "action_counts": self.action_counts
        }
        try:
            os.makedirs(os.path.dirname(self.status_file), exist_ok=True)
            with open(self.status_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass


app_manager.require_app('ryu.controller.ofp_handler')
