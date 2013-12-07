Measuring Latency Between Tor Nodes 
===

Measures the latency between two given tor (exit) nodes.

Mini-Project for CMSC396H (Fall 2013) with group members Emily Kowalcyzk, Scott DellaTorre, and Brent Schlotfeldt, and mentor Dave Levin. 

Requirements
---------
- Python 2.7 or higher
- Stem module (stem.torproject.org/)
- Patched version of Tor (patches found at https://bitbucket.org/ra_/tor-rtt)
- SocksiPy
- Socks
- Access to server with public IP address

Usage
-----
Patch tor using the patch files from TOR-RTT

Check the given torrc file, and make any necessary changes to directories or ports

Start tor in the repos root directory by running:

		tor -f torrc

Open up client.py, and verify the that the ports at the top match the ports tor and socks are using on your system

Run server.py on your server (e.g. bluepill.cs.umd.edu)

Run client.py on your local machine. When asked, enter the name of two tor exit nodes, which can be found on http://torstatus.blutmagie.de
