#!/bin/sh

#  fprints.py
#  
#
#  Created by Emily Kowalczyk on 12/6/13.
#


# IMPORTANT: must change the client's torrc file to include: FetchUselessDescriptors 1 & DownloadExtraInfo 1
# NOTE: if exit nodes need to "allow single hop", comment out the current conditional on line 42 and uncomment line 34 and 43


from stem.exit_policy import ExitPolicy, MicroExitPolicy
from stem.descriptor.remote import DescriptorDownloader
from stem.descriptor.server_descriptor import ServerDescriptor
import sys

verbose = False

downloader = DescriptorDownloader()

non_exit_nodes = []
exit_nodes = []

f1 = open("exit_nodes.txt", 'w')
f2 = open("non_exit_nodes.txt", 'w')

for arg in sys.argv:
    if arg == '-v':
        verbose = True

if verbose:
    print "--------------------------------------------------------------"
    print "                  ACTIVE RELAY INFO                           "
    print "--------------------------------------------------------------"
    
try:
    for desc in downloader.get_server_descriptors().run():
        extra = downloader.get_extrainfo_descriptors(str(desc.fingerprint)).run()
        location = extra[0].geoip_db_digest
        bluepill = desc.exit_policy.can_exit_to("128.8.126.92", 8080)
        #singlehop = desc.allow_single_hop_exits
        
        relay_info = "Nickname: %s; Fingerprint: %s; Bluepill?: %s; Location: %s; " % (desc.nickname, desc.fingerprint, bluepill, location)
        exit_policy = "Exit Policy details: $%s" % (desc.exit_policy)
        if verbose:
            print relay_info
        
        non_exit_nodes.append(str(desc.fingerprint))
        f2.write("%s\n" % str(desc.fingerprint))
        
        if bluepill:
        #if bluepill && singlehop:
            exit_nodes.append(str(desc.fingerprint))
            f1.write("%s\n" % str(desc.fingerprint))
        
        if verbose:
            print "--------------------------------------------------------------"

except Exception as exc:
    print "Unable to retrieve the consensus: %s" % exc

finally:
    f1.close
    f2.close
    print "Found ", len(non_exit_nodes), " total non-exit nodes."
    print "Found ", len(exit_nodes), "total exit nodes."






