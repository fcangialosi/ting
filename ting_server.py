import SocketServer
import re
import subprocess
import sys

class MyTCPHandler(SocketServer.BaseRequestHandler):
    """
    The RequestHandler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """
    num_pings = 20
    ping_ip_regex = re.compile("ping (\d+.\d+.\d+.\d+) \d+")
    ping_num_regex = re.compile("ping \d+.\d+.\d+.\d+ (\d+)")
    ping_data_regex = re.compile("(\d+.\d+) ms")
    echo_num_regex = re.compile("echo (\d+)")

    def ping(self, ip):
        pings = []
        cmd = ['ping', '-c',str(self.num_pings),ip]
        p = subprocess.Popen(cmd,stdout=subprocess.PIPE)
        for line in p.stdout.readlines():
            ping = self.ping_data_regex.findall(line)
            if ping != []:
                pings.append(ping[0])
        p.wait()
        pings = pings[:-1]
        return pings


    def handle(self):
        self.data = self.request.recv(1024).strip()

        if('ping' in self.data):
            self.num_pings = int(self.ping_num_regex.findall(self.data)[0])
            ip = self.ping_ip_regex.findall(self.data)[0]

            print "Pinging", ip, "(X)", self.num_pings, "times..."
            result = self.ping(ip)
            print "Data:", result

            self.request.sendall(str(result))

        elif('echo' in self.data):
            self.num_pings = int(self.echo_num_regex.findall(self.data)[0])

            print "Getting ready to echo"
            self.request.sendall("OKAY")

            for i in range(1, self.num_pings+1):
                self.data = self.request.recv(64).strip()
                print("\r"),
                print("Recieved ting " + str(i) + " from " + self.client_address[0]),
                sys.stdout.flush()
                self.request.sendall("echo")
            print("\n")

if __name__ == "__main__":
    TCP_IP = '128.8.126.92'
    TCP_PORT = 6667
    print("TCP server listening on port " + str(TCP_PORT))
    # Create the server, binding to localhost on port TCP_PORT
    server = SocketServer.TCPServer((TCP_IP, TCP_PORT), MyTCPHandler)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()

