#!/usr/bin/python2.5
"""
    This file is part of SleekXMPP.

    SleekXMPP is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    SleekXMPP is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with SleekXMPP; if not, write to the Free Software
    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""

import logging
import sleekxmpp.sleekxmpp as sleekxmpp
from optparse import OptionParser
from xml.etree import ElementTree as ET
import os
import time
import csv

class Account(object):
    def __init__(self, jid, password):
        self.jid = jid
        self.password = password
        self.rosterEntries = []
        
class RosterEntry(object):
    def __init__(self, jid, groups, name, subscription):
        self.jid = jid
        self.groups = groups
        self.name = name
        self.subscription = subscription

class TigaseCSVExporter(object):
    def __init__(self, fileName):
        self.out = file(fileName, 'w')
        pass
        
    def export(self, user):
        logging.info("Exporting account " + user.jid)
        
    def finalise(self):
        pass

class XMPPAccountExtractor(sleekxmpp.xmppclient):
    def __init__(self, jid, password, ssl=False, plugin_config = {}, plugin_whitelist=[]):
        sleekxmpp.xmppclient.__init__(self, jid, password, ssl, plugin_config, plugin_whitelist)
        logging.info("Logging in as %s" % self.jid)
        self.add_event_handler("session_start", self.start, threaded=True)
        self.add_event_handler("roster_update", self.receive_roster)
        self.add_event_handler("vcard_result", self.receive_vcard)
        self.account = Account(jid, password)
        self.rosterDone = False
        self.vcardDone = False
	
    def start(self, event):
        self.requestRoster()
        #self.requestVcard(self.jid)
        while not self.vcardDone and not self.rosterDone:
            time.sleep(1)
        self.disconnect()
	
    def receive_roster(self, event):
        for jid in event:
            self.account.rosterEntries.append(RosterEntry(jid, event[jid]['groups'], event[jid]['name'], event[jid]['subscription']))
        self.rosterDone = True
			
    def receive_vcard(self, event):
        pass
        #print event
        #self.vcardDone = True
        
    def getAccount(self):
        return self.account

def authDetailsFromFile(filename):
    """ Return a list of auth dicts
    """
    reader = csv.reader(open(filename, "rb"))
    auths = []
    for row in reader:
        auths.append({'jid':row[0],'pass':row[1]})
    return auths

if __name__ == '__main__':
    #parse command line arguements
    optp = OptionParser()
    optp.add_option('-q','--quiet', help='set logging to ERROR', action='store_const', dest='loglevel', const=logging.ERROR, default=logging.INFO)
    optp.add_option('-d','--debug', help='set logging to DEBUG', action='store_const', dest='loglevel', const=logging.DEBUG, default=logging.INFO)
    optp.add_option('-v','--verbose', help='set logging to COMM', action='store_const', dest='loglevel', const=5, default=logging.INFO)
    optp.add_option('-s','--server', help='override connection server', dest='hostname', default=None)
    #optp.add_option("-c","--config", dest="configfile", default="config.xml", help="set config file to use")
    optp.add_option("-f","--user-file", dest="userFile", default="users.csv", help="name of CSV uname/password pairs file")
    opts,args = optp.parse_args()
	
    logging.basicConfig(level=opts.loglevel, format='%(levelname)-8s %(message)s')

    #load xml config
    logging.info("Loading user file: %s" % opts.userFile)
    authDetails = authDetailsFromFile(opts.userFile)
    #config = ET.parse(os.path.expanduser(opts.configfile)).find('auth')
	

	
	
    plugin_config = {}
    #plugin_config['xep_0092'] = {'name': 'SleekXMPP Example', 'version': '0.1-dev'}
    #plugin_config['xep_0199'] = {'keepalive': True, 'timeout': 30, 'frequency': 300}
    exporter = TigaseCSVExporter()
	
    for auth in authDetails:
        extractor = XMPPAccountExtractor(auth['jid'], auth['pass'], plugin_config=plugin_config, plugin_whitelist=[])
        if opts.hostname is None:
            extractor.connect() 
        else:
            extractor.connect((opts.hostname, 5222))
        extractor.process()
        while extractor.connected:
            time.sleep(1)
        exporter.export(extractor.getAccount())
    exporter.finalise()
