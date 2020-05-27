import importlib
import sys

from mininet.topo import *
from mininet.net import *
from mininet.node import *
from mininet.cli import *

from debug_visualization import DebugVisualization

# Should show debug visualization?
debug = True

def disable_ipv6(net):
    # Disable spammy IPv6 packets.
    for node in net.hosts:
        for interface in node.intfs.values():
            node.cmd("sysctl net.ipv6.conf.{}.disable_ipv6=1".format(interface.name))
    for node in net.switches:
        for interface in node.intfs.values():
            node.cmd("sysctl net.ipv6.conf.{}.disable_ipv6=1".format(interface.name))

def main():
    debug_visualization = DebugVisualization() if debug else None

    topology_name = sys.argv[1] if len(sys.argv) > 1 else "p4_rstp"

    topo = importlib.import_module("topologies.{}".format(topology_name)).Topology()

    net = Mininet(topo=topo, controller=None, switch=None)
    disable_ipv6(net)
    sleep(1)
    if debug:
        debug_visualization.start(net)
    try:
        net.start()

        CLI(net)
    except Exception as e:
        print(e)
    finally:
        net.stop()
        if debug:
            debug_visualization.stop()

if __name__ == "__main__":
    main()
