#!/usr/bin/env python

import imp
try:
    imp.find_module('requests')
except ImportError:
    print('[-] requests not found, try: pip install requests')
    sys.exit()


import gc
import os
import sys
import time
import argparse
import json
import requests
import ConfigParser

gc.disable()

_author_ = 'dynasticorpheus@gmail.com'
_version_ = '1.1.0'

parser = argparse.ArgumentParser(description='Gigaset Elements - Command-line Interface by dynasticorpheus@gmail.com')
parser.add_argument('-c', '--config', help='fully qualified name of configuration-file', required=False)
parser.add_argument('-u', '--username', help='username (email) in use with my.gigaset-elements.com', required=False)
parser.add_argument('-p', '--password', help='password in use with my.gigaset-elements.com', required=False)
parser.add_argument('-n', '--notify', help='pushbullet token', required=False)
parser.add_argument('-e', '--events', help='show last <number> of events', type=int, required=False)
parser.add_argument('-d', '--date', help='filter events on begin date - end date (DD/MM/YYYY)', required=False, nargs=2)
parser.add_argument('-f', '--filter', help='filter events on type', required=False, choices=('door', 'motion', 'siren', 'homecoming', 'intrusion', 'systemhealth'))
parser.add_argument('-m', '--modus', help='set modus', required=False, choices=('home', 'away', 'custom'))
parser.add_argument('-s', '--status', help='show sensor status', action='store_true', required=False)
parser.add_argument('-i', '--ignore', help='ignore configuration-file at default locations', action='store_true', required=False)
parser.add_argument('-w', '--warning', help='suppress urllib3 warnings', action='store_true', required=False)
parser.add_argument('-v', '--version', help='show version', action='version', version='%(prog)s version ' + str(_version_))
args = parser.parse_args()


s = requests.Session()

url_identity = 'https://im.gigaset-elements.de/identity/api/v1/user/login'
url_events = 'https://api.gigaset-elements.de/api/v1/me/events'
url_auth = 'https://api.gigaset-elements.de/api/v1/auth/openid/begin?op=gigaset'
url_base = 'https://api.gigaset-elements.de/api/v1/me/basestations'


def configure():
    if args.config is None:
        if os.path.exists('/opt/etc/gigasetelements-cli.conf'):
            args.config = '/opt/etc/gigasetelements-cli.conf'
        if os.path.exists('/usr/local/etc/gigasetelements-cli.conf'):
            args.config = '/usr/local/etc/gigasetelements-cli.conf'
        if os.path.exists('/usr/etc/gigasetelements-cli.conf'):
            args.config = '/usr/etc/gigasetelements-cli.conf'
        if os.path.exists('/etc/gigasetelements-cli.conf'):
            args.config = '/etc/gigasetelements-cli.conf'
        if os.path.exists(os.path.expanduser('~/.gigasetelements-cli/gigasetelements-cli.conf')):
            args.config = os.path.expanduser('~/.gigasetelements-cli/gigasetelements-cli.conf')
        if args.ignore:
            args.config = None
    else:
        if os.path.exists(args.config) == False:
            print('[-] File does not exist ' + args.config)
            print
            sys.exit()
    if args.config is not None:
        print('[-] Reading configuration from ' + args.config)
        config = ConfigParser.ConfigParser()
        config.read(args.config)
        if args.username is None:
            args.username = config.get('accounts', 'username')
        if args.username == '':
            args.username = None
        if args.password is None:
            args.password = config.get('accounts', 'password')
        if args.password == '':
            args.password = None
        if args.modus is None:
            args.modus = config.get('options', 'modus')
        if args.modus == '':
            args.modus = None
        if args.notify is None:
            args.notify = config.get('accounts', 'pbtoken')
        if args.notify == '':
            args.notify = None
        if args.warning:
            requests.packages.urllib3.disable_warnings()
        else:
            if config.getboolean('options', 'nowarning'):
                requests.packages.urllib3.disable_warnings()
        return
    if None in (args.username, args.password):
        print '[-] Username and/or password missing'
        print
        sys.exit()
    if args.warning:
        requests.packages.urllib3.disable_warnings()


def connect():
    global my_basestation
    global basestation_data
    global status_data
    payload = {'password': args.password, 'email': args.username}
    try:
        r = s.post(url_identity, data=payload)
    except requests.exceptions.RequestException as e:
        print '[-] ' + str(e.message)
        sys.exit()
    commit_data = r.json()
    if r.status_code == requests.codes.ok:
        print('[-] ' + commit_data['message'])
        r = s.get(url_auth)
        if r.status_code != requests.codes.ok:
            commit_data = r.json()
            print('[-] ' + str(r.status_code) + ' ' + commit_data['error']['message'])
            sys.exit()
        print('[-] ' + r.text)
        r = s.get(url_base)
        basestation_data = r.json()
        my_basestation = basestation_data[0]['id']
        print('[-] Basestation ' + my_basestation)
        r = s.get(url_events + '?limit=1')
        status_data = r.json()
        if args.modus is None:
            print('[-] System status ' + status_data['home_state'].upper() + ' | Modus ' + basestation_data[0]['intrusion_settings']['active_mode'].upper())
    else:
        print('[-] ' + str(r.status_code) + ' ' + commit_data['message'])
        sys.exit()
        return


def modus_switch():
    switch = {'intrusion_settings': {'active_mode': args.modus}}
    r = s.post(url_base + '/' + my_basestation, data=json.dumps(switch))
    print '[-] Status ' + status_data['home_state'].upper() + ' | Modus set from ' + basestation_data[0]['intrusion_settings']['active_mode'].upper() + ' to ' + args.modus.upper()
    return


def pb_message(pbmsg):
    if args.notify is None:
        pass
    else:
        try:
            imp.find_module('pushbullet')
        except ImportError:
            print('[-] pushbullet not found, try: pip install pushbullet.py')
            sys.exit()
        from pushbullet import PushBullet
        pb = PushBullet(args.notify)
        push = pb.push_note('Gigaset Elements', pbmsg)
        print '[-] PushBullet notification sent'
    return


def list_events():
    if args.filter is None and args.date is None:
        print '[-] Showing last ' + str(args.events) + ' event(s)'
        r = s.get(url_events + '?limit=' + str(args.events))
    if args.filter is not None and args.date is None:
        print '[-] Showing last ' + str(args.events) + ' ' + str(args.filter).upper() + ' event(s)'
        r = s.get(url_events + '?limit=' + str(args.events) + '&group=' + str(args.filter))
    if args.date is not None:
        try:
            from_ts = str(int(time.mktime(time.strptime(args.date[0], '%d/%m/%Y'))) * 1000)
            to_ts = str(int(time.mktime(time.strptime(args.date[1], '%d/%m/%Y'))) * 1000)
        except:
            print('[-] Date(s) provided not in DD/MM/YYYY format')
            print
            sys.exit()
    if args.filter is None and args.date is not None:
        print '[-] Showing event(s) between ' + args.date[0] + ' and ' + args.date[1]
        r = s.get(url_events + '?from_ts=' + from_ts + '&to_ts=' + to_ts + '&limit=999')
    if args.filter is not None and args.date is not None:
        print '[-] Showing ' + str(args.filter).upper() + ' event(s) between ' + args.date[0] + ' and ' + args.date[1]
        r = s.get(url_events + '?from_ts=' + from_ts + '&to_ts=' + to_ts + '&group=' + str(args.filter) + '&limit=999')
    event_data = r.json()
    for item in event_data['events']:
        try:
            print('[-] ' + time.strftime('%m/%d/%Y %H:%M:%S', time.localtime(int(item['ts']) / 1000))) + ' ' + item['type'] + ' ' + item['o']['friendly_name']
        except KeyError:
            continue
    return


def status():
    print('[-] ') + basestation_data[0]['friendly_name'] + ' ' + basestation_data[0]['status'].upper() + ' | firmware ' + basestation_data[0]['firmware_status'].upper()
    for item in basestation_data[0]['sensors']:
        try:
            print('[-] ') + item['friendly_name'] + ' ' + item['status'].upper() + '| firmware ' + item['firmware_status'].upper(),
            if item['type'] != 'is01':
                print '| battery ' + item['battery']['state'].upper(),
            if item['type'] == 'ds02':
                print '| position ' + item['position_status'].upper(),
            print
        except KeyError:
            print
            continue
    return


try:
    print
    print 'Gigaset Elements - Command-line Interface'
    print

    configure()
    connect()

    if args.modus is not None:
        modus_switch()
        if args.status is not True:
            pb_message('Status ' + status_data['home_state'].upper() + ' | Modus set from ' + basestation_data[0]['intrusion_settings']['active_mode'].upper() + ' to ' + args.modus.upper())

    if args.status:
        status()
        pb_message('Status ' + status_data['home_state'].upper() + ' | Modus ' + basestation_data[0]['intrusion_settings']['active_mode'].upper())

    if args.events is not None and args.date is not None:
        list_events()

    print

except KeyboardInterrupt:
    print('[-] CTRL+C detected program halted')
