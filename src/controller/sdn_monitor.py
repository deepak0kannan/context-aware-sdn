#!/usr/bin/env python3
"""
Context-Aware SDN: Monitoring Engine & Feature Extractor
Ryu OpenFlow 1.3 Controller Extension

Periodically collects flow stats, port stats, and link events.
Calculates real-time rolling-window network features:
- Packet Rate (pps) & Byte Rate (Bps)
- Shannon Entropy of Source IP addresses
- Unique Source IP count
- Mean & Variance of Packet Sizes
- Flow Duration (seconds)
- Port Status (1 = UP, 0 = DOWN)
- Port RX / TX Drops
"""

import os
import time
import math
import csv
from collections import Counter, defaultdict

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ipv4, arp, ether_types
from ryu.lib import hub

# Import our MultiPathSwitch base logic
from multipath_switch import MultiPathSwitch


class SDNMonitorController(MultiPathSwitch):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SDNMonitorController, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.monitor_interval = float(os.environ.get("SDN_INTERVAL", "1.0"))  # Polling interval in seconds (default: 1.0s)

        # Flow tracking: {dpid: {(src_ip, dst_ip): {'packets': N, 'bytes': B, 'time': T}}}
        self.prev_flow_stats = defaultdict(dict)

        # Port status: {(dpid, port_no): 1 (UP) or 0 (DOWN)}
        self.port_status = defaultdict(lambda: 1)

        # Port drops: {(dpid, port_no): rx_dropped + tx_dropped}
        self.port_drops = defaultdict(int)

        # Rolling window packet sampling for entropy and size variance
        # {dpid: {'src_ips': deque, 'pkt_sizes': deque}}
        self.sampled_src_ips = defaultdict(list)
        self.sampled_pkt_sizes = defaultdict(list)
        self.max_samples = 500

        # Current scenario label (for dataset generation: 'normal', 'flash_crowd', 'ddos', 'congestion', 'link_failure')
        self.label_file = "/tmp/active_label.txt"
        self.current_label = "normal"
        self.log_file = os.environ.get("SDN_DATASET_FILE", os.path.expanduser("~/sdn_project/data/sdn_dataset.csv"))
        self.init_csv_log()

        # Spawn periodic monitoring greenlet
        self.monitor_thread = hub.spawn(self._monitor_loop)
        self.logger.info("SDNMonitorController initialized. Polling interval: %.1fs", self.monitor_interval)

    def init_csv_log(self):
        """Initialize CSV log file with header if it doesn't exist."""
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        if not os.path.exists(self.log_file):
            with open(self.log_file, mode="w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "dpid", "packet_count", "byte_count",
                    "packet_rate", "byte_rate", "flow_duration_sec",
                    "ip_src_count", "ip_src_entropy", "avg_packet_size",
                    "std_packet_size", "port_status", "rx_dropped",
                    "tx_dropped", "label"
                ])

    def _monitor_loop(self):
        """Periodic loop requesting stats from all connected switches."""
        while True:
            # Check for dynamic label updates
            if os.path.exists(self.label_file):
                try:
                    with open(self.label_file, "r") as f:
                        lbl = f.read().strip()
                        if lbl:
                            self.current_label = lbl
                except Exception:
                    pass

            for dp in list(self.datapaths.values()):
                self._request_stats(dp)
            hub.sleep(self.monitor_interval)

    def _request_stats(self, datapath):
        """Send OFPFlowStatsRequest and OFPPortStatsRequest."""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Flow stats request
        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

        # Port stats request
        port_req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(port_req)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        """Intercept packet-in messages to collect source IP entropy and packet sizes."""
        super(SDNMonitorController, self).packet_in_handler(ev)

        msg = ev.msg
        datapath = msg.datapath
        dpid = datapath.id
        pkt = packet.Packet(msg.data)
        ip_pkt = pkt.get_protocol(ipv4.ipv4)

        if ip_pkt:
            src_ip = ip_pkt.src
            pkt_size = len(msg.data)

            # Store in rolling buffer
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
        """Handle physical port link state changes (link up/down)."""
        msg = ev.msg
        reason = msg.reason
        port_no = msg.desc.port_no
        dpid = msg.datapath.id
        ofproto = msg.datapath.ofproto

        # 1 = UP, 0 = DOWN
        is_link_down = (msg.desc.state & ofproto.OFPPS_LINK_DOWN) != 0
        status = 0 if is_link_down else 1
        self.port_status[(dpid, port_no)] = status

        reason_str = "UNKNOWN"
        if reason == ofproto.OFPPR_ADD:
            reason_str = "PORT_ADDED"
        elif reason == ofproto.OFPPR_DELETE:
            reason_str = "PORT_DELETED"
            self.port_status[(dpid, port_no)] = 0
        elif reason == ofproto.OFPPR_MODIFY:
            reason_str = "PORT_MODIFIED"

        self.logger.warning(
            "[PORT_STATUS] Switch s%d Port %d changed (%s): Link is %s",
            dpid, port_no, reason_str, "DOWN" if status == 0 else "UP"
        )

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def port_stats_reply_handler(self, ev):
        """Process switch port statistics (drops, errors)."""
        dpid = ev.msg.datapath.id
        for stat in ev.msg.body:
            port_no = stat.port_no
            self.port_drops[(dpid, port_no)] = (stat.rx_dropped, stat.tx_dropped)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def flow_stats_reply_handler(self, ev):
        """Process flow statistics, calculate delta rates, and compute statistical features."""
        body = ev.msg.body
        dpid = ev.msg.datapath.id
        now = time.time()

        # We focus feature calculation primarily on Ingress Switch s1 (dpid=1) and Core s2/s3
        total_packets = 0
        total_bytes = 0
        max_duration = 0
        matched_src_ips = list(self.sampled_src_ips[dpid])
        computed_pkt_sizes = list(self.sampled_pkt_sizes[dpid])

        for stat in body:
            # Filter table-miss rule (priority 0)
            if stat.priority == 0:
                continue
            total_packets += stat.packet_count
            total_bytes += stat.byte_count
            duration = stat.duration_sec + (stat.duration_nsec / 1e9)
            if duration > max_duration:
                max_duration = duration

            # Extract source IP from flow match
            src_ip = stat.match.get('ipv4_src') or stat.match.get('arp_spa')
            if src_ip:
                matched_src_ips.append(str(src_ip))

            # Compute average packet size for flow
            if stat.packet_count > 0:
                computed_pkt_sizes.append(stat.byte_count / stat.packet_count)

        # Calculate rate deltas using previous sample
        prev = self.prev_flow_stats[dpid].get("totals", {"packets": 0, "bytes": 0, "time": now})
        time_delta = now - prev["time"]
        if time_delta <= 0:
            time_delta = 1.0

        packet_delta = max(0, total_packets - prev["packets"])
        byte_delta = max(0, total_bytes - prev["bytes"])

        packet_rate = packet_delta / time_delta
        byte_rate = byte_delta / time_delta

        # Update cache
        self.prev_flow_stats[dpid]["totals"] = {
            "packets": total_packets,
            "bytes": total_bytes,
            "time": now
        }

        # Calculate Source IP Shannon Entropy
        src_ips = matched_src_ips
        ip_count = len(set(src_ips))
        entropy = 0.0
        if src_ips:
            total_ips = len(src_ips)
            counts = Counter(src_ips)
            for cnt in counts.values():
                p = cnt / total_ips
                entropy -= p * math.log2(p)

        # Calculate Packet Size Mean and Standard Deviation
        if packet_delta > 0:
            current_avg_size = byte_delta / packet_delta
            computed_pkt_sizes.append(current_avg_size)

        pkt_sizes = computed_pkt_sizes[-50:] if computed_pkt_sizes else []
        if pkt_sizes:
            avg_size = sum(pkt_sizes) / len(pkt_sizes)
            variance = sum((x - avg_size) ** 2 for x in pkt_sizes) / len(pkt_sizes)
            std_size = math.sqrt(variance)
        else:
            avg_size = 0.0
            std_size = 0.0

        # Port status: check core links (port 6 on s1)
        core_port_status = self.port_status.get((dpid, 6), 1) if dpid == 1 else 1
        rx_drop, tx_drop = self.port_drops.get((dpid, 6), (0, 0))

        # Only log rows when there is activity or when monitoring s1
        if dpid == 1:
            row = [
                f"{now:.2f}", dpid, total_packets, total_bytes,
                f"{packet_rate:.2f}", f"{byte_rate:.2f}", f"{max_duration:.2f}",
                ip_count, f"{entropy:.4f}", f"{avg_size:.2f}",
                f"{std_size:.2f}", core_port_status, rx_drop,
                tx_drop, self.current_label
            ]

            # Append to feature CSV
            try:
                with open(self.log_file, mode="a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(row)
            except Exception as e:
                self.logger.error("Error writing to feature CSV: %s", e)

            # Log to Ryu console
            self.logger.info(
                "[MONITOR] s%d | PktRate: %6.1f pps | ByteRate: %8.1f Bps | Entropy: %5.3f | UniqueIPs: %2d | PktStd: %5.1f | Link: %s | Label: %s",
                dpid, packet_rate, byte_rate, entropy, ip_count, std_size,
                "UP" if core_port_status == 1 else "DOWN", self.current_label
            )
