from datetime import datetime
from structures import *

from timer import Timer
import rstp_util
from state_machines import *

from switch_api_thrift.ttypes import *
from switch_api_thrift.switch_api_headers import *

class RstpPort:
    """Class representing a single port in the RSTP algorithm."""
    def __init__(self, rstp_handler, port_info):
        self.rstp_handler = rstp_handler
        self.port_info = port_info
        self.port_no = port_info.port_no

        self.state = rstp_util.PORT_STATE_DISCARDING
        self.switch_state = SWITCH_PORT_STP_STATE_NONE

        self.disputed = False # Shouldn't have to do this, but the standard forgets to initialize it.
        self.portEnabled = True
        self.portId = (0x80 << 8) | self.port_no # 0x80 is the default port priority.
        self.PortPathCost = 2
        self.AdminEdgePort = False
        self.AutoEdgePort = True
        self.operPointToPointMAC = True

        # State machines.
        self.port_receive = PortReceive(rstp_handler, self)
        self.port_protocol_migration = PortProtocolMigration(rstp_handler, self)
        self.bridge_detection = BridgeDetection(rstp_handler, self)
        self.port_transmit = PortTransmit(rstp_handler, self)
        self.port_information = PortInformation(rstp_handler, self)
        self.port_role_transitions = PortRoleTransitions(rstp_handler, self)
        self.port_state_transition = PortStateTransition(rstp_handler, self)
        self.topology_change = TopologyChange(rstp_handler, self)

    def update(self):
        wasUpdated = False
        wasUpdated = self.port_receive.update() or wasUpdated
        wasUpdated = self.port_protocol_migration.update() or wasUpdated
        wasUpdated = self.bridge_detection.update() or wasUpdated
        wasUpdated = self.port_transmit.update() or wasUpdated
        wasUpdated = self.port_information.update() or wasUpdated
        wasUpdated = self.port_role_transitions.update() or wasUpdated
        wasUpdated = self.port_state_transition.update() or wasUpdated
        wasUpdated = self.topology_change.update() or wasUpdated

        if self.fdbFlush:
            if self.rstp_handler.rstpVersion():
                self.rstp_handler.switch_flush_mac_entries(self.port_no)
                self.fdbFlush = False
            elif self.rstp_handler.stpVersion():
                self.rstp_handler.start_rapid_aging_workaround() # TODO: See "start_rapid_aging_workaround" in rstp_handler.py.
                self.fdbFlush = False

        return wasUpdated

    # Update the switch stp state if needed.
    def set_switch_state(self):
        new_switch_state = None
        if self.state == rstp_util.PORT_STATE_DISCARDING:
            new_switch_state = SWITCH_PORT_STP_STATE_BLOCKING
        elif self.state == rstp_util.PORT_STATE_LEARNING:
            new_switch_state = SWITCH_PORT_STP_STATE_LEARNING
        elif self.state == rstp_util.PORT_STATE_FORWARDING:
            new_switch_state = SWITCH_PORT_STP_STATE_FORWARDING
        else:
            assert False, "Invalid port state"

        if new_switch_state != self.switch_state:
            self.rstp_handler.switch_set_port_state(self.port_no, new_switch_state)
            self.switch_state = new_switch_state


    # 17.20.1
    def AdminEdge(self):
        return self.AdminEdgePort

    # 17.20.2
    def AutoEdge(self):
        return self.AutoEdgePort

    # 17.20.4
    def EdgeDelay(self):
        if self.operPointToPointMAC:
            return self.MigrateTime()
        else:
            return self.MaxAge()

    # 17.20.5
    def forwardDelay(self):
        if self.sendRSTP:
            return self.HelloTime()
        else:
            return self.FwdDelay()

    # 17.20.6
    def FwdDelay(self):
        return self.designatedTimes.BridgeForwardDelay

    # 17.20.7
    def HelloTime(self):
        return self.designatedTimes.BridgeHelloTime

    # 17.20.8
    def MaxAge(self):
        return self.designatedTimes.BridgeMaxAge

    # 17.20.9
    def MigrateTime(self):
        return rstp_util.MIGRATE_TIME

    # 17.20.10
    def reRooted(self):
        for port in self.rstp_handler.rstp_ports.values():
            if port.portId != self.portId:
                if port.rrWhile != 0:
                    return False
        return True

    # 17.21.1
    def betterorsameInfo(self, newInfoIs):
        if (
            newInfoIs == rstp_util.RECEIVED and
            self.infoIs == rstp_util.RECEIVED and
            self.msgPriority.compare_to(self.portPriority) <= 0
        ):
            return True

        if (
            newInfoIs == rstp_util.MINE and
            self.infoIs == rstp_util.MINE and
            self.designatedPriority.compare_to(self.portPriority) <= 0
        ):
            return True
        return False

    # 17.21.3 and 17.21.4 combined.
    def disableLearningForwarding(self):
        print("Port {}: {} -> {}".format(self.port_no, rstp_util.rstp_state_to_string(self.state), rstp_util.rstp_state_to_string(rstp_util.PORT_STATE_DISCARDING)))
        self.state = rstp_util.PORT_STATE_DISCARDING

    # 17.21.5
    def enableForwarding(self):
        print("Port {}: {} -> {}".format(self.port_no, rstp_util.rstp_state_to_string(self.state), rstp_util.rstp_state_to_string(rstp_util.PORT_STATE_FORWARDING)))
        self.state = rstp_util.PORT_STATE_FORWARDING

    # 17.21.6
    def enableLearning(self):
        print("Port {}: {} -> {}".format(self.port_no, rstp_util.rstp_state_to_string(self.state), rstp_util.rstp_state_to_string(rstp_util.PORT_STATE_LEARNING)))
        self.state = rstp_util.PORT_STATE_LEARNING

    # 17.21.7
    def newTcWhile(self):
        if self.tcWhile == 0:
            if self.sendRSTP:
                self.tcWhile = self.HelloTime() + 1
                self.newInfo = True
            else:
                self.tcWhile = self.rstp_handler.rootTimes.BridgeMaxAge + self.rstp_handler.rootTimes.BridgeForwardDelay

    # 17.21.8
    def rcvInfo(self):
        self.msgPriority = PriorityVector(
            (self.last_bpdu.rootid, self.last_bpdu.rootmac),
            self.last_bpdu.pathcost,
            (self.last_bpdu.bridgeid, self.last_bpdu.bridgemac),
            self.last_bpdu.portid,
            self.portId
        )
        self.msgTimes = BridgeTimes(
            self.last_bpdu.fwddelay,
            self.last_bpdu.hellotime,
            self.last_bpdu.maxage,
            self.last_bpdu.age
        )

        is_designated_port_role = None
        if self.last_bpdu.bpdutype == rstp_util.BPDU_TYPE_CONFIGURATION:
            is_designated_port_role = True
        else:
            is_designated_port_role = rstp_util.is_port_role_designated_port(self.last_bpdu.bpduflags)

        if (
            is_designated_port_role and
            (
                self.is_msg_priority_superior() or
                (self.msgPriority.compare_to(self.portPriority) == 0 and not self.msgTimes.equals(self.portTimes))
            )
        ):
            return rstp_util.SUPERIOR_DESIGNATED_INFO

        if (
            is_designated_port_role and
            self.msgPriority.compare_to(self.portPriority) == 0 and
            self.msgTimes.equals(self.portTimes)
        ):
            return rstp_util.REPEATED_DESIGNATED_INFO

        if (
            is_designated_port_role and
            self.msgPriority.compare_to(self.portPriority) > 0
        ):
            return rstp_util.INFERIOR_DESIGNATED_INFO

        if (
            (
                rstp_util.is_port_role_root_port(self.last_bpdu.bpduflags) or
                rstp_util.is_port_role_alternate_or_backup_port(self.last_bpdu.bpduflags)
            ) and
            self.msgPriority.compare_to(self.portPriority) >= 0
        ):
            return rstp_util.INFERIOR_ROOT_ALTERNATE_INFO

        return rstp_util.OTHER_INFO

    # 17.21.9
    def recordAgreement(self):
        if (
            self.rstp_handler.rstpVersion() and
            self.operPointToPointMAC and
            rstp_util.is_agreement_set(self.last_bpdu.bpduflags)
        ):
            self.agreed = True
            self.proposing = False
        else:
            self.agreed = False

    # 17.21.10
    def recordDispute(self):
        if self.last_bpdu.bpdutype == rstp_util.BPDU_TYPE_RSTP:
            if rstp_util.is_learning_set(self.last_bpdu.bpduflags):
                # 802.1D-2004 says:
                # self.agreed = True
                # self.proposing = True
                # but this doesnt match what the describing text says.
                # 802.1Q-2018 says:
                self.disputed = True
                self.agreed = False

    # 17.21.11
    def recordProposal(self):
        if (
            rstp_util.is_port_role_designated_port(self.last_bpdu.bpduflags) and
            rstp_util.is_proposal_set(self.last_bpdu.bpduflags)
        ):
            self.proposed = True

    # 17.21.12
    def recordPriority(self):
        self.portPriority = self.msgPriority.copy()

    # 17.21.13
    def recordTimes(self):
        self.portTimes = self.msgTimes.copy()
        if self.portTimes.BridgeHelloTime < 1:
            self.portTimes.BridgeHelloTime = 1

    # 17.21.17
    def setTcFlags(self):
        if self.last_bpdu.bpdutype == rstp_util.BPDU_TYPE_RSTP or self.last_bpdu.bpdutype == rstp_util.BPDU_TYPE_CONFIGURATION:
            if rstp_util.is_topology_change_set(self.last_bpdu.bpduflags):
                self.rcvdTc = True
            if rstp_util.is_topology_change_ack_set(self.last_bpdu.bpduflags):
                self.rcvdTcAck = True
        elif self.last_bpdu.bpdutype == rstp_util.BPDU_TYPE_TOPOLOGY_CHANGE_NOTIFICATION:
            self.rcvdTcn = True

    # 17.21.19
    def txConfig(self):
        flags = 0
        if self.tcWhile != 0:
            flags |= rstp_util.BPDU_FLAGS_TOPOLOGY_CHANGE_BIT

        if self.tcAck:
            flags |= rstp_util.BPDU_FLAGS_TOPOLOGY_CHANGE_ACK_BIT

        self.rstp_handler.packet_io.send_config_bpdu(
            flags,
            self.designatedPriority.RootBridgeID[0],
            self.designatedPriority.RootBridgeID[1],
            self.designatedPriority.RootPathCost,
            self.designatedPriority.DesignatedBridgeID[0],
            self.designatedPriority.DesignatedBridgeID[1],
            self.designatedPriority.DesignatedPortID,
            self.designatedTimes.MessageAge,
            self.designatedTimes.BridgeMaxAge,
            self.designatedTimes.BridgeHelloTime,
            self.designatedTimes.BridgeForwardDelay,
            self.port_no
        )

    # 17.21.20
    def txRstp(self):
        flags = 0
        if self.tcWhile != 0:
            flags |= rstp_util.BPDU_FLAGS_TOPOLOGY_CHANGE_BIT

        if self.role == rstp_util.DESIGNATED_PORT:
            flags |= rstp_util.BPDU_FLAGS_PORT_ROLE_DESIGNATED_PORT
        elif self.role == rstp_util.ROOT_PORT:
            flags |= rstp_util.BPDU_FLAGS_PORT_ROLE_ROOT_PORT
        elif self.role == rstp_util.ALTERNATE_PORT or self.role == rstp_util.BACKUP_PORT:
            flags |= rstp_util.BPDU_FLAGS_PORT_ROLE_ALTERNATE_OR_BACKUP_PORT
        else:
            assert False

        if self.agree:
            flags |= rstp_util.BPDU_FLAGS_AGREEMENT_BIT
        if self.proposing:
            flags |= rstp_util.BPDU_FLAGS_PROPOSAL_BIT
        if self.learning:
            flags |= rstp_util.BPDU_FLAGS_LEARNING_BIT
        if self.forwarding:
            flags |= rstp_util.BPDU_FLAGS_FORWARDING_BIT

        self.rstp_handler.packet_io.send_rstp_bpdu(
            flags,
            self.designatedPriority.RootBridgeID[0],
            self.designatedPriority.RootBridgeID[1],
            self.designatedPriority.RootPathCost,
            self.designatedPriority.DesignatedBridgeID[0],
            self.designatedPriority.DesignatedBridgeID[1],
            self.designatedPriority.DesignatedPortID,
            self.designatedTimes.MessageAge,
            self.designatedTimes.BridgeMaxAge,
            self.designatedTimes.BridgeHelloTime,
            self.designatedTimes.BridgeForwardDelay,
            self.port_no
        )

    # 17.21.21
    def txTcn(self):
        self.rstp_handler.packet_io.send_tcn_bpdu(self.port_no)

    # 17.21.22
    def updtBPDUVersion(self):
        if self.last_bpdu.version == 0 or self.last_bpdu.version == 1:
            self.rcvdSTP = True
        elif self.last_bpdu.bpdutype == rstp_util.BPDU_TYPE_RSTP:
            self.rcvdRSTP = True

    # 17.21.23
    def updtRcvdInfoWhile(self):
        if round(self.portTimes.MessageAge + 1) <= self.portTimes.BridgeMaxAge:
            self.rcvdInfoWhile = 3 * self.portTimes.BridgeHelloTime
        else:
            self.rcvdInfoWhile = 0

    # From 17.6
    def is_msg_priority_superior(self):
        if self.msgPriority.compare_to(self.portPriority) < 0:
            return True
        if (
            self.msgPriority.DesignatedBridgeID == self.portPriority.DesignatedBridgeID and
            self.msgPriority.DesignatedPortID == self.portPriority.DesignatedPortID
        ):
            return True
        return False
