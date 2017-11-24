#!/usr/bin/python2

# from github.com/MONROE-PROJECT/Utilities/blob/master/monroe-experiments/usr/bin/metadata

import zmq
import os
import sys
import time
import sys
import json
import netifaces
from subprocess import Popen, PIPE, STDOUT, call
from multiprocessing import Process, Manager
from collections import OrderedDict

import pprint
pp = pprint.PrettyPrinter(indent=4)

# Only enable DEBUG mode on local testing node
DEBUG = False
CONFIGFILE = '/monroe/config'

LKL_CONFIG = {
    "debug":"0",
    "singlecpu":"1",
    "sysctl":"net.ipv4.tcp_wmem=4096 87380 6291456",
    "interfaces":[]
  }

# Default values (overwritable from the CONFIGFILE)
EXPCONFIG = {
        "zmqport": "tcp://172.17.0.1:5556",
        "nodeid": "fake.nodeid",                        # Need to overriden
        "metadata_topic": "MONROE.META",
        "verbosity": 3,                                 # 0 = "Mute", 1=error, 2=Information, 3=verbose
        "resultdir": "/monroe/results/",
        "socketwait": 60,                                # Number of seconds to wait for data on the socket
        "disabled_interfaces": ["lo",
                        "metadata",
                        # "eth0"
                        ],
        "interfaces_without_metadata": ["eth0",
                                        "wlan0"],       # Manual metadata on these IF
        }

# Helper functions
import os.path
def is_monroe_node():
    return os.path.isfile('/nodeid')
def is_vagrant_vm():
    return os.path.exists('/sent_from_host')

def check_if(ifname):
    """Check if interface is up and have got an IP address."""
    return (ifname in netifaces.interfaces() and
            netifaces.AF_INET in netifaces.ifaddresses(ifname))

def get_ip(ifname):
    """Get IP address of interface."""
    # TODO: what about AFINET6 / IPv6?
    return netifaces.ifaddresses(ifname)[netifaces.AF_INET][0]['addr']

def get_netmask(ifname):
    return netifaces.ifaddresses(ifname)[netifaces.AF_INET][0]['netmask']

"""
:param netmask: netmask ip addr (eg: 255.255.255.0)
:return: prefix length (cidr number) (eg: 24)
"""
def netmask_to_cidr(netmask):
    masklen = sum([bin(int(x)).count("1") for x in netmask.split(".")])
    # masklen = 0
    # s = mask.split(".")
    # for piece in s:
    #     if piece == 0:
    #         return masklen
    #     masklen += bin(int(piece)).count("1")
    return masklen

def get_default_gateway():
    gws=netifaces.gateways()
    pp.pprint(gws)
    if netifaces.AF_INET in gws['default']:
        LKL_CONFIG['gateway']  = gws['default'][netifaces.AF_INET][0]
        return True
    else:
        # print("No IPv4 default gateway!")
        return False

    # if netifaces.AF_INET6 in gws['default']:
    #     LKL_CONFIG['gateway6'] = gws['default'][netifaces.AF_INET6][0]


def time_now():
    return time.time()


def create_LKL_config():
    # Load config and check so we have all variables we need
    try:
        if is_monroe_node() or is_vagrant_vm():
            print("ignoring eth0")
            EXPCONFIG['disabled_interfaces'].append("eth0")
        disabled_interfaces = EXPCONFIG['disabled_interfaces']
        if_without_metadata = EXPCONFIG['interfaces_without_metadata']
    except Exception as e:
        print("Missing expconfig variable {}".format(e))
        raise e


    for ifname in netifaces.interfaces():

        # Skip disabled interfaces
        if ifname in disabled_interfaces:
            if EXPCONFIG['verbosity'] > 1:
                print("Interface is disabled, skipping {}".format(ifname))
            continue

        if 'enabled_interfaces' in EXPCONFIG and not ifname in EXPCONFIG['enabled_interfaces']:
            if EXPCONFIG['verbosity'] > 1:
                print("Interface is not enabled, skipping {}".format(ifname))
            continue

        # Interface is not up we just skip that one
        if not check_if(ifname):
            if EXPCONFIG['verbosity'] > 1:
                print("Interface is not up {}".format(ifname))
            continue

        ip      = get_ip(ifname)
        netmask = get_netmask(ifname)
        masklen = netmask_to_cidr(get_netmask(ifname))

        gw_ip ="undefined"
        # gw_ip6="undefined"
        for g in netifaces.gateways()[netifaces.AF_INET]:
            if g[1] == ifname:
                gw_ip = g[0]
                break
        # or use: ip route get 8.8.8.8 from srcIP

        LKL_IF = {  "type"   : "raw",
                    "param"  : ifname,
                    "ip"     : ip,
                    "masklen": masklen,
                    "ifgateway": gw_ip,
                }
        LKL_CONFIG["interfaces"].append(LKL_IF)

        gw = get_default_gateway()
        if not gw:
            LKL_CONFIG['gateway'] = LKL_CONFIG["interfaces"][0]["ifgateway"]

    pp.pprint(LKL_CONFIG)

    with open('lkl-config.json', 'w') as fp:
        json.dump(LKL_CONFIG, fp, indent=4)


def create_socket(topic, port):
    print("Trying to create a new socket on {}".format(port))
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect (port)
    socket.setsockopt(zmq.SUBSCRIBE, '')
    print("New socket created listening on topic : {}".format(topic))
    return socket


def create_exp_process(meta_info, expconfig, cmd):
    print("Create experiment process")
    process = Process(target=run_exp, args=(meta_info, expconfig, cmd, ))
    process.daemon = False
    return process

def run_exp(meta_info, expconfig, cmd):
    """Seperate process that runs the experiment and collect the ouput.
    """
    cfg = expconfig.copy()
    output = None

    my_env = os.environ.copy()
    my_env["LKL_HIJACK_CONFIG_FILE"] = "./lkl-config.json"

    try:
        # if cfg['verbosity'] > 2:
        print("running '{}'".format(cmd))

        # p = Popen(cmd, stdin=PIPE, stdout=PIPE, env=my_env)
        # output = p.communicate(input=json.dumps(cfg).encode())[0]

        # catching stdout in realtime from subprocess
        p = Popen(cmd, stdout=PIPE, stderr=STDOUT, env=my_env)
        for line in iter(p.stdout.readline, b''):
            print(">>> " + line.rstrip())

        # msg = json.loads(output.decode(), object_pairs_hook=OrderedDict)
        # msg["ErrorCode"] = p.returncode

        if cfg['verbosity'] > 2:
            print("Result: {}".format(output))
        # if not DEBUG:
        #     save_output(data=cfg, msg=output, tstamp=cfg['timestamp'], outdir=cfg['resultdir'])
    except Exception as e:
        if cfg['verbosity'] > 0:
            print ("Execution or parsing failed for "
                   # "command : {}, "
                   # "config : {}, "
                   "output : {}, "
                   "error: {}").format(output, e)


# if __name__ == '__main__':

if not DEBUG:
    try:
        with open(CONFIGFILE) as configfd:
            EXPCONFIG.update(json.load(configfd))
    except Exception as e:
        print("Cannot retrieve config: {}".format(e))
        # sys.exit(1)
else:
    EXPCONFIG['zmqport'] = "tcp://localhost:5556"
    EXPCONFIG['metadata_topic'] = ""
    EXPCONFIG['verbosity'] = 3
    EXPCONFIG['socketwait'] = 10



create_LKL_config()

cfg = EXPCONFIG
meta_info = None

# Ok we have some information lets start the experiment script
if cfg['verbosity'] > 1:
    print("Starting experiment")
cfg['timestamp'] = start_time_exp = time.time()

cmds = []
## plain iperf3
# cmd = ["./iperf3", "-Vd", "--no-delay", "-t" "3",
#          "-c", "130.104.230.97", "-p", "5201"]
cmds.append(["lkl-hijack", "ip", "addr"])
cmds.append(["lkl-hijack", "ip", "route get 8.8.8.8"])
# cmds.append(["lkl-hijack", "ip", "route show table 4"])
cmds.append(["lkl-hijack", "ping", "-i 0.2","-c2","8.8.8.8"])
# cmds.append(["lkl-hijack", "./iperf3_profile", "-Vd", "--no-delay", "-t", "3",
#          "-c", "130.104.230.97", "-p", "5201"])

# exp_process = create_exp_process(meta_info, cfg, cmd)
# exp_process.start()

for cmd in cmds:
    run_exp(meta_info, cfg, cmd)


def metadata(meta_ifinfo, ifname, expconfig):
    timeout=60
    time_start = time.time()

    socket = create_socket(EXPCONFIG['metadata_topic'],
                           EXPCONFIG['zmqport'])

    # Initialize poll set
    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)

    while time_now() - time_start < timeout:
        try:
            (topic, msgdata) = socket.recv().split(' ', 1)
        except zmq.ContextTerminated:
            # The context is terminated, lets try to open another socket
            # If that fails, abort
            if EXPCONFIG['verbosity'] > 0:
                print ("Error: ContextTerminated")
            socket = create_socket(EXPCONFIG['metadata_topic'],
                                   EXPCONFIG['zmqport'],
                                   EXPCONFIG['verbosity'])
            poller = zmq.Poller()
            poller.register(socket, zmq.POLLIN)
            continue
        except zmq.ZMQError as e:
            # Other zmq Error just log and quit
            if EXPCONFIG['verbosity'] > 0:
                print("Error: ZMQ failed with : {}".format(e))
            raise


        print topic
        print msgdata
        print("\n")
        sys.stdout.flush()

        if topic.startswith("MONROE.META.DEVICE.MODEM."):
            msg = json.loads(msgdata)
            # Some zmq messages do not have nodeid information so I set it here
            msg['NodeId'] = EXPCONFIG['nodeid']
