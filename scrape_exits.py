#
# Created by Frank Cangialosi 12/9/13
#

import urllib
import urllib2
from bs4 import BeautifulSoup

ips = []

iplist = open('Tor_ip_list_EXIT.csv', 'rb')
for ip in iplist.readlines():
    ips.append(ip.strip())
iplist.close

f = open("exits.txt", 'w')

count = 1
reachable_count = 0
total = len(ips)
try:
    for ip in ips:
        print "Querying {0} ({1}/{2})".format(ip,count,total)
        count += 1

        url = "http://torstatus.blutmagie.de/tor_exit_query.php"
        values = {'QueryIP':ip,'DestinationIP':'128.8.126.92','DestinationPort':'8080'}

        data = urllib.urlencode(values)
        req = urllib2.Request(url,data)
        response = urllib2.urlopen(req)
        page = response.read()

        soup = BeautifulSoup(page)

        allowed = False
        for font in soup.body.find_all('font', attrs={'color':'#00dd00'}):
            if 'would allow exiting' in font.text:
                allowed = True

        if allowed:
            reachable_count += 1
    	    print '\tThis ip does allow exiting to bluepill!'
            name = ""
            fp = ""
            for a in soup.body.find_all('a', attrs={'class':'plain'}):
                if a['href'] and 'router_detail' in a['href']:
                    name = a.text.encode('ascii', 'replace')
                    fp = a['href'][21:]
            f.write("%s %s\n" % (name,fp))
finally:
    f.close
    print '==========================================='
    print 'Successfully found', reachable_count, ' exit nodes that allow exiting to bluepill.'

