#!/usr/bin/evn python

import socket

TCP_IP = '128.8.126.92'
TCP_PORT = 8080
BUFFER_SIZE = 64
ping_count = 0

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(1)

conn, addr = s.accept()
print 'Connection address:', addr
for i in range(30):
  while 1:
    data = conn.recv(BUFFER_SIZE)
    if not data : break
    print '{0} bytes from {1}: ping_num={2}'.format(BUFFER_SIZE,addr,ping_count)
    conn.send(data)
    ping_count += 1
conn.close()

conn, addr = s.accept()
print 'Connection address:', addr
for i in range(30):
  while 1:
    data = conn.recv(BUFFER_SIZE)
    if not data : break
    print '{0} bytes from {1}: ping_num={2}'.format(BUFFER_SIZE,addr,ping_count)
    conn.send(data)
    ping_count += 1
conn.close()

conn, addr = s.accept()
print 'Connection address:', addr
for i in range(30):
  while 1:
    data = conn.recv(BUFFER_SIZE)
    if not data : break
    print '{0} bytes from {1}: ping_num={2}'.format(BUFFER_SIZE,addr,ping_count)
    conn.send(data)
    ping_count += 1
conn.close()

