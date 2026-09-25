#!/usr/bin/env python3
"""
Context-Aware SDN: Multi-Path Ryu OpenFlow 1.3 Controller
Manages 4 switches (s1, s2, s3, s4) with loop-free dual-path routing and dynamic path switching.
"""

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ipv4, arp, ether_types
from ryu.lib import hub


class MultiPathSwitch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(MultiPathSwitch, self).__init__(*args, **kwargs)
        self.datapaths = {}
        # Default active path: 'A' (via s2). Alternate: 'B' (via s3)
        self.active_path = 'A'
        self.logger.info("MultiPathSwitch OpenFlow 1.3 Controller Initialized.")

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        dpid = datapath.id
        self.datapaths[dpid] = datapath

        self.logger.info("Switch connected: dpid=%016x", dpid)

        # 1. Install table-miss flow entry (send to controller with low priority 0)
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, priority=0, match=match, actions=actions)

        # 2. Pre-install deterministic static flows per switch to prevent loops
        self.install_switch_rules(datapath, dpid)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None, idle_timeout=0, hard_timeout=0):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(
                datapath=datapath, buffer_id=buffer_id,
                priority=priority, match=match,
                instructions=inst, idle_timeout=idle_timeout,
                hard_timeout=hard_timeout
            )
        else:
            mod = parser.OFPFlowMod(
                datapath=datapath, priority=priority,
                match=match, instructions=inst,
                idle_timeout=idle_timeout, hard_timeout=hard_timeout
            )
        datapath.send_msg(mod)

    def install_switch_rules(self, datapath, dpid):
        """Install loop-free proactive forwarding rules for each switch in topology."""
        parser = datapath.ofproto_parser

        if dpid == 1:
            # Switch s1 (Ingress)
            # Ports 1..5 connect to h1..h5 (IPs 10.0.0.1 .. 10.0.0.5)
            # Port 6 -> s2 (Path A)
            # Port 7 -> s3 (Path B)
            for host_id in range(1, 6):
                host_ip = f"10.0.0.{host_id}"
                host_mac = f"00:00:00:00:00:0{host_id}"
                in_port = host_id

                # Return traffic to client host_id
                # Match IP
                match_ip = parser.OFPMatch(eth_type=0x0800, ipv4_dst=host_ip)
                self.add_flow(datapath, priority=10, match=match_ip, actions=[parser.OFPActionOutput(in_port)])
                # Match ARP
                match_arp = parser.OFPMatch(eth_type=0x0806, arp_tpa=host_ip)
                self.add_flow(datapath, priority=10, match=match_arp, actions=[parser.OFPActionOutput(in_port)])

            # Forward traffic destined for server h6 (10.0.0.6) via default Path A (port 6)
            out_port = 6 if self.active_path == 'A' else 7
            match_server_ip = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.0.0.6")
            self.add_flow(datapath, priority=10, match=match_server_ip, actions=[parser.OFPActionOutput(out_port)])
            match_server_arp = parser.OFPMatch(eth_type=0x0806, arp_tpa="10.0.0.6")
            self.add_flow(datapath, priority=10, match=match_server_arp, actions=[parser.OFPActionOutput(out_port)])

        elif dpid == 2:
            # Switch s2 (Path A Intermediate)
            # Port 1 <-> s1, Port 2 <-> s4
            # s1 -> s4
            match_fwd = parser.OFPMatch(in_port=1)
            self.add_flow(datapath, priority=10, match=match_fwd, actions=[parser.OFPActionOutput(2)])
            # s4 -> s1
            match_rev = parser.OFPMatch(in_port=2)
            self.add_flow(datapath, priority=10, match=match_rev, actions=[parser.OFPActionOutput(1)])

        elif dpid == 3:
            # Switch s3 (Path B Intermediate)
            # Port 1 <-> s1, Port 2 <-> s4
            # s1 -> s4
            match_fwd = parser.OFPMatch(in_port=1)
            self.add_flow(datapath, priority=10, match=match_fwd, actions=[parser.OFPActionOutput(2)])
            # s4 -> s1
            match_rev = parser.OFPMatch(in_port=2)
            self.add_flow(datapath, priority=10, match=match_rev, actions=[parser.OFPActionOutput(1)])

        elif dpid == 4:
            # Switch s4 (Egress)
            # Port 1: s2 (Path A), Port 2: s3 (Path B), Port 3: h6 (10.0.0.6)
            # Towards Server h6
            match_server_ip = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.0.0.6")
            self.add_flow(datapath, priority=10, match=match_server_ip, actions=[parser.OFPActionOutput(3)])
            match_server_arp = parser.OFPMatch(eth_type=0x0806, arp_tpa="10.0.0.6")
            self.add_flow(datapath, priority=10, match=match_server_arp, actions=[parser.OFPActionOutput(3)])

            # Return traffic from Server h6 to clients (10.0.0.0/24) via Path A (port 1) or Path B (port 2)
            out_port = 1 if self.active_path == 'A' else 2
            match_client_net = parser.OFPMatch(in_port=3, eth_type=0x0800)
            self.add_flow(datapath, priority=10, match=match_client_net, actions=[parser.OFPActionOutput(out_port)])
            match_client_arp = parser.OFPMatch(in_port=3, eth_type=0x0806)
            self.add_flow(datapath, priority=10, match=match_client_arp, actions=[parser.OFPActionOutput(out_port)])

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        """Fallback packet-in handler for unhandled traffic."""
        msg = ev.msg
        datapath = msg.datapath
        dpid = datapath.id
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        # Ignore LLDP
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        self.logger.debug("PacketIn: switch=%s in_port=%s src=%s dst=%s", dpid, in_port, eth.src, eth.dst)
