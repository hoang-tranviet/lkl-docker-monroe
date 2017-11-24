#!/bin/bash
#
set -x

time=`date +%Y-%m-%d-%H%M%S`
test_id=$time

log_file=/monroe/results/output-${time}.log

# Check if we are on a managed monroe node
nodeid="$(cat /nodeid)"   >> $log_file 2>&1

if [ $? -eq 0 ]
then
  echo "On Monroe node"
  cat /monroe/config
  MONROE=true
  LKL=lkl-hijack
# elif
#   echo "On local node"
#   LKL=lkl/bin/lkl-hijack.sh
else
  echo "On dev node"
  DEVNODE=true
  LKL=lkl-hijack
  # need to create manually on dev node
  mkdir -p /monroe/results/

fi

ip addr
ip route
ip route get 8.8.8.8
ip route show table 10000
ip route show table 10001

# ss -antop| grep 5556
# cat /etc/metadata-exporter.conf

cd /opt/monroe

# apt-get update

# "Installing LKL package:"
apt-get install -y ./*.deb

# this script also creates lkl-config.json
./siri-test.py

LKL_FILE="lkl-config.json"

LKL_HIJACK_CONFIG_FILE=$LKL_FILE   $LKL \
 curl --resolve multipath-tcp.org:80:130.104.230.45 http://multipath-tcp.org

ifaces="$( cat lkl-config.json |grep param| cut -f4 -d '"')"
ifcount="$(cat lkl-config.json |grep param| cut -f4 -d '"'| wc -l)"

echo "relevant ifaces: "$ifaces


inlab_server="130.104.230.97"
linode_server="139.162.73.214"

port=$(( 5201 + RANDOM % 8))


start_tcpdump() {
        # trace="/monroe/results/dump-$nodeid-$test_id.pcap"
        trace="/monroe/results/tshark-$nodeid-$test_id.pcap"

        echo "capturing packet trace to file: $trace"
        # tcpdump  -i any  -s 150 tcp and portrange 5201-5210  -w $trace  &
        # tcpdump -i $1 -s 150  -w $trace  &
        tshark -w   $trace
        sleep 0.3
}

kill_tcpdump() {
        echo "killing tcpdump"
        sleep 2
        # pkill tcpdump
        pkill tshark
}


baseopt=" -Vd --no-delay -t 3  -c $inlab_server -p $port --test-id $test_id "
cmd="LKL_HIJACK_CONFIG_FILE=$LKL_FILE   $LKL ./iperf3_profile  $baseopt"

if [[ $ifcount -gt 1 ]]; then
  IF1="$(echo $ifaces| cut -d' ' -f1)"
  IF2="$(echo $ifaces| cut -d' ' -f2)"
  # echo "$IF1 $IF2"
  cmd=$cmd" -m $IF1,$IF2"
fi

IF1="$(echo $ifaces| cut -d' ' -f1)"

start_tcpdump $IF1

(eval $cmd) >> $log_file 2>&1

## Note: iperf binary won't work if renamed

kill_tcpdump

#./metadata_subscriber.py

# ./nettest.py
