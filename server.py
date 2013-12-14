#!/usr/bin/evn python

import socket
import subprocess
import re

TCP_IP = '128.8.126.92'
TCP_PORT = 8080
BUFFER_SIZE = 128
ping_count = 0
NUM_PINGS = 20

def ping(ip):
    pings = []
    regex = re.compile("(\d+.\d+) ms")
    cmd = ['ping', '-c',str(NUM_PINGS),ip]
    p = subprocess.Popen(cmd,stdout=subprocess.PIPE)
    for line in p.stdout.readlines():
        ping = regex.findall(line)
        if ping != []:
            pings.append(int(float(ping[0])))
    p.wait()
    pings = pings[:-1]
    return pings

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(1)

while 1:
    conn, addr = s.accept()
    print 'Connection address:', addr
    while 1:
        data = conn.recv(BUFFER_SIZE)
        print data
        if not data : break
        print "=========================="
        print "==== Pinging X from D ===="
        print "=========================="
        results = ping(data)
        print results
        conn.send(str(results))
    conn.close()

    conn, addr = s.accept()
    print 'Connection address:', addr
    for i in range(NUM_PINGS):
        while 1:
            data = conn.recv(BUFFER_SIZE)
            if not data : break
            print '{0} bytes from {1}: ping_num={2}'.format(BUFFER_SIZE,addr,ping_count)
            conn.send(data)
            ping_count += 1
    conn.close()

    conn, addr = s.accept()
    print 'Connection address:', addr
    for i in range(NUM_PINGS):
        while 1:
            data = conn.recv(BUFFER_SIZE)
            if not data : break
            print '{0} bytes from {1}: ping_num={2}'.format(BUFFER_SIZE,addr,ping_count)
            conn.send(data)
            ping_count += 1
    conn.close()

    conn, addr = s.accept()
    print 'Connection address:', addr
    for i in range(NUM_PINGS):    
        while 1:
            data = conn.recv(BUFFER_SIZE)
            if not data : break
            print '{0} bytes from {1}: ping_num={2}'.format(BUFFER_SIZE,addr,ping_count)
            conn.send(data)
            ping_count += 1
    conn.close()
