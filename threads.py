from Queue import Queue, PriorityQueue
from threading import Thread
import time
import random
from collections import deque
from threading import BoundedSemaphore
import socket
from stem import CircStatus, OperationFailed, InvalidRequest, InvalidArguments, CircuitExtensionFailed
from stem.control import Controller, EventType
from random import choice
import sys
import os
import os.path
from os.path import join, dirname, isfile
sys.path.append(join(dirname(__file__), 'libs'))
from SocksiPy import socks
import re
import traceback

#####################################
destination_ip = '128.8.126.92'
destination_port = 6667
#####################################
controller_port = 9451
#####################################
socks_port = 9450
socks_host = '127.0.0.1'
socks_type = socks.PROXY_TYPE_SOCKS5
#####################################
listening_port = 6668
listening_host = ''
#####################################
curr_cid = None
#####################################
MIN_TINGS = 10
MIN_ITERS = 10
#####################################

class Experiment():
	def __init__(self, relays):
		self.nickname = relays[4] + "->" + relays[5]
		self.relays = relays[0:4]
		self.wxyz = {
			'cid' : None,
			'complete' : False,
			'last' : None,
			'times' : []
		}
		self.wx = {
			'cid' : None,
			'complete' : False,
			'last' : None,
			'times' : []
		}
		self.yz = {
			'cid' : None,
			'complete' : False,
			'last' : None,
			'times' : []
		}
		print "Created experiment " + self.nickname
	def get_circs(self):
		return [self.wxyz, self.wx, self.yz]
	def all_ready(self):
		return ((self.wxyz['complete'] or not self.wxyz['last']) and (self.wx['complete'] or not self.wx['last']) and (self.yz['complete'] or not self.yz['last']))

def get_valid_nodes():
	nodes = {}
	f = open("data/nodes/128_8_126_92/{0}/validexits_{1}_1.txt".format("4_16_2014", str(destination_port)))
	escapes = ["#","\t","\n"]
	for line in f.readlines():
		if(not line[0] in escapes):
			relay = line.strip().replace(" ","").split(",")
			nodes[relay[0]] = relay[1]
	return nodes

def pick_relays(pool, n = 4, existing = []):
	relays = [0 for x in range(n)]
	for i in range(len(relays)):
		temp = choice(pool.keys())
		while(temp in relays or temp in existing):
			temp = choice(pool.keys())
		relays[i] = temp
	return relays

def creator():
	print "[Creator]: Starting.."
	
	print "[Creator]: Getting valid nodes."
	pool = get_valid_nodes()

	#Close all non-internal circuits.
	for circ in controller.get_circuits():
		if not circ.build_flags or 'IS_INTERNAL' not in circ.build_flags:
			controller.close_circuit(circ.id)

	print "[Creator]: All non-internal circuits closed."

	# Attaches a specific circuit to the given stream (event)
	def attach_stream(event):
		try:
			controller.attach_stream(event.id, curr_cid)
		except (OperationFailed, InvalidRequest), error:
			print(traceback.format_exc())
			if str(error) in (('Unknown circuit %s' % curr_cid), "Can't attach stream to non-open origin circuit"):
				controller.close_stream(event.id)
			else:
				raise

	# An event listener, called whenever StreamEvent status changes
	def probe_stream(event):
		if event.status == 'DETACHED':
			print("[ERROR]: Stream Detached from circuit {0} (maybe)".format(curr_cid))
		if event.status == 'NEW' and event.purpose == 'USER':
			attach_stream(event)

	controller.add_event_listener(probe_stream, EventType.STREAM)
	print "[Creator]: Event listener attached."

	while True: 
		print "[Creator]: Waiting for queue to be populated"
		experiment = to_be_created.get(block=True)
		print "[Creator]: Got " + experiment.nickname + " off the queue"
		try:
			controller.get_circuit(experiment.wxyz['cid'])
			controller.get_circuit(experiment.wx['cid'])
			controller.get_circuit(experiment.yz['cid'])
			print("\t[Creator]: Found all circuits necessary for " + experiment.nickname)
		except ValueError as exc:
			print("\t[Creator]: Could not find all circuits for " + experiment.nickname + ", recreating...")
			xy = experiment.relays[1:3]
			while True:
				relays = experiment.relays
				try:
					experiment.wxyz['cid'] = controller.new_circuit(relays)
					experiment.wx['cid'] = controller.new_circuit(experiment.relays[:2])
					experiment.yz['cid'] = controller.new_circuit(experiment.relays[-2:])
					break
				except (InvalidRequest, CircuitExtensionFailed) as exc:
					print("\t[Creator]: ERROR!")
					print(vars(exc))
					wz = pick_relays(pool=pool, n=2, existing=xy)
					relays = [wz[0], xy[0], xy[1], wz[1]]
		print("\t[Creator]: Circuits built successfully!")
		to_be_sent.put(experiment)
		to_be_created.task_done()

def sender():
	print "[Sender]: Starting.."
	socks.setdefaultproxy(socks_type, socks_host, socks_port)
	socket.socket = socks.socksocket
	send_sock = socks.socksocket()
	send_sock.settimeout(15)
	print "[Sender]: SOCKS setup complete."
	while True:
		print "[Sender]: Waiting for queue to be populated.."
		experiment = to_be_sent.get(block=True)
		print "[Sender]: Got " + experiment.nickname + " off the queue"
		for circ in experiment.get_circs():
			print("\t[Sender]: Trying to send a packet to " + str(circ))
			if(not circ['complete']): # only send a packet if we dont have enough measurements for this one
				curr_cid = circ['cid'] # update global curr cid for attach stream
				send_sock.connect((destination_ip, destination_port))
				start = time.time() # keep track of start time
				send_sock.send(circ['cid'])
				send_sock.close()
				circ['last'] = start # save start time to object to remain stateless
		
		sent_pool_sema.acquire() # might be slow? perhaps investigate further
		sent_pool.append(experiment)
		sent_pool_sema.release()
		to_be_sent.task_done()
		print "\t[Sender]: All packets sent!"

def reciever():
	print "[Reciever]: Starting.."
	# set up, bind, listen, etc.
	recieve_sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	recieve_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	recieve_sock.bind((listening_host,socks_port))
	recieve_sock.listen(0) # number of queued connections, play around with this number.. 
	print "[Reciever]: Port bound, now listening.."
	while True:
		print "[Reciever]: Waiting for connection"
		conn = recieve_sock.accept()
		cid = conn[0].recv(64)
		at = time.time()
		conn[0].close()		
		print("\tReciever]: Got packet from " + cid)
		to_be_processed.put((cid,at))

def processor():
	print "[Processor]: Starting.."

	def stable_min(measurements):
	   consecutive = 1
	   curr = float("inf")
	   for x in measurements:
	     if(x < curr):
	       curr = x
	       consecutive = 1
	     else:
	       consecutive += 1
	   return consecutive

	while True:
		print "[Processor]: waiting for queue to be populated."
		cid, at = to_be_processed.get(block=True)
		print("[Processor]: Got packet from " + cid + " at " + str(at))

		exp, circ = None, None

		for e in sent_pool:
			for c in e.get_circs():
				if(c['cid'] is cid):
					exp, circ = e, c
					break

		circ['times'].append((at - circ['last'])  * 1000)
		circ['last'] = None
		if(circ['times'] >= MIN_TINGS and stable_min(circ['times'])):
			circ['complete'] = True
			print "\t[Processor]: FINISHED ONE!"
			print vars(exp)
		if(found[0].all_ready()):
			print "\t[Processor]: Giving this experiment back to creator!"
			sent_pool_sema.acquire()
			sent_pool.remove(found)
			sent_pool_sema.release()
			to_be_created.put(exp)

		to_be_processed.task_done()

print "[Main]: Creating queues.."
to_be_created = Queue()
to_be_sent = Queue()
sent_pool = deque()
sent_pool_sema = BoundedSemaphore(value=1) # only allow one thread to be accessing the list at time 
to_be_processed = Queue()

print "[Main]: Connecting to controller.."
controller = Controller.from_port(port = controller_port)
if not controller:
	print("\t[Controller]: ERROR: Couldn't connect to Tor.")
	os._exit(os.EX_UNAVAILABLE)
if not controller.is_authenticated():
	controller.authenticate()
controller.set_conf("__DisablePredictedCircuits", "1")
controller.set_conf("__LeaveStreamsUnattached", "1")


print "[Main]: Starting threads.."
# Create and start the 4 worker threads 
creator_thread = Thread(target=creator)
creator_thread.daemon = True
creator_thread.start()
sender_thread = Thread(target=sender)
sender_thread.daemon = True
sender_thread.start()
reciever_thread = Thread(target=reciever)
reciever_thread.daemon = True
reciever_thread.start()
processor_thread = Thread(target=processor)
processor_thread.daemon = True
processor_thread.start()

print "[Main]: Reading input file.."
# Read in desired circuits from input file
with open(sys.argv[1]) as f:
	regex = re.compile("^(\*|\w{40})\s(\*|\w{40})\s(\*|\w{40})\s(\*|\w{40})\s(\w+)->(\w+)$")
	for l in f.readlines():
		to_be_created.put(Experiment(list(regex.findall(l)[0])))

print "[Main]: Waiting on workers.."
# Main thread only exits once all 4 queues / lists are empty! 
# while True:
# 	to_be_created.join()
# 	to_be_sent.join()
# 	to_be_processed.join()
# 	if(to_be_created.empty() and to_be_sent.empty() and sent_pool.empty() and to_be_processed.empty()):
# 		break
to_be_created.join()
to_be_sent.join()
to_be_processed.join()

print "[Main]: All threads exited, closing."
