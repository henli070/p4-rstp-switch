#!/bin/bash
# Usage: ./run_mininet_test.sh [topology]
# Example: ./run_mininet_test.sh p4_rstp

SCRIPT_PATH=$(dirname $(realpath $0))
MININET_TEST_PATH=$SCRIPT_PATH/controlplane/mininet/mininet_test.py
rm -f $SCRIPT_PATH/mininet_logs/*.txt
(cd $SCRIPT_PATH && sudo python $MININET_TEST_PATH "$@")