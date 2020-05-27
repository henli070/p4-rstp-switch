#!/bin/bash
SCRIPT_PATH=$(dirname $(realpath $0))
g++ \
-Wall -Wextra \
-o $SCRIPT_PATH/drivers \
-I $SCRIPT_PATH/../../switch/p4-build \
-I $SCRIPT_PATH/../../switch/switchapi/include \
-I $SCRIPT_PATH/../../switch/switchapi/third-party/tommyds/include \
-I $SCRIPT_PATH/../../switch/p4src/includes \
-L $SCRIPT_PATH/../../switch/switchapi/.libs \
-L $SCRIPT_PATH/../../switch/p4-build/bmpd/.libs \
$SCRIPT_PATH/drivers.cpp \
-l:libbmswitchapi.a \
-lJudy \
-l:libpd.a \
-l:libbmpdfixed.a \
-l:libruntimestubs.a \
-l:libsimpleswitch_thrift.a \
-lpthread \
-l:libthrift.a \
-lnanomsg
