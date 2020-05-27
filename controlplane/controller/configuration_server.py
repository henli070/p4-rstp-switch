import socket
from threading import Thread
import struct
import traceback
import rstp.rstp_configuration as rstp_configuration

STATUS_SUCCESS = 0
STATUS_ERROR = 1
STATUS_INVALID_PARAMETER = 2

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

class ConfigurationServer:
    """A TCP configuration server for the controller. Can be connected to with the cli."""
    def __init__(self, rstp_configuration, port):
        self.rstp_configuration = rstp_configuration
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.settimeout(1.0)
        self.socket.bind(("", port))
        self.socket.listen(2)
        print("Configuration server listening on port {}".format(port))

    def start(self):
        self.should_run = True
        self.listen_thread = Thread(target=self._listen)
        self.listen_thread.daemon = True
        self.listen_thread.start()

    def stop(self):
        self.should_run = False
        self.listen_thread.join()

    def _listen(self):
        threads = []
        while self.should_run:
            try:
                socket, address = self.socket.accept()
                thread = Thread(target=self._client_thread, args=(socket, address))
                thread.daemon = True
                threads.append(thread)
                thread.start()
            except Exception as e:
                pass

        self.socket.close()
        for thread in threads:
            thread.join()

    def _client_thread(self, socket, address):
        socket.settimeout(1.0)
        current_buffer = bytes()
        while self.should_run:
            try:
                received_bytes = socket.recv(1024)
                if not received_bytes:
                    break
                current_buffer += received_bytes
                handled_bytes = self._handle_requests(socket, current_buffer)
                if handled_bytes < 0:
                    break
                current_buffer = current_buffer[handled_bytes:]
            except Exception as e:
                pass

        socket.close()

    def _handle_requests(self, socket, buffer):
        handled_bytes = 0
        request_start_index = 0
        i = 0
        full_response = bytes()
        while True:
            if (len(buffer) - i) < 4:
                break
            request = struct.unpack("!i", buffer[i:i+4])[0]
            i += 4

            response = bytes()
            try:
                # Bridge get requests.
                if request == GET_BRIDGE_IDENTIFIER:
                    bridge_id = self.rstp_configuration.get_bridge_identifier()
                    response += struct.pack("!i17s", bridge_id[0], bridge_id[1])
                elif request == GET_TIME_SINCE_TOPOLOGY_CHANGE:
                    response += struct.pack("!i", self.rstp_configuration.get_time_since_topology_change())
                elif request == GET_TOPOLOGY_CHANGE_COUNT:
                    response += struct.pack("!i", self.rstp_configuration.get_topology_change_count())
                elif request == GET_DESIGNATED_ROOT:
                    bridge_id = self.rstp_configuration.get_designated_root()
                    response += struct.pack("!i17s", bridge_id[0], bridge_id[1])
                elif request == GET_ROOT_PATH_COST:
                    response += struct.pack("!i", self.rstp_configuration.get_root_path_cost())
                elif request == GET_ROOT_PORT:
                    response += struct.pack("!i", self.rstp_configuration.get_root_port())
                elif request == GET_MAX_AGE:
                    response += struct.pack("!i", self.rstp_configuration.get_max_age())
                elif request == GET_HELLO_TIME:
                    response += struct.pack("!i", self.rstp_configuration.get_hello_time())
                elif request == GET_FORWARD_DELAY:
                    response += struct.pack("!i", self.rstp_configuration.get_forward_delay())
                elif request == GET_BRIDGE_MAX_AGE:
                    response += struct.pack("!i", self.rstp_configuration.get_bridge_max_age())
                elif request == GET_BRIDGE_HELLO_TIME:
                    response += struct.pack("!i", self.rstp_configuration.get_bridge_hello_time())
                elif request == GET_BRIDGE_FORWARD_DELAY:
                    response += struct.pack("!i", self.rstp_configuration.get_bridge_forward_delay())
                elif request == GET_TX_HOLD_COUNT:
                    response += struct.pack("!i", self.rstp_configuration.get_tx_hold_count())
                elif request == GET_FORCE_VERSION:
                    response += struct.pack("!i", self.rstp_configuration.get_force_version())
                # Bridge set requests.
                elif request == SET_BRIDGE_MAX_AGE:
                    if (len(buffer) - i) < 4:
                        break
                    value = struct.unpack("!i", buffer[i:i+4])[0]
                    i += 4
                    self.rstp_configuration.set_bridge_max_age(value)
                elif request == SET_BRIDGE_HELLO_TIME:
                    if (len(buffer) - i) < 4:
                        break
                    value = struct.unpack("!i", buffer[i:i+4])[0]
                    i += 4
                    self.rstp_configuration.set_bridge_hello_time(value)
                elif request == SET_BRIDGE_FORWARD_DELAY:
                    if (len(buffer) - i) < 4:
                        break
                    value = struct.unpack("!i", buffer[i:i+4])[0]
                    i += 4
                    self.rstp_configuration.set_bridge_forward_delay(value)
                elif request == SET_BRIDGE_PRIORITY:
                    if (len(buffer) - i) < 4:
                        break
                    value = struct.unpack("!i", buffer[i:i+4])[0]
                    i += 4
                    self.rstp_configuration.set_bridge_priority(value)
                elif request == SET_FORCE_VERSION:
                    if (len(buffer) - i) < 4:
                        break
                    value = struct.unpack("!i", buffer[i:i+4])[0]
                    i += 4
                    self.rstp_configuration.set_force_version(value)
                elif request == SET_TX_HOLD_COUNT:
                    if (len(buffer) - i) < 4:
                        break
                    value = struct.unpack("!i", buffer[i:i+4])[0]
                    i += 4
                    self.rstp_configuration.set_tx_hold_count(value)
                # Port get requests.
                else:
                    if (len(buffer) - i) < 4:
                        break
                    port_no = struct.unpack("!i", buffer[i:i+4])[0]
                    i += 4

                    if request == GET_PORT_UPTIME:
                        response += struct.pack("!i", self.rstp_configuration.get_port_uptime(port_no))
                    elif request == GET_PORT_STATE:
                        response += struct.pack("!i", self.rstp_configuration.get_port_state(port_no))
                    elif request == GET_PORT_IDENTIFIER:
                        response += struct.pack("!i", self.rstp_configuration.get_port_identifier(port_no))
                    elif request == GET_PORT_PATH_COST:
                        response += struct.pack("!i", self.rstp_configuration.get_port_path_cost(port_no))
                    elif request == GET_PORT_DESIGNATED_ROOT:
                        bridge_id = self.rstp_configuration.get_port_designated_root(port_no)
                        response += struct.pack("!i17s", bridge_id[0], bridge_id[1])
                    elif request == GET_PORT_DESIGNATED_COST:
                        response += struct.pack("!i", self.rstp_configuration.get_port_designated_cost(port_no))
                    elif request == GET_PORT_DESIGNATED_BRIDGE:
                        bridge_id = self.rstp_configuration.get_port_designated_bridge(port_no)
                        response += struct.pack("!i17s", bridge_id[0], bridge_id[1])
                    elif request == GET_PORT_DESIGNATED_PORT:
                        response += struct.pack("!i", self.rstp_configuration.get_port_designated_port(port_no))
                    elif request == GET_PORT_TOPOLOGY_CHANGE_ACKNOWLEDGE:
                        response += struct.pack("!?", self.rstp_configuration.get_port_topology_change_acknowledge(port_no))
                    elif request == GET_PORT_ADMIN_EDGE:
                        response += struct.pack("!?", self.rstp_configuration.get_port_admin_edge(port_no))
                    elif request == GET_PORT_OPER_EDGE:
                        response += struct.pack("!?", self.rstp_configuration.get_port_oper_edge(port_no))
                    elif request == GET_PORT_AUTO_EDGE:
                        response += struct.pack("!?", self.rstp_configuration.get_port_auto_edge(port_no))
                    elif request == GET_PORT_OPER_POINT_TO_POINT_MAC:
                        response += struct.pack("!?", self.rstp_configuration.get_port_oper_point_to_point_mac(port_no))
                    # Port set requests.
                    elif request == SET_PORT_PATH_COST:
                        if (len(buffer) - i) < 4:
                            break
                        value = struct.unpack("!i", buffer[i:i+4])[0]
                        i += 4
                        self.rstp_configuration.set_port_path_cost(port_no, value)
                    elif request == SET_PORT_PRIORITY:
                        if (len(buffer) - i) < 4:
                            break
                        value = struct.unpack("!i", buffer[i:i+4])[0]
                        i += 4
                        self.rstp_configuration.set_port_priority(port_no, value)
                    elif request == SET_PORT_ADMIN_EDGE:
                        if (len(buffer) - i) < 1:
                            break
                        value = struct.unpack("!?", buffer[i:i+1])[0]
                        i += 1
                        self.rstp_configuration.set_port_admin_edge(port_no, value)
                    elif request == SET_PORT_AUTO_EDGE:
                        if (len(buffer) - i) < 1:
                            break
                        value = struct.unpack("!?", buffer[i:i+1])[0]
                        i += 1
                        self.rstp_configuration.set_port_auto_edge(port_no, value)
                    else:
                        return -1
                # Success.
                full_response += struct.pack("!i", STATUS_SUCCESS) + response
            except rstp_configuration.InvalidParameter:
                full_response += struct.pack("!i", STATUS_INVALID_PARAMETER)
            except Exception:
                traceback.print_exc()
                full_response += struct.pack("!i", STATUS_ERROR)

            handled_bytes += (i - request_start_index)
            request_start_index = i

        if len(full_response) > 0:
            socket.sendall(full_response)

        return handled_bytes
