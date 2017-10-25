#!/bin/bash
#
cat /nodeid

if [ $? -eq 0 ]
then
  echo "On Monroe node"
  LKL_FILE="lkl.json"
else
  echo "On local node"
	LKL_FILE="lkl-local.json"
fi

ip addr
ifconfig
ip route

cd /opt/monroe

LKL_HIJACK_CONFIG_FILE=$LKL_FILE    ./bin/lkl-hijack.sh   curl --resolve multipath-tcp.org:80:130.104.230.45 http://multipath-tcp.org
LKL_HIJACK_CONFIG_FILE=$LKL_FILE    ./bin/lkl-hijack.sh   ./mptcp_iperf3 -c 130.104.230.97 -p 5206 -t 3