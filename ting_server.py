import SocketServer
import sys
import datetime
from struct import pack, unpack

response = pack('!c', '!')

class MyTCPHandler(SocketServer.BaseRequestHandler):
    """
    The RequestHandler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def handle(self):
        self.data = self.request.recv(1)
        print("[{0}] Connected to {1}".format(str(datetime.datetime.now()),str(self.client_address[0])))
        while (self.data and unpack('!c',self.data) != 'X'):
            self.request.sendall(response) # echo
            print(self.data)
            self.data = self.request.recv(1)
        print("Connection from client closed.")
            

if __name__ == "__main__":
    TCP_IP = '128.8.126.92'
    TCP_PORT = int(sys.argv[1])
    print("TCP server listening on port " + str(TCP_PORT))
    # Create the server, binding to localhost on port TCP_PORT
    server = SocketServer.TCPServer((TCP_IP, TCP_PORT), MyTCPHandler)
    server.allow_reuse_address = True
    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down...")
        pass
    finally:
        server.server_close()
