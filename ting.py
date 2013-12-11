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
    _avg = numpy.mean(np)*1000
    _min = numpy.min(np)*1000
    _max = numpy.max(np)*1000
    _med = numpy.median(np)*1000
    _std = numpy.std(np)*1000
    return [_avg,_min,_max,_std]

# Given two arrays with the same length, subtracts all elements in b from a
def subtract_arrays(a,b):
    for i in range(len(a)):
        a[i] -= b[i]
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
    regex = re.compile("(\d+.\d+)")
    cmd = ['ping', '-c',str(NUM_PINGS),ip]
    p = subprocess.Popen(cmd,stdout=subprocess.PIPE)
    line = p.stdout.readlines()[-1]
    stats = regex.findall(line)
    p.wait()
    return stats

def get_valid_nodes():
    files = os.listdir(".")
    exits = {}
    for name in files:
        if name == "exits.txt":
            print "Found list of active relays!"
            f = open(name)
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

def ting(t, sock, msg):
    # Connect to bluepill server at port 8080
    try:
        sock.connect((TCP_IP, TCP_PORT))
        for i in range(NUM_PINGS):
            # Name of the exit relay that bluepill will connect to
            print '{0} bytes to {1}: ping_num={2}'.format(BUFFER_SIZE,TCP_IP,i)
            # Take measurement of time when message is sent
            start_time = time.time()

            # Send name of exit node to bluepill 
            sock.send(msg)

            # Store data recieved from bluepill
            data = sock.recv(BUFFER_SIZE)

            # Take measurement of time when response is recieved
            end_time = time.time()
            t[i] = (end_time-start_time)
        sock.close()

        return get_stats(t), data
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

# Choose 4 node circuit of W, X, Y, and Z
relays = choose_relays(controller)

# Add stream prober 
listen = controller.add_event_listener(probe_stream, EventType.STREAM)

sock = setup_proxy()

print exits[relays[1]]
print "======================================"
print "======== Tinging Full Circuit ========"
print "======================================"
t_total, results = ting(swxyzd, sock, exits[relays[1]])
print t_total
print results

print "======================================"
print "========== Pinging W from S =========="
print "======================================"
r_sw = ping(exits[relays[0]])
print r_sw

print "==== Waiting for bluepill to finish ping from D to X"
time.sleep(30)

print exits[relays[3]]
global curr_cid 
curr_cid = sub_one
controller.remove_event_listener(listen)
listen = controller.add_event_listener(probe_stream, EventType.STREAM)
sock = setup_proxy()
print "==========================================="
print "======== Tinging Sub Circuit (W,X) ========"
print "==========================================="
t_wx, results = ting(swxd, sock, exits[relays[3]])
print t_wx
print results

print "======================================"
print "========== Pinging Y from S =========="
print "======================================"
r_sy = ping(exits[relays[0]])
print r_sy

print "==== Waiting for bluepill to finish ping from D to Z"
time.sleep(30)

global curr_cid
curr_cid = sub_two
controller.remove_event_listener(listen)
listen = controller.add_event_listener(probe_stream, EventType.STREAM)
sock = setup_proxy()
print "==========================================="
print "======== Tinging Sub Circuit (Y,Z) ========"
print "==========================================="
t_yz,results = ting(syzd, sock, "empty")
print t_yz
print results

t_xy = subtract_arrays(subtract_arrays(t_total,t_wx),t_yz) 

print "======== Final AVG/MIN/MAX/STD ========"
print t_xy


