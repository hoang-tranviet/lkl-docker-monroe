#!/bin/bash
#
set -x

cat /nodeid

if [ $? -eq 0 ]
then
  echo "On Monroe node"
  LKL_FILE="lkl-config.json"
  cat /monroe/config

else
  echo "On local node"
	LKL_FILE="lkl-local.json"
fi


ip addr
ip route

ss -antop| grep 5556
cat /etc/metadata-exporter.conf

cd /opt/monroe
./metadata

# "Installing LKL package:"
apt-get install ./lkl_4.13.0-20171027_amd64.deb


LKL_HIJACK_CONFIG_FILE=$LKL_FILE    lkl-hijack   curl --resolve multipath-tcp.org:80:130.104.230.45 http://multipath-tcp.org

LKL_HIJACK_CONFIG_FILE=$LKL_FILE    lkl-hijack   ./mptcp_iperf3 -c 130.104.230.97 -p 5206 -t 3


#./metadata_subscriber.py

# ./nettest.py