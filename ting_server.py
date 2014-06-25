import socket 
import sys
import datetime
from struct import pack, unpack

response = pack('!c','!')

host = '' 
port = int(sys.argv[1])
backlog = 1
size = 1

print("TCP Server listening on port " + str(port)) 

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
s.bind((host,port)) 
s.listen(backlog) 

while 1: 
    client, address = s.accept() 
    print("Connection accepted from " + str(address))
    data = client.recv(size)
    while (data and (unpack('!c',data) != 'X')): 
        client.send(data) 
        data = client.recv(size) 
    client.close()
    print("Connection closed.")
    sys.stdout.flush()
