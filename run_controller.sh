#!/bin/bash
# Example usage: ./run_controller.sh --api-rpc-port 9000 --config-port 11000 --cpu-interface veth251 --mac 00:00:00:00:01:00 --port-no 1 --port-no 2

SCRIPT_PATH=$(dirname $(realpath $0))
PYTHONPATH=$SCRIPT_PATH/switch/switchapi:$PYTHON_PATH
CONTROLLER_PATH=$SCRIPT_PATH/controlplane/controller/controller.py
sudo env "PYTHONPATH=$PYTHONPATH" python $CONTROLLER_PATH "$@"