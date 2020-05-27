import rstp_util

DEBUG_PRINT = False

class StateMachine:
    def __init__(self, port=None):
        self.state = None
        self.port = port

    def enter_state(self, new_state):
        old_state_name = self.state_name(self.state) if self.state != None else "none"
        new_state_name = self.state_name(new_state)
        if DEBUG_PRINT:
            if self.port:
                print("Port {}: {} ({} -> {})".format(self.port.port_no, self.__class__.__name__, old_state_name, new_state_name))
            else:
                print("{} ({} -> {})".format(self.__class__.__name__, old_state_name, new_state_name))
        self.state = new_state
        self.on_enter_state()
        return True

# 17.28
class PortRoleSelection(StateMachine):
    INIT_BRIDGE = 0
    ROLE_SELECTION = 1

    def __init__(self, rstp_handler):
        self.rstp_handler = rstp_handler
        StateMachine.__init__(self)

    def update(self):
        if self.rstp_handler.BEGIN:
            return self.enter_state(PortRoleSelection.INIT_BRIDGE)

        if self.state == PortRoleSelection.INIT_BRIDGE:
            return self.enter_state(PortRoleSelection.ROLE_SELECTION)
        elif self.state == PortRoleSelection.ROLE_SELECTION:
            for port in self.rstp_handler.rstp_ports.values():
                if port.reselect:
                    return self.enter_state(PortRoleSelection.ROLE_SELECTION)
        else:
            assert False
        return False

    def on_enter_state(self):
        if self.state == PortRoleSelection.INIT_BRIDGE:
            self.rstp_handler.updtRoleDisabledTree()
        elif self.state == PortRoleSelection.ROLE_SELECTION:
            self.rstp_handler.clearReselectTree()
            self.rstp_handler.updtRolesTree()
            self.rstp_handler.setSelectedTree()
        else:
            assert False

    def state_name(self, state):
        if state == PortRoleSelection.INIT_BRIDGE:
            return "init_bridge"
        elif state == PortRoleSelection.ROLE_SELECTION:
            return "role_selection"
        else:
            assert False

# 17.23
class PortReceive(StateMachine):
    DISCARD = 0
    RECEIVE = 1

    def __init__(self, rstp_handler, rstp_port):
        self.rstp_handler = rstp_handler
        self.port = rstp_port
        StateMachine.__init__(self, rstp_port)

    def update(self):
        if self.rstp_handler.BEGIN:
            return self.enter_state(PortReceive.DISCARD)
        if (
            (self.port.rcvdBPDU or self.port.edgeDelayWhile != self.port.MigrateTime()) and
            not self.port.portEnabled
        ):
            return self.enter_state(PortReceive.DISCARD)

        if self.state == PortReceive.DISCARD:
            if self.port.rcvdBPDU and self.port.portEnabled:
                return self.enter_state(PortReceive.RECEIVE)
        elif self.state == PortReceive.RECEIVE:
            if self.port.rcvdBPDU and self.port.portEnabled and not self.port.rcvdMsg:
                return self.enter_state(PortReceive.RECEIVE)
        else:
            assert False
        return False

    def on_enter_state(self):
        if self.state == PortReceive.DISCARD:
            self.port.rcvdBPDU = False
            self.port.rcvdRSTP = False
            self.port.rcvdSTP = False
            self.port.rcvdMsg = False
            self.port.edgeDelayWhile = self.port.MigrateTime()
        elif self.state == PortReceive.RECEIVE:
            self.port.updtBPDUVersion()
            self.port.operEdge = False
            self.port.rcvdBPDU = False
            self.port.rcvdMsg = True
            self.port.edgeDelayWhile = self.port.MigrateTime()
        else:
            assert False

    def state_name(self, state):
        if state == PortReceive.DISCARD:
            return "discard"
        elif state == PortReceive.RECEIVE:
            return "receive"
        else:
            assert False

# 17.24
class PortProtocolMigration(StateMachine):
    CHECKING_RSTP = 0
    SELECTING_STP = 1
    SENSING = 2

    def __init__(self, rstp_handler, rstp_port):
        self.rstp_handler = rstp_handler
        self.port = rstp_port
        StateMachine.__init__(self, rstp_port)

    def update(self):
        if self.rstp_handler.BEGIN:
            return self.enter_state(PortProtocolMigration.CHECKING_RSTP)

        if self.state == PortProtocolMigration.CHECKING_RSTP:
            if self.port.mdelayWhile == 0:
                return self.enter_state(PortProtocolMigration.SENSING)
            elif self.port.mdelayWhile != self.port.MigrateTime() and not self.port.portEnabled:
                return self.enter_state(PortProtocolMigration.CHECKING_RSTP)
        elif self.state == PortProtocolMigration.SELECTING_STP:
            if self.port.mdelayWhile == 0 or not self.port.portEnabled or self.port.mcheck:
                return self.enter_state(PortProtocolMigration.SENSING)
        elif self.state == PortProtocolMigration.SENSING:
            if self.port.sendRSTP and self.port.rcvdSTP:
                return self.enter_state(PortProtocolMigration.SELECTING_STP)
            elif (
                not self.port.portEnabled or
                self.port.mcheck or
                (self.rstp_handler.rstpVersion() and not self.port.sendRSTP and self.port.rcvdRSTP)
            ):
                return self.enter_state(PortProtocolMigration.CHECKING_RSTP)
        else:
            assert False
        return False

    def on_enter_state(self):
        if self.state == PortProtocolMigration.CHECKING_RSTP:
            self.port.mcheck = False
            self.port.sendRSTP = self.rstp_handler.rstpVersion()
            self.port.mdelayWhile = self.port.MigrateTime()
        elif self.state == PortProtocolMigration.SELECTING_STP:
            self.port.sendRSTP = False
            self.port.mdelayWhile = self.port.MigrateTime()
        elif self.state == PortProtocolMigration.SENSING:
            self.port.rcvdRSTP = False
            self.port.rcvdSTP = False
        else:
            assert False

    def state_name(self, state):
        if state == PortProtocolMigration.CHECKING_RSTP:
            return "checking_rstp"
        elif state == PortProtocolMigration.SELECTING_STP:
            return "selecting_stp"
        elif state == PortProtocolMigration.SENSING:
            return "sensing"
        else:
            assert False


# 17.25
class BridgeDetection(StateMachine):
    EDGE = 0
    NOT_EDGE = 1

    def __init__(self, rstp_handler, rstp_port):
        self.rstp_handler = rstp_handler
        self.port = rstp_port
        StateMachine.__init__(self, rstp_port)

    def update(self):
        if self.rstp_handler.BEGIN and self.port.AdminEdge():
            return self.enter_state(BridgeDetection.EDGE)
        elif self.rstp_handler.BEGIN and not self.port.AdminEdge():
            return self.enter_state(BridgeDetection.NOT_EDGE)

        if self.state == BridgeDetection.EDGE:
            if (
                (not self.port.portEnabled and not self.port.AdminEdge()) or
                not self.port.operEdge
            ):
                return self.enter_state(BridgeDetection.NOT_EDGE)
        elif self.state == BridgeDetection.NOT_EDGE:
            if (
                (not self.port.portEnabled and self.port.AdminEdge()) or
                (
                    self.port.edgeDelayWhile == 0 and
                    self.port.AutoEdge() and
                    self.port.sendRSTP and
                    self.port.proposing
                )
            ):
                return self.enter_state(BridgeDetection.EDGE)
        else:
            assert False
        return False

    def on_enter_state(self):
        if self.state == BridgeDetection.EDGE:
            self.port.operEdge = True
        elif self.state == BridgeDetection.NOT_EDGE:
            self.port.operEdge = False
        else:
            assert False

    def state_name(self, state):
        if state == BridgeDetection.EDGE:
            return "edge"
        elif state == BridgeDetection.NOT_EDGE:
            return "not_edge"
        else:
            assert False

# 17.26
class PortTransmit(StateMachine):
    TRANSMIT_INIT = 0
    TRANSMIT_CONFIG = 1
    TRANSMIT_PERIODIC = 2
    TRANSMIT_TCN = 3
    TRANSMIT_RSTP = 4
    IDLE = 5

    def __init__(self, rstp_handler, rstp_port):
        self.rstp_handler = rstp_handler
        self.port = rstp_port
        StateMachine.__init__(self, rstp_port)

    def update(self):
        if self.rstp_handler.BEGIN:
            return self.enter_state(PortTransmit.TRANSMIT_INIT)

        if self.state == PortTransmit.TRANSMIT_INIT:
            return self.enter_state(PortTransmit.IDLE)
        elif self.state == PortTransmit.TRANSMIT_CONFIG:
            return self.enter_state(PortTransmit.IDLE)
        elif self.state == PortTransmit.TRANSMIT_PERIODIC:
            return self.enter_state(PortTransmit.IDLE)
        elif self.state == PortTransmit.TRANSMIT_TCN:
            return self.enter_state(PortTransmit.IDLE)
        elif self.state == PortTransmit.TRANSMIT_RSTP:
            return self.enter_state(PortTransmit.IDLE)
        elif self.state == PortTransmit.IDLE:
            if (self.port.selected and not self.port.updtInfo):
                if (self.port.helloWhen == 0):
                    return self.enter_state(PortTransmit.TRANSMIT_PERIODIC)

                if (
                    not self.port.sendRSTP and
                    self.port.newInfo and
                    self.port.role == rstp_util.DESIGNATED_PORT and
                    (self.port.txCount < self.rstp_handler.TxHoldCount) and
                    self.port.helloWhen != 0
                ):
                    return self.enter_state(PortTransmit.TRANSMIT_CONFIG)

                if (
                    not self.port.sendRSTP and
                    self.port.newInfo and
                    self.port.role == rstp_util.ROOT_PORT and
                    (self.port.txCount < self.rstp_handler.TxHoldCount) and
                    self.port.helloWhen != 0
                ):
                    return self.enter_state(PortTransmit.TRANSMIT_TCN)

                if (
                    self.port.sendRSTP and
                    self.port.newInfo and
                    (self.port.txCount < self.rstp_handler.TxHoldCount) and
                    self.port.helloWhen != 0
                ):
                    return self.enter_state(PortTransmit.TRANSMIT_RSTP)
        else:
            assert False
        return False

    def on_enter_state(self):
        if self.state == PortTransmit.TRANSMIT_INIT:
            self.port.newInfo = True
            self.port.txCount = 0
        elif self.state == PortTransmit.TRANSMIT_CONFIG:
            self.port.newInfo = False
            self.port.txConfig()
            self.port.txCount += 1
            self.port.tcAck = False
        elif self.state == PortTransmit.TRANSMIT_PERIODIC:
            self.port.newInfo = (
                self.port.newInfo or
                (
                    self.port.role == rstp_util.DESIGNATED_PORT or
                    (self.port.role == rstp_util.ROOT_PORT and self.port.tcWhile != 0)
                )
            )
        elif self.state == PortTransmit.TRANSMIT_TCN:
            self.port.newInfo = False
            self.port.txTcn()
            self.port.txCount += 1
        elif self.state == PortTransmit.TRANSMIT_RSTP:
            self.port.newInfo = False
            self.port.txRstp()
            self.port.txCount += 1
            self.port.tcAck = False
        elif self.state == PortTransmit.IDLE:
            self.port.helloWhen = self.port.HelloTime()
        else:
            assert False

    def state_name(self, state):
        if state == PortTransmit.TRANSMIT_INIT:
            return "transmit_init"
        elif state == PortTransmit.TRANSMIT_CONFIG:
            return "transmit_config"
        elif state == PortTransmit.TRANSMIT_PERIODIC:
            return "transmit_periodic"
        elif state == PortTransmit.TRANSMIT_TCN:
            return "transmit_tcn"
        elif state == PortTransmit.TRANSMIT_RSTP:
            return "transmit_rstp"
        elif state == PortTransmit.IDLE:
            return "idle"
        else:
            assert False

# 17.27
class PortInformation(StateMachine):
    DISABLED = 0
    AGED = 1
    UPDATE = 2
    CURRENT = 3
    SUPERIOR_DESIGNATED = 4
    REPEATED_DESIGNATED = 5
    INFERIOR_DESIGNATED = 6
    NOT_DESIGNATED = 7
    OTHER = 8
    RECEIVE = 9

    def __init__(self, rstp_handler, rstp_port):
        self.rstp_handler = rstp_handler
        self.port = rstp_port
        StateMachine.__init__(self, rstp_port)

    def update(self):
        if (
            self.rstp_handler.BEGIN or
            (not self.port.portEnabled and self.port.infoIs != rstp_util.DISABLED)
        ):
            return self.enter_state(PortInformation.DISABLED)

        if self.state == PortInformation.DISABLED:
            if self.port.rcvdMsg:
                return self.enter_state(PortInformation.DISABLED)
            if self.port.portEnabled:
                return self.enter_state(PortInformation.AGED)
        elif self.state == PortInformation.AGED:
            if self.port.selected and self.port.updtInfo:
                return self.enter_state(PortInformation.UPDATE)
        elif self.state == PortInformation.UPDATE:
            return self.enter_state(PortInformation.CURRENT)
        elif self.state == PortInformation.CURRENT:
            if self.port.selected and self.port.updtInfo:
                return self.enter_state(PortInformation.UPDATE)
            if (
                self.port.infoIs == rstp_util.RECEIVED and
                self.port.rcvdInfoWhile == 0 and
                not self.port.updtInfo and
                not self.port.rcvdMsg
            ):
                return self.enter_state(PortInformation.AGED)
            if self.port.rcvdMsg and not self.port.updtInfo:
                return self.enter_state(PortInformation.RECEIVE)
        elif self.state == PortInformation.SUPERIOR_DESIGNATED:
            return self.enter_state(PortInformation.CURRENT)
        elif self.state == PortInformation.REPEATED_DESIGNATED:
            return self.enter_state(PortInformation.CURRENT)
        elif self.state == PortInformation.INFERIOR_DESIGNATED:
            return self.enter_state(PortInformation.CURRENT)
        elif self.state == PortInformation.NOT_DESIGNATED:
            return self.enter_state(PortInformation.CURRENT)
        elif self.state == PortInformation.OTHER:
            return self.enter_state(PortInformation.CURRENT)
        elif self.state == PortInformation.RECEIVE:
            if self.port.rcvdInfo == rstp_util.SUPERIOR_DESIGNATED_INFO:
                return self.enter_state(PortInformation.SUPERIOR_DESIGNATED)
            if self.port.rcvdInfo == rstp_util.REPEATED_DESIGNATED_INFO:
                return self.enter_state(PortInformation.REPEATED_DESIGNATED)
            if self.port.rcvdInfo == rstp_util.INFERIOR_DESIGNATED_INFO:
                return self.enter_state(PortInformation.INFERIOR_DESIGNATED)
            if self.port.rcvdInfo == rstp_util.INFERIOR_ROOT_ALTERNATE_INFO:
                return self.enter_state(PortInformation.NOT_DESIGNATED)
            if self.port.rcvdInfo == rstp_util.OTHER_INFO:
                return self.enter_state(PortInformation.OTHER)
        else:
            assert False
        return False

    def on_enter_state(self):
        if self.state == PortInformation.DISABLED:
            self.port.rcvdMsg = False
            self.port.proposing = False
            self.port.proposed = False
            self.port.agree = False
            self.port.agreed = False
            self.port.rcvdInfoWhile = 0
            self.port.infoIs = rstp_util.DISABLED
            self.port.reselect = True
            self.port.selected = False
        elif self.state == PortInformation.AGED:
            self.port.infoIs = rstp_util.AGED
            self.port.reselect = True
            self.port.selected = False
        elif self.state == PortInformation.UPDATE:
            self.port.proposing = False
            self.port.proposed = False
            self.port.agreed = self.port.agreed and self.port.betterorsameInfo(rstp_util.MINE) # 802.1D-2004 doesn't specify what argument to pass, but 802.1Q-2018 does.
            self.port.synced = self.port.synced and self.port.agreed
            self.port.portPriority = self.port.designatedPriority.copy()
            self.port.portTimes = self.port.designatedTimes.copy()
            self.port.updtInfo = False
            self.port.infoIs = rstp_util.MINE
            self.port.newInfo = True
        elif self.state == PortInformation.CURRENT:
            pass
        elif self.state == PortInformation.SUPERIOR_DESIGNATED:
            self.port.agreed = False
            self.port.proposing = False
            self.port.recordProposal()
            self.port.setTcFlags()
            self.port.agree = self.port.agree and self.port.betterorsameInfo(rstp_util.RECEIVED) # 802.1D-2004 doesn't specify what argument to pass, but 802.1Q-2018 does.
            self.port.recordPriority()
            self.port.recordTimes()
            self.port.updtRcvdInfoWhile()
            self.port.infoIs = rstp_util.RECEIVED
            self.port.reselect = True
            self.port.selected = False
            self.port.rcvdMsg = False
        elif self.state == PortInformation.REPEATED_DESIGNATED:
            self.port.recordProposal()
            self.port.setTcFlags()
            self.port.updtRcvdInfoWhile()
            self.port.rcvdMsg = False
        elif self.state == PortInformation.INFERIOR_DESIGNATED:
            self.port.recordDispute()
            self.port.rcvdMsg = False
        elif self.state == PortInformation.NOT_DESIGNATED:
            self.port.recordAgreement()
            self.port.setTcFlags()
            self.port.rcvdMsg = False
        elif self.state == PortInformation.OTHER:
            self.port.rcvdMsg = False
        elif self.state == PortInformation.RECEIVE:
            self.port.rcvdInfo = self.port.rcvInfo()
        else:
            assert False

    def state_name(self, state):
        if state == PortInformation.DISABLED:
            return "disabled"
        elif state == PortInformation.AGED:
            return "aged"
        elif state == PortInformation.UPDATE:
            return "update"
        elif state == PortInformation.CURRENT:
            return "current"
        elif state == PortInformation.SUPERIOR_DESIGNATED:
            return "superior_designated"
        elif state == PortInformation.REPEATED_DESIGNATED:
            return "repeated_designated"
        elif state == PortInformation.INFERIOR_DESIGNATED:
            return "inferior_designated"
        elif state == PortInformation.NOT_DESIGNATED:
            return "not_designated"
        elif state == PortInformation.OTHER:
            return "other"
        elif state == PortInformation.RECEIVE:
            return "receive"
        else:
            assert False
# 17.29
class PortRoleTransitions(StateMachine):
    # Disabled port states.
    INIT_PORT = 0
    DISABLE_PORT = 1
    DISABLED_PORT = 2
    # Root port states.
    ROOT_PROPOSED = 3
    ROOT_AGREED = 4
    ROOT_FORWARD = 5
    ROOT_LEARN = 6
    REROOT = 7
    REROOTED = 8
    ROOT_PORT = 9
    # Designated port states.
    DESIGNATED_PROPOSE = 10
    DESIGNATED_SYNCED = 11
    DESIGNATED_RETIRED = 12
    DESIGNATED_PORT = 13
    DESIGNATED_FORWARD = 14
    DESIGNATED_LEARN = 15
    DESIGNATED_DISCARD = 16
    # Alternated and Backup port states.
    ALTERNATE_PROPOSED = 17
    ALTERNATE_AGREED = 18
    ALTERNATE_PORT = 19
    BLOCK_PORT = 20
    BACKUP_PORT = 21

    def __init__(self, rstp_handler, rstp_port):
        self.rstp_handler = rstp_handler
        self.port = rstp_port
        StateMachine.__init__(self, rstp_port)

    def update(self):
        if self.rstp_handler.BEGIN:
            return self.enter_state(PortRoleTransitions.INIT_PORT)

        if self.port.selected and not self.port.updtInfo:
            if self.port.role != self.port.selectedRole:
                if self.port.selectedRole == rstp_util.DISABLED_PORT:
                    return self.enter_state(PortRoleTransitions.DISABLE_PORT)
                elif self.port.selectedRole == rstp_util.ROOT_PORT:
                    return self.enter_state(PortRoleTransitions.ROOT_PORT)
                elif self.port.selectedRole == rstp_util.DESIGNATED_PORT:
                    return self.enter_state(PortRoleTransitions.DESIGNATED_PORT)
                elif (
                    self.port.selectedRole == rstp_util.ALTERNATE_PORT or
                    self.port.selectedRole == rstp_util.BACKUP_PORT
                ):
                    return self.enter_state(PortRoleTransitions.BLOCK_PORT)
                else:
                    assert False

            # Conditional, not global transitions.
            if self.state == PortRoleTransitions.DISABLE_PORT:
                if not self.port.learning and not self.port.forwarding:
                    return self.enter_state(PortRoleTransitions.DISABLED_PORT)
            elif self.state == PortRoleTransitions.DISABLED_PORT:
                if (
                    self.port.fdWhile != self.port.MaxAge() or
                    self.port.sync or
                    self.port.reRoot or
                    not self.port.synced
                ):
                    return self.enter_state(PortRoleTransitions.DISABLED_PORT)
            elif self.state == PortRoleTransitions.ROOT_PORT:
                if self.port.proposed and not self.port.agree:
                    return self.enter_state(PortRoleTransitions.ROOT_PROPOSED)
                if (
                    (self.rstp_handler.allSynced() and not self.port.agree) or
                    (self.port.proposed and self.port.agree)
                ):
                    return self.enter_state(PortRoleTransitions.ROOT_AGREED)
                if not self.port.forward and not self.port.reRoot:
                    return self.enter_state(PortRoleTransitions.REROOT)

                # The next two conditions don't have explicit precedence in 802.1D-2004,
                # but do in 802.1Q-2018, so going by that.
                if (
                    (
                        self.port.fdWhile == 0 or
                        (self.port.reRooted() and self.port.rbWhile == 0 and self.rstp_handler.rstpVersion())
                    ) and
                    self.port.learn and
                    not self.port.forward
                ):
                    return self.enter_state(PortRoleTransitions.ROOT_FORWARD)
                if (
                    (
                        self.port.fdWhile == 0 or
                        (self.port.reRooted() and self.port.rbWhile == 0 and self.rstp_handler.rstpVersion())
                    ) and
                    not self.port.learn
                ):
                    return self.enter_state(PortRoleTransitions.ROOT_LEARN)
                if self.port.reRoot and self.port.forward:
                    return self.enter_state(PortRoleTransitions.REROOTED)
                if self.port.rrWhile != self.port.FwdDelay():
                    return self.enter_state(PortRoleTransitions.ROOT_PORT)
            elif self.state == PortRoleTransitions.DESIGNATED_PORT:
                if (
                    not self.port.forward and
                    not self.port.agreed and
                    not self.port.proposing and
                    not self.port.operEdge
                ):
                    return self.enter_state(PortRoleTransitions.DESIGNATED_PROPOSE)
                if (
                    (
                        not self.port.learning and
                        not self.port.forwarding and
                        not self.port.synced
                    ) or
                    (self.port.agreed and not self.port.synced) or
                    (self.port.operEdge and not self.port.synced) or
                    (self.port.sync and self.port.synced)
                ):
                    return self.enter_state(PortRoleTransitions.DESIGNATED_SYNCED)
                if self.port.rrWhile == 0 and self.port.reRoot:
                    return self.enter_state(PortRoleTransitions.DESIGNATED_RETIRED)
                if (
                    (
                        self.port.fdWhile == 0 or
                        self.port.agreed or
                        self.port.operEdge
                    ) and
                    (self.port.rrWhile == 0 or not self.port.reRoot) and
                    not self.port.sync and
                    (self.port.learn and not self.port.forward)
                ):
                    return self.enter_state(PortRoleTransitions.DESIGNATED_FORWARD)
                if (
                    (
                        self.port.fdWhile == 0 or
                        self.port.agreed or
                        self.port.operEdge
                    ) and
                    (self.port.rrWhile == 0 or not self.port.reRoot) and
                    not self.port.sync and
                    not self.port.learn
                ):
                    return self.enter_state(PortRoleTransitions.DESIGNATED_LEARN)

                if (
                    (
                        (self.port.sync and not self.port.synced) or
                        (self.port.reRoot and self.port.rrWhile != 0) or
                        self.port.disputed
                    ) and
                    not self.port.operEdge and
                    (self.port.learn or self.port.forward)
                ):
                    return self.enter_state(PortRoleTransitions.DESIGNATED_DISCARD)
            elif self.state == PortRoleTransitions.BLOCK_PORT:
                if not self.port.learning and not self.port.forwarding:
                    return self.enter_state(PortRoleTransitions.ALTERNATE_PORT)
            elif self.state == PortRoleTransitions.ALTERNATE_PORT:
                if self.port.proposed and not self.port.agree:
                    return self.enter_state(PortRoleTransitions.ALTERNATE_PROPOSED)
                if (
                    (self.rstp_handler.allSynced() and not self.port.agree) or
                    (self.port.proposed and self.port.agree)
                ):
                    return self.enter_state(PortRoleTransitions.ALTERNATE_AGREED)
                if (
                    (self.port.rbWhile != 2 * self.port.HelloTime()) and
                    (self.port.role == rstp_util.BACKUP_PORT)
                ):
                    return self.enter_state(PortRoleTransitions.BACKUP_PORT)
                if (
                    (self.port.fdWhile != self.port.forwardDelay()) or
                    self.port.sync or
                    self.port.reRoot or
                    not self.port.synced
                ):
                    return self.enter_state(PortRoleTransitions.ALTERNATE_PORT)

        # Unconditional transitions.
        if self.state == PortRoleTransitions.INIT_PORT:
            return self.enter_state(PortRoleTransitions.DISABLE_PORT)
        elif self.state == PortRoleTransitions.ROOT_PROPOSED:
            return self.enter_state(PortRoleTransitions.ROOT_PORT)
        elif self.state == PortRoleTransitions.ROOT_AGREED:
            return self.enter_state(PortRoleTransitions.ROOT_PORT)
        elif self.state == PortRoleTransitions.ROOT_FORWARD:
            return self.enter_state(PortRoleTransitions.ROOT_PORT)
        elif self.state == PortRoleTransitions.ROOT_LEARN:
            return self.enter_state(PortRoleTransitions.ROOT_PORT)
        elif self.state == PortRoleTransitions.REROOT:
            return self.enter_state(PortRoleTransitions.ROOT_PORT)
        elif self.state == PortRoleTransitions.REROOTED:
            return self.enter_state(PortRoleTransitions.ROOT_PORT)
        elif self.state == PortRoleTransitions.DESIGNATED_PROPOSE:
            return self.enter_state(PortRoleTransitions.DESIGNATED_PORT)
        elif self.state == PortRoleTransitions.DESIGNATED_SYNCED:
            return self.enter_state(PortRoleTransitions.DESIGNATED_PORT)
        elif self.state == PortRoleTransitions.DESIGNATED_RETIRED:
            return self.enter_state(PortRoleTransitions.DESIGNATED_PORT)
        elif self.state == PortRoleTransitions.DESIGNATED_FORWARD:
            return self.enter_state(PortRoleTransitions.DESIGNATED_PORT)
        elif self.state == PortRoleTransitions.DESIGNATED_LEARN:
            return self.enter_state(PortRoleTransitions.DESIGNATED_PORT)
        elif self.state == PortRoleTransitions.DESIGNATED_DISCARD:
            return self.enter_state(PortRoleTransitions.DESIGNATED_PORT)
        elif self.state == PortRoleTransitions.ALTERNATE_PROPOSED:
            return self.enter_state(PortRoleTransitions.ALTERNATE_PORT)
        elif self.state == PortRoleTransitions.ALTERNATE_AGREED:
            return self.enter_state(PortRoleTransitions.ALTERNATE_PORT)
        elif self.state == PortRoleTransitions.BACKUP_PORT:
            return self.enter_state(PortRoleTransitions.ALTERNATE_PORT)
        return False

    def on_enter_state(self):
        if self.state == PortRoleTransitions.INIT_PORT:
            self.port.role = rstp_util.DISABLED_PORT
            self.port.learn = False
            self.port.forward = False
            self.port.synced = False
            self.port.sync = True
            self.port.reRoot = True
            self.port.rrWhile = self.port.FwdDelay()
            self.port.fdWhile = self.port.MaxAge()
            self.port.rbWhile = 0
        elif self.state == PortRoleTransitions.ROOT_PROPOSED:
            self.rstp_handler.setSyncTree()
            self.port.proposed = False
        elif self.state == PortRoleTransitions.ROOT_AGREED:
            self.port.proposed = False
            self.port.sync = False
            self.port.agree = True
            self.port.newInfo = True
        elif self.state == PortRoleTransitions.ROOT_FORWARD:
            self.port.fdWhile = 0
            self.port.forward = True
        elif self.state == PortRoleTransitions.ROOT_LEARN:
            self.port.fdWhile = self.port.forwardDelay()
            self.port.learn = True
        elif self.state == PortRoleTransitions.REROOT:
            self.rstp_handler.setReRootTree()
        elif self.state == PortRoleTransitions.REROOTED:
            self.port.reRoot = False
        elif self.state == PortRoleTransitions.DESIGNATED_PROPOSE:
            self.port.proposing = True
            self.port.edgeDelayWhile = self.port.EdgeDelay()
            self.port.newInfo = True
        elif self.state == PortRoleTransitions.DESIGNATED_SYNCED:
            self.port.rrWhile = 0
            self.port.synced = True
            self.port.sync = False
        elif self.state == PortRoleTransitions.DESIGNATED_RETIRED:
            self.port.reRoot = False
        elif self.state == PortRoleTransitions.DESIGNATED_FORWARD:
            self.port.forward = True
            self.port.fdWhile = 0
            self.port.agreed = self.port.sendRSTP
        elif self.state == PortRoleTransitions.DESIGNATED_LEARN:
            self.port.learn = True
            self.port.fdWhile = self.port.forwardDelay()
        elif self.state == PortRoleTransitions.DESIGNATED_DISCARD:
            self.port.learn = False
            self.port.forward = False
            self.port.disputed = False
            self.port.fdWhile = self.port.forwardDelay()
        elif self.state == PortRoleTransitions.ALTERNATE_PROPOSED:
            self.rstp_handler.setSyncTree()
            self.port.proposed = False
        elif self.state == PortRoleTransitions.ALTERNATE_AGREED:
            self.port.proposed = False
            self.port.agree = True
            self.port.newInfo = True
        elif self.state == PortRoleTransitions.BACKUP_PORT:
            self.port.rbWhile = 2 * self.port.HelloTime()
        elif self.state == PortRoleTransitions.DISABLE_PORT:
            self.port.role = self.port.selectedRole
            self.port.learn = False
            self.port.forward = False
        elif self.state == PortRoleTransitions.DISABLED_PORT:
            self.port.fdWhile = self.port.MaxAge()
            self.port.synced = True
            self.port.rrWhile = 0
            self.port.sync = False
            self.port.reRoot = False
        elif self.state == PortRoleTransitions.ROOT_PORT:
            self.port.role = rstp_util.ROOT_PORT
            self.port.rrWhile = self.port.FwdDelay()
        elif self.state == PortRoleTransitions.DESIGNATED_PORT:
            self.port.role = rstp_util.DESIGNATED_PORT
        elif self.state == PortRoleTransitions.BLOCK_PORT:
            self.port.role = self.port.selectedRole
            self.port.learn = False
            self.port.forward = False
        elif self.state == PortRoleTransitions.ALTERNATE_PORT:
            # 802.1D-2004 says to use FwdDelay here, but that leads to an infinite loop
            # and 802.1Q-2018 say forwardDelay.
            self.port.fdWhile = self.port.forwardDelay()
            self.port.synced = True
            self.port.rrWhile = 0
            self.port.sync = False
            self.port.reRoot = False
        else:
            assert False

    def state_name(self, state):
        if state == PortRoleTransitions.INIT_PORT:
            return "init_port"
        elif state == PortRoleTransitions.ROOT_PROPOSED:
            return "root_proposed"
        elif state == PortRoleTransitions.ROOT_AGREED:
            return "root_agreed"
        elif state == PortRoleTransitions.ROOT_FORWARD:
            return "root_forward"
        elif state == PortRoleTransitions.ROOT_LEARN:
            return "root_learn"
        elif state == PortRoleTransitions.REROOT:
            return "reroot"
        elif state == PortRoleTransitions.REROOTED:
            return "rerooted"
        elif state == PortRoleTransitions.DESIGNATED_PROPOSE:
            return "designated_propose"
        elif state == PortRoleTransitions.DESIGNATED_SYNCED:
            return "designated_synced"
        elif state == PortRoleTransitions.DESIGNATED_RETIRED:
            return "designated_retired"
        elif state == PortRoleTransitions.DESIGNATED_FORWARD:
            return "designated_forward"
        elif state == PortRoleTransitions.DESIGNATED_LEARN:
            return "designated_learn"
        elif state == PortRoleTransitions.DESIGNATED_DISCARD:
            return "designated_discard"
        elif state == PortRoleTransitions.ALTERNATE_PROPOSED:
            return "alternate_proposed"
        elif state == PortRoleTransitions.ALTERNATE_AGREED:
            return "alternated_agreed"
        elif state == PortRoleTransitions.BACKUP_PORT:
            return "backup_port"
        elif state == PortRoleTransitions.DISABLE_PORT:
            return "disable_port"
        elif state == PortRoleTransitions.DISABLED_PORT:
            return "disabled_port"
        elif state == PortRoleTransitions.ROOT_PORT:
            return "root_port"
        elif state == PortRoleTransitions.DESIGNATED_PORT:
            return "designated_port"
        elif state == PortRoleTransitions.BLOCK_PORT:
            return "block_port"
        elif state == PortRoleTransitions.ALTERNATE_PORT:
            return "alternate_port"
        else:
            assert False
# 17.30
class PortStateTransition(StateMachine):
    DISCARDING = 0
    LEARNING = 1
    FORWARDING = 2

    def __init__(self, rstp_handler, rstp_port):
        self.rstp_handler = rstp_handler
        self.port = rstp_port
        StateMachine.__init__(self, rstp_port)

    def update(self):
        if self.rstp_handler.BEGIN:
            return self.enter_state(PortStateTransition.DISCARDING)

        if self.state == PortStateTransition.DISCARDING:
            if self.port.learn:
                return self.enter_state(PortStateTransition.LEARNING)
        elif self.state == PortStateTransition.LEARNING:
            if not self.port.learn:
                return self.enter_state(PortStateTransition.DISCARDING)
            if self.port.forward:
                return self.enter_state(PortStateTransition.FORWARDING)
        elif self.state == PortStateTransition.FORWARDING:
            if not self.port.forward:
                return self.enter_state(PortStateTransition.DISCARDING)
        else:
            assert False
        return False

    def on_enter_state(self):
        if self.state == PortStateTransition.DISCARDING:
            self.port.disableLearningForwarding()
            self.port.learning = False
            self.port.forwarding = False
        elif self.state == PortStateTransition.LEARNING:
            self.port.enableLearning()
            self.port.learning = True
        elif self.state == PortStateTransition.FORWARDING:
            self.port.enableForwarding()
            self.port.forwarding = True
        else:
            assert False

    def state_name(self, state):
        if state == PortStateTransition.DISCARDING:
            return "discarding"
        elif state == PortStateTransition.LEARNING:
            return "learning"
        elif state == PortStateTransition.FORWARDING:
            return "forwarding"
        else:
            assert False

# 17.23
class TopologyChange(StateMachine):
    INACTIVE = 0
    LEARNING = 1
    DETECTED = 2
    ACTIVE = 3
    NOTIFIED_TCN = 4
    NOTIFIED_TC = 5
    PROPAGATING = 6
    ACKNOWLEDGED = 7

    def __init__(self, rstp_handler, rstp_port):
        self.rstp_handler = rstp_handler
        self.port = rstp_port
        StateMachine.__init__(self, rstp_port)

    def update(self):
        if self.rstp_handler.BEGIN:
            return self.enter_state(TopologyChange.INACTIVE)

        if self.state == TopologyChange.INACTIVE:
            if self.port.learn and not self.port.fdbFlush:
                return self.enter_state(TopologyChange.LEARNING)
        elif self.state == TopologyChange.LEARNING:
            if (
                (
                    self.port.role == rstp_util.ROOT_PORT or
                    self.port.role == rstp_util.DESIGNATED_PORT
                ) and
                self.port.forward and not self.port.operEdge
            ):
                return self.enter_state(TopologyChange.DETECTED)
            if (
                (self.port.role != rstp_util.ROOT_PORT) and
                (self.port.role != rstp_util.DESIGNATED_PORT) and
                not (self.port.learn or self.port.learning) and
                not (self.port.rcvdTc or self.port.rcvdTcn or self.port.rcvdTcAck or self.port.tcProp)
            ):
                return self.enter_state(TopologyChange.INACTIVE)
            if (
                self.port.rcvdTc or
                self.port.rcvdTcn or
                self.port.rcvdTcAck or
                self.port.tcProp
            ):
                return self.enter_state(TopologyChange.LEARNING)
        elif self.state == TopologyChange.DETECTED:
            return self.enter_state(TopologyChange.ACTIVE)
        elif self.state == TopologyChange.ACTIVE:
            if (
                (
                    self.port.role != rstp_util.ROOT_PORT and
                    self.port.role != rstp_util.DESIGNATED_PORT
                ) or
                self.port.operEdge
            ):
                return self.enter_state(TopologyChange.LEARNING)
            if self.port.rcvdTcn:
                return self.enter_state(TopologyChange.NOTIFIED_TCN)
            if self.port.rcvdTc:
                return self.enter_state(TopologyChange.NOTIFIED_TC)
            if self.port.tcProp and not self.port.operEdge:
                return self.enter_state(TopologyChange.PROPAGATING)
            if self.port.rcvdTcAck:
                return self.enter_state(TopologyChange.ACKNOWLEDGED)
        elif self.state == TopologyChange.NOTIFIED_TCN:
            return self.enter_state(TopologyChange.NOTIFIED_TC)
        elif self.state == TopologyChange.NOTIFIED_TC:
            return self.enter_state(TopologyChange.ACTIVE)
        elif self.state == TopologyChange.PROPAGATING:
            return self.enter_state(TopologyChange.ACTIVE)
        elif self.state == TopologyChange.ACKNOWLEDGED:
            return self.enter_state(TopologyChange.ACTIVE)
        else:
            assert False
        return False

    def on_enter_state(self):
        if self.state == TopologyChange.INACTIVE:
            self.port.fdbFlush = True
            self.port.tcWhile = 0
            self.port.tcAck = False
        elif self.state == TopologyChange.LEARNING:
            self.port.rcvdTc = False
            self.port.rcvdTcn = False
            self.port.rcvdTcAck = False
            self.port.tcProp = False
        elif self.state == TopologyChange.DETECTED:
            self.port.newTcWhile()
            self.rstp_handler.setTcPropTree(self.port.port_no)
            self.port.newInfo = True
        elif self.state == TopologyChange.ACTIVE:
            pass
        elif self.state == TopologyChange.NOTIFIED_TCN:
            self.port.newTcWhile()
        elif self.state == TopologyChange.NOTIFIED_TC:
            self.port.rcvdTcn = False
            self.port.rcvdTc = False
            if self.port.role == rstp_util.DESIGNATED_PORT:
                self.port.tcAck = True
            self.rstp_handler.setTcPropTree(self.port.port_no) # Standard says setTcPropBridge(), but that function doesn't exist.
        elif self.state == TopologyChange.PROPAGATING:
            self.port.newTcWhile()
            self.port.fdbFlush = True
            self.port.tcProp = False
        elif self.state == TopologyChange.ACKNOWLEDGED:
            self.port.tcWhile = 0
            self.port.rcvdTcAck = False
        else:
            assert False

    def state_name(self, state):
        if state == TopologyChange.INACTIVE:
            return "inactive"
        elif state == TopologyChange.LEARNING:
            return "learning"
        elif state == TopologyChange.DETECTED:
            return "detected"
        elif state == TopologyChange.ACTIVE:
            return "active"
        elif state == TopologyChange.NOTIFIED_TCN:
            return "notified_tcn"
        elif state == TopologyChange.NOTIFIED_TC:
            return "notified_tc"
        elif state == TopologyChange.PROPAGATING:
            return "propagating"
        elif state == TopologyChange.ACKNOWLEDGED:
            return "acknowledged"
        else:
            assert False
