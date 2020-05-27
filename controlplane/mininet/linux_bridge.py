from mininet.node import Switch
from mininet.util import quietRun

import time

class LinuxBridge(Switch):
    def __init__(self, name, prio=None, rstp=False, **kwargs):
        Switch.__init__(self, name, **kwargs)
        self.prio = prio
        self.rstp = rstp
        self.running = False

        # Checks.
        if "command not found" in self.cmd("brctl"):
            assert False, "bridge-utils needs to be installed to use the LinuxBridge switch."
        if self.rstp:
            if "command not found" in self.cmd("mstpctl"):
                assert False, "mstpd needs to be installed to use rstp on the LinuxBridge switch (https://github.com/mstpd/mstpd)."
            if self.prio:
                if self.prio % 4096 != 0:
                    assert False, "mstpd can only handle priorities that are multiples of 0x1000."

    def start(self, controllers):
        self.cmd("brctl addbr", self)
        self.cmd("brctl stp", self, "on")
        stp_version = "rstp" if self.rstp else "stp"
        print("Starting {} (LinuxBridge, {})".format(self.name, stp_version))

        if self.rstp:
            self.cmd("mstpctl addbridge", self)

        for interface in self.intfList():
            if self.name in interface.name:
                self.cmd("brctl addif", self, interface)
                if self.rstp:
                    self.cmd("mstpctl setportpathcost", self, interface, 2)

        if self.prio:
            if self.rstp:
                self.cmd("mstpctl setforcevers", self, "rstp")
                self.cmd("mstpctl settreeprio", self, 0, self.prio // 0x1000)
            else:
                self.cmd("brctl setbridgeprio", self, self.prio)

        self.cmd("ifconfig", self, "up")

        self.running = True

    def stop(self, deleteIntfs=True):
        print("Stopping {}".format(self.name))
        self.running = False
        if self.rstp:
           self.cmd("mstpctl delbridge ", self)
        self.cmd("ifconfig", self, "down")
        self.cmd("brctl delbr", self)
        Switch.stop(self, deleteIntfs)

    @classmethod
    def setup(cls):
        # Without this they seem to block a lot of traffic.
        cmd = "sysctl net.bridge.bridge-nf-call-iptables"
        out = quietRun(cmd).strip()
        if out.endswith("1"):
            quietRun("sysctl net.bridge.bridge-nf-call-iptables=0")
