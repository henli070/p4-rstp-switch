import rstp_util

class BridgeTimes:
    """Data structure for the bridge times of the RSTP standard."""
    def __init__(
        self,
        BridgeForwardDelay,
        BridgeHelloTime,
        BridgeMaxAge,
        MessageAge
    ):
        self.BridgeForwardDelay = BridgeForwardDelay
        self.BridgeHelloTime = BridgeHelloTime
        self.BridgeMaxAge = BridgeMaxAge
        self.MessageAge = MessageAge

    def copy(self):
        return BridgeTimes(
            self.BridgeForwardDelay,
            self.BridgeHelloTime,
            self.BridgeMaxAge,
            self.MessageAge
        )

    def equals(self, other):
        return (
            self.BridgeForwardDelay == other.BridgeForwardDelay and
            self.BridgeHelloTime == other.BridgeHelloTime and
            self.BridgeMaxAge == other.BridgeMaxAge and
            self.MessageAge == other.MessageAge
        )

class PriorityVector:
    """Data structure for the priority vectors of the RSTP standard."""
    def __init__(
        self,
        RootBridgeID,
        RootPathCost,
        DesignatedBridgeID,
        DesignatedPortID,
        BridgePortID
    ):
        self.RootBridgeID = RootBridgeID
        self.RootPathCost = RootPathCost
        self.DesignatedBridgeID = DesignatedBridgeID
        self.DesignatedPortID = DesignatedPortID
        self.BridgePortID = BridgePortID

    def copy(self):
        return PriorityVector(
            self.RootBridgeID,
            self.RootPathCost,
            self.DesignatedBridgeID,
            self.DesignatedPortID,
            self.BridgePortID
        )

    def compare_to(self, other):
        """Returns -1 if better, 0 if equal, 1 if other is better."""
        if rstp_util.is_id_better(self.RootBridgeID, other.RootBridgeID):
            return -1
        elif self.RootBridgeID != other.RootBridgeID:
            return 1

        if self.RootPathCost < other.RootPathCost:
            return -1
        elif self.RootPathCost != other.RootPathCost:
            return 1

        if rstp_util.is_id_better(self.DesignatedBridgeID, other.DesignatedBridgeID):
            return -1
        elif self.DesignatedBridgeID != other.DesignatedBridgeID:
            return 1

        if self.DesignatedPortID < other.DesignatedPortID:
            return -1
        elif self.DesignatedPortID != other.DesignatedPortID:
            return 1

        if self.BridgePortID < other.BridgePortID:
            return -1
        elif self.BridgePortID != other.BridgePortID:
            return 1

        return 0
