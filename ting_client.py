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
from numpy import array
import multiprocessing
import numpy
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

ting_version = "1.0"
destination_ip = '128.8.126.92'
buffer_size = 64
socks_host = '127.0.0.1'
socks_type = socks.PROXY_TYPE_SOCKS5
relay_names = ['w','x','y','z']


"""
Thrown when destination is not reachable via a public ip address
"""
class NotReachableException(Exception):
	"""Exception raised when connections are timing out

    Attributes:
		msg -- details about the connection being made
		func  -- function where error occured
		dest -- (if ping, destination ip to which ping failed)
	"""
	def __init__(self, msg, func, dest):
		self.msg = msg
		self.func = func
		self.dest = dest


def createFile(self):
	"""
	Create file for output writing, and any 
	directories needed that do not already exist
	"""
	self._current_ting = 1
	self._ting_dir = args['data_dir'] + "tings/" + "{0}_{1}_{2}".format(now.month, now.day, now.year) + "/"
	current_dir = os.path.dirname(os.path.realpath(__file__))
	first_sub = current_dir + "/" + self._ting_dir
	filenum = 0
	if(not os.path.exists(first_sub)):
		os.makedirs(first_sub)
	else:
		ting_files = os.listdir(first_sub)
		regex = re.compile("ting_\w+_(\d+).txt")
		filenums = []
		for f in ting_files:
			filenums.append(int(regex.findall(f)[0]))
		if not filenums == []:
			filenum = max(filenums)
	self._output_file = self._ting_dir + "ting_{0}_{1}.txt".format(self._mode,filenum+1)

	self.writeFileHeader()

def setup_data_dirs(self):
	current_dir = os.path.dirname(os.path.realpath(__file__))
	if(not os.path.exists(current_dir + "/" + self._data_dir + "nodes/")):
		os.makedirs(current_dir + "/" + self._data_dir + "nodes/")
	if(not os.path.exists(current_dir + "/" + self._data_dir + "tings/")):
		os.makedirs(current_dir + "/" + self._data_dir + "tings/")

	ip_underscore = self._destination_ip.replace(".", "_")
	now = datetime.datetime.now()
	date_underscore = "{0}_{1}_{2}".format(now.month, now.day, now.year)
	first_sub = current_dir + "/data/nodes/%s" % ip_underscore

	filenum = 1
	if(os.path.exists(first_sub)):
			second_sub = first_sub + "/" + date_underscore
			if(os.path.exists(second_sub)):
				node_files = os.listdir(second_sub)
				regex = re.compile("validexits_\d+_(\d+).txt")
				filenums = []
				for f in node_files:
					if "validexits" in f:
						filenums.append(int(regex.findall(f)[0]))
				if not filenums == []:
					filenum = max(filenums)

	self._valid_exits_fname = "{0}nodes/{1}/{2}/validexits_{3}_{4}.txt".format(self._data_dir, str(ip_underscore), date_underscore, str(self._destination_port), str(filenum))
	self._blacklist_fname = "{0}nodes/{1}/{2}/blacklist_{3}_{4}.txt".format(self._data_dir, str(ip_underscore), date_underscore, str(self._destination_port), str(filenum))

def get_valid_nodes(destination_port):
	exit_nodes = {}
	output_file = "data/nodes/{0}/{1}/validexits_{2}_{3}.txt".format(str(destination_ip.replace(".", "_")), "3_22_2014", str(destination_port), str(1))

	cmd = ['python', 'get_nodes_fast.py', '-di', destination_ip, '-dp', str(destination_port)]
	p = subprocess.Popen(cmd, shell=False)
	p.communicate()
	p.wait()
	f = open(output_file)
	
	escapes = ["#", "\t", "\n"]
	for line in f.readlines():
		if(not line[0] in escapes):
			relay = line.strip().replace(" ", "").split(",")
			exit_nodes[relay[0]] = relay[1]
	f.close()

	return exit_nodes
	#*** REMOVE ANY BLACKLISTED STUFF


#*** NEED SOME NOTION OF BLACKLIST ME THINKS

# Given an ip, spawns a new process to run standard ping, and returns an array of measurements in ms
# If any pings timeout, reruns up to five times. After five tries, returns an empty array signaling failure
def ping(ip):
	pings = []
	attempts = 0
	while((len(pings) < 10) and attempts < 5):
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

# Computes typical ping stats for a given array of ting times
def get_stats(arr):
	np = array(arr)
	_avg = numpy.mean(np)
	_min = numpy.min(np)
	_max = numpy.max(np)
	_med = numpy.median(np)
	_std = numpy.std(np)
	return {'average':_avg,'min':_min,'max':_max,"median":_med,"std":_std}


def get_random_pairs(num_pairs):
	fps = self._exits.keys()[:num_pairs]
	pairs = []
	for i in range(num_pairs):
		j = i+1
		while(j < num_pairs):
			pairs.append([fps[i], fps[j]])
			j += 1
	shuffle(pairs)	
	return pairs

	#*** MAKE EXITS HASH A GLOBAL OR SOMETHING? SYNC READ SHOULD BE FINE RIGHTTT

"""
Controller class that does all of the work
"""
class TingWorker():
	def __init__(self, controller_port, socks_port, destination_port, job_stack, result_queue, id_num):
		self.id_num = id_num
		self._controller_port = controller_port
		self._socks_port = socks_port
		self._destination_port = destination_port
		self._job_stack = job_stack
		self._result_queue = result_queue
		print("[{0}] Worker created with cp {1}, dp {2}, sp {3} | id=[{4}]".format(datetime.datetime.now(),controller_port,destination_port,socks_port,id_num))
		self._ping_cache = {}
		self._exits = get_valid_nodes(destination_port)
		self._controller = self.initialize_controller()
		print("[{0}] Controller successfully initialized on port {1} | id=[{2}]".format(datetime.datetime.now(), controller_port, id_num))

	def initialize_controller(self):
		controller = Controller.from_port(port = self._controller_port)
		if not controller:
			sys.stderr.write("ERROR: Couldn't connect to Tor.\n")
			sys.exit
		if not controller.is_authenticated():
			controller.authenticate()
		controller.set_conf("__DisablePredictedCircuits", "1")
		controller.set_conf("__LeaveStreamsUnattached", "1")

		# Close all non-internal circuits.
		for circ in controller.get_circuits():
			if not circ.build_flags or 'IS_INTERNAL' not in circ.build_flags:
				controller.close_circuit(circ.id)

		# Attaches a specific circuit to the given stream (event)
		def attach_stream(event):
			try:
				self._controller.attach_stream(event.id, self._curr_cid)
			except (OperationFailed, InvalidRequest), error:
				print(traceback.format_exc())
				if str(error) in (('Unknown circuit %s' % self._curr_cid), "Can't attach stream to non-open origin circuit"):
					self._controller.close_stream(event.id)
				else:
					raise

		# An event listener, called whenever StreamEvent status changes
		def probe_stream(event):
			if event.status == 'DETACHED':
				print("[ERROR]: Stream Detached from circuit {0}...".format(curr_cid))
				#*** WRITE TO STANDARD ERR OR SOMETHING
			if event.status == 'NEW' and event.purpose == 'USER':
				attach_stream(event)

		controller.add_event_listener(probe_stream, EventType.STREAM)
		print("[{0}] Event listener added!".format(self.id_num))
		return controller

	# Tell socks to use tor as a proxy 
	def setup_proxy(self):
	    socks.setdefaultproxy(socks_type, socks_host, self._socks_port)
	    socket.socket = socks.socksocket
	    sock = socks.socksocket()
	    sock.settimeout(20) # Streams usually detach within 20 seconds
	    return sock

	def remove_outliers(self, measurements):
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
		good_ones = []
		for r_xy in measurements:
			if(lower < r_xy < upper):
				good_ones.append(r_xy)
		closeness = float(len(good_ones)) / len(measurements)
		return (closeness, good_ones)

	# Builds all necessary circuits for the list of 4 given relays
	# If no relays given, 4 are chosen at random
	# Returns the list of relays used in building circuits
	def build_circuits(self, relays = []):
		"""
		Builds all 3 necessary circuits
		If X,Y are given, tries different pairs of W,Z until all 3 circuits can be created
		Returns the list of relays used in the final circuit building
		"""

		pick_wz = False
		while True:
			try:
				if len(relays) == 2:
					wz = self.pick_relays(n=2, existing=relays)
					relays = [wz[0], relays[0], relays[1], wz[1]]
					pick_wz = True

				self._full_id = None
				self._sub_one_id = None
				self._sub_two_id = None

				failed_creating = "W,X,Y,Z"
				self._full_id = self._controller.new_circuit(relays, await_build = True)
				failed_creating = "W,X"
				self._sub_one_id = self._controller.new_circuit(relays[:2], await_build = True)
				failed_creating = "Y,Z"
				self._sub_two_id = self._controller.new_circuit(relays[-2:], await_build = True)
				print("[{0}] All circuits built successfully.".format(str(datetime.datetime.now())))
				return relays

			except(InvalidRequest, CircuitExtensionFailed) as exc:
				print(vars(exc))
				print("FAILED CREATING: " + failed_creating)
				if self._full_id is not None:
					self._controller.close_circuit(self._full_id)
				if self._sub_one_id is not None:
					self._controller.close_circuit(self._sub_one_id)
				if self._sub_two_id is not None:
					self._controller.close_circuit(self._sub_two_id)
				#** PERHAPS WRITE SOMETHING HERE ABOUT BUILD ERROR 
				if(pick_wz):
					relays = relays[1:3]

	# N - number of relays to pick
	# Existing - list of relays already in the circuit being built
	# Exits - dictionary of valid exit nodes
	def pick_relays(self, n = 4, existing = []):
		relays = [0 for x in range(n)]
		for i in range(len(relays)):
			temp = choice(self._exits.keys())
			while(temp in relays or temp in existing):
				temp = choice(self._exits.keys())
			relays[i] = temp
		return relays

	# Run a ping through a Tor circuit, return array of times measured
	def ting(self,path):
		arr = []
		current_min = 10000000
		consecutive_min = 0
		stable = False

		try:
			self._sock.connect((destination_ip,self._destination_port))
			msg = "echo"
			self._sock.send(msg)
			data = self._sock.recv(buffer_size)
			if data == "OKAY":
				while(not stable):
					msg = str("ting")

					start_time = time.time()
					self._sock.send(msg)
					data = self._sock.recv(buffer_size)
					end_time = time.time()

					sample = (end_time - start_time)*1000
					arr.append(sample)
					if(sample < current_min): 
						current_min = sample
						consecutive_min = 0
					else:
						consecutive_min += 1

					if(consecutive_min >= 10):
						stable = True
						self._sock.send("done")
						data = self._sock.recv(buffer_size)
			else:
				raise NotReachableException("Did not recieve a response over Tor circuit", "t_"+path,'')
			self._sock.close()
			return arr
		except TypeError as exc:
			print("Failed to connect using the given circuit: ", exc)
			raise NotReachableException("Failed to connect using the given circuit: ", "t_"+path,'')

	# Run 2 pings and 3 tings, return details of all measurements
	def find_r_xy(self, relays):
		count = 0
		r_xd = []
		r_sy = []
		events = {}

		start = time.time()

		ip_x = self._exits[relays[1]]

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
			while(len(r_xd) <= 4):
				if(count is 3):
					#***add_to_blacklist(ip_x)
					raise NotReachableException('Could not collect enough ping measurements. Tried 3 times, and got < 5/10 responses each time.','p_xd',str(ip_x))
				s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				s.connect((destination_ip, self._destination_port))
				msg = "ping {0} {1}".format(ip_x, 10)
				s.send(msg)
				response = s.recv(1024)
				s.close()
				r_xd = deserialize_ping_data(response)
				if(len(r_xd) < 1):
					#***add_to_blacklist(ip_x)
					raise NotReachableException('All ping requests timed out. Probably not a public IP address?','p_xd',str(ip_x))
				count = count + 1
			self._ping_cache[ip_x] = (start, r_xd)
			end = time.time()
			events['p_xd'] = {
				'time_elapsed' : (end-start),
				'measurements' : r_xd
			}

		start = time.time()

		ip_y = self._exits[relays[2]]

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
			while(len(r_sy) <= 4):
				if(count is 3):
					#***add_to_blacklist(ip_y)
					raise NotReachableException('Could not collect enough ping measurements. Tried 3 times, and got < 5/10 responses each time.','p_xd',str(ip_y))
				s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				s.connect((destination_ip, self._destination_port))
				msg = "ping {0} {1}".format(ip_y, 10)
				s.send(msg)
				response = s.recv(1024)
				s.close()
				r_sy = deserialize_ping_data(response)
				if(len(r_sy) < 1):
					#***add_to_blacklist(ip_y)
					raise NotReachableException('All ping requests timed out. Probably not a public IP address?','p_xd',str(ip_y))
				count = count + 1

			self._ping_cache[ip_y] = (start, r_sy)
			end = time.time()
			events['p_sy'] = {
				'time_elapsed' : (end-start),
				'measurements' : r_sy
			}		

		circuits = [self._full, self._sub_one, self._sub_two]
		paths = ["swxyzd", "swxd", "syzd"]
		index = 0
		tings = {}

		# Ting the 3 tor circuits
		for cid in circuits:
			self._curr_cid = cid
			path = paths[index]

			self._sock = self.setup_proxy()
			start = time.time()
			tings[path] = self.ting(path)
			self._sock = self._sock.close()
			end = time.time()
			events[path] = {
				'time_elapsed' : (end-start),
				'measurements' : arr
			}
			index += 1

		r_xy = min(tings['swxyzd']) - min(tings['swxd']) - min(tings['syzd']) + min(r_xd) + min(r_sy)

		return (events, r_xy)

	# Main execution loop
	def run(self):
		sys.stdout.write('[%s] [pid=%s] now running..\n' % (self.id_num, os.getpid()))
		
		while(not self._job_stack.empty()):
			result = {}
			job = self._job_stack.get(False)
			nickname_x = job[4]
			nickname_y = job[5]
			sys.stdout.write('[%s] [pid=%s] executing job.. %s\n' % (self.id_num, os.getpid(),(nickname_x)+"->"+(nickname_y)))
			#*** GENERALIZE TO MAKE WORK FOR ANY NUMBER OF STARS, ASSUMING THEYRE ON THE ENDS FOR NOW
			relays = self.build_circuits(job[1:3])
			sys.stdout.write('[%s] [pid=%s] circuits built! %s\n' % (self.id_num, os.getpid(),str(job)))
			result['circuit'] = {}
			for i in range(len(relays)):
				result['circuit'][relay_names[i]] = {}
				result['circuit'][relay_names[i]]['ip'] = self._exits[relays[i]]
				result['circuit'][relay_names[i]]['fp'] = relays[i]

			try:
				events, r_xy = self.find_r_xy(relays)
				result['events'] = events
				result['r_xy'] = r_xy
			except (NotReachableException, CircuitExtensionFailed, OperationFailed, InvalidRequest, InvalidArguments, socks.Socks5Error, socket.timeout) as exc:
				result['events'] = {}
				result['events']['error'] = {
					'time_occurred' : str(datetime.datetime.now()),
					'type' : exc.__class__.__name__,
					'details' : vars(exc)
				}
			except Queue.Empty:
				break # empty() is not reliable due to multiprocessing semantics

			self._result_queue.put(((nickname_x)+"->"+(nickname_y),result),False)

		self._controller.close()
		sys.stdout.write('[%s] completed\n' % (self.id_num))

def create_and_spawn(controller_port, socks_port, destination_port, job_stack, results_queue, i):
	print("Creating worker " + str(i))
	worker = TingWorker(controller_port, socks_port, destination_port, job_stack, results_queue, i)
	worker.run()

def main():
	parser = argparse.ArgumentParser(prog='Ting', description='Ting measures round-trip times between two indivudal nodes in the Tor network.')
	parser.add_argument('-i', '--input-file', help="Path to input file containing settings and list of circuits",required=True)
	parser.add_argument('-o', '--output-file', help="Path to output file",required=True)
	parser.add_argument('-m', '--message', help="Message for future reference, describing this particular run",required=True)
	args = vars(parser.parse_args())

	begin = str(datetime.datetime.now())

	job_stack = multiprocessing.Queue()

	# Read and parse input file
	f = open(args['input_file'])
	r = f.readlines()
	f.close()
	regex = re.compile("^(\*|\w{40})\s(\*|\w{40})\s(\*|\w{40})\s(\*|\w{40})\s(\w+)->(\w+)$")
	for l in reversed(r):
		job_stack.put_nowait(list(regex.findall(l)[0]))

	results_queue = multiprocessing.Queue()

	controller_port = 9051
	socks_port = 9050
	destination_port = 6667

	for i in range(3):
		multiprocessing.Process(target=create_and_spawn, args=(controller_port, socks_port, destination_port, job_stack, results_queue, i)).start()

	# workers = []
	# for i in range(3):
	# 	workers.append(TingWorker(controller_port, socks_port, destination_port, job_stack, results_queue, i))

	# for worker in workers:
	# 	worker.start()

	# for worker in workers:
	# 	worker.join()

	# write output file
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
		results['data'][result[0]] = result[1]

	f = open(args['output_file'],'w')
	f.write(json.dumps(results, indent=4, separators=(',',': ')))
	f.close()

if __name__ == "__main__":
	main()