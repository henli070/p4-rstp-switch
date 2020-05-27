class PortInfo:
    """Keeps various data about a switch port."""
    def __init__(
        self,
        port_no,
        interface,
        vlan_port
    ):
        self.port_no = port_no
        self.interface = interface
        self.vlan_port = vlan_port