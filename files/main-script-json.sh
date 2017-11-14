#!/bin/bash
#
set -x

# iperf binary won't work if renamed, use alias instead
Siri="iperf3_profile"

cat /nodeid

if [ $? -eq 0 ]
then
  echo "On Monroe node"
  LKL_FILE="lkl-config.json"
  cat /monroe/config
  IF="op0"
else
  echo "On local node"
	LKL_FILE="lkl-local.json"
  IF="eth0"
fi


ip addr
ip route

ss -antop| grep 5556
cat /etc/metadata-exporter.conf

cd /opt/monroe
./metadata

# "Installing LKL package:"
apt-get install -y ./*.deb


LKL_HIJACK_CONFIG_FILE=$LKL_FILE   lkl-hijack \
 curl --resolve multipath-tcp.org:80:130.104.230.45 http://multipath-tcp.org

LKL_HIJACK_CONFIG_FILE=$LKL_FILE   lkl-hijack \
 ./iperf3_profile --no-delay  -t 3 -c 130.104.230.97 -p 5209 -m $IF,$IF


#./metadata_subscriber.py

# ./nettest.py