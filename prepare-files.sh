DOCKER_DIR="$(pwd)"

rm -r files/lkl files/*.deb                     2> /dev/null

LKL_DIR="/run/media/hoang/home/hoang/multipathtcp/lkl-mptcp"
echo "compile LKL"
cd $LKL_DIR/tools/lkl  && make -j4

echo "create LKL deb package"
cd $LKL_DIR   && rm *.deb *.rpm  deb/* -r       2> /dev/null
./.circleci/pkgbuild.sh

cd $DOCKER_DIR
cp $LKL_DIR/*.deb files/

IPERF_DIR="/run/media/hoang/home/hoang/multipathtcp/iperf-mptcp/iperf"
cp $IPERF_DIR/src/.libs/iperf3_profile  files/
# iperf3_profile in .libs is the only binary that I found can work alone
# renamed iperf binary won't work, weird!
# cp $IPERF_DIR/src/.libs/iperf3_profile  files/mptcp_siri