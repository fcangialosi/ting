#!/usr/bin/evn python

#
# Created by Frank Cangialosi on 12/6/13.
#

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


TCP_IP = '128.8.126.92' # bluepill ip
TCP_PORT = 8080 # port bluepill is listening on
BUFFER_SIZE = 64 # arbitrary
SOCKS_HOST = "127.0.0.1" # localhost                                            
SOCKS_PORT = 9050 # port connecting with tor socks
SOCKS_TYPE = socks.PROXY_TYPE_SOCKS5
CONTROLLER_PORT = 9051 # port for connecting with stem controller
NUM_PINGS = 20
curr_cid = 0 # Circuit ID for entire circuit, to be updated later when circuit created
sub_one = 0 # Circuit ID for first sub circuit
sub_two = 0 # Circuit ID for second sub circuit
swxyzd = [0 for x in range(NUM_PINGS)] # holds all ting times for entire circuit containing all 4 relays
swxd = [0 for x in range(NUM_PINGS)] # holds all ting times for first half circuit
syzd = [0 for x in range(NUM_PINGS)] # holds all ting times for second half circuit
 
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

# Given two arrays with the same length, subtracts all elements in b from a
def subtract_arrays(a,b):
    for i in range(len(a)):
        a[i] -= b[i]
    return a

# Given two arrays with the same length, adds all elements in b to the corresponding element in a
def add_arrays(a,b):
    for i in range(len(a)):
        a[i] += float(b[i])
    return a

def choose_relays(controller):
    while True:
        try:
            relays = exits.keys()
            relay_w = choice(relays)
            while (relay_w == 'Unnamed'):
                relay_w = choice(relays)

            relay_x = choice(relays)
            while (relay_w == relay_x or relay_x == 'Unnamed'):
                relay_x = choice(relays)

            relay_y = choice(relays)
            while(relay_y == relay_w or relay_y == relay_x or relay_y == 'Unnamed'):
                relay_y = choice(relays)
    
            relay_z = choice(relays)
            while(relay_z == relay_w or relay_z == relay_x or relay_z == relay_y or relay_z == 'Unnamed'):
                relay_z = choice(relays)

            print "Trying W,X,Y,Z: %s, %s, %s, %s" % (relay_w, relay_x, relay_y, relay_z)
            print "%s, %s, %s, %s" % (exits[relay_w], exits[relay_x], exits[relay_y],exits[relay_z])
            global curr_cid
            curr_cid = create_circuit([relay_w,relay_x,relay_y,relay_z])
            print "Circuit created successfully. CID is", curr_cid

            global sub_one
            print "==== Creating W,X"
            sub_one = create_circuit([relay_w,relay_x])
            print "==== First sub-circuit created successfully. CID is", sub_one

            global sub_two
            print "==== Creating Y,Z"
            sub_two = create_circuit([relay_y,relay_z])
            print "==== Second sub-circuit created successfully. CID is", sub_two

            print "==\n== All circuits created sucessfully...\n=="
            return [relay_w,relay_x,relay_y,relay_z]
        except (InvalidRequest,CircuitExtensionFailed) as exc:
            print "==", exc

def create_circuit(relays):
    # Check if the circuit with those nodes exists already, if so, use it, if not, create a new circuit
    result = check_for_circuit(relays)
    if result is -1:
        print "No circuit currently exists with those relays, creating..."
        # Block until the circuit is successfully built
        cid = controller.new_circuit(relays, await_build=True)
    else:
        cid = result
    return cid

# Given an ip or address, uses standard ping, and returns a 4-element array of the min,avg,max,stddev
def ping(ip):
    pings = []
    regex = re.compile("(\d+.\d+) ms")
    cmd = ['ping', '-c',str(NUM_PINGS),ip]
    p = subprocess.Popen(cmd,stdout=subprocess.PIPE)
    for line in p.stdout.readlines():
        print line
        ping = regex.findall(line)
        if ping != []:
            pings.append(float(ping[0]))
    p.wait()
    pings = pings[:-1]
    return pings

def get_valid_nodes():
    files = os.listdir("./../data")
    exits = {}
    for name in files:
        if name == "valid_exits.txt":
            print "Found list of active relays!"
            f = open("./../data/valid_exits.txt")
            for line in f.readlines():
                relay = line.strip().split()
                exits[relay[0]] = relay[1]
            f.close()
    if not exits:
        print "Could not find list of exit nodes"
        print "Downloading list"
        print "....."
        cmd = ['python', 'scrape_exits.py']
        p = subprocess.Popen(cmd,stdout=subprocess.PIPE)
        for line in p.stdout:
            print line
        p.wait()
        print "Download complete!"
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
            for i in range(NUM_PINGS):
                # Name of the exit relay that bluepill will connect to
                MESSAGE = str(i)
                print '{0} bytes to {1}: ping_num={2}'.format(BUFFER_SIZE,TCP_IP,i)
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
        return t
    except TypeError as exc:
        print "Failed to conect using the given circuit.", exc


############################################################
############################################################

# Connect to Stem controller, set configs, and authenticate 
controller = Controller.from_port(port = CONTROLLER_PORT)
controller.authenticate()
controller.set_conf("__DisablePredictedCircuits", "1")
controller.set_conf("__LeaveStreamsUnattached", "1")

exits = get_valid_nodes()
while 1:
    try:
        # Choose 4 node circuit of W, X, Y, and Z
        relays = choose_relays(controller)

        print "=================================="
        print "======== Pinging X from D ========"
        print "=================================="
        print "== Connecting to Bluepill"
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((TCP_IP, TCP_PORT))
        print "== Sending IP of X to Bluepill"
        s.send("ping {0}".format(exits[relays[1]]))
        print "Waiting for ping results..."
        dpings = s.recv(1024)
        regex = re.compile("(\d+.\d+)")
        temp = regex.findall(dpings)
        r_xd = []
        for x in temp:
            r_xd.append(float(x))
        print "R_XD", r_xd
        print "== Recieved ping results from Bluepill"
        print '--- ting statistics ---'
        print NUM_PINGS, 'packets transmitted'
        print 'rtt avg/min/max/med/stddev =', get_stats(r_xd)
        s.close()

        print "=================================="
        print "======== Pinging Y from S ========"
        print "=================================="
        r_sy = ping(exits[relays[2]])
        while(len(r_sy) != 20):
            print "== Not enough pings"
            r_sy = ping(exits[relays[2]])
        print '--- ping statistics ---'
        print NUM_PINGS, 'packets transmitted'
        print 'rtt avg/min/max/med/stddev =', get_stats(r_sy)

        # Add stream prober 
        listen = controller.add_event_listener(probe_stream, EventType.STREAM)

        sock = setup_proxy()

        print "============================================="
        print "======== Tinging D with Full Circuit ========"
        print "============================================="
        t_total = ting(swxyzd, sock)
        print '--- ting statistics ---'
        print NUM_PINGS, 'packets transmitted'
        print 'rtt avg/min/max/med/stddev =', get_stats(t_total)

        global curr_cid 
        curr_cid = sub_one
        controller.remove_event_listener(listen)
        listen = controller.add_event_listener(probe_stream, EventType.STREAM)
        sock = setup_proxy()
        print "=================================================="
        print "======== Tinging D with Sub Circuit (W,X) ========"
        print "=================================================="
        t_wx = ting(swxd, sock)
        print '--- ting statistics ---'
        print NUM_PINGS, 'packets transmitted'
        print 'rtt avg/min/max/med/stddev =', get_stats(t_wx)

        global curr_cid
        curr_cid = sub_two
        controller.remove_event_listener(listen)
        listen = controller.add_event_listener(probe_stream, EventType.STREAM)
        sock = setup_proxy()
        print "=================================================="
        print "======== Tinging D with Sub Circuit (Y,Z) ========"
        print "=================================================="
        t_yz = ting(syzd, sock)
        print '--- ting statistics ---'
        print NUM_PINGS, 'packets transmitted'
        print 'rtt avg/min/max/med/stddev =', get_stats(t_yz)

        #t_xy = subtract_arrays(subtract_arrays(t_total,t_wx),t_yz) 
        #t_xy = add_arrays(add_arrays(t_xy,r_sy),r_xd)
        #t_xy = get_stats(t_xy)

        r_xy = [0 for x in range(NUM_PINGS)]
        for i in range(len(t_total)):
            r_xy[i] = t_total[i] - t_wx[i] - t_yz[i] + r_sy[i] + r_xd[i]

        print "=================================="
        print "=================================="
        print "--- Ting between {0} and {1} ---".format(relays[1],relays[2])
        print "R_XY", r_xy
        print "STATS: ", get_stats(r_xy)
        print "=================================="
        print "=================================="
        print ""
        print "=================================="
        print "=================================="

        f = open("../data/correct.txt", "a")
        f.write("--- Ting between {0} and {1} on {2} ---\n".format(relays[1],relays[2],str(datetime.datetime.now())))
        f.write("==== R_XY: %s\n" % str(get_stats(r_xy)))
        f.write("Circuit:\n%s(%s)\n%s(%s)\n%s(%s)\n%s(%s)\n" % (relays[0], exits[relays[0]], relays[1], exits[relays[1]], relays[2], exits[relays[2]], relays[3], exits[relays[3]]))
        f.write("T_TOTAL: %s\n" % str(get_stats(t_total)))
        f.write("T_WX: %s\n" % str(get_stats(t_wx)))
        f.write("T_YZ: %s\n" % str(get_stats(t_yz)))
        f.write("R_SY: %s\n" % str(get_stats(r_sy)))
        f.write("R_XD: %s\n" % str(get_stats(r_xd)))
        f.close()
    except KeyboardInterrupt as exc:
        print exc
        print "Exiting safely."
        break
    except Exception as exc:
        print "================================"
        print "======== ERROR OCCURRED ========"
        print exc
        print "======== ERROR OCCURRED ========"
        print "================================"

    