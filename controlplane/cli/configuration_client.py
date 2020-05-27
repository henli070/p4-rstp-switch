import socket
import struct

STATUS_SUCCESS = 0
STATUS_ERROR = 1
STATUS_INVALID_PARAMETER = 2

# Copy pasted from configuration_server.py
# Bridge get requests.
GET_BRIDGE_IDENTIFIER = 0
GET_TIME_SINCE_TOPOLOGY_CHANGE = 1
GET_TOPOLOGY_CHANGE_COUNT = 2
GET_DESIGNATED_ROOT = 3
GET_ROOT_PATH_COST = 4
GET_ROOT_PORT = 5
GET_MAX_AGE = 6
GET_HELLO_TIME = 7
GET_FORWARD_DELAY = 8
GET_BRIDGE_MAX_AGE = 9
GET_BRIDGE_HELLO_TIME = 10
GET_BRIDGE_FORWARD_DELAY = 11
GET_TX_HOLD_COUNT = 12
GET_FORCE_VERSION = 13
# Bridge set requests.
SET_BRIDGE_MAX_AGE = 14
SET_BRIDGE_HELLO_TIME = 15
SET_BRIDGE_FORWARD_DELAY = 16
SET_BRIDGE_PRIORITY = 17
SET_FORCE_VERSION = 18
SET_TX_HOLD_COUNT = 19
# Port get requests.
GET_PORT_UPTIME = 20
GET_PORT_STATE = 21
GET_PORT_IDENTIFIER = 22
GET_PORT_PATH_COST = 23
GET_PORT_DESIGNATED_ROOT = 24
GET_PORT_DESIGNATED_COST = 25
GET_PORT_DESIGNATED_BRIDGE = 26
GET_PORT_DESIGNATED_PORT = 27
GET_PORT_TOPOLOGY_CHANGE_ACKNOWLEDGE = 28
GET_PORT_ADMIN_EDGE = 29
GET_PORT_OPER_EDGE = 30
GET_PORT_AUTO_EDGE = 31
GET_PORT_OPER_POINT_TO_POINT_MAC = 32
# Port set requests.
SET_PORT_PATH_COST = 33
SET_PORT_PRIORITY = 34
SET_PORT_ADMIN_EDGE = 35
SET_PORT_AUTO_EDGE = 36

class ConfigurationClient:
    def __init__(self, address, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((address, port))

        self.receive_buffer = bytes()

    # Get bridge configuration.
    def get_bridge_identifier(self):
        self.socket.sendall(struct.pack("!i", GET_BRIDGE_IDENTIFIER))
        return self._read_identifier_response()

    def get_time_since_topology_change(self):
        self.socket.sendall(struct.pack("!i", GET_TIME_SINCE_TOPOLOGY_CHANGE))
        return self._read_integer_response()

    def get_topology_change_count(self):
        self.socket.sendall(struct.pack("!i", GET_TOPOLOGY_CHANGE_COUNT))
        return self._read_integer_response()

    def get_designated_root(self):
        self.socket.sendall(struct.pack("!i", GET_DESIGNATED_ROOT))
        return self._read_identifier_response()

    def get_root_path_cost(self):
        self.socket.sendall(struct.pack("!i", GET_ROOT_PATH_COST))
        return self._read_integer_response()

    def get_root_port(self):
        self.socket.sendall(struct.pack("!i", GET_ROOT_PORT))
        return self._read_integer_response()

    def get_max_age(self):
        self.socket.sendall(struct.pack("!i", GET_MAX_AGE))
        return self._read_integer_response()

    def get_hello_time(self):
        self.socket.sendall(struct.pack("!i", GET_HELLO_TIME))
        return self._read_integer_response()

    def get_forward_delay(self):
        self.socket.sendall(struct.pack("!i", GET_FORWARD_DELAY))
        return self._read_integer_response()

    def get_bridge_max_age(self):
        self.socket.sendall(struct.pack("!i", GET_BRIDGE_MAX_AGE))
        return self._read_integer_response()

    def get_bridge_hello_time(self):
        self.socket.sendall(struct.pack("!i", GET_BRIDGE_HELLO_TIME))
        return self._read_integer_response()

    def get_bridge_forward_delay(self):
        self.socket.sendall(struct.pack("!i", GET_BRIDGE_FORWARD_DELAY))
        return self._read_integer_response()

    def get_tx_hold_count(self):
        self.socket.sendall(struct.pack("!i", GET_TX_HOLD_COUNT))
        return self._read_integer_response()

    def get_force_version(self):
        self.socket.sendall(struct.pack("!i", GET_FORCE_VERSION))
        return self._read_integer_response()

    # Set bridge configuration.
    def set_bridge_max_age(self, value):
        self.socket.sendall(struct.pack("!ii", SET_BRIDGE_MAX_AGE, value))
        return self._read_integer()

    def set_bridge_hello_time(self, value):
        self.socket.sendall(struct.pack("!ii", SET_BRIDGE_HELLO_TIME, value))
        return self._read_integer()

    def set_bridge_forward_delay(self, value):
        self.socket.sendall(struct.pack("!ii", SET_BRIDGE_FORWARD_DELAY, value))
        return self._read_integer()

    def set_bridge_priority(self, value):
        self.socket.sendall(struct.pack("!ii", SET_BRIDGE_PRIORITY, value))
        return self._read_integer()

    def set_force_version(self, value):
        self.socket.sendall(struct.pack("!ii", SET_FORCE_VERSION, value))
        return self._read_integer()

    def set_tx_hold_count(self, value):
        self.socket.sendall(struct.pack("!ii", SET_TX_HOLD_COUNT, value))
        return self._read_integer()

    # Read port configuration.
    def get_port_uptime(self, port_no):
        self.socket.sendall(struct.pack("!ii", GET_PORT_UPTIME, port_no))
        return self._read_integer_response()

    def get_port_state(self, port_no):
        self.socket.sendall(struct.pack("!ii", GET_PORT_STATE, port_no))
        return self._read_integer_response()

    def get_port_identifier(self, port_no):
        self.socket.sendall(struct.pack("!ii", GET_PORT_IDENTIFIER, port_no))
        return self._read_integer_response()

    def get_port_path_cost(self, port_no):
        self.socket.sendall(struct.pack("!ii", GET_PORT_PATH_COST, port_no))
        return self._read_integer_response()

    def get_port_designated_root(self, port_no):
        self.socket.sendall(struct.pack("!ii", GET_PORT_DESIGNATED_ROOT, port_no))
        return self._read_identifier_response()

    def get_port_designated_cost(self, port_no):
        self.socket.sendall(struct.pack("!ii", GET_PORT_DESIGNATED_COST, port_no))
        return self._read_integer_response()

    def get_port_designated_bridge(self, port_no):
        self.socket.sendall(struct.pack("!ii", GET_PORT_DESIGNATED_BRIDGE, port_no))
        return self._read_identifier_response()

    def get_port_designated_port(self, port_no):
        self.socket.sendall(struct.pack("!ii", GET_PORT_DESIGNATED_PORT, port_no))
        return self._read_integer_response()

    def get_port_topology_change_acknowledge(self, port_no):
        self.socket.sendall(struct.pack("!ii", GET_PORT_TOPOLOGY_CHANGE_ACKNOWLEDGE, port_no))
        return self._read_boolean_response()

    def get_port_admin_edge(self, port_no):
        self.socket.sendall(struct.pack("!ii", GET_PORT_ADMIN_EDGE, port_no))
        return self._read_boolean_response()

    def get_port_oper_edge(self, port_no):
        self.socket.sendall(struct.pack("!ii", GET_PORT_OPER_EDGE, port_no))
        return self._read_boolean_response()

    def get_port_auto_edge(self, port_no):
        self.socket.sendall(struct.pack("!ii", GET_PORT_AUTO_EDGE, port_no))
        return self._read_boolean_response()

    def get_port_oper_point_to_point_mac(self, port_no):
        self.socket.sendall(struct.pack("!ii", GET_PORT_OPER_POINT_TO_POINT_MAC, port_no))
        return self._read_boolean_response()

    # Set port configuration.
    def set_port_path_cost(self, port_no, value):
        self.socket.sendall(struct.pack("!iii", SET_PORT_PATH_COST, port_no, value))
        return self._read_integer()

    def set_port_priority(self, port_no, value):
        self.socket.sendall(struct.pack("!iii", SET_PORT_PRIORITY, port_no, value))
        return self._read_integer()

    def set_port_admin_edge(self, port_no, value):
        self.socket.sendall(struct.pack("!ii?", SET_PORT_ADMIN_EDGE, port_no, value))
        return self._read_integer()

    def set_port_auto_edge(self, port_no, value):
        self.socket.sendall(struct.pack("!iii", SET_PORT_AUTO_EDGE, port_no, value))
        return self._read_integer()

    # Socket helpers.
    def _read_socket(self):
        received_bytes = self.socket.recv(1024)
        if received_bytes is None:
            self.socket.close()
            raise Exception("Socket closed.")
        self.receive_buffer += received_bytes

    def _read_boolean(self):
        while len(self.receive_buffer) < 1:
            self._read_socket()
        value = struct.unpack("!?", self.receive_buffer[:1])[0]
        self.receive_buffer = self.receive_buffer[1:]
        return value

    def _read_integer(self):
        while len(self.receive_buffer) < 4:
            self._read_socket()
        value = struct.unpack("!i", self.receive_buffer[:4])[0]
        self.receive_buffer = self.receive_buffer[4:]
        return value

    def _read_mac_string(self):
        while len(self.receive_buffer) < 17:
            self._read_socket()
        value = struct.unpack("!17s", self.receive_buffer[:17])[0]
        self.receive_buffer = self.receive_buffer[17:]
        return value

    def _read_integer_response(self):
        status = self._read_integer()

        if status != STATUS_SUCCESS:
            return (status, None)

        return (status, self._read_integer())

    def _read_boolean_response(self):
        status = self._read_integer()

        if status != STATUS_SUCCESS:
            return (status, None)

        return (status, self._read_boolean())

    def _read_identifier_response(self):
        status = self._read_integer()

        if status != STATUS_SUCCESS:
            return (status, None)

        prio = self._read_integer()
        mac_string = self._read_mac_string()
        return (status, (prio, mac_string))