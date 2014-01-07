import numpy as np
import statsmodels.api as sm # recommended import according to the docs
import matplotlib.pyplot as plt
import re

f = open("../data/graph_cp")
r = f.readlines()
xy_cp = []
regex = re.compile("(-*\d+.\d+)")
for l in r:
	if "====" in l:
		temp = regex.findall(l)
		xy_cp.append(float(temp[3]))
print(len(xy_cp))
f.close()

f = open("../data/graph")
r = f.readlines()
xy_home = []
regex = re.compile("(-*\d+.\d+)")
for l in r:
	if "====" in l:
		temp = regex.findall(l)
		xy_home.append(float(temp[3]))
print(len(xy_home))
f.close()

sorted_cp = np.sort(xy_cp)
print(np.mean(sorted_cp))
plt.plot(sorted_cp, np.arange(len(sorted_cp)*1.0)/len(sorted_cp))
sorted_home = np.sort(xy_home)
print(np.mean(sorted_home))
plt.plot(sorted_home, np.arange(len(sorted_home)*1.0)/len(sorted_home))
plt.xticks([-50,0,37,50,100,150])
plt.xlabel("Round-Trip Time (Milliseconds)")
plt.legend(['S on UMD Campus Network (129.2.165.67)', 'S on Verizon Home Network (173.67.5.95)'], loc='lower right')
plt.savefig('cdf.jpg')