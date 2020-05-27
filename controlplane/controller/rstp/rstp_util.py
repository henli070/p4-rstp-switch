# Various constants and utility functions for RSTP.

MIGRATE_TIME = 3

BPDU_TYPE_CONFIGURATION = 0x00
BPDU_TYPE_TOPOLOGY_CHANGE_NOTIFICATION = 0x80
BPDU_TYPE_RSTP = 0x02
BPDU_FLAGS_TOPOLOGY_CHANGE_BIT = 0x1
BPDU_FLAGS_TOPOLOGY_CHANGE_ACK_BIT = 0x80

BPDU_FLAGS_PROPOSAL_BIT = 0x02
BPDU_FLAGS_LEARNING_BIT = 0x10
BPDU_FLAGS_FORWARDING_BIT = 0x20
BPDU_FLAGS_AGREEMENT_BIT = 0x40
BPDU_FLAGS_PORT_ROLE_UNKNOWN = 0x00
BPDU_FLAGS_PORT_ROLE_ALTERNATE_OR_BACKUP_PORT = 0x04
BPDU_FLAGS_PORT_ROLE_ROOT_PORT = 0x08
BPDU_FLAGS_PORT_ROLE_DESIGNATED_PORT = 0x0C

def is_port_role_designated_port(flags):
    return (flags & 0x0C) == BPDU_FLAGS_PORT_ROLE_DESIGNATED_PORT
def is_port_role_root_port(flags):
    return (flags & 0x0C) == BPDU_FLAGS_PORT_ROLE_ROOT_PORT
def is_port_role_alternate_or_backup_port(flags):
    return (flags & 0x0C) == BPDU_FLAGS_PORT_ROLE_ALTERNATE_OR_BACKUP_PORT
def is_port_role_unknown(flags):
    return (flags & 0x0C) == BPDU_FLAGS_PORT_ROLE_UNKNOWN
def is_proposal_set(flags):
    return (flags & BPDU_FLAGS_PROPOSAL_BIT) != 0
def is_learning_set(flags):
    return (flags & BPDU_FLAGS_LEARNING_BIT) != 0
def is_forwarding_set(flags):
    return (flags & BPDU_FLAGS_FORWARDING_BIT) != 0
def is_agreement_set(flags):
    return (flags & BPDU_FLAGS_AGREEMENT_BIT) != 0
def is_topology_change_set(flags):
    return (flags & BPDU_FLAGS_TOPOLOGY_CHANGE_BIT) != 0
def is_topology_change_ack_set(flags):
    return (flags & BPDU_FLAGS_TOPOLOGY_CHANGE_ACK_BIT) != 0

DEFAULT_AGING_TIME = 300 # 300 seconds is recommended.

# Selected to match the ones used by switch.p4, but their values don't matter.
PORT_STATE_DISCARDING = 4
PORT_STATE_LEARNING = 2
PORT_STATE_FORWARDING = 3

def rstp_state_to_string(rstp_state):
    if rstp_state is None:
        return "None"
    if rstp_state == PORT_STATE_DISCARDING:
        return "DISCARDING"
    if rstp_state == PORT_STATE_FORWARDING:
        return "FORWARDING"
    if rstp_state == PORT_STATE_LEARNING:
        return "LEARNING"
    assert False

# Values for infoIs. (17.19.10)
RECEIVED = 0
MINE = 1
AGED = 2
DISABLED = 3

# Values for selectedRole and role.
DISABLED_PORT = 0
DESIGNATED_PORT = 1
ROOT_PORT = 2
ALTERNATE_PORT = 3
BACKUP_PORT = 4

# Values for rcvdInfo.
SUPERIOR_DESIGNATED_INFO = 0
REPEATED_DESIGNATED_INFO = 1
INFERIOR_DESIGNATED_INFO = 2
INFERIOR_ROOT_ALTERNATE_INFO = 3
OTHER_INFO = 4

def is_id_better(id, other_id):
    """Checks if an id is better than another. 'id' and 'other_id' are tuples of a priority value and a mac address string."""
    id_prio = id[0]
    id_mac_int = int(id[1].translate(None, ":"), 16)
    other_id_prio = other_id[0]
    other_id_mac_int = int(other_id[1].translate(None, ":"), 16)

    if id_prio != other_id_prio:
        return id_prio < other_id_prio
    return id_mac_int < other_id_mac_int