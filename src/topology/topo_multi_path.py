r"""
Context-Aware SDN: Multi-Path Network Topology
Mininet Topology with 6 Hosts, 4 OpenFlow 1.3 Switches, and 2 Redundant Core Paths.

Topology Graph:
      h1  h2  h3  h4  h5
       \   \   |   /   /
             [ s1 ] (Ingress Switch)
            /      \
      Path A        Path B
     (10Mbps)      (10Mbps)
        /              \
     [ s2 ]          [ s3 ]
        \              /
         \            /
             [ s4 ] (Egress Switch)
               |
             [ h6 ] (Target Server)
"""

import sys
import argparse
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel, info


class MultiPathTopo(Topo):
    """Multi-path topology with redundant intermediate switches."""

    def build(self):
        info('*** Creating Switches (OpenFlow 1.3)\n')
        # Protocols set to OpenFlow13
        s1 = self.addSwitch('s1', protocols='OpenFlow13', dpid='0000000000000001')
        s2 = self.addSwitch('s2', protocols='OpenFlow13', dpid='0000000000000002')
        s3 = self.addSwitch('s3', protocols='OpenFlow13', dpid='0000000000000003')
        s4 = self.addSwitch('s4', protocols='OpenFlow13', dpid='0000000000000004')

        info('*** Creating Hosts\n')
        # Client hosts h1-h5
        h1 = self.addHost('h1', ip='10.0.0.1/24', mac='00:00:00:00:00:01')
        h2 = self.addHost('h2', ip='10.0.0.2/24', mac='00:00:00:00:00:02')
        h3 = self.addHost('h3', ip='10.0.0.3/24', mac='00:00:00:00:00:03')
        h4 = self.addHost('h4', ip='10.0.0.4/24', mac='00:00:00:00:00:04')
        h5 = self.addHost('h5', ip='10.0.0.5/24', mac='00:00:00:00:00:05')

        # Server host h6
        h6 = self.addHost('h6', ip='10.0.0.6/24', mac='00:00:00:00:00:06')

        info('*** Creating Access Links (100 Mbps, 1ms delay)\n')
        # Connecting clients to s1 (Ports 1 to 5 on s1)
        self.addLink(h1, s1, port1=1, port2=1, bw=100, delay='1ms')
        self.addLink(h2, s1, port1=1, port2=2, bw=100, delay='1ms')
        self.addLink(h3, s1, port1=1, port2=3, bw=100, delay='1ms')
        self.addLink(h4, s1, port1=1, port2=4, bw=100, delay='1ms')
        self.addLink(h5, s1, port1=1, port2=5, bw=100, delay='1ms')

        # Connecting s4 to server h6 (Port 3 on s4)
        self.addLink(h6, s4, port1=1, port2=3, bw=100, delay='1ms')

        info('*** Creating Core Redundant Links (10 Mbps)\n')
        # Path A: s1 <-> s2 <-> s4 (5ms delay)
        # s1: port 6 -> s2: port 1
        self.addLink(s1, s2, port1=6, port2=1, bw=10, delay='5ms')
        # s2: port 2 -> s4: port 1
        self.addLink(s2, s4, port1=2, port2=1, bw=10, delay='5ms')

        # Path B: s1 <-> s3 <-> s4 (10ms delay)
        # s1: port 7 -> s3: port 1
        self.addLink(s1, s3, port1=7, port2=1, bw=10, delay='10ms')
        # s3: port 2 -> s4: port 2
        self.addLink(s3, s4, port1=2, port2=2, bw=10, delay='10ms')


topos = {'multipath': (lambda: MultiPathTopo())}


def run(controller_ip='127.0.0.1', controller_port=6653, test_mode=False):
    """Start Mininet network and connect to Ryu remote controller."""
    topo = MultiPathTopo()
    info('*** Initializing Mininet Network\n')
    net = Mininet(
        topo=topo,
        switch=OVSSwitch,
        controller=None,
        link=TCLink,
        autoSetMacs=True,
        autoStaticArp=True
    )

    info('*** Adding Remote Ryu Controller at %s:%s\n' % (controller_ip, controller_port))
    controller = net.addController(
        name='ryu_c0',
        controller=RemoteController,
        ip=controller_ip,
        port=controller_port
    )

    info('*** Starting Network\n')
    net.start()

    if test_mode:
        info('*** Running Connectivity Test: pingall\n')
        dropped = net.pingAll()
        info('*** PingAll dropped: %.2f%%\n' % dropped)
        net.stop()
        return dropped
    else:
        info('*** Network is Ready. Starting CLI. (Type "exit" to quit)\n')
        CLI(net)
        net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    parser = argparse.ArgumentParser(description='Multi-path SDN Mininet Topology')
    parser.add_argument('--controller-ip', default='127.0.0.1', help='Ryu controller IP')
    parser.add_argument('--controller-port', type=int, default=6653, help='Ryu controller OpenFlow port')
    parser.add_argument('--test', action='store_true', help='Run automated ping test and exit')
    args = parser.parse_args()

    run(controller_ip=args.controller_ip, controller_port=args.controller_port, test_mode=args.test)
