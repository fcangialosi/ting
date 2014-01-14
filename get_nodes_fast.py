import json
import urllib2
import re
import datetime
import time
import argparse
import os.path
import sys

regex = re.compile('(\d+)-(\d+)')
ip_regex = re.compile('(\d+.\d+.\d+.\d+):\d+')
filenum = 1

parser = argparse.ArgumentParser(description='Pull most recent list of valid Tor exit nodes for the given host and port from torstatus.blutmagie.de')
parser.add_argument('-dp', '--destination-port', help="Specify destination port.",default='6667')
parser.add_argument('-di', '--destination-ip', help="Specify destination ip address.", default='128.8.126.92')
args = vars(parser.parse_args())    

ip_underscore = args['destination_ip'].replace(".", "_")
now = datetime.datetime.now()
date_underscore = "{0}_{1}_{2}".format(now.month, now.day, now.year)

current_dir = os.path.dirname(os.path.realpath(__file__))
first_sub = current_dir + "/data/nodes/%s" % ip_underscore
second_sub = current_dir + "/data/nodes/%s/%s" % (ip_underscore, date_underscore)
if(not os.path.exists(first_sub)):
    os.makedirs(first_sub)
if(not os.path.exists(second_sub)):
    os.makedirs(second_sub)

filename = current_dir + "/data/nodes/{0}/{1}/validexits_{2}_{3}.txt".format(ip_underscore, date_underscore, args['destination_port'], filenum)

while(os.path.exists(filename)):
    filenum = filenum + 1
    filename = current_dir + "/data/nodes/{0}/{1}/validexits_{2}_{3}.txt".format(ip_underscore, date_underscore, args['destination_port'], filenum)


destination_ip = args['destination_ip']
destination_port = args['destination_port']

f = open(filename, 'w+')
f.write("# List of all valid exit nodes to {0}:{1}\n".format(destination_ip, destination_port))
f.write("# Download began at {0}\n".format(datetime.datetime.now()))
f.write("# FINGERPRINT, IP, ROUTER_NAME\n\t(LATITUDE, LONGITUDE), COUNTRY\n\t(Optional) UNIVERSITY: HOST_NAME, UNIVERSITY_NAME\n\n")

data = json.load(urllib2.urlopen('https://onionoo.torproject.org/details?type=relay&running=true&fields=nickname,fingerprint,or_addresses,exit_policy_summary,latitude,longitude,flags,host_name,as_name'))

def allows_exiting(exit_policy):
	if not 'accept' in exit_policy:
		if 'reject' in exit_policy:
			for ports in exit_policy['reject']:
				r = regex.search(ports)
				if r and int(r.groups()[0]) <= int(destination_port) <= int(r.groups()[1]):
					return False
			return True
	if destination_port in exit_policy['accept']:
		return True
	for ports in exit_policy['accept']:
		r = regex.search(ports)
		if r and int(r.groups()[0]) <= int(destination_port) <= int(r.groups()[1]):
			return True
	return False

counter = 0
start_time = time.time()
for relay in data['relays']:
	if not 'Exit' in relay['flags']:
		continue
	if not allows_exiting(relay['exit_policy_summary']):
		continue
	fingerprint = "NONE"
	ip = "NONE"
	nickname = "NONE"
	lat = "NONE"
	log = "NONE"
	country = "NONE"
	host_name = "NONE"
	as_name = "NONE"
	if('fingerprint' in relay):
		fingerprint = relay['fingerprint']
	if('or_addresses' in relay):
		r = ip_regex.search(relay['or_addresses'][0])
		ip = r.groups()[0]
	if('nickname' in relay):
		nickname = relay['nickname']
	if('latitude' in relay):
		lat = relay['latitude']
	if('longitude' in relay):
		lon = relay['longitude']
	if('country' in relay):
		country = relay['country']
	if('host_name' in relay):
		host_name = relay['host_name']
	if('as_name' in relay):
		as_name = relay['as_name']
	f.write("{0}, {1}, {2}\n\t({3},{4}), {5}\n".format(fingerprint.lower(), ip, nickname, lat, lon, country))
	if('.edu' in host_name.lower() or 'university' in as_name.lower() or 'institue' in as_name.lower()):
		f.write('\tUNIVERSITY: {0}, {1}\n'.format(as_name,host_name))
	counter = counter + 1

end_time = time.time()

print("Took {0} seconds to download {1} valid exit nodes".format(str(end_time-start_time),counter))
f.close()