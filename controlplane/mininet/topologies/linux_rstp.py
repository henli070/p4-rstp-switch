from topology_base import TopologyBase

class Topology(TopologyBase):
    def __init__(self):
        TopologyBase.__init__(self)

    def build(self, **_opts):
        # Hosts:
        h1 = self.addHost("h1")
        h2 = self.addHost("h2")
        h3 = self.addHost("h3")

        # Switches:
        s1 = self.addLinuxBridge("s1", prio=0x1000, rstp=True)
        s2 = self.addLinuxBridge("s2", prio=0x2000, rstp=True)
        s3 = self.addLinuxBridge("s3", prio=0x3000, rstp=True)
        s4 = self.addLinuxBridge("s4", prio=0x4000, rstp=True)
        s5 = self.addLinuxBridge("s5", prio=0x5000, rstp=True)
        s6 = self.addLinuxBridge("s6", prio=0x6000, rstp=True)

        # Switch links:
        self.addLink(s1, s2)
        self.addLink(s1, s3)
        self.addLink(s1, s4)
        self.addLink(s1, s5)
        self.addLink(s1, s6)
        self.addLink(s2, s3)
        self.addLink(s2, s4)
        self.addLink(s2, s5)
        self.addLink(s2, s6)
        self.addLink(s3, s4)
        self.addLink(s3, s5)
        self.addLink(s3, s6)
        self.addLink(s4, s5)
        self.addLink(s4, s6)
        self.addLink(s5, s6)

        # Host links:
        self.addLink(h1, s1)
        self.addLink(h2, s2)
        self.addLink(h3, s3)