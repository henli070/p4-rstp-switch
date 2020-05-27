#!/bin/bash
# A simple cli for the contoller.
# Usage: ./run_cli.sh <config-port> [address]

CLI_PATH=$(dirname $(realpath $0))/controlplane/cli/cli.py
python $CLI_PATH "$@"