#!/bin/bash
#
set -x

cat /nodeid

if [ $? -eq 0 ]
then
  echo "On Monroe node"
  LKL_FILE="lkl.json"
  cat /monroe/config

else
  echo "On local node"
	LKL_FILE="lkl-local.json"
fi

ip addr
ifconfig
ip route

cd /opt/monroe

echo "Installing LKL package:"
apt-get install ./lkl_4.13.0-20171027_amd64.deb

LKL_HIJACK_CONFIG_FILE=$LKL_FILE    lkl-hijack   curl --resolve multipath-tcp.org:80:130.104.230.45 http://multipath-tcp.org

LKL_HIJACK_CONFIG_FILE=$LKL_FILE    lkl-hijack   ./mptcp_iperf3 -c 130.104.230.97 -p 5206 -t 3

LKL_HIJACK_CONFIG_FILE=$LKL_FILE    lkl-hijack   ./metadata

#./metadata_subscriber.py

# ./nettest.py