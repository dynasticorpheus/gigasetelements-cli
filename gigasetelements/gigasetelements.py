#!/usr/bin/env python

import imp
import gc
import os
import sys
import time
import datetime
import argparse
import json
import ConfigParser

import requests
import colorama
from crontab import CronTab
from pushbullet import PushBullet


_author_ = 'dynasticorpheus@gmail.com'
_version_ = '1.2.1'

parser = argparse.ArgumentParser(description='Gigaset Elements - Command-line Interface by dynasticorpheus@gmail.com')
parser.add_argument('-c', '--config', help='fully qualified name of configuration-file', required=False)
parser.add_argument('-u', '--username', help='username (email) in use with my.gigaset-elements.com', required=False)
parser.add_argument('-p', '--password', help='password in use with my.gigaset-elements.com', required=False)
parser.add_argument('-n', '--notify', help='pushbullet token', required=False, metavar='TOKEN')
parser.add_argument('-e', '--events', help='show last <number> of events', type=int, required=False)
parser.add_argument('-d', '--date', help='filter events on begin date - end date', required=False, nargs=2, metavar='DD/MM/YYYY')
parser.add_argument('-o', '--cronjob', help='schedule cron job at HH:MM (requires -m option)', required=False, metavar='HH:MM')
parser.add_argument('-r', '--remove', help='remove all cron jobs linked to this program', action='store_true', required=False)
parser.add_argument('-f', '--filter', help='filter events on type', required=False, choices=('door', 'motion', 'siren', 'homecoming', 'intrusion', 'systemhealth'))
parser.add_argument('-m', '--modus', help='set modus', required=False, choices=('home', 'away', 'custom'))
parser.add_argument('-s', '--sensor', help='show sensor status', action='store_true', required=False)
parser.add_argument('-a', '--camera', help='show camera status', action='store_true', required=False)
parser.add_argument('-i', '--ignore', help='ignore configuration-file at predefined locations', action='store_true', required=False)
parser.add_argument('-q', '--quiet', help='do not send pushbullet message', action='store_true', required=False)
parser.add_argument('-w', '--warning', help='suppress urllib3 warnings', action='store_true', required=False)
parser.add_argument('-v', '--version', help='show version', action='version', version='%(prog)s version ' + str(_version_))

gc.disable()
colorama.init()
args = parser.parse_args()
s = requests.Session()

url_identity = 'https://im.gigaset-elements.de/identity/api/v1/user/login'
url_auth = 'https://api.gigaset-elements.de/api/v1/auth/openid/begin?op=gigaset'
url_events = 'https://api.gigaset-elements.de/api/v1/me/events'
url_base = 'https://api.gigaset-elements.de/api/v1/me/basestations'
url_camera = 'https://api.gigaset-elements.de/api/v1/me/cameras'
url_test = 'http://httpbin.org/status/503'


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARN = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def log(str, type=0, exit=0):
    if type == 0:
        print '[-] ' + str
    if type == 1:
        print bcolors.OKGREEN + '[-] ' + str + bcolors.ENDC
    if type == 2:
        print bcolors.WARN + '[-] ' + str + bcolors.ENDC
    if type == 3:
        print bcolors.FAIL + '[-] ' + str + bcolors.ENDC
    if exit == 1:
        print
        sys.exit()
    return


def os_type(str):
    if os.name == str:
        return True
    else:
        return False


def color(str):
    normal = ['ok', 'online', 'closed', 'up_to_date', 'home', 'auto', 'on', 'hd', 'cable', 'wifi']
    if str.lower() in normal:
        str = bcolors.OKGREEN + str.upper() + bcolors.ENDC
    else:
        str = bcolors.FAIL + str.upper() + bcolors.ENDC
    return str


def configure():
    global credfromfile
    credfromfile = False
    if args.config is None:
        locations = ['/opt/etc/gigasetelements-cli.conf', '/usr/local/etc/gigasetelements-cli.conf', '/usr/etc/gigasetelements-cli.conf',
                     '/etc/gigasetelements-cli.conf', os.path.expanduser('~/.gigasetelements-cli/gigasetelements-cli.conf')]
        for i in locations:
            if os.path.exists(i):
                args.config = i
        if args.ignore:
            args.config = None
    else:
        if os.path.exists(args.config) == False:
            log('File does not exist ' + args.config, 3, 1)
    if args.config is not None:
        log('Reading configuration from ' + args.config)
        config = ConfigParser.ConfigParser()
        config.read(args.config)
        if args.username is None:
            args.username = config.get('accounts', 'username')
            credfromfile = True
        if args.username == '':
            args.username = None
            credfromfile = False
        if args.password is None:
            args.password = config.get('accounts', 'password')
            credfromfile = True
        if args.password == '':
            args.password = None
            credfromfile = False
        if args.modus is None:
            args.modus = config.get('options', 'modus')
        if args.modus == '':
            args.modus = None
        if args.notify is None:
            args.notify = config.get('accounts', 'pbtoken')
        if args.notify == '':
            args.notify = None
        else:
            if config.getboolean('options', 'nowarning'):
                args.warning = True
        return
    if None in (args.username, args.password):
        log('Username and/or password missing', 3, 1)


def is_json(myjson):
    try:
        json_object = json.loads(myjson)
    except ValueError, e:
        return False
    return True


def restget(url):
    data = ''
    try:
        r = s.get(url, timeout=90, stream=False)
    except requests.exceptions.RequestException as e:
        log(str(e.message), 3, 1)
    if r.status_code != requests.codes.ok:
        log('HTTP error ' + str(r.status_code), 3, 1)
    if is_json(r.text):
        data = r.json()
    if data == '':
        data = r.text
    return data


def restpost(url, payload):
    try:
        r = s.post(url, data=payload, timeout=90, stream=False)
    except requests.exceptions.RequestException as e:
        log(str(e.message), 3, 1)
    if r.status_code != requests.codes.ok:
        log('HTTP error ' + str(r.status_code), 3, 1)
    commit_data = r.json()
    return commit_data


def connect():
    global basestation_data
    global status_data
    if args.warning:
        try:
            requests.packages.urllib3.disable_warnings()
        except:
            pass
    payload = {'password': args.password, 'email': args.username}
    commit_data = restpost(url_identity, payload)
    log(commit_data['message'])
    s.headers['Connection'] = 'close'
    auth_data = restget(url_auth)
    s.headers['Connection'] = 'keep-alive'
    log(auth_data)
    basestation_data = restget(url_base)
    log('Basestation ' + basestation_data[0]['id'])
    status_data = restget(url_events + '?limit=1')
    if args.modus is None:
        log('System status ' + status_data['home_state'].upper() + ' | Modus ' + basestation_data[0]['intrusion_settings']['active_mode'].upper())
    return


def modus_switch():
    switch = {'intrusion_settings': {'active_mode': args.modus}}
    restpost(url_base + '/' + basestation_data[0]['id'], json.dumps(switch))
    log('Status ' + color(status_data['home_state']) + ' | Modus set from ' + color(basestation_data[0]['intrusion_settings']['active_mode']) + ' to ' + color(args.modus))
    return


def isTimeFormat(input):
    try:
        time.strptime(input, '%H:%M')
        return True
    except ValueError:
        return False


def add_cron(schedule):
    if args.modus is None:
        log('Please also specify modus using -m option to schedule cron job', 3, 1)
    if isTimeFormat(args.cronjob):
        cron = CronTab(user=True)
        now = datetime.datetime.now()
        timer = now.replace(hour=time.strptime(args.cronjob, '%H:%M')[3], minute=time.strptime(args.cronjob, '%H:%M')[4], second=0, microsecond=0)
        if credfromfile:
            job = cron.new(command=os.path.realpath(__file__) + ' -m ' + args.modus, comment='added by gigasetelements-cli on ' + str(now)[:16])
        else:
            job = cron.new(command=os.path.realpath(__file__) + ' -u ' + args.username + ' -p ' + args.password + ' -m ' + args.modus, comment='added by gigasetelements-cli on ' + str(now)[:16])
        job.month.on(datetime.datetime.now().strftime('%-m'))
        if now < timer:
            job.day.on(datetime.datetime.now().strftime('%-d'))
        else:
            job.day.on(str((int(datetime.datetime.now().strftime('%-d')) + 1)))
            timer = now.replace(day=(int(datetime.datetime.now().strftime('%-d')) + 1), hour=time.strptime(args.cronjob, '%H:%M')[3], minute=time.strptime(args.cronjob, '%H:%M')[4], second=0, microsecond=0)
        job.hour.on(time.strptime(args.cronjob, '%H:%M')[3])
        job.minute.on(time.strptime(args.cronjob, '%H:%M')[4])
        cron.write()
        log('Cron job scheduled | Modus will be set to ' + color(args.modus) + ' on ' + timer.strftime('%A %d %B %Y %H:%M'))
    else:
        log('Please use valid time (00:00 - 23:59)', 3, 1)
    return


def remove_cron():
    origin = command = os.path.realpath(__file__)
    cron = CronTab(user=True)
    iter = cron.find_command(origin)
    count = 0
    for i in iter:
        log('Cron job removed | ' + str(i))
        count = count + 1
    cron.remove_all(origin)
    cron.write()
    if count == 0:
        log('No cron jobs found for removal | ' + origin)
    return


def pb_message(pbmsg):
    if args.notify is not None and args.quiet is not True:
        try:
            pb = PushBullet(args.notify)
        except pushbullet.errors.InvalidKeyError:
            log('Pushbullet notification not sent due to incorrect token', 2)
        except pushbullet.errors.PushbulletError:
            log('Pushbullet notification not sent due to unknown error', 2)
        else:
            push = pb.push_note('Gigaset Elements', pbmsg)
            log('PushBullet notification sent')
    return


def list_events():
    if args.filter is None and args.date is None:
        log('Showing last ' + str(args.events) + ' event(s)')
        event_data = restget(url_events + '?limit=' + str(args.events))
    if args.filter is not None and args.date is None:
        log('Showing last ' + str(args.events) + ' ' + str(args.filter).upper() + ' event(s)')
        event_data = restget(url_events + '?limit=' + str(args.events) + '&group=' + str(args.filter))
    if args.date is not None:
        try:
            from_ts = str(int(time.mktime(time.strptime(args.date[0], '%d/%m/%Y'))) * 1000)
            to_ts = str(int(time.mktime(time.strptime(args.date[1], '%d/%m/%Y'))) * 1000)
        except:
            log('Please provide date(s) in DD/MM/YYYY format', 3, 1)
    if args.filter is None and args.date is not None:
        log('Showing event(s) between ' + args.date[0] + ' and ' + args.date[1])
        event_data = restget(url_events + '?from_ts=' + from_ts + '&to_ts=' + to_ts + '&limit=999')
    if args.filter is not None and args.date is not None:
        log('Showing ' + str(args.filter).upper() + ' event(s) between ' + args.date[0] + ' and ' + args.date[1])
        event_data = restget(url_events + '?from_ts=' + from_ts + '&to_ts=' + to_ts + '&group=' + str(args.filter) + '&limit=999')
    for item in event_data['events']:
        try:
            print('[-] ' + time.strftime('%m/%d/%Y %H:%M:%S', time.localtime(int(item['ts']) / 1000))) + ' ' + item['type'] + ' ' + item['o']['friendly_name']
        except KeyError:
            continue
    return


def sensor():
    print('[-] ') + basestation_data[0]['friendly_name'] + ' ' + color(basestation_data[0]['status']) + ' | firmware ' + color(basestation_data[0]['firmware_status'])
    for item in basestation_data[0]['sensors']:
        try:
            print('[-] ') + item['friendly_name'] + ' ' + color(item['status']) + ' | firmware ' + color(item['firmware_status']),
            if item['type'] != 'is01':
                print '| battery ' + color(item['battery']['state']),
            if item['type'] == 'ds02':
                print '| position ' + color(item['position_status']),
            print
        except KeyError:
            print
            continue
    return


def camera():
    global camera_data
    camera_data = restget(url_camera)
    if len(camera_data[0]['id']) == 12:
        for item in camera_data:
            try:
                print('[-] ') + camera_data[0]['friendly_name'] + ' ' + color(camera_data[0]['status']) + ' | firmware ' + color(camera_data[0]['firmware_status']),
                print(' | quality ' + color(camera_data[0]['settings']['quality']) + ' | nightmode ' + color(camera_data[0]['settings']['nightmode']) + ' | mic ' + color(camera_data[0]['settings']['mic'])),
                print(' | connection ' + color(camera_data[0]['settings']['connection']) + ' | motion detection ' + color(camera_data[0]['motion_detection']['status']))
            except KeyError:
                print
                continue
    return


def main():
    try:
        print
        print 'Gigaset Elements - Command-line Interface'
        print

        configure()

        if os_type('posix'):
            if args.cronjob is not None:
                add_cron(args.cronjob)
                if args.sensor is False and args.events is None:
                    print
                    sys.exit()
            if args.remove and args.cronjob is None:
                remove_cron()
                if args.sensor is False and args.events is None:
                    print
                    sys.exit()

        connect()

        if args.modus is not None and args.cronjob is None:
            modus_switch()
            if args.sensor is not True:
                pb_message('Status ' + status_data['home_state'].upper() + ' | Modus set from ' + basestation_data[0]['intrusion_settings']['active_mode'].upper() + ' to ' + args.modus.upper())

        if args.camera:
            camera()

        if args.sensor:
            sensor()
            pb_message('Status ' + status_data['home_state'].upper() + ' | Modus ' + basestation_data[0]['intrusion_settings']['active_mode'].upper())

        if args.events is None and args.date is None:
            pass
        else:
            list_events()

        print

    except KeyboardInterrupt:
        log('CTRL+C detected program halted', 3)
