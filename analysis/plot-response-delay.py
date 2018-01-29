#! /usr/bin/env python

# INPUT:
#   ./results/{date-time-id}/

# OUTPUT:
# plot request-response delay of siri-like app

from __future__ import print_function
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
                    help="Directory which stores results (exp ID)",
                    default="15918/")
parser.add_argument('--pdf', '-p',
                    help="Save figures as PDF. By default we save as PNG only",
                    action='store_true',
                    default="False")


args = parser.parse_args()

exp_dir = args.expdir

test_run_list = []

inl_ip    ="130.104.230.97"
linode_ip ="139.162.73.214"

delays = {"Inlab": {"TCP":[], "MPTCP":[]},
          "Japan": {"TCP":[], "MPTCP":[]}}


def get_gps_speed(file):
    speed = []
    with open(file) as metadata:
        for line in metadata:
            try:
                meta = json.loads(line)
                if "Speed" in meta and meta["Speed"] != None:
                    speed.append(meta["Speed"])
            except ValueError:
                pass
        if speed:
            avg_speed = sum(speed)/len(speed)
            print ("speed: " + str(round(avg_speed,1)))
            return avg_speed
        else:
            return None

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
        print (rssi)
    return rssi

def get_delays_from_iperf_output(file, rssi, speed, primary_iface, type):

    with open(file) as output_file:
        server = "Inlab"

        for line in output_file:

            if linode_ip in line:
                server = "Japan"

            # get first interface name
            if (primary_iface == None) and ("ifparams:" in line):
                pattern = re.compile(r"ifparams:\s*(\S+)")
                if pattern.search(line) != None:
                    str = pattern.search(line).group(0)
                    primary_iface = str.split(":")[1]
                    print (primary_iface)
                    break

            if "Request-response delay:" in line:
                delaystr = line.split(':')[1].strip()
                print("delay: "+ delaystr+'\t', end="")
                delay = float(delaystr)

                signal = 0
                if (primary_iface != None) and primary_iface in rssi:
                    signal = rssi[primary_iface]
                else:
                    print (" primary_iface not found ")
                    if not rssi:
                        print (" RSSI not found ")
                        return
                    signal = rssi[rssi.keys()[0]]
                delays[server][type].append((delay, signal, speed))
        print("")

def get_primary_iface(file):
    iface = None
    with open(file) as f:
        for line in f:
            pattern = re.compile(r"IF1=\s*(\S+)")
            if pattern.search(line) != None:
                str = pattern.search(line).group(0)
                iface = str.split("=")[1]
                print (iface)
                break
    return iface

def load_test_run_data():
    print("loading data from json")

    for test_run in sorted(os.listdir(exp_dir)):
        test_run_path = os.path.join(exp_dir, test_run)
        if not os.path.isdir(test_run_path):
            continue
        print("test_run:" + test_run)
        os.chdir(test_run_path)
        primary_iface = None

        for file in os.listdir("./"):
            if file.startswith("metadata.log"):
                rssi = get_SignalStrength(file)
                speed = get_gps_speed(file)
            if file.startswith("container.log"):
                primary_iface = get_primary_iface(file)

        if primary_iface == None:
            print ("container.log not found?")

        for file in os.listdir("./"):
            if file.startswith("output-201"):
                print("mptcp:")
                get_delays_from_iperf_output(file, rssi, speed, primary_iface, type="MPTCP")
            if file.startswith("output-tcp"):
                print("tcp:")
                get_delays_from_iperf_output(file, rssi, speed, primary_iface, type="TCP")

        os.chdir("../..")

    print("loading done")

################
####  Plot  ####

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress

def plot_delay_vs_signal(datatype, server, legend='inside'):
    fig, ax = plt.subplots()
    # ax.set_facecolor(BACKGROUND_COLOR)

    for type in ["TCP","MPTCP"]:
        data = delays[server][type]
        # x = np.arange(0, len(values), 1)
        signals = [v[1] for v in data]
        values = [v[0] for v in data]
        print(str(type) + " average of "+str(len(values)) +": "+ str(sum(values)/len(values)))

        # get the correlation and p-value (confidence)
        # print np.corrcoef(values, signals)[0, 1]
        print(linregress(values, signals))

        ax.scatter(signals, values, label= type + " Delay")

    plt.legend(loc='best')
    plt.xlabel('RSSI of primary interface (dBm)')
    plt.ylabel(datatype + ' (' +'second'+ ')')

    plt.title(server + " server")
    plt.grid()
    # plt.show()
    if (args.pdf == True):
        fig.savefig('Request-Response-Delay-'+ str(server)+'-Scatter.pdf', bbox_inches='tight')
    else:
        fig.savefig('Request-Response-Delay-'+ str(server)+'-Scatter.png', bbox_inches='tight')

def plot_delay_vs_speed(datatype, server, legend='inside'):
    fig, ax = plt.subplots()

    for type in ["TCP","MPTCP"]:
        data = delays[server][type]
        values = [v[0] for v in data]
        speed = [v[2] for v in data]
        if all(v is None for v in speed):
            print("no gps speed info found")
            return

        ax.scatter(speed, values, label= type + " Delay")

    plt.legend(loc='best')
    plt.xlabel('Node speed (km/h)')
    plt.ylabel(datatype + ' (' +'second'+ ')')

    plt.title(server + " server")
    plt.grid()
    if (args.pdf == True):
        fig.savefig('Delay-vs-Speed-'+ str(server)+'-Scatter.pdf', bbox_inches='tight')
    else:
        fig.savefig('Delay-vs-Speed-'+ str(server)+'-Scatter.png', bbox_inches='tight')

def plot_cdf(datatype, server, legend='inside'):
    fig, ax = plt.subplots()

    for type in ["TCP","MPTCP"]:
        data = delays[server][type]
        values = [v[0] for v in data]
        # alternatively: cdf plot in one line
        # plt.plot(np.sort(values), np.linspace(0, 1, len(values), endpoint=False))
        sorted_ = np.sort(values)
        yvals = np.arange(len(sorted_))/float(len(sorted_) -1)
        ax.plot(sorted_, yvals, label= type + " Delay", lw=1.5)


    plt.legend(loc='best')
    plt.ylabel('CDF')
    plt.xlabel(datatype + ' (' +'second'+ ')')
    plt.ylim([0,1])

    plt.title(server + " server")
    plt.grid()
    # plt.show()
    if (args.pdf == True):
        fig.savefig('Request-Response-Delay-'+ str(server)+'-CDF.pdf', bbox_inches='tight')
    else:
        fig.savefig('Request-Response-Delay-'+ str(server)+'-CDF.png', bbox_inches='tight')

load_test_run_data()
os.chdir(exp_dir)

for server in delays:
    # print delays[server],
    print("")
    plot_delay_vs_signal('Request-Response Delay', server)
    plot_delay_vs_speed('Request-Response Delay', server)
    plot_cdf('Request-Response Delay', server)
