Ting: Latency Between Tor Nodes
===

The Ting project aims to calculate real latency times between any two relays on the Tor network, without having control over them. 

***

Requirements
---------
- Python 2.7+
- Stem module (stem.torproject.org/)
- Patched version of Tor (included in tor/)
- SocksiPy (included in libs/)
- SOCKS
- Access to server with public IP address

Setup
-----
Install the patched version of tor found in tor/. You may also need to install the openssl, libevent 
and zlib libraries if you do not already have them on your computer. 

Check the given torrc file in tor/, and make any necessary changes to directories or ports

Start tor by running the following command within tor/:

		tor -f torrc

Run ting_server.py on your server (e.g. bluepill.cs.umd.edu)

Running Ting
------------

Once the above setup is complete, run Ting with

		python ting_client.py MODE

Ting has four primary modes (there is no default, you must specify one):

- check: This mode allows you to quickly check a single iteration of a single circuit. Using this mode requires that you specify the pair X and Y using the `-p X_RELAY Y_RELAY` command line option. W and Z are selected at random.
- pairs: This mode allows you to collect data on all pairs in a subset of the list of Tor nodes. The size of this subset defaults to 100, but can be changed with the `-ss SUBSET_SIZE` option. Ting will randomly choose `SUBSET_SIZE` nodes from the list of relays, and then iterates through all possible pairs between them (a simple gaussian sum).
- rerun: Given the path to a Ting output file wih `-r RERUN_FILE_PATH`, this mode reruns Ting with the exact same settings required to produce that output file. There is no default, the file path must be specified. 
- verify: This mode keeps X and Y consistent, while randomly changing W and Z. In theory, the calculation for X and Y should be about the same each time, as our method of calculation is independent of any other hosts in the circuit. By default, it picks a random pair of X and Y to use at the beginning, but X and Y can be specified using the `-p X_RELAY Y_RELAY` option.

A few important command line options worth noting:
- `-o` optimizes Ting by keeping a cache of Ping results, to prevent re-pinging the exact same nodes. 
- `-nt' specifies the number of times to Ting each node or circuit. This is essentially equivalent to ping's `-c` option

Although there are other command line options available to specify ports, destination, etc, these are quite simple and can be found by running 

	python ting_client.py -h

	

An typical example run of the Ting client might be:

	python ting_client.py pairs -np 10 -nt 100 -o -v

This iterates through all possible pairs of 10 randomly selected nodes in the list of valid relays, Tinging each circuit 100 times. It also caches ping results and prints  information about data and streams verbosely.


Known Issues
------------
- Sometimes circuit creation hangs indefinitely

Credits
-------
Mentors:
- Dave Levin
- Neil Spring
