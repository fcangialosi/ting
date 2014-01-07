import numpy as np
import statsmodels.api as sm # recommended import according to the docs
import matplotlib.pyplot as plt
import re

f = open("./data/nodes/128_8_126_92/1_7_2014/validexits_6667_1.txt")
r = f.readlines()
f.close()

nodes = []
for l in r:
	if l[0] == "\t":
		nodes.append(l)

data = []
regex = re.compile("(\d+) Day\(s\) \d+ Hour\(s\) \d+ Minute\(s\) \d+ Second\(s\)")
for node in nodes:
	uptime = node.split(",")[3].strip()
	days = int(regex.findall(uptime)[0])
	if(days > 5):
		data.append(int(node.split(",")[4].strip().split("/")[2]))

sorted = np.sort(data)
plt.plot(sorted, np.arange(len(sorted)*1.0)/len(sorted))
plt.xlabel("Observed Bandwidth (Bytes)")
plt.ylabel("Percentage of Routers")
plt.savefig('bandwidth_graph.png')