#!/bin/sh

#  fprints.py
#  
#
#  Created by Emily Kowalczyk on 12/6/13.
#  Modified by Scott DellaTorre on 12/8/13.

# Usage: python fprints.py [-v] [-fp] [port]
# -v (verbose): generate verbose output
# -fp (find ports): determine the number of exit relays available for # 					bluepill at each port
# -sh (single hop): require exit relays to allow single hop
# port: when the -fp flag is not set, you can optionally specify which port to find exit/non-exit relays for (default 8080)


# IMPORTANT: must change the client's torrc file to include: FetchUselessDescriptors 1 & DownloadExtraInfo 1

from stem.exit_policy import ExitPolicy, MicroExitPolicy
from stem.descriptor.remote import DescriptorDownloader
from stem.descriptor.server_descriptor import ServerDescriptor
import sys

BLUEPILL_IP = "128.8.126.92"

find_ports = False
req_single_hop = False
verbose = False

downloader = DescriptorDownloader()

port = 8080

for arg in sys.argv[1:]:
	if arg == '-v':
		verbose = True
	elif arg == '-fp':
		find_ports = True
	elif arg == '-sh':
		req_single_hop = True
	else:
		port = int(arg)

if verbose:
	print "--------------------------------------------------------------"
	print "                  ACTIVE RELAY INFO                           "
	print "--------------------------------------------------------------"

if (find_ports):

	f3 = open("ports.txt", 'w')

	fps_by_port = list()
	for i in range (0, 65535):
		fps_by_port.append((i, list()))
		
	descs = downloader.get_server_descriptors().run()

	for count in range (0, len(descs)-1):
	
		if verbose and count * 100 / len(descs) > (count - 1) * 100 / len(descs):
			print str((count * 100 / len(descs))) + "% complete."

		desc = descs[count]
		
		if not desc.exit_policy.is_exiting_allowed():
			continue
			
		ports = list()
		for i in range (0, 65535):
			ports.append(-1)

		for rule in desc.exit_policy._get_rules():
			
			if rule.is_port_wildcard():
				min = 1
				max = 65535
				test_port = None
			else:
				min = rule.min_port
				max = rule.max_port
				test_port = min
		
			if rule.is_match(BLUEPILL_IP, test_port):

				for i in range (min, max):
					if ports[i] == -1:
						ports[i] = 1 if rule.is_accept else 0
						
		
		for i in range (0, 65535):
			if (ports[i] == 1):
				fps_by_port[i][1].append(desc.fingerprint)

	sorted_fps = sorted(fps_by_port, key=lambda descs: len(descs[1]), reverse = True)

	for i in range (0, 65535):
		f3.write("port %d: %d matches\n" % (sorted_fps[i][0], len(sorted_fps[i][1])))
		#for desc in sorted_fps[i]:
		#	f3.write(" %s" % desc)
		#f3.write("\n")
		
	f3.close

else:

	f1 = open("exit_nodes.txt", 'w')
	f2 = open("non_exit_nodes.txt", 'w')
	
	non_exit_nodes = []
	exit_nodes = []

	for desc in downloader.get_server_descriptors().run():
		try:
			#extra = downloader.get_extrainfo_descriptors(str(desc.fingerprint)).run()
			#location = extra[0].geoip_db_digest

			bluepill = desc.exit_policy.can_exit_to(BLUEPILL_IP, port)
			single_hop = desc.allow_single_hop_exits
			if single_hop and not req_single_hop:
				print "Found Single Hop Router!!!"
				relay_info = "Nickname: %s; Fingerprint: %s; Bluepill?: %s;  " % (desc.nickname, desc.fingerprint, bluepill)
				exit_policy = "Exit Policy details: $%s" % (desc.exit_policy)
				if verbose:
					print relay_info

			non_exit_nodes.append(str(desc.fingerprint))
			f2.write("%s\n" % str(desc.fingerprint))

			if bluepill and ((not req_single_hop) or single_hop):
				#if bluepill && singlehop:
				exit_nodes.append(str(desc.fingerprint))
				f1.write("%s\n" % str(desc.fingerprint))

			if verbose:
				print "--------------------------------------------------------------"
		except Exception as exc:
			print "Unable to retrieve the consensus: %s" % exc
			
	print "Found ", len(non_exit_nodes), " total non-exit nodes."
	print "Found ", len(exit_nodes), "total exit nodes."

	f1.close
	f2.close
