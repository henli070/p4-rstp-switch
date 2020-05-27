# P4 RSTP Switch
This repository contains an implementation of the Rapid Spanning Tree Protocol on top of the Switch.p4 project.

## Pulling the Switch.p4 Project
git submodule update --init --recursive

This needs to be done after cloning this repository.

## Installing Dependencies
This has been tested on Ubuntu 16.04.

If you don't already have python installed, run:  
sudo apt install python python-pip  
pip install --upgrade pip

### For Switch.p4
Install BMv2 (https://github.com/p4lang/behavioral-model), but use "./configure --with-pdfixed" instead of just "./configure".

Install p4c-bm (https://github.com/p4lang/p4c-bm). Note: You might get an error while installing the pip dependencies for it, but it will still work.

If you want to run Switch.p4's tests, then install PTF (https://github.com/p4lang/ptf).

### For the Controller
pip install scapy

### For the Mininet Test
sudo apt install mininet python-tk  
pip install networkx matplotlib

To be able to use the topologies including Linux STP switches, run:  
sudo apt install bridge-utils

Additionally, for tests including Linux RSTP switches, MSTPD (https://github.com/mstpd/mstpd) is also needed. Clone it and run:  
./autogen.sh  
./configure  
make  
sudo make install

## Building Switch.p4
cd switch  
./autogen.sh  
./configure --with-bmv2 --with-switchapi  
make

## Building the Drivers
controlplane/drivers/build.sh

## Running the Switch
This is an example for starting the switch with two ports.
More ports can be setup by adding -i and --port-no arguments to BMv2 and the controller.
To start multiple switches, use different interfaces, notification addresses, port arguments and MACs for each.

### Using Virtual Interfaces
If running with virtual interfaces, set these up by running:  
sudo switch/tools/veth_setup.sh

This creates the interface pairs veth0-veth1, veth2-veth3, veth4-veth5, etc.

To remove them afterwards, run:  
sudo switch/tools/veth_teardown.sh

Spammy IPv6 packets can be disabled by running:  
sudo switch/tools/veth_disable_ipv6.sh

### Using Real Interfaces
If using real interfaces, replace "veth0" and "veth2" in the BMv2 command below with the real ones.

The virtual CPU interface pair is still needed and can be set up as follows:  
sudo ip link add name veth250 type veth peer name veth251  
sudo ip link set dev veth250 up  
sudo ip link set dev veth251 up  

### Starting BMv2
./run_bmv2.sh --thrift-port 10000 --notifications-addr ipc:///tmp/bmv2-0-notifications.ipc -i 1@veth0 -i 2@veth2 -i 64@veth250

Available arguments: See ./run_bmv2.sh -h

### Starting the Drivers
./run_drivers.sh 9000 10000 ipc:///tmp/bmv2-0-notifications.ipc

Available arguments: \<switchapi-rpc-port> \<bmv2-thrift-port> \<bmv2-ipc-address>

### Starting the RSTP Controller
./run_controller.sh --api-rpc-port 9000 --config-port 11000 --cpu-interface veth251 --mac 00:00:00:00:01:00 --port-no 1 --port-no 2

Available arguments: See ./run_controller.sh -h

### Connecting with the Management CLI (optional)
./run_cli.sh 11000

Available arguments: \<config-port> [controller-address]

## Running the Mininet Test
./run_mininet_test.sh [topology]

This starts multiple switches in Mininet and opens a graphical visualization showing the status of the switches, hosts and links.

### Example Interactions
Bringing the link between s1 and s2 down:  
link s1 s2 down

Bringing it back up:  
link s1 s2 up

Stopping switch s1:  
switch s1 stop

Starting it again:  
switch s1 start

To open a terminal on host h1:  
xterm h1

Pinging h2 from h1's terminal:  
ping 10.0.0.2

### Available Topologies
- p4_rstp
- p4_stp
- p4_mix
- linux_rstp
- linux_stp
- linux_mix
- mix_rstp
- mix_stp
- mix_mix

For example, p4_mix is a topology with p4 switches, where some are run with RSTP and some with STP.
