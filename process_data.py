import re

def deserialize_ping_data(data):
    regex = re.compile("(\d+.\d+)")
    temp = regex.findall(data)
    pings = []
    for x in temp:
            pings.append(float(x))
    return pings

def fifth(arr):
	arr.sort()
	return arr[49]

with open("data/tings/1_11_2014/ting_verify_4.txt") as f:
	r = f.readlines()
	data = []
	for l in r:
		if l[:2] == "\t[":
			data.append(l[1:])

	index = 0
	trial_num = 1
	rxys_min = []
	rxys_fifth = []
	while index < len(data):
		times = data[index:(index+5)]
		arrs = []
		for t in times:
			arrs.append(deserialize_ping_data(t))
		rxy_min = min(arrs[2]) - min(arrs[3]) - min(arrs[4]) + min(arrs[0]) + min(arrs[1])
		rxy_fifth = fifth(arrs[2]) - fifth(arrs[3]) - fifth(arrs[4]) + min(arrs[0]) + min(arrs[1])
		rxys_min.append(rxy_min)
		rxys_fifth.append(rxy_fifth)
		index = index + 5
		trial_num = trial_num + 1

	print(rxys_min)
	print(rxys_fifth)
