from mininet.node import Switch

import tempfile
import socket
import struct
import threading
import time
import os

cpu_port = 64

class SwitchP4(Switch):
    PORT_STATE_DISCARDING = 4
    PORT_STATE_LEARNING = 2
    PORT_STATE_FORWARDING = 3

    switch_id = 0

    def __init__(
        self,
        name,
        rstp = False,
        mac = None,
        prio = None,
        bmv2_logging = False,
        pcap = False,
        **kwargs
    ):
        Switch.__init__(self, name, **kwargs)
        self.rstp = rstp
        self.bmv2_logging = bmv2_logging
        self.pcap = pcap
        self.mac = mac
        self.config_socket = None
        self.running = False
        self.prio = prio

    def start(self, controllers):
        stp_version = "rstp" if self.rstp else "stp"
        print("Starting {} (SwitchP4, {})".format(self.name, stp_version))
        self.setup_cpu_port()

        # Ports.
        thrift_port = 10000 + SwitchP4.switch_id
        api_rpc_port = 9000 + SwitchP4.switch_id
        self.config_port = 11000 + SwitchP4.switch_id

        # Parameters.
        bmv2_parameters = ""
        driver_parameters = ""
        controller_parameters = ""
        for port, interface in self.intfs.items():
            if not interface.IP():
                bmv2_parameters += " -i {}@{}".format(port, interface.name)
                controller_parameters += " --port-no {}".format(port)
                # Work around the fact that BMv2 has problems if started with downed interfaces.
                self.cmd("ifconfig {} up".format(interface.name))

        bmv2_parameters += " -i {}@{}-cpu0".format(cpu_port, self.name)
        bmv2_parameters += " --log-file mininet_logs/bmv2-{}".format(self.name) if self.bmv2_logging else ""
        bmv2_parameters += " --pcap ." if self.pcap else ""
        bmv2_parameters += " --notifications-addr ipc:///tmp/bmv2-{}-notifications.ipc".format(SwitchP4.switch_id)
        bmv2_parameters += " --thrift-port {}".format(thrift_port)
        driver_parameters += " {} {} ipc:///tmp/bmv2-{}-notifications.ipc".format(api_rpc_port, thrift_port, SwitchP4.switch_id)
        controller_parameters += " --mac {}".format(self.mac) if self.mac != None else ""
        controller_parameters += " --cpu-interface {}-cpu1".format(self.name)
        controller_parameters += " --api-rpc-port {}".format(api_rpc_port)
        controller_parameters += " --stp-version {}".format(stp_version)
        controller_parameters += " --config-port {}".format(self.config_port)
        controller_parameters += " --bridge-prio {}".format(self.prio) if self.prio != None else ""

        # Run BMv2.
        with tempfile.NamedTemporaryFile() as f:
            self.cmd("simple_switch switch/p4-build/bmpd/switch.json{} > {} 2>&1 & echo $! >> {}".format(
                bmv2_parameters,
                "/dev/null" if self.bmv2_logging else "mininet_logs/bmv2-{}.txt".format(self.name),
                f.name
            ))
            self.bmv2_pid = int(f.read())

        time.sleep(1)
        # Run SwitchAPI drivers.
        with tempfile.NamedTemporaryFile() as f:
            self.cmd("stdbuf -o0 controlplane/drivers/drivers{} > mininet_logs/drivers-{}.txt 2>&1 & echo $! >> {}".format(
                driver_parameters,
                self.name,
                f.name
            ))
            self.switchapi_pid = int(f.read())

        time.sleep(1)
        # Run local controller.
        with tempfile.NamedTemporaryFile() as f:
            self.cmd("PYTHONPATH={}/switch/switchapi:$PYTHON_PATH python -u controlplane/controller/controller.py{} > mininet_logs/controller-{}.txt 2>&1 & echo $! >> {}".format(
                os.getcwd(),
                controller_parameters,
                self.name,
                f.name
            ))
            self.controller_pid = int(f.read())
        SwitchP4.switch_id += 1

        self.running = True

    def stop(self, deleteIntfs=True):
        print("Stopping {}".format(self.name))
        self.config_socket = None
        self.cmd("kill {}".format(self.controller_pid))
        self.cmd("wait {}".format(self.controller_pid))
        self.cmd("kill {}".format(self.switchapi_pid))
        self.cmd("wait {}".format(self.switchapi_pid))
        self.cmd("kill {}".format(self.bmv2_pid))
        self.cmd("wait {}".format(self.bmv2_pid))
        self.teardown_cpu_port()
        if deleteIntfs:
            self.deleteIntfs()
        self.running = False

    def get_port_state(self, port_no):
        while self.running:
            if not self.config_socket:
                self.config_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.config_socket.settimeout(1.0)
                while self.running:
                    try:
                        self.config_socket.connect(("localhost", self.config_port))
                        break
                    except Exception as e:
                        pass
                    time.sleep(0.2)

            GET_PORT_STATE = 21
            try:
                self.config_socket.sendall(struct.pack("!ii", GET_PORT_STATE, port_no))
                return struct.unpack("!ii", self.config_socket.recv(1500))[1]
            except Exception as e:
                self.config_socket = None
        # Switch not even running, so just return forwarding.
        return SwitchP4.PORT_STATE_FORWARDING

    def setup_cpu_port(self):
        # Add virtual CPU port.
        interface0 = "{}-cpu0".format(self.name)
        interface1 = "{}-cpu1".format(self.name)
        self.cmd("ip link add name {} type veth peer name {}".format(interface0, interface1))
        self.cmd("ip link set dev {} up".format(interface0))
        self.cmd("ip link set dev {} up".format(interface1))
        self.cmd("sysctl net.ipv6.conf.{}.disable_ipv6=1".format(interface0))
        self.cmd("sysctl net.ipv6.conf.{}.disable_ipv6=1".format(interface1))

    def teardown_cpu_port(self):
        interface0 = "{}-cpu0".format(self.name)
        self.cmd("ip link delete {} type veth".format(interface0))