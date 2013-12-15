import SocketServer
import re
import subprocess

class MyTCPHandler(SocketServer.BaseRequestHandler):
    """
    The RequestHandler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """
    NUM_PINGS = 20

    def ping(self, ip):
        pings = []
        regex = re.compile("(\d+.\d+) ms")
        cmd = ['ping', '-c',str(self.NUM_PINGS),ip]
        p = subprocess.Popen(cmd,stdout=subprocess.PIPE)
        for line in p.stdout.readlines():
            ping = regex.findall(line)
            if ping != []:
                pings.append(ping[0])
        p.wait()
        pings = pings[:-1]
        return pings


    def handle(self):
        self.data = self.request.recv(1024).strip()
        if('ping' in self.data):
            print "Pinging", self.data[5:], "(X)"
            result = self.ping(self.data[5:])
            print result
            self.request.sendall(str(result))
        elif('echo' in self.data):
            print "Getting ready to echo"
            self.request.sendall("OKAY")
            for i in range(self.NUM_PINGS):
                self.data = self.request.recv(64).strip()
                print "Recieved ting", i, "from", self.client_address[0]
                print self.data
                self.request.sendall("echo")

if __name__ == "__main__":
    TCP_IP = '128.8.126.92'
    TCP_PORT = 8080
    # Create the server, binding to localhost on port 9999
    server = SocketServer.TCPServer((TCP_IP, TCP_PORT), MyTCPHandler)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
