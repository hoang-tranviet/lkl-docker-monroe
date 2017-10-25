LKL_DIR="/home/hoang/multipathtcp/lkl-mptcp/tools/lkl"
IPERF_DIR="/home/hoang/multipathtcp/iperf-mptcp/iperf"

rm -r files/lkl

mkdir -p files/lkl/bin
cp  $LKL_DIR/bin/lkl-hijack.sh  files/lkl/bin/
cp  $LKL_DIR/liblkl-hijack.so   files/lkl/liblkl-hijack.so

cp $IPERF_DIR/src/.libs/iperf3_profile  files/mptcp_iperf3