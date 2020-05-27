from datetime import datetime
from threading import Lock
import time

from timer import Timer
from structures import PriorityVector, BridgeTimes
from rstp_port import RstpPort
from state_machines import PortRoleSelection
import rstp_util

from switch_api_thrift.ttypes import *
from switch_api_thrift.switch_api_headers import *

device = 0

class RstpHandler:
    """Implementation of the Rapid Spanning Tree Protocol (IEEE 802.1D-2004)"""
    def __init__(
        self,
        switch_api_client,
        packet_io,
        vlan,
        port_infos,
        bridge_prio,
        bridge_mac,
        rstp
    ):
        self.client = switch_api_client
        self.packet_io = packet_io
        self.vlan = vlan

        self.rstp_ports = {}
        self.callback_lock = Lock() # Lock so multiple callbacks don't run at the same time.

        # Set default aging time.
        self.current_aging_time = None
        self.switch_set_aging_time(rstp_util.DEFAULT_AGING_TIME)

        # Add STP group, needed for setting port states.
        self.stp_group = self.client.switcht_api_stp_group_create(device, SWITCH_PORT_STP_MODE_RSTP)
        self.client.switcht_api_stp_group_vlans_add(device, self.stp_group, 1, [self.vlan])
        self.second_timer = Timer(self.second_timer_callback)
        self.rapid_aging_timer = Timer(self.rapid_aging_workaround_callback) # TODO: See comment in "start_rapid_aging_workaround".

        self.BridgeIdentifier = (bridge_prio, bridge_mac)
        self.BridgePriority = PriorityVector(self.BridgeIdentifier, 0, self.BridgeIdentifier, 0, 0)

        self.last_topology_change_time = None
        self.topology_change_count = 0

        # Initialize defaults (17.14)
        self.BridgeTimes = BridgeTimes(15, 2, 20, 0)
        self.TxHoldCount = 6

        # 17.13.4
        self.ForceProtocolVersion = 2 if rstp else 0

        for port_info in port_infos.values():
            self.rstp_ports[port_info.port_no] = RstpPort(self, port_info)

        self.port_role_selection = PortRoleSelection(self)

    def do_begin_states(self):
        # The standard claims execution order of states doesn't matter,
        # but the wrong order while BEGIN is True results in attempted use of undefined variables.
        # Therefore we initialize the state machines in an order that works.
        self.BEGIN = True
        # Start with all state machines who's BEGIN states don't depend on any variables.
        for port in self.rstp_ports.values():
            port.initialize_time = datetime.now()

            port.port_information.update()
            port.port_transmit.update()
            port.bridge_detection.update()
            port.port_protocol_migration.update()
            port.port_receive.update()
            port.port_state_transition.update()
            port.topology_change.update()

        # PortRoleSelection must be run twice so that updtRolesTree() gets called.
        self.port_role_selection.update()
        self.BEGIN = False
        self.port_role_selection.update()

        # Finish with the state machine that depend on updtRolesTree() having been called.
        self.BEGIN = True
        for port in self.rstp_ports.values():
            port.port_role_transitions.update()
        self.BEGIN = False

        self.update()

    def initialize(self):
        with self.callback_lock:
            self.do_begin_states()
            self.second_timer.start(1.0)
            return True

    # Update all state machines.
    def update(self):
        # Check if there was a topology change active.
        was_topology_change = False
        for port in self.rstp_ports.values():
            if port.tcWhile > 0:
                was_topology_change = True

        # Do all state machine updates.
        needsUpdate = True
        while needsUpdate:
            needsUpdate = False
            needsUpdate = self.port_role_selection.update() or needsUpdate
            for port in self.rstp_ports.values():
                needsUpdate = port.update() or needsUpdate

        # Check if there's a topology change active after update.
        topology_change = False
        for port in self.rstp_ports.values():
            if port.tcWhile > 0:
                topology_change = True
            port.set_switch_state()

        if topology_change:
            self.last_topology_change_time = datetime.now()
            if not was_topology_change:
                self.topology_change_count += 1

    def start_rapid_aging(self):
        self.rapid_aging_timer.start(self.rootTimes.BridgeForwardDelay)
        self.switch_set_aging_time(self.rootTimes.BridgeForwardDelay)

    def rapid_aging_callback(self):
        with self.callback_lock:
            self.switch_set_aging_time(rstp_util.DEFAULT_AGING_TIME)
            self.rapid_aging_timer.stop()

    def start_rapid_aging_workaround(self):
        # TODO: This is used as a workaround for SwitchAPI not updating aging for existing entries
        # when aging time is changed. Once this problem is fixed, "start_rapid_aging" and "rapid_aging_callback"
        # should be used instead.
        if not self.rapid_aging_timer.is_active():
            self.rapid_aging_timer.start(self.rootTimes.BridgeForwardDelay)

    def rapid_aging_workaround_callback(self):
        with self.callback_lock:
            self.client.switcht_api_mac_table_entries_delete_by_vlan(
                device = device,
                vlan_handle = self.vlan
            )
            self.rapid_aging_timer.stop()

    def bpdu_received_callback(self, packet, in_port):
        with self.callback_lock:
            if in_port not in self.rstp_ports:
                return
            rstp_port = self.rstp_ports[in_port]
            rstp_port.last_bpdu = packet
            # 17.19.25
            rstp_port.rcvdBPDU = True
            self.update()

    # 17.20.11
    def rstpVersion(self):
        return self.ForceProtocolVersion >= 2

    # 17.20.12
    def stpVersion(self):
        return self.ForceProtocolVersion < 2

    # 17.22
    def second_timer_callback(self):
        with self.callback_lock:
            if self.BEGIN:
                return
            # TICK
            for port in self.rstp_ports.values():
                if port.helloWhen > 0:
                    port.helloWhen -= 1
                if port.tcWhile > 0:
                    port.tcWhile -= 1
                if port.fdWhile > 0:
                    port.fdWhile -= 1
                if port.rcvdInfoWhile > 0:
                    port.rcvdInfoWhile -= 1
                if port.rrWhile > 0:
                    port.rrWhile -= 1
                if port.rbWhile > 0:
                    port.rbWhile -= 1
                if port.mdelayWhile > 0:
                    port.mdelayWhile -= 1
                if port.edgeDelayWhile > 0:
                    port.edgeDelayWhile -= 1
                if port.txCount > 0:
                    port.txCount -= 1

            self.update()

    # 17.21.24
    def updtRoleDisabledTree(self):
        for port in self.rstp_ports.values():
            port.selectedRole = rstp_util.DISABLED_PORT

    # 17.21.25
    def updtRolesTree(self):
        # (a), (b) and (c)
        self.rootPriority = self.BridgePriority.copy()
        self.rootPortId = 0
        self.rootTimes = self.BridgeTimes.copy()
        for port in self.rstp_ports.values():
            if port.infoIs == rstp_util.RECEIVED:
                rootPathPriorityVector = port.portPriority.copy()
                rootPathPriorityVector.RootPathCost += port.PortPathCost

                if rootPathPriorityVector.DesignatedBridgeID != self.BridgePriority.DesignatedBridgeID:
                    if rootPathPriorityVector.compare_to(self.rootPriority) < 0:
                        self.rootPriority = rootPathPriorityVector
                        self.rootPortId = self.rootPriority.BridgePortID
                        self.rootTimes = port.portTimes.copy()
                        self.rootTimes.MessageAge = round(self.rootTimes.MessageAge + 1)

        # (d) and (e)
        for port in self.rstp_ports.values():
            port.designatedPriority = PriorityVector(
                self.rootPriority.RootBridgeID,
                self.rootPriority.RootPathCost,
                self.BridgeIdentifier,
                port.portId,
                port.portId
            )
            port.designatedTimes = self.rootTimes.copy()
            port.designatedTimes.BridgeHelloTime = self.BridgeTimes.BridgeHelloTime

        # (f) to (l)
        for port in self.rstp_ports.values():
            if port.infoIs == rstp_util.DISABLED:
                # (f)
                port.selectedRole = rstp_util.DISABLED_PORT
            else:
                if port.infoIs == rstp_util.AGED:
                    # (g)
                    port.updtInfo = True
                    port.selectedRole = rstp_util.DESIGNATED_PORT
                elif port.infoIs == rstp_util.MINE:
                    # (h)
                    port.selectedRole = rstp_util.DESIGNATED_PORT
                    if (
                        port.portPriority.compare_to(port.designatedPriority) != 0 or
                        not port.portTimes.equals(self.rootTimes)
                    ):
                        port.updtInfo = True
                elif port.infoIs == rstp_util.RECEIVED:
                    if self.rootPortId == port.portId:
                        # (i)
                        port.selectedRole = rstp_util.ROOT_PORT
                        port.updtInfo = False
                    else:
                        if port.designatedPriority.compare_to(port.portPriority) < 0:
                            # (l)
                            port.selectedRole = rstp_util.DESIGNATED_PORT
                            port.updtInfo = True
                        else:
                            if port.portPriority.DesignatedBridgeID != self.BridgeIdentifier:
                                # (j)
                                port.selectedRole = rstp_util.ALTERNATE_PORT
                                port.updtInfo = False
                            else:
                                # (k)
                                port.selectedRole = rstp_util.BACKUP_PORT
                                port.updtInfo = False

    # 17.21.14
    def setSyncTree(self):
        for port in self.rstp_ports.values():
            port.sync = True

    # 17.21.15
    def setReRootTree(self):
        for port in self.rstp_ports.values():
            port.reRoot = True

    # 17.21.16
    def setSelectedTree(self):
        for port in self.rstp_ports.values():
            if port.reselect:
                return
        for port in self.rstp_ports.values():
            port.selected = True

    # 17.21.18
    def setTcPropTree(self, port_no):
        for port in self.rstp_ports.values():
            if port.port_no != port_no:
                port.tcProp = True

    # 17.21.2
    def clearReselectTree(self):
        for port in self.rstp_ports.values():
            port.reselect = False

    # 17.20.3
    def allSynced(self):
        for port in self.rstp_ports.values():
            if port.selected and port.role == port.selectedRole:
                if port.synced or self.rootPortId == port.portId:
                    continue
            return False
        return True

    # 17.21.2
    def clearReselectTree(self):
        for port in self.rstp_ports.values():
            port.reselect = False

    def switch_set_port_state(self, port_no, stp_state):
        self.client.switcht_api_stp_port_state_set(
            device = device,
            stp_handle = self.stp_group,
            intf_handle = self.rstp_ports[port_no].port_info.interface,
            stp_state = stp_state
        )

    def switch_flush_mac_entries(self, port_no):
        self.client.switcht_api_mac_table_entries_delete_by_interface(
            device = device,
            intf_handle = self.rstp_ports[port_no].port_info.interface
        )

    def switch_set_aging_time(self, aging_time):
        if aging_time != self.current_aging_time:
            self.current_aging_time = aging_time
            self.client.switcht_api_vlan_aging_interval_set(self.vlan, aging_time * 1000)

    def teardown(self):
        with self.callback_lock:
            self.second_timer.cancel()
            self.rapid_aging_timer.cancel()
            self.client.switcht_api_stp_group_vlans_remove(device, self.stp_group, 1, [self.vlan])
            self.client.switcht_api_stp_group_delete(device, self.stp_group)
