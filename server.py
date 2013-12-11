#!/usr/bin/evn python

import socket
import os
import sys
import subprocess

TCP_IP = '128.8.126.92'
TCP_PORT = 8080
BUFFER_SIZE = 64
ping_count = 0
NUM_PINGS = 30

def ping(ip):
    regex = re.compile("(\d+.\d+)")
    cmd = ['ping', '-c',str(NUM_PINGS),ip]
    p = subprocess.Popen(cmd,stdout=subprocess.PIPE)
    line = p.stdout.readlines()[-1]
    stats = regex.findall(line)
    p.wait()
    return stats

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(1)

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

print "===="
print "======== Pinging", data, "========"
print "===="
r_xd = str(ping(data))

conn, addr = s.accept()
print 'Connection address:', addr
for i in range(NUM_PINGS):
  while 1:
    data = conn.recv(BUFFER_SIZE)
    if not data : break
    print '{0} bytes from {1}: ping_num={2}'.format(BUFFER_SIZE,addr,ping_count)
    if i == (NUM_PINGS-1):
        conn.send(r_xd)
    else:
        conn.send(data)
    ping_count += 1
conn.close()

print "===="
print "======== Pinging", data, "========"
print "===="
r_zd = str(ping(data))

conn, addr = s.accept()
print 'Connection address:', addr
for i in range(NUM_PINGS):
  while 1:
    data = conn.recv(BUFFER_SIZE)
    if not data : break
    print '{0} bytes from {1}: ping_num={2}'.format(BUFFER_SIZE,addr,ping_count)
    if i == (NUM_PINGS-1):
        conn.send(r_zd)
    else:
        conn.send(data)
    ping_count += 1
conn.close()

