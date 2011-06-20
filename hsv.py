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

try:
        opts, args = getopt.getopt(sys.argv[1:], "h",
                ["help", "memberid=", "memberpin="])
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
                sys.exit()

        elif o in ("--memberid"):
                memberid = int(a)

        elif o in ("--memberpin"):
                memberpin = int(a)

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
html = req.read()
html = StringIO.StringIO(html)
doc = lxml.etree.parse(html, lxml.etree.HTMLParser())

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
cookie = req.info()['Set-Cookie']
html = req.read()
html = StringIO.StringIO(html)
doc = lxml.etree.parse(html, lxml.etree.HTMLParser())
url = site + urllib.unquote(doc.xpath('//a/@href')[0])

headers = { 'Cookie' : cookie }
req = urllib2.urlopen(urllib2.Request(url, headers=headers))
html = req.read()
html = StringIO.StringIO(html)
doc = lxml.etree.parse(html, lxml.etree.HTMLParser())

events = []
for event in doc.xpath(
                '//div[@id="ctl00_UpcomingBookings1_TodaysBookingsPanel"]/table/tr'):
        atime = event.xpath('td/text()')[0]
        year = str(datetime.datetime.now().year)
        atime = year + "/" + atime
        atime = datetime.datetime(*(time.strptime(atime, "%Y/%d/%m %H:%M")[0:6]))
        atime = atime.isoformat(' ')

        event = event.xpath('td/a/@title')[0].split(' ')[0].strip()
        events.append([atime, event])


events.sort()

cal = vobject.iCalendar()
for e in events:
        event = cal.add('vevent')
        event.add('summary').value = e[1]
        event.add('location').value = "Hertfordshire Sports Village"
        event.add('dstart').value = e[0]
        event.add('dsend').value = e[0]

print cal.serialize()

