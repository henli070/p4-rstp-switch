import threading
from scapy.all import *

EHTER_TYPE_CPU = 0x9000

class FabricHeader(Packet):
    name = "Fabric Header"
    fields_desc = [
        BitField("packet_type", 0, 3),
        BitField("header_version", 0, 2),
        BitField("packet_version", 0, 2),
        BitField("pad1", 0, 1),
        BitField("fabric_color", 0, 3),
        BitField("fabric_qos", 0, 5),
        XByteField("dst_device", 0),
        XShortField("dst_port_or_group", 0),
    ]

class FabricCpuHeader(Packet):
    name = "Fabric Cpu Header"
    fields_desc = [
        BitField("egress_queue", 0, 5),
        BitField("tx_bypass", 0, 1),
        BitField("reserved1", 0, 2),
        XShortField("ingress_port", 0),
        XShortField("ingress_ifindex", 0),
        XShortField("ingress_bd", 0),

        XShortField("reason_code", 0),
        XShortField("mcast_grp", 0)
    ]

class FabricPayloadHeader(Packet):
    name = "Fabric Payload Header"
    fields_desc = [XShortField("ether_type", 0)]

class PacketIo:
    """Handles packet incoming on the CPU port, and allows sending packets out of the switch."""
    BPDU_SIZE = 0x26
    RSTP_BPDU_SIZE = 0x27
    def __init__(self, cpu_interface, self_mac, packet_in_callback):
        self.cpu_interface = cpu_interface
        self.mac = self_mac
        self.packet_in_callback = packet_in_callback

        bind_layers(Ether, FabricHeader, type=EHTER_TYPE_CPU)
        bind_layers(FabricHeader, FabricCpuHeader, packet_type=0x05)
        bind_layers(FabricCpuHeader, FabricPayloadHeader)

    def start_sniffing(self):
        sniffing_thread = threading.Thread(target=self._cpu_port_sniffing)
        sniffing_thread.daemon = True
        sniffing_thread.start()

    def _handle_packet_in(self, packet):
        if not FabricPayloadHeader in packet:
            return
        # Create a new packet without the cpu headers.
        packet_raw = str(packet)
        new_packet_raw = packet_raw[0:12] + packet_raw[30:]
        new_packet = Ether(new_packet_raw)
        self.packet_in_callback(new_packet, packet.ingress_port)

    def _cpu_port_sniffing(self):
        sniff(iface=self.cpu_interface, prn=lambda x: self._handle_packet_in(x), filter="inbound")

    def send_config_bpdu(
        self,
        bpdu_flags,
        root_prio,
        root_mac,
        root_path_cost,
        bridge_prio,
        bridge_mac,
        port_id,
        message_age,
        max_age,
        hello_time,
        forward_delay,
        out_port
    ):
        """Send a STP BPDU out on the switch port identified by out_port."""
        ether = Ether(src=self.mac, dst="01:80:c2:00:00:00", type=EHTER_TYPE_CPU)
        fabric_header = FabricHeader(dst_port_or_group=out_port)
        fabric_cpu_header = FabricCpuHeader(tx_bypass=1, reason_code=0xFFFF)

        bpdu = STP(
            proto=0,
            version=0,
            bpdutype=0x00,
            bpduflags=bpdu_flags,
            rootid=root_prio,
            rootmac=root_mac,
            pathcost=root_path_cost,
            bridgeid=bridge_prio,
            bridgemac=bridge_mac,
            portid=port_id,
            age=message_age,
            maxage=max_age,
            hellotime=hello_time,
            fwddelay=forward_delay
        )
        pkt = ether / fabric_header / fabric_cpu_header / FabricPayloadHeader(ether_type=PacketIo.BPDU_SIZE) / LLC() / bpdu

        sendp(pkt, iface=self.cpu_interface, verbose=False)

    def send_tcn_bpdu(self, out_port):
        """Sends a topology change notification BPDU on the switch port identified by out_port."""
        ether = Ether(src=self.mac, dst="01:80:c2:00:00:00", type=EHTER_TYPE_CPU)
        fabric_header = FabricHeader(dst_port_or_group=out_port)
        fabric_cpu_header = FabricCpuHeader(tx_bypass=1, reason_code=0xFFFF)

        bpdu = STP(bpdutype=0x80) # Topology change BPDU.

        pkt = ether / fabric_header / fabric_cpu_header / FabricPayloadHeader(ether_type=PacketIo.BPDU_SIZE) / LLC() / bpdu

        sendp(pkt, iface=self.cpu_interface, verbose=False)

    def send_rstp_bpdu(
        self,
        bpdu_flags,
        root_prio,
        root_mac,
        root_path_cost,
        bridge_prio,
        bridge_mac,
        port_id,
        message_age,
        max_age,
        hello_time,
        forward_delay,
        out_port
    ):
        """Send a RSTP BPDU out on the switch port identified by out_port."""
        ether = Ether(src=self.mac, dst="01:80:c2:00:00:00", type=EHTER_TYPE_CPU)
        fabric_header = FabricHeader(dst_port_or_group=out_port)
        fabric_cpu_header = FabricCpuHeader(tx_bypass=1, reason_code=0xFFFF)

        version_1_length = Padding("\x00")

        bpdu = STP(
            proto=0,
            version=0x02,
            bpdutype=0x02,
            bpduflags=bpdu_flags,
            rootid=root_prio,
            rootmac=root_mac,
            pathcost=root_path_cost,
            bridgeid=bridge_prio,
            bridgemac=bridge_mac,
            portid=port_id,
            age=message_age,
            maxage=max_age,
            hellotime=hello_time,
            fwddelay=forward_delay
        ) / version_1_length
        pkt = ether / fabric_header / fabric_cpu_header / FabricPayloadHeader(ether_type=PacketIo.RSTP_BPDU_SIZE) / LLC() / bpdu

        sendp(pkt, iface=self.cpu_interface, verbose=False)