#!/usr/bin/env python
#Copyright (C) 2011 Thomas Stewart <thomas@stewarts.org.uk>
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

import getopt
import urllib, urllib2
import StringIO, lxml.etree
import time, datetime
import vobject
import sys, pprint; pp = pprint.PrettyPrinter(depth=6)

memberid = 0
memberpin = 0
listonly = False

try:
        opts, args = getopt.getopt(sys.argv[1:], "hil",
                ["help", "memberid=", "memberpin=", "list"])
except getopt.error, msg:
        print str(msg)
        sys.exit(2)

for o, a in opts:
        if o in ("-h", "--help"):
                print "hsv [options...]"
                print "Utility to download and parse Hertfordshire Sports Village class"
                print "bookings and ouput ical file"
                print "  -h --help        this info"
                print "     --memberid  hsv member id"
                print "     --memberpin hsv member pin"
                print "  -l --list      dont generate ics"
                sys.exit()

        elif o in ("--memberid"):
                memberid = int(a)

        elif o in ("--memberpin"):
                memberpin = int(a)

        elif o in ("-l", "--list"):
                listonly = True

if(memberid == 0 or memberpin == 0):
        print "Error: memberid or memberpin not set"
        sys.exit()

def dump_doc(doc):
        f = open("t.html", "w")
        doc.write(f)
        f.close()
        sys.exit()

class NoRedirectHandler(urllib2.HTTPRedirectHandler):
        def http_error_302(self, req, fp, code, msg, headers):
                infourl = urllib.addinfourl(fp, headers, req.get_full_url())
                infourl.status = code
                infourl.code = code
                return infourl

site = 'http://hsvbookings.herts.ac.uk'
url = site + '/Connect/mrmlogin.aspx'
req = urllib2.urlopen(url)
time.sleep(5)
html = req.read()
html = StringIO.StringIO(html)
doc = lxml.etree.parse(html, lxml.etree.HTMLParser())
#dump_doc(doc)

params = {}
params['__VIEWSTATE'] = doc.xpath('//input[@name="__VIEWSTATE"]/@value')[0]
params['__VIEWSTATEENCRYPTED'] = ''
params['__EVENTVALIDATION'] \
        = doc.xpath('//input[@name="__EVENTVALIDATION"]/@value')[0]
params['ctl00$MainContent$InputLogin'] = memberid
params['ctl00$MainContent$JavascriptEnabled'] = ''
params['ctl00$MainContent$InputPassword'] = memberpin
params['ctl00$MainContent$btnLogin'] = 'Login'
params['ctl00$MemberSearchCtl$txtSearchField'] = ''
params['ctl00$MemberSearchCtl$ddlFindMethod'] = '0'

opener = urllib2.build_opener(NoRedirectHandler)
urllib2.install_opener(opener)
req = urllib2.urlopen(urllib2.Request(url, urllib.urlencode(params)))
time.sleep(5)
cookie = req.info()['Set-Cookie']
html = req.read()
html = StringIO.StringIO(html)
doc = lxml.etree.parse(html, lxml.etree.HTMLParser())
#dump_doc(doc)
url = site + urllib.unquote(doc.xpath('//a/@href')[0])

headers = { 'Cookie' : cookie }
req = urllib2.urlopen(urllib2.Request(url, headers=headers))
time.sleep(5)
html = req.read()
html = StringIO.StringIO(html)
doc = lxml.etree.parse(html, lxml.etree.HTMLParser())
#dump_doc(doc)
url = site + urllib.unquote(doc.xpath('//li[@id="ctl00_ctl09_ManageBookingsli"]/a/@href')[0])

req = urllib2.urlopen(urllib2.Request(url, headers=headers))
time.sleep(5)
html = req.read()
html = StringIO.StringIO(html)
doc = lxml.etree.parse(html, lxml.etree.HTMLParser())
#dump_doc(doc)

events = []
for event in doc.xpath('//table[@class="viewMyBookingsTable"]/tr'):
        if(len(event.xpath('td/span/text()')) == 0):
                continue
        location = event.xpath('td/span/text()')[0]
        eventdsc = event.xpath('td[4]/text()')[0].strip().split(' ')[0]

        year = str(datetime.datetime.now().year)
        daymonth = event.xpath('td[2]/text()')[0].strip().split(' ')[1:3]
        setime = event.xpath('td[3]/text()')[0].strip().split(' ')
        stime = setime[0]
        etime = setime[2]

        stime = stime + ' ' + daymonth[0] + '/' + daymonth[1] + '/' + year
        stime = datetime.datetime(*(time.strptime(stime, "%H:%M %d/%b/%Y")[0:6]))
        stime = stime.strftime("%Y%m%dT%H%M00")

        etime = etime + ' ' + daymonth[0] + '/' + daymonth[1] + '/' + year
        etime = datetime.datetime(*(time.strptime(etime, "%H:%M %d/%b/%Y")[0:6]))
        etime = etime.strftime("%Y%m%dT%H%M00")

        events.append([location, eventdsc, stime, etime])

events = sorted(events, key=lambda event: event[2])
if(listonly):
     pp.pprint(events)
     sys.exit()

cal = vobject.iCalendar()
cal.add('method').value = 'PUBLISH'
for event in events:
        vevent = cal.add('vevent')
        vevent.add('summary').value = event[1]
        vevent.add('location').value = event[0]
        vevent.add('dstart').value = event[2]
        vevent.add('dsend').value = event[3]

print cal.serialize()

