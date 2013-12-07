#!/usr/bin/evn python

import socket

TCP_IP = '128.8.126.92'
TCP_PORT = 8080
BUFFER_SIZE = 20

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(1)

conn, addr = s.accept()
print 'Connection address:', addr
while 1:
    data = conn.recv(BUFFER_SIZE)
    if not data : break
    print "Name of Relay B: ", data
    conn.send(data)
conn.close()
