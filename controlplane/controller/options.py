import argparse

class Options:
    """Parsing of command line arguments."""
    VERSION_RSTP = 0
    VERSION_STP = 1

    def __init__(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--port-no", action="append", type=int, help="Use multiple times to specify which switch ports the controller should handle.")
        parser.add_argument("--api-rpc-port", action="store", type=int, required=True, help="Port used to connect to SwitchAPI.")
        parser.add_argument("--mac", action="store", required=True, help="MAC address of the switch.")
        parser.add_argument("--bridge-prio", action="store", type=int, default=0x8000, help="The rstp bridge priority for this bridge. Default: 0x8000")
        parser.add_argument("--cpu-interface", action="store", required=True, help="The interface that is connected to the CPU port of the switch.")
        parser.add_argument("--stp-version", action="store", default="rstp", choices=["stp", "rstp"], help="Which version of stp to use. Default: rstp")
        parser.add_argument("--config-port", action="store", type=int, required=False, help="If present, this port can be used to configure the switch using the CLI.")
        arguments = parser.parse_args()

        self.port_nos = arguments.port_no
        self.rpc_port = arguments.api_rpc_port
        self.mac = arguments.mac
        self.bridge_prio = arguments.bridge_prio
        self.cpu_interface = arguments.cpu_interface
        self.config_port = arguments.config_port
        self.stp_version = Options.VERSION_RSTP if arguments.stp_version == "rstp" else Options.VERSION_STP