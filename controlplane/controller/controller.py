import sys
import os
import time
import signal
from scapy.all import *

from switch_api_thrift.ttypes import *
from switch_api_thrift.switch_api_headers import *
import switch_api_thrift.switch_api_rpc as switch_api_rpc

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

from options import Options
from packet_io import PacketIo
from rstp.rstp_handler import RstpHandler
from configuration_server import ConfigurationServer
from rstp.rstp_configuration import RstpConfiguration

device = 0
from port_info import PortInfo

class Controller:
    """The main controller class."""
    def __init__(self):
        self.options = Options()
        self.mac = self.options.mac
        self.cpu_interface = self.options.cpu_interface
        self.config_port = self.options.config_port
        self.rstp = True if self.options.stp_version == Options.VERSION_RSTP else False
        self.bridge_prio = self.options.bridge_prio

        self.transport = TSocket.TSocket("localhost", self.options.rpc_port)
        self.transport = TTransport.TBufferedTransport(self.transport)
        self.protocol = TBinaryProtocol.TBinaryProtocol(self.transport)

        self.client = switch_api_rpc.Client(self.protocol)
        self.transport.open()

    def handle_packet_in(self, packet, in_port):
        if STP in packet:
            self.rstp_handler.bpdu_received_callback(packet, in_port)

    def setup(self):
        self.client.switcht_api_init(device)
        self.vlan = self.client.switcht_api_vlan_create(device, 10)

        self.port_infos = {}
        for port_no in self.options.port_nos:
            iu = interface_union(port_lag_handle=port_no)
            interface_info = switcht_interface_info_t(device=device, type=SWITCH_API_INTERFACE_L2_VLAN_ACCESS, u=iu, mac=self.mac, label=0)
            interface = self.client.switcht_api_interface_create(device, interface_info)
            vlan_port = switcht_vlan_port_t(handle=interface, tagging_mode=SWITCH_VLAN_PORT_UNTAGGED)
            self.client.switcht_api_vlan_ports_add(device, self.vlan, vlan_port)
            self.port_infos[port_no] = PortInfo(port_no, interface, vlan_port)

        # Redirect STP to cpu port.
        hostif_group = switcht_hostif_group_t(queue_id=1, priority=1000) # TODO: These values taken from test case, what effect do they have?
        self.hostif_group_id = self.client.switcht_api_hostif_group_create(device, hostif_group)
        stp_rcode_info = switcht_api_hostif_rcode_info_t(
            reason_code = SWITCH_HOSTIF_REASON_CODE_STP,
            action = SWITCH_ACL_ACTION_REDIRECT_TO_CPU,
            hostif_group_id = self.hostif_group_id
        )
        self.client.switcht_api_hostif_reason_code_create(device, stp_rcode_info)

        self.packet_io = PacketIo(self.cpu_interface, self.mac, self.handle_packet_in)
        self.rstp_handler = RstpHandler(self.client, self.packet_io, self.vlan, self.port_infos, self.bridge_prio, self.mac, self.rstp)
        self.rstp_configuration = RstpConfiguration(self.rstp_handler)

    def teardown(self):
        self.rstp_handler.teardown()

        self.client.switcht_api_hostif_reason_code_delete(device, SWITCH_HOSTIF_REASON_CODE_STP)
        self.client.switcht_api_hostif_group_delete(device, self.hostif_group_id)

        for port_info in self.port_infos.values():
            self.client.switcht_api_vlan_ports_remove(device, self.vlan, port_info.vlan_port)
            self.client.switcht_api_interface_delete(device, port_info.interface)
        self.client.switcht_api_vlan_delete(device, self.vlan)

    def run(self):
        if not self.rstp_handler.initialize():
            return
        self.packet_io.start_sniffing()

        if self.config_port:
            config_server = ConfigurationServer(self.rstp_configuration, self.config_port)
            config_server.start()

        signal.signal(signal.SIGTERM, self.stop)
        signal.signal(signal.SIGINT, self.stop)
        self.should_run = True
        while self.should_run:
            time.sleep(1)

        if self.config_port:
            config_server.stop()

    def stop(self, signum=None, frame=None):
        self.should_run = False

if __name__ == "__main__":
    controller = Controller()
    controller.setup()
    controller.run()
    controller.teardown()
    controller.transport.close()
    print("Exited gracefully!")