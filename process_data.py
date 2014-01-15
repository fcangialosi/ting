import re
import sys
import matplotlib.pyplot as plt
import numpy as np

def deserialize_ping_data(data):
    regex = re.compile("(\d+.\d+)")
    temp = regex.findall(data)
    pings = []
    for x in temp:
            pings.append(float(x))
    return pings

x = 5
def percentile(arr):
        arr.sort()
        return arr[x-1]

# Example: data/tings/1_11_2014/ting_verify_4.txt
with open(sys.argv[1]) as f:
        r = f.readlines()
        data = []
        for l in r:
                if l[:2] == "\t[":
                        data.append(l[1:])

index = 0
trial_num = 1
rxys_min = []
rxys_percentile = []
while index < len(data):
        times = data[index:(index+5)]
        arrs = []
        for t in times:
                arrs.append(deserialize_ping_data(t))
        rxy_min = min(arrs[2]) - min(arrs[3]) - min(arrs[4]) + min(arrs[0]) + min(arrs[1])
        rxy_percentile = percentile(arrs[2]) - percentile(arrs[3]) - percentile(arrs[4]) + min(arrs[0]) + min(arrs[1])
        rxys_min.append(rxy_min)
        rxys_percentile.append(rxy_percentile)
        index = index + 5
        trial_num = trial_num + 1


sorted_min = np.sort(rxys_min)
sorted_percentile = np.sort(rxys_percentile)
print(sorted_min)
print(sorted_percentile)
plt.plot(sorted_min, np.arange(len(sorted_min)*1.0)/len(sorted_min))
plt.plot(sorted_percentile, np.arange(len(sorted_percentile)*1.0)/len(sorted_percentile))
plt.xlabel("Time (ms)")
plt.ylabel("CDF")
plt.legend(['Min','{0} percentile'.format(x)], loc='best')
plt.savefig(sys.argv[1][:-4]+".png")
