from datetime import datetime

class InvalidParameter(Exception):
    pass

class RstpConfiguration:
    """An interface for reading and setting configuration for RstpHandler, following 802.1D-2004, section 14.8."""

    def __init__(self, rstp_handler):
        self.rstp_handler = rstp_handler

    def _verify_port_parameter(self, port_no):
        if port_no < 1 or port_no > 4095:
            raise InvalidParameter()
        if not port_no in self.rstp_handler.rstp_ports:
            raise InvalidParameter()

    # Get bridge configuration.
    def get_bridge_identifier(self):
        """Returns the bridge identifier as a tuple of priority and mac address."""
        return self.rstp_handler.BridgeIdentifier

    def get_time_since_topology_change(self):
        if self.rstp_handler.last_topology_change_time != None:
            return (datetime.now() - self.rstp_handler.last_topology_change_time).total_seconds()
        return -1

    def get_topology_change_count(self):
        return self.rstp_handler.topology_change_count

    def get_designated_root(self):
        """Returns the designated root as a tuple of priority and mac address."""
        return self.rstp_handler.rootPriority.RootBridgeID

    def get_root_path_cost(self):
        return self.rstp_handler.rootPriority.RootPathCost

    def get_root_port(self):
        return self.rstp_handler.rootPortId

    def get_max_age(self):
        return self.rstp_handler.rootTimes.BridgeMaxAge

    def get_hello_time(self):
        return self.rstp_handler.rootTimes.BridgeHelloTime

    def get_forward_delay(self):
        return self.rstp_handler.rootTimes.BridgeForwardDelay

    def get_bridge_max_age(self):
        return self.rstp_handler.BridgeTimes.BridgeMaxAge

    def get_bridge_hello_time(self):
        return self.rstp_handler.BridgeTimes.BridgeHelloTime

    def get_bridge_forward_delay(self):
        return self.rstp_handler.BridgeTimes.BridgeForwardDelay

    def get_tx_hold_count(self):
        return self.rstp_handler.TxHoldCount

    def get_force_version(self):
        return self.rstp_handler.ForceProtocolVersion

    # Set bridge configuration.
    def set_bridge_max_age(self, value):
        with self.rstp_handler.callback_lock:
            self.rstp_handler.BridgeTimes.BridgeMaxAge = value
            for port in self.rstp_handler.rstp_ports.values():
                port.reselect = True
                port.selected = False
            self.rstp_handler.update()

    def set_bridge_hello_time(self, value):
        with self.rstp_handler.callback_lock:
            self.rstp_handler.BridgeTimes.BridgeHelloTime = value
            for port in self.rstp_handler.rstp_ports.values():
                port.reselect = True
                port.selected = False
            self.rstp_handler.update()

    def set_bridge_forward_delay(self, value):
        with self.rstp_handler.callback_lock:
            self.rstp_handler.BridgeTimes.BridgeForwardDelay = value
            for port in self.rstp_handler.rstp_ports.values():
                port.reselect = True
                port.selected = False
            self.rstp_handler.update()

    def set_bridge_priority(self, value):
        # 14.3 k)
        if value < 0 or value > 61440 or value % 4096 != 0:
            raise InvalidParameter()
        with self.rstp_handler.callback_lock:
            self.rstp_handler.BridgePriority.RootBridgeID = (value, self.rstp_handler.BridgePriority.RootBridgeID[1])
            self.rstp_handler.BridgePriority.DesignatedBridgeID = (value, self.rstp_handler.BridgePriority.DesignatedBridgeID[1])
            self.rstp_handler.BridgeIdentifier = (value, self.rstp_handler.BridgeIdentifier[1])
            for port in self.rstp_handler.rstp_ports.values():
                port.reselect = True
                port.selected = False
            self.rstp_handler.update()

    def set_force_version(self, value):
        with self.rstp_handler.callback_lock:
            self.rstp_handler.ForceProtocolVersion = value
            self.rstp_handler.do_begin_states()

    def set_tx_hold_count(self, value):
        with self.rstp_handler.callback_lock:
            self.rstp_handler.TxHoldCount = value
            for port in self.rstp_handler.rstp_ports.values():
                port.txCount = 0
                port.reselect = True
                port.selected = False
            self.rstp_handler.update()

    # Read port configuration.
    def get_port_uptime(self, port_no):
        self._verify_port_parameter(port_no)
        return (datetime.now() - self.rstp_handler.rstp_ports[port_no].initialize_time).total_seconds()

    def get_port_state(self, port_no):
        self._verify_port_parameter(port_no)
        return self.rstp_handler.rstp_ports[port_no].state

    def get_port_identifier(self, port_no):
        self._verify_port_parameter(port_no)
        return self.rstp_handler.rstp_ports[port_no].portId

    def get_port_path_cost(self, port_no):
        self._verify_port_parameter(port_no)
        return self.rstp_handler.rstp_ports[port_no].PortPathCost

    def get_port_designated_root(self, port_no):
        self._verify_port_parameter(port_no)
        return self.rstp_handler.rstp_ports[port_no].portPriority.RootBridgeID

    def get_port_designated_cost(self, port_no):
        self._verify_port_parameter(port_no)
        return self.rstp_handler.rstp_ports[port_no].portPriority.RootPathCost

    def get_port_designated_bridge(self, port_no):
        self._verify_port_parameter(port_no)
        return self.rstp_handler.rstp_ports[port_no].portPriority.DesignatedBridgeID

    def get_port_designated_port(self, port_no):
        self._verify_port_parameter(port_no)
        return self.rstp_handler.rstp_ports[port_no].portPriority.DesignatedPortID

    def get_port_topology_change_acknowledge(self, port_no):
        self._verify_port_parameter(port_no)
        return self.rstp_handler.rstp_ports[port_no].tcAck

    def get_port_admin_edge(self, port_no):
        self._verify_port_parameter(port_no)
        return self.rstp_handler.rstp_ports[port_no].AdminEdgePort

    def get_port_oper_edge(self, port_no):
        self._verify_port_parameter(port_no)
        return self.rstp_handler.rstp_ports[port_no].operEdge

    def get_port_auto_edge(self, port_no):
        self._verify_port_parameter(port_no)
        return self.rstp_handler.rstp_ports[port_no].AutoEdgePort

    def get_port_oper_point_to_point_mac(self, port_no):
        self._verify_port_parameter(port_no)
        return self.rstp_handler.rstp_ports[port_no].operPointToPointMAC

    # Set port configuration.
    def set_port_path_cost(self, port_no, value):
        with self.rstp_handler.callback_lock:
            self._verify_port_parameter(port_no)
            port = self.rstp_handler.rstp_ports[port_no]
            port.PortPathCost = value
            port.reselect = True
            port.selected = False
            self.rstp_handler.update()

    def set_port_priority(self, port_no, value):
        with self.rstp_handler.callback_lock:
            self._verify_port_parameter(port_no)
            # 14.3 j)
            if value < 0 or value > 240 or value % 16 != 0:
                raise InvalidParameter()
            port = self.rstp_handler.rstp_ports[port_no]
            port.portId = (value << 8) | port.port_no
            port.reselect = True
            port.selected = False
            self.rstp_handler.update()

    def set_port_admin_edge(self, port_no, value):
        with self.rstp_handler.callback_lock:
            self._verify_port_parameter(port_no)
            port = self.rstp_handler.rstp_ports[port_no]
            port.AdminEdgePort = value
            port.reselect = True
            port.selected = False
            self.rstp_handler.update()

    def set_port_auto_edge(self, port_no, value):
        with self.rstp_handler.callback_lock:
            self._verify_port_parameter(port_no)
            port = self.rstp_handler.rstp_ports[port_no]
            port.AutoEdgePort = value
            port.reselect = True
            port.selected = False
            self.rstp_handler.update()