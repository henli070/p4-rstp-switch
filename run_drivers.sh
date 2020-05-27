#!/bin/bash
# Usage: ./run_drivers.sh <switchapi-rpc-port> <bmv2-thrift-port> <bmv2-ipc-address>
# Example: ./run_drivers.sh 9000 10000 ipc:///tmp/bmv2-0-notifications.ipc

SCRIPT_PATH=$(dirname $(realpath $0))
DRIVERS=$SCRIPT_PATH/controlplane/drivers/drivers
sudo $DRIVERS "$@"