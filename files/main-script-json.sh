#!/bin/bash
#
set -x

start_tcpdump() {
        server=$1
        trace="/monroe/results/dump-$test_id-$server-$nodeid-$2.pcap.log"
        # echo "capturing packet trace to file: $trace"
        # tcpdump  -i $2  -s 150 tcp and portrange 5201-5210  -w $trace  &
        tcpdump -i $2 -s 150 not icmp and not port 5556  -w $trace  &
        sleep 0.3
}

kill_tcpdump() {
        echo "killing tcpdump"
        pkill tcpdump
        pkill tcpdump
}

iptables_bypass_kernel_stack() {
  # preventive measure: drop incoming pkt to stack, but seems also affect (lkl) ourself
  # iptables -A INPUT -p tcp --source-port $port -j DROP
  # reactive measure: drop outgoing RST
  iptables -A OUTPUT -p tcp --tcp-flags RST RST -d $1 -j DROP
}

iptables_cleanup() {
  # iptables -D INPUT -p tcp --source-port $port -j DROP
  iptables -D OUTPUT -p tcp --tcp-flags RST RST -d $1 -j DROP
}

test_curl() {

  iptables_bypass_kernel_stack 130.104.230.45

  LKL_HIJACK_CONFIG_FILE=$LKL_FILE   $LKL \
   curl --resolve multipath-tcp.org:80:130.104.230.45 http://multipath-tcp.org  --connect-timeout 2

  iptables_cleanup 130.104.230.45
}

run_tcp_test() {
  echo "Run TCP test"

  tcpdump -i $IF1 -s 150 tcp and portrange 5201-5300  -w /monroe/results/dump-tcp-$server.pcap.log  &
  sleep 0.3

  iperf_cmd="LKL_HIJACK_CONFIG_FILE=lkl-mptcp-disabled.json   $LKL  $iperf"

  error=1
  # repeat until we find a free server port
  while [[ $error -eq 1 ]]
  do
    sleep $(( 5 + RANDOM % 5 ))s

    iptables_bypass_kernel_stack $server
    port=$(( 5201 + RANDOM % 100 ))
    (eval $iperf_cmd -p $port) >> $log_tcp 2>&1
    error=$?
    iptables_cleanup $server
  done

  pkill tcpdump
}


time=`date +%Y-%m-%d-%H%M%S`
test_id=$time

nodeid="$(cat /nodeid)"
log_file=/monroe/results/output-${time}-default-sched-${nodeid}.log
log_file2=/monroe/results/output-${time}-server-sched-${nodeid}.log
log_tcp=/monroe/results/output-tcp-test.log

# Check if we are on a managed monroe node
cat /nodeid   >> $log_file 2>&1

if [ $? -eq 0 ]; then
  # echo "On Monroe node"
  cat /monroe/config
  # MONROE_NODE=true
  LKL=lkl-hijack
else
  # echo "On dev node"
  # DEVNODE=true
  LKL=lkl-hijack
  # need to create manually on dev node
  mkdir -p /monroe/results/

fi

ip addr
ip route
ip rule show

iface="$(ip route get 8.8.8.8|  cut -d' ' -f5| head -1)"

# ss -antop| grep 5556
# cat /etc/metadata-exporter.conf

cd /opt/monroe

# "Installing LKL package:"
apt-get install -y ./*.deb    > /dev/null

# this script creates lkl-config.json and metadata.log
./siri-test.py &

sleep 1

LKL_FILE="lkl-config.json"


ifaces="$( cat lkl-config.json |grep param| cut -f4 -d '"')"
ifcount="$(cat lkl-config.json |grep param| cut -f4 -d '"'| wc -l)"

if [ $ifcount -eq 0 ]; then
    echo "no cellular interface found, terminate now"
    exit 1
fi
if [ $ifcount -eq 1 ]; then
  echo "Only one interface found, terminate now"
  exit 1
fi

echo "relevant ifaces: "$ifaces  >> $log_file

# tcpdump -s 150 -i $iface not icmp -w /monroe/results/dump-all  &
test_curl

inlab_server="130.104.230.97"
linode_server="139.162.73.214"

if (( RANDOM % 2 )); then
  echo "run test against linode_server first"
  server1=$linode_server
  server2=$inlab_server
else
  echo "run test against inlab_server first"
  server1=$inlab_server
  server2=$linode_server
fi

for server in $server1 $server2; do
  ## Note: iperf binary won't work if renamed
  iperf="./iperf3_profile --no-delay -t 24 -i 0 -c $server --test-id $test_id "
  cmd="LKL_HIJACK_CONFIG_FILE=$LKL_FILE   $LKL  $iperf"

  IF1="$(echo $ifaces| cut -d' ' -f1)"

  run_tcp_test $iperf


  IF2="$(echo $ifaces| cut -d' ' -f2)"
  # echo "$IF1 $IF2"
  cmd=$cmd" -m $IF1,$IF2"

  start_tcpdump $server $IF1
  start_tcpdump $server $IF2

  echo "run exp against server with default scheduler"
  error=1
  # repeat until we find a free server port
  while [[ $error -eq 1 ]]; do
    sleep $(( 5 + RANDOM % 5 ))s

    iptables_bypass_kernel_stack $server

    port=$(( 5201 + RANDOM % 50))
    command=$cmd" -p $port"
    # execute command here, output to log file
    (eval $command) >> $log_file 2>&1
    error=$?

    iptables_cleanup $server
    # iptables -L -v
  done


  echo "run exp against server scheduler"
  error=1
  # repeat until we find a free server port
  while [[ $error -eq 1 ]]; do
    sleep $(( 5 + RANDOM % 5 ))s

    iptables_bypass_kernel_stack $server

    port=$(( 5251 + RANDOM % 50))
    command=$cmd" -p $port"
    # execute command here, output to log file
    (eval $command) >> $log_file2 2>&1
    error=$?

    iptables_cleanup $server
    # iptables -L -v
  done

  kill_tcpdump


done
