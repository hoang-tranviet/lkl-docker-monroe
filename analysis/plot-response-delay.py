#! /usr/bin/env python

# INPUT:
#   ./results/{date-time-id}/

# OUTPUT:
# plot request-response delay of siri-like app

import os
import pprint
import argparse
import re

BACKGROUND_COLOR="0.9"

# try to use simplejson - which is generally 3 times faster than original json package
try:
    import simplejson as json
except ImportError:
    import json

parser = argparse.ArgumentParser(description="plot iperf test results from json")
parser.add_argument('--expdir', '-d',
                    help="Directory to store results",
                    default="15918/")

args = parser.parse_args()

exp_dir = args.expdir

test_run_list = []

inl_ip    ="130.104.230.97"
linode_ip ="139.162.73.214"

delays = {"inl": [], "linode":[] }

def get_SignalStrength(file):
    rssi = {}
    with open(file) as metadata:
        for line in metadata:
            try:
                meta = json.loads(line)
                if "RSSI" in meta:
                    rssi[meta["InternalInterface"]] = meta["RSSI"]
            except ValueError:
                pass
        print rssi
    return rssi

def get_delays_from_iperf_output(file, rssi):
    with open(file) as output_file:
        server = "inl"
        for line in output_file:

            if linode_ip in line:
                server = "linode"

            iface = None
            # get first interface name
            if "-m" in line:
                pattern = re.compile(r"-m \s*(\S+)")
                ifaces = pattern.search(line).group(0)
                iface = ifaces.split(",")[0]

            if "Request-response delay:" in line:
                delaystr = line.split(':')[1].strip()
                # print("get delay: "+ delaystr)
                delay = float(delaystr)

                signal = 0
                if (iface != None) and iface in rssi:
                    signal = rssi[iface]
                else:
                    signal = rssi[rssi.keys()[0]]

                delays[server].append((delay, signal))

def load_test_run_data():
    print("loading data from json")

    for test_run in sorted(os.listdir(exp_dir)):
        print("test_run:" + test_run)
        test_run_dir = exp_dir+test_run
        os.chdir(test_run_dir)

        for file in os.listdir("./"):
            if file.startswith("metadata.log"):
                rssi = get_SignalStrength(file)

            if file.startswith("output-"):
                get_delays_from_iperf_output(file, rssi)

        os.chdir("../..")

    print("loading done")

################
####  Plot  ####

import numpy as np
import matplotlib.pyplot as plt

def plot_graph(datatype, server, legend='inside'):
    fig, ax = plt.subplots()
    ax.set_facecolor(BACKGROUND_COLOR)

    # x = np.arange(0, len(values), 1)
    signals = [v[1] for v in delays[server]]
    values = [v[0] for v in delays[server]]
    print(len(values),len(signals))

    ax.scatter(signals, values, label='delay')

    plt.legend(loc='best')
    plt.xlabel('RSSI')
    plt.ylabel(datatype + ' (' +'second'+ ')')

    plt.grid()
    plt.show()


load_test_run_data()

for server in delays:
    print delays[server],
    print("")
    plot_graph('delay', server)
