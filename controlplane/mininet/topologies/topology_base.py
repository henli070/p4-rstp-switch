from mininet.topo import Topo
from switch_p4 import SwitchP4
from linux_bridge import LinuxBridge

class TopologyBase(Topo):
    def __init__(self):
        Topo.__init__(self)

    def addSwitchP4(self, name, **kwargs):
        return Topo.addSwitch(self, name, cls=SwitchP4, **kwargs)

    def addLinuxBridge(self, name, **kwargs):
        return Topo.addSwitch(self, name, cls=LinuxBridge, **kwargs)

    def addLink(self, n1, n2):
        Topo.addLink(self, n1, n2, intfName1="{}-{}".format(n1, n2), intfName2="{}-{}".format(n2, n1))