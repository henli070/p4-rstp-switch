#!/bin/bash
# Example usage:
# sudo switch/tools/veth_setup.sh
# ./run_bmv2.sh --thrift-port 10000 --notifications-addr ipc:///tmp/bmv2-0-notifications.ipc -i 1@veth0 -i 2@veth2 -i 64@veth250
# sudo switch/tools/veth_teardown.sh

SCRIPT_PATH=$(dirname $(realpath $0))
BMV2=simple_switch
JSON_PATH=$SCRIPT_PATH/switch/p4-build/bmpd/switch.json
sudo $BMV2 $JSON_PATH "$@"