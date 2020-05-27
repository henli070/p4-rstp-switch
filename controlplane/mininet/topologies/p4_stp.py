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
        s1 = self.addSwitchP4("s1", mac="00:00:00:00:01:00", rstp=False)
        s2 = self.addSwitchP4("s2", mac="00:00:00:00:02:00", rstp=False)
        s3 = self.addSwitchP4("s3", mac="00:00:00:00:03:00", rstp=False)
        s4 = self.addSwitchP4("s4", mac="00:00:00:00:04:00", rstp=False)
        s5 = self.addSwitchP4("s5", mac="00:00:00:00:05:00", rstp=False)
        s6 = self.addSwitchP4("s6", mac="00:00:00:00:06:00", rstp=False)

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