#!/bin/bash
#
cat /nodeid

ip addr
ifconfig
ip route

cd /opt/monroe


LKL_HIJACK_NET_IFTYPE=raw LKL_HIJACK_NET_IFPARAMS=op0   LKL_HIJACK_NET_IP=172.18.1.3 LKL_HIJACK_NET_NETMASK_LEN=24   LKL_HIJACK_NET_GATEWAY=172.18.1.1   ./bin/lkl-hijack.sh   curl --resolve multipath-tcp.org:80:130.104.230.45 http://multipath-tcp.org
LKL_HIJACK_NET_IFTYPE=raw LKL_HIJACK_NET_IFPARAMS=op0   LKL_HIJACK_NET_IP=172.18.1.3 LKL_HIJACK_NET_NETMASK_LEN=24   LKL_HIJACK_NET_GATEWAY=172.18.1.1   ./bin/lkl-hijack.sh   iperf/src/.libs/iperf3_profile -c 130.104.230.97 -p 5206 -t 3

LKL_HIJACK_NET_IFTYPE=raw LKL_HIJACK_NET_IFPARAMS=op0   LKL_HIJACK_NET_IP=172.18.1.2 LKL_HIJACK_NET_NETMASK_LEN=24   LKL_HIJACK_NET_GATEWAY=172.18.1.1   ./bin/lkl-hijack.sh   iperf/src/.libs/iperf3_profile -c 130.104.230.97 -p 5207 -t 3

LKL_HIJACK_CONFIG_FILE=$LKL_FILE   $LKL \
./iperf3_profile  -Vd --no-delay -t 3 -c 139.162.73.214 -p 5201