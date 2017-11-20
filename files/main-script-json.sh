#!/bin/bash
#
set -x

# Check if we are on a managed monroe node
cat /nodeid 2> /dev/null

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
ip rule
ip route show table 10000
ip route show table 10001

# ss -antop| grep 5556
# cat /etc/metadata-exporter.conf

cd /opt/monroe

# apt-get update
# apt-get install -y --no-install-recommends apt-utils

# "Installing LKL package:"
apt-get install -y ./*.deb

rm *.deb
# this script also creates lkl-config.json
./siri-test.py

LKL_HIJACK_CONFIG_FILE=$LKL_FILE   lkl-hijack \
 curl --resolve multipath-tcp.org:80:130.104.230.45 http://multipath-tcp.org

ifaces="$( cat lkl-config.json |grep param| cut -f4 -d '"')"
ifcount="$(cat lkl-config.json |grep param| cut -f4 -d '"'| wc -l)"

# if [[ $((ifcount)) == '2' ]]; then
#   IF1="$(echo ifaces| cut
#   LKL_HIJACK_CONFIG_FILE=$LKL_FILE   lkl-hijack \
#   ./iperf3_profile  -Vd --no-delay -t 3 -c 139.162.73.214 -p 5201 -m $IF,$IF
# else
    # LKL_HIJACK_CONFIG_FILE=$LKL_FILE   lkl-hijack \
    # ./iperf3_profile  -Vd --no-delay -t 3 -c 139.162.73.214 -p 5201
# fi
## Note: iperf binary won't work if renamed


#./metadata_subscriber.py

# ./nettest.py