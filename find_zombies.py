# add to cron job: (specifically for bluepill)
# crontab -e 
# 0 * * * * /usr/bin/python /home/frank/ting/find_zombies.py 

import os
import time

pwd = '/home/frank/ting/'
num_clients = 10
margin = 10 # if the file has not been touched for this many mins or more, restart it

zombies = []

for i in range(num_clients):
	log = pwd + "client_{0}.log".format(num_clients)
	log_mtime = int(os.stat(log).st_mtime)
	now = int(time.time())
	
	elapsed_mins = (now - log_mtime) / 60

	if elapsed_mins >= margin:
		zombies.append(i)

for i in zombies:
	f = open(pwd + "pids/{0}.pid".format(i))
	r = f.readlines()
	f.close()
	
	pid = r[0].strip()
	os.kill(pid, 9)



