import cmd
import sys
import configuration_client

PORT_STATE_DISCARDING = 4
PORT_STATE_LEARNING = 2
PORT_STATE_FORWARDING = 3

class Cli(cmd.Cmd):
    def __init__(self, address, port):
        cmd.Cmd.__init__(self)
        self.client = configuration_client.ConfigurationClient(address, port)
        Cli.prompt = "{}>".format(address)

    def emptyline(self):
        pass

    def do_EOF(self, args):
        print("")
        return "exited"

    # Get bridge configuration.
    def do_bridge_identifier(self, args):
        """Get the bridge identifier as (priority, mac)."""
        self.print_get_result("BridgeIdentifier", self.client.get_bridge_identifier())

    def do_time_since_topology_change(self, args):
        """Get the time in seconds since last topology change."""
        self.print_get_result("TimeSinceTopologyChange", self.client.get_time_since_topology_change())

    def do_topology_change_count(self, args):
        """Get the number of topology changes."""
        self.print_get_result("TopologyChangeCount", self.client.get_topology_change_count())

    def do_designated_root(self, args):
        """Get the root bridge identifier as (priority, mac)."""
        self.print_get_result("DesignatedRoot", self.client.get_designated_root())

    def do_root_path_cost(self, args):
        """Get the cost to the root bridge."""
        self.print_get_result("RootPathCost", self.client.get_root_path_cost())

    def do_root_port(self, args):
        """Get the root port."""
        self.print_get_result("RootPort", self.client.get_root_port())

    def do_max_age(self, args):
        """Get the root bridge max age."""
        self.print_get_result("MaxAge", self.client.get_max_age())

    def do_hello_time(self, args):
        """Get the root bridge hello time."""
        self.print_get_result("HelloTime", self.client.get_hello_time())

    def do_forward_delay(self, args):
        """Get the root bridge forward delay."""
        self.print_get_result("ForwardDelay", self.client.get_forward_delay())

    def do_bridge_max_age(self, args):
        """Get the bridge max age."""
        self.print_get_result("BridgeMaxAge", self.client.get_bridge_max_age())

    def do_bridge_hello_time(self, args):
        """Get the bridge hello time."""
        self.print_get_result("BridgeHelloTime", self.client.get_bridge_hello_time())

    def do_bridge_forward_delay(self, args):
        """Get the bridge forward delay."""
        self.print_get_result("BridgeForwardDelay", self.client.get_bridge_forward_delay())

    def do_tx_hold_count(self, args):
        """Get the bridge transmit hold count."""
        self.print_get_result("TxHoldCount", self.client.get_tx_hold_count())

    def do_force_version(self, args):
        """Get the bridge force version (0=STP compatibility, 2=RSTP)"""
        self.print_get_result("ForceVersion", self.client.get_force_version())

    def do_bridge_dump(self, args):
        """Dump all info about the bridge."""
        self.do_bridge_identifier(args)
        self.do_time_since_topology_change(args)
        self.do_topology_change_count(args)
        self.do_designated_root(args)
        self.do_root_path_cost(args)
        self.do_root_port(args)
        self.do_max_age(args)
        self.do_hello_time(args)
        self.do_forward_delay(args)
        self.do_bridge_max_age(args)
        self.do_bridge_hello_time(args)
        self.do_bridge_forward_delay(args)
        self.do_tx_hold_count(args)
        self.do_force_version(args)

    # Set bridge configuration.
    def do_set_bridge_max_age(self, args):
        try:
            value = int(args, 0)
            self.print_set_result("BridgeMaxAge", self.client.set_bridge_max_age(value))
        except ValueError:
            self.help_set_bridge_max_age()

    def help_set_bridge_max_age(self):
        print("Usage: set_bridge_max_age <age>")

    def do_set_bridge_hello_time(self, args):
        try:
            value = int(args, 0)
            self.print_set_result("BridgeHelloTime", self.client.set_bridge_hello_time(value))
        except ValueError:
            self.help_set_bridge_hello_time()

    def help_set_bridge_hello_time(self):
        print("Usage: set_bridge_hello_time <time>")

    def do_set_bridge_forward_delay(self, args):
        try:
            value = int(args, 0)
            self.print_set_result("BridgeForwardDelay", self.client.set_bridge_forward_delay(value))
        except ValueError:
            self.help_set_bridge_forward_delay()

    def help_set_bridge_forward_delay(self):
        print("Usage: set_bridge_forward_delay <delay>")

    def do_set_bridge_priority(self, args):
        try:
            value = int(args, 0)
            self.print_set_result("BridgePriority", self.client.set_bridge_priority(value))
        except ValueError:
            self.help_set_bridge_priority()

    def help_set_bridge_priority(self):
        print("Usage: set_bridge_priority <priority>")

    def do_set_force_version(self, args):
        try:
            value = int(args, 0)
            self.print_set_result("ForceVersion", self.client.set_force_version(value))
        except ValueError:
            self.help_set_force_version()

    def help_set_force_version(self):
        print("Usage: set_force_version <version>")

    def do_set_tx_hold_count(self, args):
        try:
            value = int(args, 0)
            self.print_set_result("TxHoldCount", self.client.set_tx_hold_count(value))
        except ValueError:
            self.help_set_tx_hold_count()

    def help_set_tx_hold_count(self):
        print("Usage: set_tx_hold_count <count>")

    # Read port configuration.
    def do_port_uptime(self, args):
        try:
            port_no = int(args, 0)
            self.print_get_result("Uptime", self.client.get_port_uptime(port_no))
        except ValueError:
            self.help_port_uptime()

    def help_port_uptime(self):
        print("Usage: port_uptime <port>")

    def do_port_state(self, args):
        try:
            port_no = int(args, 0)

            # Do this one manually to give nicer print.
            name = "State"
            result = self.client.get_port_state(port_no)
            if result[0] != configuration_client.STATUS_SUCCESS:
                print("Failed to get {}! ({})".format(name, self.fail_reason(result[0])))
            else:
                state = result[1]
                if state == PORT_STATE_DISCARDING:
                    state_string = "Discarding"
                elif state == PORT_STATE_FORWARDING:
                    state_string = "Forwarding"
                elif state == PORT_STATE_LEARNING:
                    state_string = "Learning"
                else:
                    state_string = "Invalid!"

                print("{} = {} ({})".format(name, state, state_string))
        except ValueError:
            self.help_port_state()

    def help_port_state(self):
        print("Usage: port_state <port>")

    def do_port_identifier(self, args):
        try:
            port_no = int(args, 0)
            self.print_get_result("Identifier", self.client.get_port_identifier(port_no))
        except ValueError:
            self.help_port_identifier()

    def help_port_identifier(self):
        print("Usage: port_identifier <port>")

    def do_port_path_cost(self, args):
        try:
            port_no = int(args, 0)
            self.print_get_result("PathCost", self.client.get_port_path_cost(port_no))
        except ValueError:
            self.help_port_path_cost()

    def help_port_path_cost(self):
        print("Usage: port_path_cost <port>")

    def do_port_designated_root(self, args):
        try:
            port_no = int(args, 0)
            self.print_get_result("DesignatedRoot", self.client.get_port_designated_root(port_no))
        except ValueError:
            self.help_port_designated_root()

    def help_port_designated_root(self):
        print("Usage: port_designated_root <port>")

    def do_port_designated_cost(self, args):
        try:
            port_no = int(args, 0)
            self.print_get_result("DesignatedCost", self.client.get_port_designated_cost(port_no))
        except ValueError:
            self.help_port_designated_cost()

    def help_port_designated_cost(self):
        print("Usage: port_designated_cost <port>")

    def do_port_designated_bridge(self, args):
        try:
            port_no = int(args, 0)
            self.print_get_result("DesignatedBridge", self.client.get_port_designated_bridge(port_no))
        except ValueError:
            self.help_port_designated_bridge()

    def help_port_designated_bridge(self):
        print("Usage: port_designated_bridge <port>")

    def do_port_designated_port(self, args):
        try:
            port_no = int(args, 0)
            self.print_get_result("DesignatedPort", self.client.get_port_designated_port(port_no))
        except ValueError:
            self.help_port_designated_port()

    def help_port_designated_port(self):
        print("Usage: port_designated_port <port>")

    def do_port_topology_change_acknowledge(self, args):
        try:
            port_no = int(args, 0)
            self.print_get_result("TopologyChangeAcknowledge", self.client.get_port_topology_change_acknowledge(port_no))
        except ValueError:
            self.help_port_topology_change_acknowledge()

    def help_port_topology_change_acknowledge(self):
        print("Usage: port_topology_change_acknowledge <port>")

    def do_port_admin_edge(self, args):
        try:
            port_no = int(args, 0)
            self.print_get_result("AdminEdge", self.client.get_port_admin_edge(port_no))
        except ValueError:
            self.help_port_admin_edge()

    def help_port_admin_edge(self):
        print("Usage: port_admin_edge <port>")

    def do_port_oper_edge(self, args):
        try:
            port_no = int(args, 0)
            self.print_get_result("OperEdge", self.client.get_port_oper_edge(port_no))
        except ValueError:
            self.help_port_oper_edge()

    def help_port_oper_edge(self):
        print("Usage: port_oper_edge <port>")

    def do_port_auto_edge(self, args):
        try:
            port_no = int(args, 0)
            self.print_get_result("AutoEdge", self.client.get_port_auto_edge(port_no))
        except ValueError:
            self.help_port_auto_edge()

    def help_port_auto_edge(self):
        print("Usage: port_auto_edge <port>")

    def do_port_oper_point_to_point_mac(self, args):
        try:
            port_no = int(args, 0)
            self.print_get_result("OperPointToPointMac", self.client.get_port_oper_point_to_point_mac(port_no))
        except ValueError:
            self.help_port_oper_point_to_point_mac()

    def help_port_oper_point_to_point_mac(self):
        print("Usage: port_oper_point_to_point_mac <port>")

    def do_port_dump(self, args):
        try:
            port_no = int(args, 0)
            self.do_port_uptime(args)
            self.do_port_state(args)
            self.do_port_identifier(args)
            self.do_port_path_cost(args)
            self.do_port_designated_root(args)
            self.do_port_designated_cost(args)
            self.do_port_designated_bridge(args)
            self.do_port_designated_port(args)
            self.do_port_topology_change_acknowledge(args)
            self.do_port_admin_edge(args)
            self.do_port_oper_edge(args)
            self.do_port_auto_edge(args)
            self.do_port_oper_point_to_point_mac(args)
        except ValueError:
            self.help_port_dump()

    def help_port_dump(self):
        print("Usage: port_dump <port>")

    # Set port configuration.
    def do_set_port_path_cost(self, args):
        try:
            port_no = int(args.split()[0], 0)
            value = int(args.split()[1], 0)
            self.print_set_result("PathCost", self.client.set_port_path_cost(port_no, value))
        except ValueError:
            self.help_set_port_path_cost()

    def help_set_port_path_cost(self):
        print("Usage: set_port_path_cost <port> <cost>")

    def do_set_port_priority(self, args):
        try:
            port_no = int(args.split()[0], 0)
            value = int(args.split()[1], 0)
            self.print_set_result("PortPriority", self.client.set_port_priority(port_no, value))
        except ValueError:
            self.help_set_port_priority()

    def help_set_port_priority(self):
        print("Usage: set_port_priority <port> <priority>")

    def do_set_port_admin_edge(self, args):
        try:
            port_no = int(args.split()[0], 0)
            value = bool(args.split()[1], 0)
            self.print_set_result("AdminEdge", self.client.set_port_admin_edge(port_no, value))
        except ValueError:
            self.help_set_port_admin_edge()

    def help_set_port_admin_edge(self):
        print("Usage: set_port_admin_edge <port> <True|False>")

    def do_set_port_auto_edge(self, args):
        try:
            port_no = int(args.split()[0], 0)
            value = bool(args.split()[1], 0)
            self.print_set_result("AutoEdge", self.client.set_port_auto_edge(port_no, value))
        except ValueError:
            self.help_set_port_auto_edge()

    def help_set_port_auto_edge(self):
        print("Usage: set_port_auto_edge <port> <True|False>")

    def print_get_result(self, name, result):
        if result[0] != configuration_client.STATUS_SUCCESS:
            print("Failed to get {}! ({})".format(name, self.fail_reason(result[0])))
        else:
            print("{} = {}".format(name, result[1]))

    def fail_reason(self, status):
        if status == configuration_client.STATUS_ERROR:
            return "Internal error"
        elif status == configuration_client.STATUS_INVALID_PARAMETER:
            return "Invalid parameter"
        else:
            return "Unknown reason ({})".format(status)

    def print_set_result(self, name, result):
        if result != configuration_client.STATUS_SUCCESS:
            print("Failed to set {}! ({})".format(name, self.fail_reason(result)))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please specify port to connect to.")
        exit()
    port = int(sys.argv[1])
    address = "localhost"
    if len(sys.argv) > 2:
        address = sys.argv[2]
    Cli(address, port).cmdloop()