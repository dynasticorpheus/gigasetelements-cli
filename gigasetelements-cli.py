#!/usr/bin/env python

_author_  = 'dynasticorpheus@gmail.com'
_version_ = '1.0.2'

import gc ; gc.disable()
import os
import time
import argparse 
import json 
import requests
import ConfigParser
from pushbullet import PushBullet


parser = argparse.ArgumentParser(description='Gigaset Elements - Command Line Interface by dynasticorpheus@gmail.com')
parser.add_argument('-u','--username', help='username (email) in use with my.gigaset-elements.com', required=False)
parser.add_argument('-p','--password', help='password in use with my.gigaset-elements.com',required=False)
parser.add_argument('-c','--config', help='filename of configuration-file',required=False)
parser.add_argument('-n','--notify', help='pushbullet token',required=False)
parser.add_argument('-e','--events', help='show last <number> of events',type=int, required=False)
parser.add_argument('-m','--modus', help='set modus',required=False, choices=('home', 'away', 'custom'))
parser.add_argument('-s','--status', help='show system status', action='store_true', required=False)
parser.add_argument('-w','--warning', help='suppress authentication warnings', action='store_true', required=False)
parser.add_argument('-v','--version', help='show version', action='version', version="%(prog)s version "+str(_version_))
args = parser.parse_args()


if args.warning != True : pass
else:
	requests.packages.urllib3.disable_warnings()


s = requests.Session()


def configure() :
	if args.config == None : pass
	else:
		if os.path.exists(args.config) == False : print('[-]  File does not exist '+args.config) ; print ; exit()
		print('[-]  Reading configuration from '+args.config)
		config = ConfigParser.ConfigParser()
		config.read(args.config)
		if args.username == None : args.username = config.get("general", "username")
		if args.password == None : args.password = config.get("general", "password")
		if args.modus == None : args.modus = config.get("general", "modus")
		if args.notify == None : args.notify = config.get("general", "notify")
		if args.notify == '' : args.notify = None
		return;


def connect() :
        global my_basestation
	payload = {'password': args.password, 'email': args.username}
	r = s.post("https://im.gigaset-elements.de/identity/api/v1/user/login", data=payload)
	commit_data = r.json()
	if ( r == '' ) : print "[-] Connection error" ; print ; exit()

	elif ( commit_data["status"] == 'ok' ) :
		print('[-] '), ; print(commit_data["message"])
                my_reefssid = commit_data["reefssid"]
		r2 = s.get('https://api.gigaset-elements.de/api/v1/auth/openid/begin?op=gigaset')
		print('[-] '), ; print(r2.text)
		r3 = s.get('https://api.gigaset-elements.de/api/v1/me/basestations')
		basestation_data = r3.json()
		my_basestation = basestation_data[0]["id"]
		print('[-]  Basestation'), ; print(my_basestation)
	else:	
 		print "[-]  Authentication error" ; print ; exit()
	return;


def modus_switch() :
	switch = {"intrusion_settings":{"active_mode":args.modus}} 
	r4 = s.post('https://api.gigaset-elements.de/api/v1/me/basestations/'+my_basestation, data=json.dumps(switch))
	return;


def pb_message() :
	if args.notify == None : pass
	else:
		pb = PushBullet(args.notify)
		push = pb.push_note("Gigaset Elements", 'Modus set to '+args.modus.upper())
		print "[-]  PushBullet notification sent"
	return;


def list_events() :
	print "[-]  Showing last "+str(args.events)+" event(s)"
	r5 = s.get('https://api.gigaset-elements.de/api/v1/me/events?limit='+str(args.events))
	event_data = r5.json()
	for item in event_data["events"]:
		try:
			print("[-] "), ; print(time.strftime('%m/%d/%Y %H:%M:%S',  time.localtime(int(item['ts'])/1000))),
			print item['type'],
			print item['o']['friendly_name']
		except KeyError:
			print
			continue
	return;


def status() :
	r6 = s.get('https://api.gigaset-elements.de/api/v1/me/events?limit=1')
	status_data = r6.json()
	print("[-]  Status "+status_data["home_state"])
	return;


print
print "Gigaset Elements - Command Line Interface"
print

configure()
connect()


if args.modus == None : pass
else:
	modus_switch()
	print "[-]  Modus set to "+args.modus.upper()
	pb_message()


if args.status != True : pass
else:
	status()


if args.events == None : pass
else:
	list_events()


print
