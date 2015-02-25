#!/usr/bin/env python

import imp
try:
    imp.find_module('requests')
except ImportError:
    print('requests not found, try: pip install requests')
    exit()

try:
    imp.find_module('pushbullet')
except ImportError:
    print('pushbullet not found, try: pip install pushbullet.py')
    exit()


import gc
import os
import time
import argparse
import json
import requests
import ConfigParser
from pushbullet import PushBullet

gc.disable()

_author_ = 'dynasticorpheus@gmail.com'
_version_ = '1.0.5'

parser = argparse.ArgumentParser(description='Gigaset Elements - Command-line Interface by dynasticorpheus@gmail.com')
parser.add_argument('-u', '--username', help='username (email) in use with my.gigaset-elements.com', required=False)
parser.add_argument('-p', '--password', help='password in use with my.gigaset-elements.com', required=False)
parser.add_argument('-c', '--config', help='filename of configuration-file', required=False)
parser.add_argument('-n', '--notify', help='pushbullet token', required=False)
parser.add_argument('-e', '--events', help='show last <number> of events', type=int, required=False)
parser.add_argument('-m', '--modus', help='set modus', required=False, choices=('home', 'away', 'custom'))
parser.add_argument('-s', '--status', help='show system / sensor status', action='store_true', required=False)
parser.add_argument('-w', '--warning', help='suppress authentication warnings', action='store_true', required=False)
parser.add_argument('-v', '--version', help='show version', action='version', version="%(prog)s version "+str(_version_))
args = parser.parse_args()


s = requests.Session()


def configure():
    if args.warning is True:
        requests.packages.urllib3.disable_warnings()
    if args.config is None:
        pass
    else:
        if os.path.exists(args.config) == False:
            print('[-]  File does not exist '+args.config)
            print
            exit()
        print('[-]  Reading configuration from '+args.config)
        config = ConfigParser.ConfigParser()
        config.read(args.config)
        if args.username is None:
            args.username = config.get("accounts", "username")
        if args.username == '':
            args.username = None
        if args.password is None:
            args.password = config.get("accounts", "password")
        if args.password == '':
            args.password = None
        if args.modus is None:
            args.modus = config.get("options", "modus")
        if args.modus == '':
            args.modus = None
        if args.notify is None:
            args.notify = config.get("accounts", "pbtoken")
        if args.notify == '':
            args.notify = None
        if args.warning is True:
            requests.packages.urllib3.disable_warnings()
        else:
            if config.getboolean("options", "nowarning"):
                requests.packages.urllib3.disable_warnings()
        return


def connect():
    global my_basestation
    payload = {'password': args.password, 'email': args.username}
    r = s.post("https://im.gigaset-elements.de/identity/api/v1/user/login", data=payload)
    commit_data = r.json()
    if(r == ''):
        print "[-] Connection error"
        print
        exit()

    elif(commit_data["status"] == 'ok'):
        print('[-] '),
        print(commit_data["message"])
        my_reefssid = commit_data["reefssid"]
        r2 = s.get('https://api.gigaset-elements.de/api/v1/auth/openid/begin?op=gigaset')
        print('[-] '),
        print(r2.text)
        r3 = s.get('https://api.gigaset-elements.de/api/v1/me/basestations')
        basestation_data = r3.json()
        my_basestation = basestation_data[0]["id"]
        print('[-]  Basestation'),
        print(my_basestation)
    else:
        print "[-]  Authentication error"
        print
        exit()
        return


def modus_switch():
    switch = {"intrusion_settings": {"active_mode": args.modus}}
    r4 = s.post('https://api.gigaset-elements.de/api/v1/me/basestations/'+my_basestation, data=json.dumps(switch))
    return


def pb_message():
    if args.notify is None:
        pass
    else:
        pb = PushBullet(args.notify)
        push = pb.push_note("Gigaset Elements", 'Modus set to '+args.modus.upper())
        print "[-]  PushBullet notification sent"
    return


def list_events():
    print "[-]  Showing last "+str(args.events)+" event(s)"
    r5 = s.get('https://api.gigaset-elements.de/api/v1/me/events?limit='+str(args.events))
    event_data = r5.json()
    for item in event_data["events"]:
        try:
            print("[-] "),
            print(time.strftime('%m/%d/%Y %H:%M:%S',  time.localtime(int(item['ts'])/1000))),
            print item['type'],
            print item['o']['friendly_name']
        except KeyError:
            print
            continue
    return


def status():
    r6 = s.get('https://api.gigaset-elements.de/api/v1/me/basestations')
    sensor_data = r6.json()
    print("[-] "),
    print(sensor_data[0]["friendly_name"]),
    print(sensor_data[0]["status"]),
    print "| firmware",
    print(sensor_data[0]["firmware_status"])
    for item in sensor_data[0]["sensors"]:
        try:
            print("[-] "),
            print item['friendly_name'],
            print item['status'],
            print "| firmware",
            print item['firmware_status'],
            if item['type'] != "is01":
                print "| battery",
                print item['battery']['state'],
            if item['type'] == "ds02":
                print "| position",
                print item['position_status'],
            print
        except KeyError:
            print
            continue

    r7 = s.get('https://api.gigaset-elements.de/api/v1/me/events?limit=1')
    status_data = r7.json()
    print("[-]  Home status "+status_data["home_state"])
    return


try:
    print
    print "Gigaset Elements - Command-line Interface"
    print

    configure()
    connect()


    if args.modus is None:
        pass
    else:
        modus_switch()
        print "[-]  Modus set to "+args.modus.upper()
        pb_message()


    if args.status is not True:
        pass
    else:
        status()


    if args.events is None:
        pass
    else:
        list_events()


    print

except KeyboardInterrupt:
    print("[-]  CTRL+C detected program halted")

