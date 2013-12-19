#!/usr/bin/evn python

#
# Created by Frank Cangialosi on 12/6/13.
#
from __future__ import print_function
import time
import socket
import socks 
from stem import CircStatus, OperationFailed, InvalidRequest, InvalidArguments, CircuitExtensionFailed
from stem.control import Controller, EventType
from pprint import pprint
import sys
from random import choice
import os
import subprocess
from pprint import pprint 
from numpy import array
import numpy
import inspect
import re
import datetime
import argparse

def setup_argparse():
    parser = argparse.ArgumentParser(description='Ting is like ping, but instead meausres round-trip times between two indivudal nodes in the Tor network.')
    parser.add_argument('-a','--check-accuracy', help='Determine accuracy of measurements by changing only W and Z for a consistent X and Y.', action='store_true')
    parser.add_argument('-n', '--num-pairs', help="Number of pairs to test. Defaults to infinite", default=100)
    parser.add_argument('-dp', '--destination-port', help="Specify destination port.",default=8080)
    parser.add_argument('-di', '--destination-ip', help="Specify destination ip address.", default='128.8.126.92')
    parser.add_argument('-p', '--num-tings', help="Specify the number of times to ting each circuit.", default=20)
    parser.add_argument('-c', '--check-one', help="Quickly run for a single X and Y.", nargs=2)
    parser.add_argument('-o', '--output-file', help="Specify where to save log file.", default="ting_data.txt")
    parser.add_argument('-d', '--data-dir', help="Specify a different home directory from which to read and write data", default="../data/")
    return parser

parser = setup_argparse()
args = vars(parser.parse_args())

TCP_IP = args['destination_ip']# bluepill ip
TCP_PORT = args['destination_port'] # port bluepill is listening on
BUFFER_SIZE = 64 # arbitrary
SOCKS_HOST = "127.0.0.1" # localhost                                            
SOCKS_PORT = 9050 # port connecting with tor socks
SOCKS_TYPE = socks.PROXY_TYPE_SOCKS5
CONTROLLER_PORT = 9051 # port for connecting with stem controller
NUM_TINGS = args['num_tings']
NUM_PAIRS = args['num_pairs']
CHECK_ONE = args['check_one']
ACCURACY = args['check_accuracy']
OUTPUT = args['output_file']
DATA_DIR = args['data_dir']
curr_cid = 0 # Circuit ID for entire circuit, to be updated later when circuit created
sub_one = 0 # Circuit ID for first sub circuit
sub_two = 0 # Circuit ID for second sub circuit
swxyzd = [0 for x in range(int(NUM_TINGS))] # holds all ting times for entire circuit containing all 4 relays
swxd = [0 for x in range(int(NUM_TINGS))] # holds all ting times for first half circuit
syzd = [0 for x in range(int(NUM_TINGS))] # holds all ting times for second half circuit
 

class NotReachableException(Exception):
    pass



# Tell socks to use tor as a proxy 
def setup_proxy():
    socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, SOCKS_HOST, SOCKS_PORT)
    socket.socket = socks.socksocket
    sock = socks.socksocket()
    return sock

# Attaches a specific circuit to the given stream (event)
def attach_stream(event):
    try:
        controller.attach_stream(event.id, curr_cid)
    except (OperationFailed, InvalidRequest), error:
        if str(error) in (('Unknown circuit %s' % curr_cid), "Can't attach stream to non-open " + "origin circuit"):
            # If circuit is already closed, close stream too.
            controller.close_stream(event.id)
        else:
            raise

# An event listener, called whenever StreamEvent status changes
def probe_stream(event):
    if event.status == 'NEW' and event.purpose == 'USER':
        attach_stream(event)

def make_title():
    print("\n-------------------------")
    print("     _____ _         \n    |_   _|_|___ ___ \n      | | | |   | . |\n      |_| |_|_|_|_  |\n                |___|")
    print("\n------ Version 1.0 ------")

    print("Socks on port {0}".format(SOCKS_PORT))
    print("Tor Controller on port {0}".format(CONTROLLER_PORT))
    print("Destination is {0} on port {1}".format(TCP_IP,TCP_PORT))
    if(ACCURACY):
        print("Checking {0} pairs of W and Z for consistency of X and Y".format(NUM_PAIRS))
    elif(CHECK_ONE):
        print("Checking a single pair: {0} | {1}".format(CHECK_ONE[0],CHECK_ONE[1]))
    else:
        print("Calculating measurements for all combinations of {0} random nodes".format(NUM_PAIRS))
        print("{0} pairs in total.".format(int(NUM_PAIRS)*(int(NUM_PAIRS)-1)/2))
    print("Tinging each circuit {0} times with a {1}-byte packet".format(NUM_TINGS,BUFFER_SIZE))
    print("Writing all output to: {0} in {1}".format(OUTPUT,DATA_DIR))
    print("---------------------------")



# Check list of circuits to see if one with the exist same relays already exists
def check_for_circuit(relays):
    for circ in controller.get_circuits():
        found = True
        if len(circ.path) == len(relays):
            for i in range(len(circ.path)-1):
                if (circ.path[i][1] != relays[i]):
                    found = False
                if i == len(relays)-1:
                    break
            if found:
                return circ.id
    return -1

# Computes typical ping stats for a given array of ting times
def get_stats(rtt):
    np = array(rtt)
    _avg = numpy.mean(np)
    _min = numpy.min(np)
    _max = numpy.max(np)
    _med = numpy.median(np)
    _std = numpy.std(np)
    return [_avg,_min,_max,_med,_std]

def pick_relays(n, exits):
    relays = [0 for x in range(n)]
    for i in range(len(relays)):
        temp = choice(exits)
        while(temp in relays or temp == 'Unnamed'):
            temp = choice(exits)
        relays[i] = temp
    return relays

def pick_n_more_relays(n,existing,exits):
    relays = [0 for x in range(n)]
    for i in range(len(relays)):
        temp = choice(exits)
        while(temp in relays or temp == 'Unnamed' or temp in existing):
            temp = choice(exits)
        relays[i] = temp
    return relays

def build_random_circuit(controller):
    fails = 0
    print("Choosing nodes...")
    while True:
        try:
            relays = pick_relays(4, exits.keys())

            global curr_cid
            curr_cid = create_circuit([relays[0],relays[1],relays[2],relays[3]])
           
            global sub_one
            sub_one = create_circuit([relays[0],relays[1]])

            global sub_two
            sub_two = create_circuit([relays[2],relays[3]])

            print("Took {0} trials to find valid nodes.".format(fails))
            print("Circuits created successfully. CID is", curr_cid)

            return [relays[0],relays[1],relays[2],relays[3]]
        except (InvalidRequest,CircuitExtensionFailed) as exc:
            fails = fails+1

def create_circuit(relays):
    # Check if the circuit with those nodes exists already, if so, use it, if not, create a new circuit
    result = check_for_circuit(relays)
    if result is -1:
        print("No circuit currently exists with those relays, creating...")
        # Block until the circuit is successfully built
        cid = controller.new_circuit(relays, await_build=True)
    else:
        cid = result
    return cid

# Given an ip or address, uses standard ping, and returns a 4-element array of the min,avg,max,stddev
def ping(ip):
    pings = []
    regex = re.compile("(\d+.\d+) ms")
    cmd = ['ping', '-c',str(NUM_TINGS),ip]
    p = subprocess.Popen(cmd,stdout=subprocess.PIPE)
    for line in p.stdout.readlines():
        ping = regex.findall(line)
        if ping != [] and "DUP" not in line:
            pings.append(float(ping[0]))
    p.wait()
    pings = pings[:-1]
    return pings

def get_valid_nodes():
    files = os.listdir(DATA_DIR)
    exits = {}
    for name in files:
        if name == "valid_exits.txt":
            f = open(DATA_DIR + "valid_exits.txt")
            for line in f.readlines():
                relay = line.strip().split()
                exits[relay[0]] = relay[1]
            f.close()
    if not exits:
        print("=== Could not find list of exit nodes, downloading...")
        cmd = ['python', 'scrape_exits.py']
        p = subprocess.Popen(cmd,stdout=subprocess.PIPE)
        for line in p.stdout:
            print(line)
        p.wait()
        print("=== Download complete!")
        f = open(name)
        for line in f.readlines():
            relay = line.strip().split()
            exits[relay[0]] = relay[1]
        f.close()
    return exits

def ting(t, sock):
    # Connect to bluepill server at port 8080
    try:
        sock.connect((TCP_IP, TCP_PORT))
        sock.send("echo")
        data = sock.recv(BUFFER_SIZE)
        if data == "OKAY":
            for i in range(int(NUM_TINGS)):
                # Name of the exit relay that bluepill will connect to
                MESSAGE = str(i)
                print('{0} bytes to {1}: ping_num={2}'.format(BUFFER_SIZE,TCP_IP,i), end='\r')
                sys.stdout.flush()
                # Take measurement of time when message is sent
                start_time = time.time()

                # Send name of exit node to bluepill 
                sock.send(MESSAGE)

                # Store data recieved from bluepill
                data = sock.recv(BUFFER_SIZE)

                # Take measurement of time when response is recieved
                end_time = time.time()
                t[i] = (end_time-start_time)*1000
        sock.close()
        print('Finished {0} pings to {1}'.format(NUM_TINGS,TCP_IP))
        return t
    except TypeError as exc:
        print("Failed to conect using the given circuit.", exc)

def extract_ping_data(data):
    regex = re.compile("(\d+.\d+)")
    temp = regex.findall(data)
    pings = []
    for x in temp:
        pings.append(float(x))
    return pings

def calculate_r_xy(relays):
    global curr_cid 

    # Tell bluepill to ping X
    print("----- Pinging X from D -----")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((TCP_IP, TCP_PORT))
    s.send("ping {0}".format(exits[relays[1]]))
    resp = s.recv(1024)
    r_xd = extract_ping_data(resp)
    print("R_XD:", r_xd)
    print("--- ping statistics ---")
    print('rtt avg/min/max/med/stddev =', get_stats(r_xd))
    s.close()

    print("----- Pinging Y from S -----")
    r_sy = ping(exits[relays[2]])
    fails = 0
    while(len(r_sy) != int(NUM_TINGS)):
        if(len(r_sy) < 1 or fails > 4):
            raise NotReachableException
        print("== Not enough pings")
        fails = fails + 1
        r_sy = ping(exits[relays[2]])
    print("R_SY:", r_sy)
    print('--- ping statistics ---')
    print('rtt avg/min/max/med/stddev =', get_stats(r_sy))

    # Add stream prober 
    listen = controller.add_event_listener(probe_stream, EventType.STREAM)
    
    # Use Tor as proxy
    sock = setup_proxy()

    print("------ Ting S,W,X,Y,Z ------")
    t_total = ting(swxyzd, sock)
    print("T_TOTAL:", t_total)
    print('--- ting statistics ---')
    print('rtt avg/min/max/med/stddev =', get_stats(t_total))

    curr_cid = sub_one
    controller.remove_event_listener(listen)
    listen = controller.add_event_listener(probe_stream, EventType.STREAM)
    sock = setup_proxy()
    print("------- Ting S,W,X,D -------")
    t_wx = ting(swxd, sock)
    print("T_WX:", t_wx)
    print('--- ting statistics ---')
    print('rtt avg/min/max/med/stddev =', get_stats(t_wx))

    curr_cid = sub_two
    controller.remove_event_listener(listen)
    listen = controller.add_event_listener(probe_stream, EventType.STREAM)
    sock = setup_proxy()
    print("------- Ting S,Y,Z,D -------")
    t_yz = ting(syzd, sock)
    print("T_YZ:", t_yz)
    print('--- ting statistics ---')
    print('rtt avg/min/max/med/stddev =', get_stats(t_yz))

    r_xy = [0 for x in range(int(NUM_TINGS))]
    for i in range(len(t_total)):
        r_xy[i] = t_total[i] - t_wx[i] - t_yz[i] + r_sy[i] + r_xd[i]

    print("--- Ting between {0} and {1} ---".format(relays[1],relays[2]))
    print("R_XY", r_xy)
    print("STATS: ", get_stats(r_xy))


    f = open((DATA_DIR + "ting_pair_data_{0}_{1}_{2}_{3}_{4}".format(d.month,d.day,d.year,d.hour,d.minute)), 'a')
    f.write("--- Ting between {0} and {1} on {2} ---\n".format(relays[1],relays[2],str(datetime.datetime.now())))
    f.write("==== R_XY: %s\n" % str(get_stats(r_xy)))
    f.write("Circuit:\n%s(%s)\n%s(%s)\n%s(%s)\n%s(%s)\n" % (relays[0], exits[relays[0]], relays[1], exits[relays[1]], relays[2], exits[relays[2]], relays[3], exits[relays[3]]))
    f.write("T_TOTAL: %s\n" % str(get_stats(t_total)))
    f.write("T_WX: %s\n" % str(get_stats(t_wx)))
    f.write("T_YZ: %s\n" % str(get_stats(t_yz)))
    f.write("R_SY: %s\n" % str(get_stats(r_sy)))
    f.write("R_XD: %s\n" % str(get_stats(r_xd)))
    f.close()



############################################################
############################################################

make_title()

global controller
# Connect to Stem controller, set configs, and authenticate 
controller = Controller.from_port(port = CONTROLLER_PORT)
controller.authenticate()
controller.set_conf("__DisablePredictedCircuits", "1")
controller.set_conf("__LeaveStreamsUnattached", "1")

# Load list of possible exit nodes
exits = get_valid_nodes()

count = 0 
# Choose 4 node circuit of W, X, Y, and Z
if(ACCURACY):
    xy = pick_relays(2, exits.keys())
    full_set = []
    for i in range(len(NUM_PAIRS)):
        print('ay')
else:
    full_set = []
    node_set = pick_relays(int(NUM_PAIRS), exits.keys())
    for i in range(len(node_set)):
        for j in range(len(node_set))[i+1:]:
            full_set.append((node_set[i],node_set[j]))

    total = len(full_set)

    d = datetime.datetime.now()
    f = open(DATA_DIR + "all_pairs_{0}_{1}_{2}_{3}_{4}.txt".format(d.month,d.day,d.year,d.hour,d.minute), 'w')
    f.write("--- {0}\n".format(str(d)))
    f.write("--- Measuring tings between all possible combinations\n")
    f.write("--- {0} total pairs\n".format(int(NUM_PAIRS)*(int(NUM_PAIRS)-1)/2))
    f.write("{0} node set: ".format(NUM_PAIRS))
    f.write(str(full_set))
    f.close()

    for pair in full_set:
        try: 
            count = count + 1
            xy = [pair[0], pair[1]]
            wz = pick_n_more_relays(2,xy,exits.keys())
            wxyz = (wz[0],xy[0],xy[1],wz[1])
            
            print("===========================")
            print("Tinging pair {0}/{1}".format(count,total))
            print("W: %s (%s)\nX: %s (%s)\nY: %s (%s)\nZ: %s (%s)" % (wxyz[0], exits[wxyz[0]], wxyz[1], exits[wxyz[1]], wxyz[2], exits[wxyz[2]], wxyz[3], exits[wxyz[3]]))
            print("===========================")

            start = time.time()
            calculate_r_xy(wxyz)
            end = time.time()

            print("TOTAL TIME ELAPSED: {0} seconds\n".format(end-start))
        except Exception as exc:
            print ("===== ERROR: {0}".format(exc))


