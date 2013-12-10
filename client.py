#!/usr/bin/evn python

#
# Created by Frank Cangialosi on 12/6/13.
#

import time
import socket
import socks 
from stem import CircStatus, OperationFailed, InvalidRequest, InvalidArguments
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

TCP_IP = '128.8.126.92' # bluepill ip
TCP_PORT = 8080 # port bluepill is listening on
BUFFER_SIZE = 64 # arbitrary
SOCKS_HOST = "127.0.0.1" # localhost                                            
SOCKS_PORT = 9050 # port connecting with tor socks
SOCKS_TYPE = socks.PROXY_TYPE_SOCKS5
CONTROLLER_PORT = 9051 # port for connecting with stem controller
cid = 0 # Circuit ID, to be updated later when circuit created
sxyd = [0 for x in range(30)]

# Attaches a specific circuit to the given stream (event)
def attach_stream(event):
    try:
        controller.attach_stream(event.id, cid)
    except (OperationFailed, InvalidRequest), error:
        if str(error) in (('Unknown circuit %s' % cid), "Can't attach stream to non-open " + "origin circuit"):
            # If circuit is already closed, close stream too.
            controller.close_stream(event.id)
        else:
            raise

# An event listener, called whenever StreamEvent status changes
def probe_stream(event):
    if event.status == 'CLOSED':
        self._stream_finished.set()
    elif event.status == 'NEW' and event.purpose == 'USER':
        attach_stream(event)

# Check list of circuits to see if one with the exist same relays already exists
def check_for_circuit(relay_a,relay_b):
    for circ in controller.get_circuits():
        if (circ.path[0][1] == relay_a and circ.path[1][1] == relay_b):
            print "found!"
            return circ.id
    return -1

def check_params():
    for arg in sys.argv:
        if arg == "-r":
            return True
    return False

def get_valid_nodes():
    files = os.listdir(".")
    exits = []
    for name in files:
        if name == "exits.txt":
            print "Found list of active relays!"
            f = open(name)
            for line in f.readlines():
                exits.append(line.strip().split()[0])
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
            exits.append(line.strip().split()[0])
        f.close()
    return exits

############################################################
############################################################

# Look for any command line arguments
random = check_params()

# Connect to Stem controller, set configs, and authenticate 
controller = Controller.from_port(port = CONTROLLER_PORT)
controller.authenticate()
controller.set_conf("__DisablePredictedCircuits", "1")
controller.set_conf("__LeaveStreamsUnattached", "1")

# Select the nodes randomly if flag is set or manually if not
if random:
    exits = get_valid_nodes()
    relay_a = choice(exits)
    relay_b = choice(exits)
    while (relay_a == relay_b):
        relay_b = choice(exits)
    print "Chose relays %s and %s" % (relay_a, relay_b)
else:
    # Create circuit from given relays, or find cid of old one 
    #    if cicuit with same relays already exists
    print "Note that BOTH nodes must be exit relays"
    relay_a = raw_input("Name or fingerprint of first relay: ")
    relay_b = raw_input("Name or fingerprint of second relay: ")
    print "\n"

# Check if the circuit with those nodes exists already, if so, use it, if not, create a new circuit
result = check_for_circuit(relay_a,relay_b)
print result
if result is -1:
    # Block until the circuit is successfully built
    cid = controller.new_circuit([relay_a,relay_b], await_build=True)
else:
    cid = result

# Add stream prober 
controller.add_event_listener(probe_stream, EventType.STREAM)

# Tell socks to use tor as a proxy 
socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, SOCKS_HOST, SOCKS_PORT)
socket.socket = socks.socksocket
sock = socks.socksocket()

# Connect to bluepill server at port 8080
try:
    sock.connect((TCP_IP, TCP_PORT))

    for i in range(30):
        # Name of the exit relay that bluepill will connect to
        controller.get_streams()[0].circ_id
        MESSAGE = str(controller.get_circuit(cid).path[0][1])
        print '{0} bytes to {1}: ping_num={2}'.format(BUFFER_SIZE,TCP_IP,i)
        # Take measurement of time when message is sent
        start_time = time.time()

        # Send name of exit node to bluepill 
        sock.send(MESSAGE)

        # Store data recieved from bluepill
        data = sock.recv(BUFFER_SIZE)

        # Take measurement of time when response is recieved
        end_time = time.time()
        sxyd[i] = (end_time-start_time)
    sock.close()

    np = array(sxyd)
    print "Echo from Bluepill: ", data
    print "Total round trip time data: " # total round trip time to bluepill and back
    print "Average: ", numpy.mean(np)*1000, "ms"
    print "Min: ", numpy.min(np)*1000, "ms"
    print "Max: ", numpy.max(np)*1000, "ms"
    print "Stddev: ", numpy.std(np)*1000, "ms"
except TypeError as exc:
    print "Failed to conect using the given circuit.", exc

