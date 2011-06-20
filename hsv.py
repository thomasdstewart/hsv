#!/usr/bin/env python
import urllib, urllib2
import StringIO, lxml.etree
import time, datetime
import vobject
import sys, pprint; pp = pprint.PrettyPrinter(depth=6)

memberid = 
memberpin = 

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

