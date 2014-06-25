from __future__ import print_function
import time
import socket
from stem import CircStatus, OperationFailed, InvalidRequest, InvalidArguments, CircuitExtensionFailed
from stem.control import Controller, EventType
import sys
from random import choice, shuffle
import os
import subprocess
from pprint import pprint 
import multiprocessing
import numpy
import Queue
import inspect
import re
import datetime
import argparse
import traceback
import os.path
from os.path import join, dirname, isfile
sys.path.append(join(dirname(__file__), 'libs'))
from SocksiPy import socks 
import json
import random
import signal
import urllib2
from struct import pack, unpack

ting_version = "1.0"
destination_ip = '128.8.126.92'
buffer_size = 64
socks_host = '127.0.0.1'
socks_type = socks.PROXY_TYPE_SOCKS5
relay_names = ['w','x','y','z']

def log(msg):
	print("{0} {1}".format(datetime.datetime.now(), msg))
	sys.stdout.flush()

class NotReachableException(Exception):
	"""
	Exception raised when a host is not responding to pings

    Attributes:
		msg -- details about the connection being made
		func  -- function where error occured
		dest -- (if ping, destination ip to which ping failed)
	"""
	def __init__(self, msg, func, dest):
		self.msg = msg
		self.func = func
		self.dest = dest

class CircuitConnectionException(Exception):
	"""
	Exception raised when we are unable to communicate with the 
	the desintation through a given circuit

	May be caused if socket.connect() fails, 
	or if socket.recv() times out

	"""

	def __init__(self, msg, circuit, exc):
		self.msg = msg
		self.circuit = circuit
		self.exc = exc


def allows_exiting(exit_policy, destination_port):
	exit_regex = re.compile('(\d+)-(\d+)')
	if not 'accept' in exit_policy:
		if 'reject' in exit_policy:
			for ports in exit_policy['reject']:
				r = exit_regex.search(ports)
				if r and int(r.groups()[0]) <= int(destination_port) <= int(r.groups()[1]):
					return False
			return True
	if destination_port in exit_policy['accept']:
		return True
	for ports in exit_policy['accept']:
		r = exit_regex.search(ports)
		if r and int(r.groups()[0]) <= int(destination_port) <= int(r.groups()[1]):
			return True
	return False

def get_valid_nodes(destination_port):
	log("Downloading current list of relays and finding best exit nodes... (this may take a few seconds)")
	data = json.load(urllib2.urlopen('https://onionoo.torproject.org/details?type=relay&running=true&fields=nickname,fingerprint,or_addresses,exit_policy_summary,latitude,longitude,flags,host_name,as_name,observed_bandwidth'))

	all_relays = {}
	all_exits = {}
	good_exits = {}

	for relay in data['relays']:
		if('or_addresses' in relay):
			ip = relay['or_addresses'][0].split(':')[0]
			relay.pop("or_addresses", None)
			if(allows_exiting(relay['exit_policy_summary'],destination_port)):
				relay.pop("exit_policy_summary", None)
				all_exits[ip] = relay
				#if('observed_bandwidth' in relay):
				#	if (relay['observed_bandwidth'] > 10000000):
				#		good_exits[ip] = relay
				good_exits[ip] = relay
			relay.pop("exit_policy_summary", None)
			all_relays[ip] = relay
	log("Found {0} possible exit nodes that accept connections on {1}".format(len(good_exits), destination_port))
	return (all_relays, all_exits, good_exits)

# Given an ip, spawns a new process to run standard ping, and returns an array of measurements in ms
# If any pings timeout, reruns up to five times. After five tries, returns an empty array signaling failure
def ping(ip):
	pings = []
	attempts = 0
	while((len(pings) < 6) and attempts < 3):
		attempts += 1
		regex = re.compile("(\d+.\d+) ms")
		cmd = ['ping','-c', '10', ip]
		p = subprocess.Popen(cmd,stdout=subprocess.PIPE)
		lines = p.stdout.readlines()
		for line in lines:
			ping = regex.findall(line)
			if ping != [] and "DUP" not in line:
				pings.append(float(ping[0]))
		p.wait()
		pings = pings[:-1]
	return pings

# Data = string representation of array of pings times
# Deserializes string into array of floats and returns it
def deserialize_ping_data(data):
	regex = re.compile("(\d+.\d+)")
	temp = regex.findall(data)
	pings = []
	for x in temp:
		pings.append(float(x))
	return pings

def get_stats(arr):
	np = numpy.array(arr)
	return [numpy.mean(np),numpy.min(np),numpy.max(np),numpy.median(np),numpy.std(np)]

def remove_outliers(measurements):
	sorted_arr = numpy.sort(measurements)
	left = sorted_arr[0:len(sorted_arr)/2]
	if((len(sorted_arr) % 2) == 0):
		right = sorted_arr[len(sorted_arr)/2:]
	else:
		right = sorted_arr[len(sorted_arr)/2+1:]
	q1 = int(numpy.median(left))
	q3 = int(numpy.median(right))
	iqr = q3 - q1
	lower = q1 - (1.5*iqr)
	upper = q3 + (1.5*iqr)
	if(lower is upper): # All measurements within same integer value
		return (1.0, measurements)
	else:
		good_ones = []
		for r_xy in measurements:
			if(lower < r_xy < upper):
				good_ones.append(r_xy)
		closeness = float(len(good_ones)) / len(measurements)
		return (closeness, good_ones)


class TingWorker():
	def __init__(self, controller_port, socks_port, destination_port, job_stack, result_queue, write_output_file):
		self._controller_port = controller_port
		self._socks_port = socks_port
		self._destination_port = destination_port
		self._job_stack = job_stack
		self._result_queue = result_queue
		log("Ting running with controller on {0} and socks on {1}".format(controller_port,socks_port))
		log("Destination is {0}:{1}".format(destination_ip,destination_port))
		self._ping_cache = {}
		self._all_relays, self._all_exits, self._good_exits = get_valid_nodes(destination_port)
		self._controller = self.initialize_controller()
		self._curr_cid = 0
		self._write_output_file = write_output_file
		log("Controller successfully initialized.")
		sys.stdout.flush()

	def initialize_controller(self):
		controller = Controller.from_port(port = self._controller_port)
		if not controller:
			sys.stderr.write("ERROR: Couldn't connect to Tor.\n")
			sys.exit
		if not controller.is_authenticated():
			controller.authenticate()
		controller.set_conf("__DisablePredictedCircuits", "1")
		controller.set_conf("__LeaveStreamsUnattached", "1")

		# Attaches a specific circuit to the given stream (event)
		def attach_stream(event):
			try:
				self._controller.attach_stream(event.id, self._curr_cid)
			except (OperationFailed, InvalidRequest), error:
				log(traceback.format_exc())
				if str(error) in (('Unknown circuit %s' % self._curr_cid), "Can't attach stream to non-open origin circuit"):
					self._controller.close_stream(event.id)
					log("[ERROR]: " + str(error))
				else:
					raise

		# An event listener, called whenever StreamEvent status changes
		def probe_stream(event):
			if event.status == 'DETACHED':
				log("[ERROR]: Stream Detached from circuit {0}...".format(self._curr_cid))
				#*** WRITE TO STANDARD ERR OR SOMETHING
			if event.status == 'NEW' and event.purpose == 'USER':
				attach_stream(event)

		controller.add_event_listener(probe_stream, EventType.STREAM)
		return controller

	# Tell socks to use tor as a proxy 
	def setup_proxy(self):
	    socks.setdefaultproxy(socks_type, socks_host, self._socks_port)
	    socket.socket = socks.socksocket
	    sock = socks.socksocket()
	    sock.settimeout(10) # Streams usually detach within 20 seconds
	    return sock

	# Builds all necessary circuits for the list of 4 given relays
	# If no relays given, 4 are chosen at random
	# Returns the list of relays used in building circuits
	def build_circuits(self, ips = []):
		"""
		Builds all 3 necessary circuits
		If X,Y are given, tries different pairs of W,Z until all 3 circuits can be created
		Returns the list of relays used in the final circuit building
		"""

		pick_wz = False
		while True:
			try:
				wz = self.pick_good_exits(n=2, existing=ips)
				all_ips = [wz[0], ips[0], ips[1], wz[1]]
				relays = []
				for ip in all_ips:
					relays.append(self._all_relays[ip]['fingerprint'])

				self._full_id = None
				self._sub_one_id = None
				self._sub_two_id = None

				log("Building ciruits...")
				failed_creating = "W,X,Y,Z"
				self._full_id = self._controller.new_circuit(relays, await_build = True)
				failed_creating = "W,X"
				self._sub_one_id = self._controller.new_circuit(relays[:2], await_build = True)
				failed_creating = "Y,Z"
				self._sub_two_id = self._controller.new_circuit(relays[-2:], await_build = True)
				log("All 3 circuits built successfully, using the following relays:\n\tW: {0}\n\tX: {1}\n\tY: {2}\n\tZ: {3}".format(all_ips[0],all_ips[1],all_ips[2],all_ips[3]))
				return (relays, all_ips)

			except(InvalidRequest, CircuitExtensionFailed) as exc:
				if('message' in vars(exc)):
					log("{0} {1}".format(failed_creating, vars(exc)['message']))
				else:
					log("[ERROR]: {0} Circuit failed to be created, reason unknown.".format(failed_creating))

				if self._full_id is not None:
					self._controller.close_circuit(self._full_id)
				if self._sub_one_id is not None:
					self._controller.close_circuit(self._sub_one_id)
				if self._sub_two_id is not None:
					self._controller.close_circuit(self._sub_two_id)

	# N - number of relays to pick
	# Existing - list of relays already in the circuit being built
	# Exits - dictionary of valid exit nodes
	def pick_good_exits(self, n = 2, existing = []):
		ips = [0 for x in range(n)]
		for i in range(len(ips)):
			temp = choice(self._good_exits.keys())
			while(temp in ips or temp in existing):
				temp = choice(self._good_exits.keys())
			ips[i] = temp
		return ips

	# Run a ping through a Tor circuit, return array of times measured
	def ting(self,path):
		arr = []

		current_min = 10000000
		consecutive_min = 0
		stable = False
		msg = pack("!c", "!")
		done = pack("!c", "X")

		try:
			print("\tTrying to connect..")
			self._sock.connect((destination_ip,self._destination_port))
			print("\tConnected successfully!")

			while(not stable):
				start_time = time.time()
				self._sock.send(msg)
				data = self._sock.recv(1)
				end_time = time.time()

				sample = (end_time - start_time)*1000

				arr.append(sample)
				if(sample < current_min): 
					current_min = sample
					consecutive_min = 0
				else:
					consecutive_min += 1

				if(consecutive_min >= 10):
					self._sock.send(done)
					stable = True
					self._sock.shutdown(socket.SHUT_RDWR)
					self._sock.close()
			return arr

		except socket.error, e:
			log("Failed to connect using the given circuit: " + str(e) + "\nClosing connection.")
			if isinstance(e.args, tuple):
				print("\terrno %d" % e[0])
			if(self._sock):
				self._sock.shutdown(socket.SHUT_RDWR)
				self._sock.close()
			raise CircuitConnectionException("Failed to connect using the given circuit: ", "t_"+path, str(exc))

	# Run 2 pings and 3 tings, return details of all measurements
	def find_r_xy(self, ips):
		count = 0
		r_xd = []
		r_sy = []
		events = {}

		start = time.time()

		ip_x = ips[1]
		log("Ping x...")
		# Only use the cached value if it is less than an hour old
		if ip_x in self._ping_cache and (time.time() - self._ping_cache[ip_x][0]) < 3600: 
			age = time.time() - self._ping_cache[ip_x][0]
			r_xd = self._ping_cache[ip_x][1]
			end = time.time()
			events['p_xd'] = {
				'cache_age' : age,
				'elapsed' : (end-start),
				'measurements' : r_xd
			}
		else: 
			r_xd = ping(ip_x)
			self._ping_cache[ip_x] = (start, r_xd)
			if(not r_xd):
				raise NotReachableException('Could not collect enough ping measurements. Tried 3 times, and got < 5/10 responses each time.','p_xd',str(ip_x))
			end = time.time()
			events['p_xd'] = {
				'time_elapsed' : (end-start),
				'measurements' : r_xd
			}
		log("Results: " + str(r_xd))

		start = time.time()

		ip_y = ips[2]
		log("Ping y...")
		# Only use the cached value if it is less than an hour old
		if ip_y in self._ping_cache and (time.time() - self._ping_cache[ip_y][0]) < 3600: 
			age = time.time() - self._ping_cache[ip_y][0]
			r_sy = self._ping_cache[ip_y][1]
			end = time.time()
			events['p_sy'] = {
				'cache_age' : age,
				'elapsed' : (end-start),
				'measurements' : r_sy
			}
		else:
			r_sy = ping(ip_y)
			self._ping_cache[ip_y] = (start, r_sy) 
			if(not r_sy):
				raise NotReachableException('Could not collect enough ping measurements. Tried 3 times, and got < 5/10 responses each time.','p_sy',str(ip_y))
			end = time.time()
			events['p_sy'] = {
				'time_elapsed' : (end-start),
				'measurements' : r_sy
			}
		log("Results: " + str(r_sy))		

		circuits = [self._full_id, self._sub_one_id, self._sub_two_id]
		paths = ["swxyzd", "swxd", "syzd"]
		index = 0
		tings = {}

		# Ting the 3 tor circuits
		for cid in circuits:
			self._curr_cid = cid
			self._sock = self.setup_proxy()
			path = paths[index]
			log("Ting " + path)
			start = time.time()
			tings[path] = self.ting(path)
			end = time.time()
			events[path] = {
				'time_elapsed' : (end-start),
				'measurements' : tings[path]
			}
			log("Results: " + str(tings[path]))
			index += 1

		r_xy = min(tings['swxyzd']) - min(tings['swxd']) - min(tings['syzd']) + min(r_xd) + min(r_sy)

		return (events, r_xy)

	# Main execution loop
	def run(self):

		while(not self._job_stack.empty()):			
			try:
				job = self._job_stack.get(False)
			except Queue.Empty:
				break # empty() is not reliable due to multiprocessing semantics

			log('Measuring pair: %s->%s\n' % (job[0],job[1]))

			stable = False
			all_rxy = []
			not_reachable = False
			while(not stable):
				result = {}
				r_xy = 0
				relays, all_ips = self.build_circuits(job) 
				result['circuit'] = {}
				for i in range(len(relays)):
					result['circuit'][relay_names[i]] = {}
					result['circuit'][relay_names[i]]['ip'] = all_ips[i]
					result['circuit'][relay_names[i]]['fp'] = relays[i]
				result['iteration'] = (len(all_rxy)+1)
				try:
					events, r_xy = self.find_r_xy(all_ips)
					result['events'] = events
					result['r_xy'] = r_xy
					if(r_xy > 0):
						all_rxy.append(r_xy)
				except (NotReachableException, CircuitConnectionException, CircuitExtensionFailed, OperationFailed, InvalidRequest, InvalidArguments, socks.Socks5Error, socket.timeout) as exc:
					result['events'] = {}
					result['events']['error'] = {
						'time_occurred' : str(datetime.datetime.now()),
						'type' : exc.__class__.__name__,
						'details' : vars(exc)
					}
					if(exc.__class__.__name__ is 'NotReachableException'):
						not_reachable = True

				self._result_queue.put(((all_ips[1])+"->"+(all_ips[2]),result),False)
				if(not_reachable):
					log("NotReachableException: We couldn't get enough ping responses from X or Y, \
						so we can't calculate the latency between them. Moving on to the next pair in the list...")
					break # if it was not reachable building new circuits wont help, just skip this job

				if(r_xy):
					log("Finished iteration {0}, r_xy={1}".format(result['iteration'],r_xy))

				if(len(all_rxy) >= 10):
					stable = True
					f = open('finished.txt', 'w')
					f.write(job[0] + " " + job[1] + "\n")
					f.close()
					
			log("Saving results...")
			self._write_output_file()
			
		self._controller.close()

def create_and_spawn(controller_port, socks_port, destination_port, job_stack, results_queue, write_output_file):
	worker = TingWorker(controller_port, socks_port, destination_port, job_stack, results_queue, write_output_file)
	worker.run()

def main():
	parser = argparse.ArgumentParser(prog='Ting', description='Ting measures round-trip times between two indivudal nodes in the Tor network.')
	parser.add_argument('-i', '--input-file', help="Path to input file containing settings and list of circuits",required=True)
	parser.add_argument('-o', '--output-file', help="Path to output file",required=True)
	parser.add_argument('-m', '--message', help="Message for future reference, describing this particular run",required=True)
	parser.add_argument('-dp', '--destination-port', help="Port of server running on Bluepill", default=6667)
	parser.add_argument('-sp', '--socks-port', help="Port being used by Tor", default=9050)
	parser.add_argument('-cp', '--controller-port', help="Port being used by Stem", default=9051)

	args = vars(parser.parse_args())

	begin = str(datetime.datetime.now())

	job_stack = Queue.Queue()

	# Read and parse input file
	f = open(args['input_file'])
	r = f.readlines()
	f.close()

	regex = re.compile("^(\d+.\d+.\d+.\d+)\s(\d+.\d+.\d+.\d+)$")
	for l in r:
		job_stack.put_nowait(list(regex.findall(l)[0]))

	results_queue = Queue.Queue()

	controller_port = int(args['controller_port'])
	socks_port = int(args['socks_port'])
	destination_port = int(args['destination_port'])

	def catch_sigint(signal, frame):
		write_output_file()
		sys.exit(0)

	def write_output_file():
		results = {}
		results['version'] = ting_version
		results['time_begin'] = begin
		results['header'] = {
			'source_ip' : destination_ip,
			'destination_ip' : destination_ip,
			'stem_controller_ports' : [controller_port],
			'socks5_ports' : [socks_port],
			'destination_ports' : [destination_port],
			'buffer_size' : buffer_size,
			'min_tings' : '10',
			'input_file' : args['input_file'],
			'output_file' : args['output_file'],
			'notes' : args['message'] 
		}
		results['data'] = {}
		while(not results_queue.empty()):
			result = results_queue.get(False)
			if(not result[0] in results['data']):
				results['data'][result[0]] = [result[1]]
			else:
				results['data'][result[0]].append(result[1])

		f = open(args['output_file'],'w')
		f.write(json.dumps(results, indent=4, separators=(',',': ')))
		f.close()

	signal.signal(signal.SIGINT, catch_sigint) # Still write output even if process killed

	create_and_spawn(controller_port,socks_port,destination_port,job_stack,results_queue,write_output_file)
	
	write_output_file()

if __name__ == "__main__":
	main()

