#
# Created by Frank Cangialosi 12/9/13
#

import urllib
import urllib2
from bs4 import BeautifulSoup
import argparse
import datetime

parser = argparse.ArgumentParser(description='Pull most recent list of valid Tor exit nodes for the given host and port from torstatus.blutmagie.de')
parser.add_argument('-dp', '--destination-port', help="Specify destination port.",default=8080)
parser.add_argument('-di', '--destination-ip', help="Specify destination ip address.", default='128.8.126.92')
parser.add_argument('-v', '--verbose', action='store_true')
args = vars(parser.parse_args())    

if(args['verbose']):
    print("Finding all valid Tor exit nodes that can access {0} at {1}".format(args['destination_ip'],args['destination_port']))
ips = []
iplist = urllib.urlopen('http://torstatus.blutmagie.de/ip_list_exit.php/Tor_ip_list_EXIT.csv')
for ip in iplist.readlines():
    ips.append(ip.strip())
iplist.close

f = open("data/nodes/validexits_{0}_{1}.txt".format(args['destination_ip'],args['destination_port']), 'w+')
f.write("# %s\n" % str(datetime.datetime.now()))
f.write("# ROUTER_NAME, IP, FINGERPRINT, HOSTNAME, COUNTRY, PLATFORM, UPTIME, BANDWITH(Max/Burse/Observed in Bps), FAMILY, ROUTER_FLAGS\n")
count = 1
reachable_count = 0
total = len(ips)
try:
    for ip in ips:
        if(args['verbose']):
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
            if(args['verbose']):
    	       print '\tThis ip does allow exiting to bluepill!'
            name = ""
            fp = ""
            for a in soup.body.find_all('a', attrs={'class':'plain'}):
                if a['href'] and 'router_detail' in a['href']:
                    name = a.text.encode('ascii', 'replace')
                    fp = a['href'][21:]
                    url = 'http://torstatus.blutmagie.de/' + a['href']

            f.write("%s, %s, %s, " % (name,ip,fp))

            response = urllib2.urlopen(url)
            page = response.read()
            soup = BeautifulSoup(page)

            keys = ['Hostname:', 'Country Code:', 'Platform / Version:', 'Current Uptime:', 'Bandwidth (Max/Burst/Observed - In Bps):', 'Family:']
            props = {}
            trs = soup.body.find_all('tr')
            for tr in trs[2:]:
                tds = tr.find_all('td')
                if tds[0].text in keys:
                    text = tds[1].text.encode('ascii','ignore')
                    props[tds[0].text] = text
            
            props[keys[3]] = props[keys[3]].replace(',','')
            f.write("%s, %s, %s, %s, %s, %s, " % (props[keys[0]],props[keys[1]],props[keys[2]],props[keys[3]],props[keys[4]],props[keys[5]]))

            for tr in soup.body.find_all('tr', attrs={'class':'nr'}):
                tds = tr.find_all('td')
                if(tds[1].attrs['class'][0] == 'F1'):
                    f.write("%s " % tds[0].text.encode('ascii','ignore').replace(':','').replace(' ','').upper())
            f.write("\n")
            
finally:
    f.close
    if(args['verbose']):
        print '==========================================='
        print 'Successfully found', reachable_count, ' exit nodes that allow exiting to bluepill.'

