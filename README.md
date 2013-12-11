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

Download the csv of all valid tor exit nodes from torstatus.blutmagie.de and place it in the repos root directory

Run

		python scrape_exits.py

Check the given torrc file, and make any necessary changes to directories or ports

Start tor in the repos root directory by running:

		tor -f torrc

Open up ting.py, and verify the that the ports at the top match the ports tor and socks are using on your system

Run server.py on your server (e.g. bluepill.cs.umd.edu)

Run ting with

		python ting

By default, it will choose 4 random valid exit nodes from the scrape_exits list.

More advanced command line options specifying nodes and other parameters to come. 
