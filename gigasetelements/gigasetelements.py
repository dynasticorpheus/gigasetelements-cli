#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""Main code for gigasetelements command-line interface."""

from __future__ import (absolute_import, division, print_function, unicode_literals)

import os
import sys
import time
import datetime
import json
import logging

from builtins import (dict, int, str, open)
from future.moves.urllib.parse import urlparse

try:
    from colorama import init, Fore
    from requests.packages.urllib3 import disable_warnings
    import requests
    import configargparse
    import unidecode
except ImportError as error:
    sys.exit(str(error) + '. Please install from PyPI: pip install --upgrade ' + str(error).rsplit(None, 1)[-1] + '\n')

if os.name == 'posix':
    try:
        from crontab import CronTab
        from daemonize import Daemonize
    except ImportError as error:
        sys.exit(str(error) + '. Please install from PyPI: pip install --upgrade ' + str(error).rsplit(None, 1)[-1])

if any(arg in sys.argv for arg in ['-i', '--ignore']):
    CONFPATH = []
elif os.name == 'nt':
    CONFPATH = [os.path.join(os.environ['APPDATA'], os.path.normpath('gigasetelements-cli/gigasetelements-cli.conf'))]
else:
    CONFPATH = ['/opt/etc/gigasetelements-cli.conf', '/usr/local/etc/gigasetelements-cli.conf', '/usr/etc/gigasetelements-cli.conf',
                '/etc/gigasetelements-cli.conf', os.path.expanduser('~/.gigasetelements-cli/gigasetelements-cli.conf'),
                os.path.expanduser('~/.config/gigasetelements-cli/gigasetelements-cli.conf'), os.path.expanduser('~/.gigasetelements-cli'),
                os.path.expanduser('~/Library/Application Support/gigasetelements-cli/gigasetelements-cli.conf')]

_AUTHOR_ = 'dynasticorpheus@gmail.com'
_VERSION_ = '2023.4.0'

LOGCL = {0: Fore.RESET, 1: Fore.GREEN, 2: Fore.YELLOW, 3: Fore.RED}
LEVEL = {'intrusion': '4', 'unusual': '3', 'button': '2', 'ok': '1', 'green': '1', 'orange': '3', 'red': '4', 'home': '10',
         'custom': '20', 'away': '30', 'night': '40'}

SENSOR_FRIENDLY = {'ws02': 'window_sensor', 'ps01': 'presence_sensor', 'ps02': 'presence_sensor', 'ds01': 'door_sensor',
                   'ds02': 'door_sensor', 'is01': 'indoor_siren', 'sp01': 'smart_plug', 'sp02': 'smart_plug', 'bn01': 'button',
                   'yc01': 'camera', 'sd01': 'smoke', 'um01': 'umos', 'hb01': 'hue_bridge', 'hb01.hl01': 'hue_light',
                   'bs01': 'base_station', 'wd01': 'water_sensor', 'cl01': 'climate_sensor', 'ts01': 'thermostat'}

AUTH_EXPIRE = 14400

JSONFILE = os.path.join(os.path.expanduser('~'), 'gigasetelements-cli.json')

URL_STATUS = 'https://status.gigaset-elements.de/api/v1/status'
URL_IDENTITY = 'https://im.gigaset-elements.de/identity/api/v1/user/login'
URL_AUTH = 'https://api.gigaset-elements.de/api/v1/auth/openid/begin?op=gigaset'
URL_EVENTS = 'https://api.gigaset-elements.de/api/v2/me/events'
URL_BASE = 'https://api.gigaset-elements.de/api/v1/me/basestations'
URL_CAMERA = 'https://api.gigaset-elements.de/api/v1/me/cameras'
URL_HEALTH = 'https://api.gigaset-elements.de/api/v2/me/health'
URL_DEVICES = 'https://api.gigaset-elements.de/api/v1/me/devices'
URL_STATES = 'https://api.gigaset-elements.de/api/v1/me/states'
URL_CHANNEL = 'https://api.gigaset-elements.de/api/v1/me/notifications/users/channels'
URL_RELEASE = 'https://pypi.python.org/pypi/gigasetelements-cli/json'
URL_ELEMENTS = 'https://api.gigaset-elements.de/api/v2/me/elements'

parser = configargparse.ArgParser(description='Gigaset Elements - Command-line Interface by dynasticorpheus@gmail.com', default_config_files=CONFPATH)
parser.add_argument('-c', '--config', help='fully qualified name of configuration-file', required=False, is_config_file=True)
parser.add_argument('-u', '--username', help='username (email) in use with my.gigaset-elements.com', required=True)
parser.add_argument('-p', '--password', help='password in use with my.gigaset-elements.com', required=True)
parser.add_argument('-n', '--notify', help='pushbullet token', required=False, metavar='TOKEN')
parser.add_argument('-e', '--events', help='show last <number> of events', type=int, required=False)
parser.add_argument('-d', '--date', help='filter events on begin date - end date', required=False, nargs=2, metavar='DD/MM/YYYY')
parser.add_argument('-o', '--cronjob', help='schedule cron job at HH:MM (requires --modus or --record)', required=False, metavar='HH:MM')
parser.add_argument('-x', '--remove', help='remove all cron jobs linked to this program', action='store_true', required=False)
parser.add_argument('-f', '--filter', help='filter events on type', required=False, choices=(
    'door', 'window', 'motion', 'siren', 'plug', 'button', 'homecoming', 'intrusion', 'systemhealth', 'camera', 'phone', 'smoke', 'umos'))
parser.add_argument('-m', '--modus', help='set modus', required=False, choices=('home', 'away', 'custom', 'night'))
parser.add_argument('-k', '--delay', help='set alarm timer delay in seconds (use 0 to disable)', type=int, required=False)
parser.add_argument('-D', '--daemon', help='daemonize during monitor mode', action='store_true', required=False)
parser.add_argument('-z', '--notifications', help='show notification status', action='store_true', required=False)
parser.add_argument('-X', '--panic', help='trigger alarm', action='store_true', required=False)
parser.add_argument('-U', '--end', help='end alarm', action='store_true', required=False)
parser.add_argument('-l', '--log', help='fully qualified name of log file', required=False)
parser.add_argument('-R', '--rules', help='show custom rules', action='store_true', required=False)
parser.add_argument('-P', '--pid', help='fully qualified name of pid file', default='/var/run/gigasetelements-cli.pid', required=False)
parser.add_argument('-s', '--sensor', help='''show sensor status (use -ss to include sensor id's)''', action='count', default=0, required=False)
parser.add_argument('-b', '--siren', help='arm/disarm siren', required=False, choices=('arm', 'disarm'))
parser.add_argument('-B', '--sensorid', help='select sensor', type=str, required=False, metavar='sensor id')
parser.add_argument('-g', '--plug', help='switch plug on/off', required=False, choices=('on', 'off'))
parser.add_argument('-y', '--privacy', help='switch privacy mode on/off', required=False, choices=('on', 'off'))
parser.add_argument('-a', '--stream', help='start camera cloud based streams', type=str, required=False, metavar='MAC address')
parser.add_argument('-r', '--record', help='switch camera recording on/off', type=str, required=False, metavar='MAC address')
parser.add_argument('-A', '--snapshot', help='download camera snapshot', type=str, required=False, metavar='MAC address')
parser.add_argument('-t', '--monitor', help='show events using monitor mode', action='store_true', required=False)
parser.add_argument('-i', '--ignore', help='ignore configuration-file at predefined locations', action='store_true', required=False)
parser.add_argument('-N', '--noupdate', help='do not periodically check for updates', action='store_true', required=False)
parser.add_argument('-j', '--restart', help='automatically restart program in case of a connection error', action='store_true', required=False)
parser.add_argument('-J', '--restartdelay', help='set restart delay in seconds', type=int, required=False, default=60)
parser.add_argument('-q', '--quiet', help='do not send pushbullet message', action='store_true', required=False)
parser.add_argument('-I', '--insecure', help='disable SSL/TLS certificate verification', action='store_true', required=False)
parser.add_argument('-S', '--silent', help='suppress urllib3 warnings', action='store_true', required=False)
parser.add_argument('-E', '--elements', help='write elements json object to file', nargs='?', const=JSONFILE, type=str, required=False)
parser.add_argument('-v', '--version', help='show version', action='version', version='%(prog)s version ' + str(_VERSION_))

args = parser.parse_args()
init(autoreset=True)
s = requests.Session()
s.mount('http://', requests.adapters.HTTPAdapter(max_retries=3))
s.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))
POST, GET, DELETE = s.post, s.get, s.delete


if args.silent:
    try:
        disable_warnings()
    except NameError:
        pass


def restart_program():
    """Restarts the current program."""
    if args.daemon:
        os.remove(args.pid)
    python = sys.executable
    os.execl(python, python, * sys.argv)
    return


def log(logme, rbg=0, exitnow=0, newline=None):
    """Print output in selected color and provide program exit on critical error."""
    if sys.version_info[0] < 3:
        logme = unicode(logme)
    if os.name == 'nt' or args.log is not None:
        logme = unidecode.unidecode(logme)
    if os.name == 'posix' and args.log is None and sys.version_info[0] <  3 and sys.stdout.encoding is None:
        logme = unidecode.unidecode(logme)
    if args.log is not None:
        logger = logging.getLogger(__name__)
        logger.info('[' + time.strftime('%c') + '] ' + logme)
    if newline == 2:
        print('\r\x1b[K', end='')
    if newline is not None:
        newline = ' '
    print(LOGCL[rbg] + '[-] ' + logme, end=newline)
    if exitnow == 1:
        if args.restart:
            time.sleep(args.restartdelay)
            restart_program()
        sys.exit('\n')
    return


def filewritable(filetype, fileloc, mustexit=1):
    """Test if file can be opened for writing."""
    writable = False
    try:
        target = open(fileloc, 'w')
        target.close()
        writable = True
    except IOError as error:
        log(filetype.ljust(17) + ' | ' + color('error'.ljust(8)) + ' | ' + str(error), 0, mustexit)
    return writable


def color(txt):
    """Add color to string based on presence in list and return in uppercase."""
    green = ['ok', 'online', 'closed', 'up_to_date', 'home', 'auto', 'on', 'hd', 'cable', 'normal', 'daemon', 'wifi', 'ended',
             'started', 'active', 'green', 'armed', 'pushed', 'verified', 'loaded', 'success', 'download', 'scheduled', 'write']
    orange = ['orange', 'warning', 'update']
    if args.log is not None:
        txt = txt.upper()
    else:
        if txt.lower().strip() in green:
            txt = Fore.GREEN + txt.upper() + Fore.RESET
        elif txt.lower().strip() in orange:
            txt = Fore.YELLOW + txt.upper() + Fore.RESET
        else:
            txt = Fore.RED + txt.upper() + Fore.RESET
    return txt


def rest(method, url, payload=None, header=False, timeout=90, end=1, silent=False):
    """REST interaction using requests module."""
    request = None
    data = ''
    if args.insecure:
        pem = False
    else:
        pem = True
    if header:
        header = {'content-type': 'application/json; charset=UTF-8'}
    else:
        header = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'}
    try:
        if method == POST:
            request = method(url, timeout=timeout, data=payload, headers=header, allow_redirects=True, verify=pem)
        else:
            request = method(url, timeout=timeout, headers=header, allow_redirects=True, verify=pem)
    except requests.exceptions.RequestException as error:
        if not silent:
            log('ERROR'.ljust(17) + ' | ' + 'UNKNOWN'.ljust(8) + ' | ' + str(error), 3, end)
    if request is not None:
        if not silent:
            if not request.ok:  # pylint: disable=no-member
                urlsplit = urlparse(request.url)
                log('HTTP ERROR'.ljust(17) + ' | ' + str(request.status_code).ljust(8) + ' | ' + request.reason + ' ' + str(urlsplit.path), 3, end)
        contenttype = request.headers.get('Content-Type', default='').split(';')[0]
        if contenttype == 'application/json' or request.url == URL_STATUS:
            data = request.json()
        elif contenttype == 'image/jpeg':
            data = request.content
        else:
            data = request.text
    return data


def authenticate(reauthenticate=False):
    """Gigaset Elements API authentication."""
    status_maintenance = rest(GET, URL_STATUS)
    if status_maintenance['isMaintenance']:
        log('Maintenance'.ljust(17) + ' | ' + 'DETECTED'.ljust(8) + ' | Please try later', 2, 1)
    auth_time = time.time()
    auth_type = 'Re-authentication'
    payload = {'password': args.password, 'email': args.username}
    commit_data = rest(POST, URL_IDENTITY, payload)
    if not reauthenticate:
        log('Identity'.ljust(17) + ' | ' + color('verified') + ' | ' + commit_data['message'])
        auth_type = auth_type[3:].title()
    rest(GET, URL_AUTH)
    log(auth_type.ljust(17) + ' | ' + color('success'.ljust(8)) + ' | ')
    return auth_time


def systemstatus():
    """Gigaset Elements system status retrieval."""
    basestation_data = rest(GET, URL_BASE)
    log('Basestation'.ljust(17) + ' | ' + color(basestation_data[0]['status'].ljust(8)) + ' | ' + basestation_data[0]['id'])
    camera_data = rest(GET, URL_CAMERA)
    status_data = rest(GET, URL_HEALTH)
    elements_data = rest(GET, URL_ELEMENTS)
    if status_data['system_health'] == 'green':
        status_data['status_msg_id'] = ''
    else:
        status_data['status_msg_id'] = ' | ' + status_data['status_msg_id']
    if args.modus is None:
        log('Status'.ljust(17) + ' | ' + color(status_data['system_health'].ljust(8)) +
            status_data['status_msg_id'].upper() + ' | Modus ' + color(basestation_data[0]['intrusion_settings']['active_mode']))
    return basestation_data, status_data, camera_data, elements_data


def check_version():
    """Check if new version exists on pypi."""
    from distutils.version import StrictVersion
    remotedata = rest(GET, URL_RELEASE, None, False, 2, 0, True)
    if remotedata is not None:
        remoteversion = str(remotedata['info']['version'])
        if StrictVersion(_VERSION_) < StrictVersion(remoteversion):
            log('Program'.ljust(17) + ' | ' + color('update'.ljust(8)) + ' | Version ' + remoteversion +
                ' is available. Run pip install --upgrade gigasetelements-cli')
    return


def collect_hw(basestation_data, camera_data):
    """Retrieve sensor list and details."""
    sensor_id = {}
    sensor_exist = dict.fromkeys(list(SENSOR_FRIENDLY.values()), False)
    for item in basestation_data[0]['sensors']:
        sensor_id.setdefault(item['type'], []).append(item['id'])
    try:
        for mac in camera_data:
            sensor_id.setdefault('yc01', []).append(mac['id'])
    except IndexError:
        pass
    for item in sensor_id:
        sensor_exist.update(dict.fromkeys([SENSOR_FRIENDLY[item]], True))
    return sensor_id, sensor_exist


def modus_switch(basestation_data, status_data):
    """Switch alarm modus."""
    switch = {'intrusion_settings': {'active_mode': args.modus}}
    rest(POST, URL_BASE + '/' + basestation_data[0]['id'], json.dumps(switch))
    log('Status'.ljust(17) + ' | ' + color(status_data['system_health'].ljust(8)) + status_data['status_msg_id'].upper() +
        ' | Modus set from ' + color(basestation_data[0]['intrusion_settings']['active_mode']) + ' to ' + color(args.modus))
    return


def trigger_alarm():
    """Trigger alarm."""
    switch = {'action': 'alarm.user.start'}
    rest(POST, URL_DEVICES + '/webfrontend/sink', json.dumps(switch))
    log('Alarm'.ljust(17) + ' | ' + color('trigger'.ljust(8)) + ' | ')
    return


def end_alarm():
    """End alarm."""
    rest(DELETE, URL_STATES + '/userAlarm')
    log('Alarm'.ljust(17) + ' | ' + color('ended'.ljust(8)) + ' | ')
    return


def set_delay(basestation_data):
    """Set alarm trigger delay."""
    switch = {"intrusion_settings": {"modes": [{"away": {"trigger_delay": str(args.delay * 1000)}}]}}
    rest(POST, URL_BASE + '/' + basestation_data[0]['id'], json.dumps(switch))
    if args.delay > 0:
        log('Alarm timer'.ljust(17) + ' | ' + color(('delayed').ljust(8)) + ' | ' + str(args.delay) + ' seconds')
    else:
        log('Alarm timer'.ljust(17) + ' | ' + color(('normal').ljust(8)) + ' | ' + 'No delay')
    return


def set_privacy(basestation_data):
    """Set privacy mode."""
    moduslist = ['home', 'custom', 'night']
    for modus in moduslist:
        switch = {"intrusion_settings": {"modes": [{modus: {"privacy_mode": str(args.privacy in "on").lower()}}]}}
        rest(POST, URL_BASE + '/' + basestation_data[0]['id'], json.dumps(switch))
    log('Privacy mode'.ljust(17) + ' | ' + color(args.privacy.ljust(8)) + ' | ')
    return


def siren(basestation_data, sensor_exist):
    """Dis(arm) siren."""
    if not sensor_exist['indoor_siren']:
        log('Siren'.ljust(17) + ' | ' + 'ERROR'.ljust(8) + ' | Not found', 3, 1)
    moduslist = ['home', 'away', 'custom', 'night']
    for modus in moduslist:
        switch = {"intrusion_settings": {"modes": [{modus: {"sirens_on": str(args.siren in "arm").lower()}}]}}
        rest(POST, URL_BASE + '/' + basestation_data[0]['id'], json.dumps(switch))
    log('Siren'.ljust(17) + ' | ' + color((args.siren + 'ED').ljust(8)) + ' | ')
    return


def plug(basestation_data, sensor_exist, sensor_id):
    """Switch Plug on or off."""
    if not sensor_exist['smart_plug']:
        log('Plug'.ljust(17) + ' | ' + 'ERROR'.ljust(8) + ' | Not found', 3, 1)
    switch = {"name": args.plug}
    if args.sensorid is not None:
        plugid = args.sensorid.lower()
    elif 'sp02' in sensor_id:
        plugid = sensor_id['sp02'][0]
    else:
        plugid = sensor_id['sp01'][0]
    rest(POST, URL_BASE + '/' + basestation_data[0]['id'] + '/endnodes/' + plugid + '/cmd', json.dumps(switch), True)
    log('Plug'.ljust(17) + ' | ' + color(args.plug.ljust(8)) + ' | ')
    return


def istimeformat(timestr):
    """Validate if string has correct time format."""
    try:
        time.strptime(timestr, '%H:%M')
        return True
    except ValueError:
        return False


def add_cron():
    """Add job to crontab to set alarm modus or trigger recording."""
    if os.name == 'nt':
        log('Cronjob'.ljust(17) + ' | ' + 'ERROR'.ljust(8) + ' | Not supported on windows OS', 3, 1)
    elif args.modus is None and args.record is None:
        log('Cronjob'.ljust(17) + ' | ' + 'ERROR'.ljust(8) + ' | Requires --modus or --record', 3, 1)
    if args.modus:
        action = ' --modus ' + args.modus + ' '
    else:
        action = ' --record ' + args.record + ' '
    if istimeformat(args.cronjob):
        cron = CronTab(user=True)
        now = datetime.datetime.now()
        timer = now.replace(hour=time.strptime(args.cronjob, '%H:%M')[3], minute=time.strptime(args.cronjob, '%H:%M')[4], second=0, microsecond=0)
        job = cron.new('gigasetelements-cli -u ' + args.username + ' -p ' + args.password +
                       action, comment='added by gigasetelements-cli on ' + str(now)[:16])
        job.month.on(datetime.datetime.now().strftime('%-m'))
        if now < timer:
            job.day.on(datetime.datetime.now().strftime('%-d'))
        else:
            job.day.on(str((int(datetime.datetime.now().strftime('%-d')) + 1)))
            timer = now.replace(day=(int(datetime.datetime.now().strftime('%-d')) + 1), hour=time.strptime(args.cronjob, '%H:%M')
                                [3], minute=time.strptime(args.cronjob, '%H:%M')[4], second=0, microsecond=0)
        job.hour.on(time.strptime(args.cronjob, '%H:%M')[3])
        job.minute.on(time.strptime(args.cronjob, '%H:%M')[4])
        cron.write()
        log('Cronjob'.ljust(17) + ' | ' + color('scheduled'.ljust(8)) + ' |' + action + '| ' + timer.strftime('%A %d %B %Y %H:%M'), 0, 1)
    else:
        log('Cronjob'.ljust(17) + ' | ' + 'ERROR'.ljust(8) + ' | Use valid time (00:00 - 23:59)', 3, 1)
    return


def remove_cron():
    """Remove all jobs from crontab setting alarm modus."""
    if os.name == 'nt':
        log('Cronjob'.ljust(17) + ' | ' + 'ERROR'.ljust(8) + ' | Not supported on windows OS', 3, 1)
    cron = CronTab(user=True)
    existing = cron.find_command('gigasetelements-cli')
    count = 0
    for i in existing:
        log('Cronjob'.ljust(17) + ' | ' + color('removed'.ljust(8)) + ' | ' + str(i))
        count += 1
    if count == 0:
        log('Cronjob'.ljust(17) + ' | ' + color('warning'.ljust(8)) + ' | ' + 'No items found for removal', 0, 1)
    else:
        cron.remove_all(command='gigasetelements-cli')
        cron.write()
        sys.exit('\n')
    return


def pb_message(pbmsg):
    """Send message using pushbullet module."""
    from pushbullet import PushBullet, InvalidKeyError, PushbulletError
    try:
        pushb = PushBullet(args.notify)
    except InvalidKeyError:
        log('Notification'.ljust(17) + ' | ' + color('token'.ljust(8)) + ' | ')
    except PushbulletError:
        log('Notification'.ljust(17) + ' | ' + color('error'.ljust(8)) + ' | ')
    else:
        pushb.push_note('Gigaset Elements', pbmsg)
        log('Notification'.ljust(17) + ' | ' + color('pushed'.ljust(8)) + ' | ')
    return


def list_events():
    """List past events optionally filtered by date and/or type."""
    if args.filter is None and args.date is None:
        log('Event(s)'.ljust(17) + ' | ' + str(args.events).ljust(8) + ' | ' + 'No filter')
        event_data = rest(GET, URL_EVENTS + '?limit=' + str(args.events))
    if args.filter is not None and args.date is None:
        log('Event(s)'.ljust(17) + ' | ' + str(args.events).ljust(8) + ' | ' + args.filter.title())
        event_data = rest(GET, URL_EVENTS + '?limit=' + str(args.events) + '&group=' + str(args.filter))
    if args.date is not None:
        try:
            from_ts = str(int(time.mktime(time.strptime(args.date[0], '%d/%m/%Y'))) * 1000)
            to_ts = str(int(time.mktime(time.strptime(args.date[1], '%d/%m/%Y'))) * 1000)
        except ValueError:
            log('Event(s)'.ljust(17) + ' | ' + 'ERROR'.ljust(8) + ' | ' + 'Date(s) filter not in DD/MM/YYYY format', 3, 1)
    if args.filter is None and args.date is not None:
        log('Event(s)'.ljust(17) + ' | ' + 'DATE'.ljust(8) + ' | ' + args.date[0] + ' - ' + args.date[1])
        event_data = rest(GET, URL_EVENTS + '?from_ts=' + from_ts + '&to_ts=' + to_ts + '&limit=999')
    if args.filter is not None and args.date is not None:
        log('Event(s)'.ljust(17) + ' | ' + '*'.ljust(8) + ' | ' + args.filter.title() + ' | ' + args.date[0] + ' - ' + args.date[1])
        event_data = rest(GET, URL_EVENTS + '?from_ts=' + from_ts + '&to_ts=' + to_ts + '&group=' + str(args.filter) + '&limit=999')
    for item in event_data['events']:
        try:
            if 'type' in item['o']:
                log(time.strftime('%m/%d/%y %H:%M:%S', time.localtime(int(item['ts']) / 1000)) + ' | ' + item['o']
                    ['type'].ljust(8) + ' | ' + item['type'] + ' ' + item['o'].get('friendly_name', item['o']['type']))
        except KeyError:
            log(time.strftime('%m/%d/%y %H:%M:%S', time.localtime(int(item['ts']) / 1000)) + ' | ' + item['type'].ljust(8) + ' | ' + item['source_type'])
            continue
    return


def monitor(auth_time, basestation_data, status_data):
    """List events realtime optionally filtered by type."""
    url_monitor = URL_EVENTS + '?limit=10'
    if args.filter is not None:
        url_monitor = url_monitor + '&group=' + args.filter
    log('Monitor mode'.ljust(17) + ' | ' + color('started'.ljust(8)) + ' | ' + 'CTRL+C to exit')
    from_ts = str(int(time.time()) * 1000)
    try:
        while 1:
            lastevents = rest(GET, url_monitor + '&from_ts=' + from_ts)
            for item in reversed(lastevents['events']):
                try:
                    if 'type' in item['o']:
                        log(time.strftime('%m/%d/%y %H:%M:%S', time.localtime(int(item['ts']) / 1000)) + ' | ' + item['o'][
                            'type'].ljust(8) + ' | ' + item['type'] + ' ' + item['o'].get('friendly_name', item['o']['type']), 0, 0, 2)
                    else:
                        log(time.strftime('%m/%d/%y %H:%M:%S', time.localtime(int(item['ts']) / 1000)) +
                            ' | ' + 'system'.ljust(8) + ' | ' + item['source_type'] + ' ' + item['type'], 0, 0, 2)
                    from_ts = str(int(item['ts']) + 1)
                except KeyError:
                    continue
            if time.time() - auth_time >= AUTH_EXPIRE:
                auth_time = authenticate(reauthenticate=True)
            else:
                time.sleep(1)
    except KeyboardInterrupt:
        log('Program'.ljust(17) + ' | ' + color('halted'.ljust(8)) + ' | ' + 'CTRL+C', 0, 1, 2)
    return


def sensor(basestation_data, sensor_exist, camera_data, elements_data):
    """Show sensor details and current state."""
    log(basestation_data[0]['friendly_name'].ljust(17) + ' | ' + color(basestation_data[0]
                                                                       ['status'].ljust(8)) + ' | firmware ' + color(basestation_data[0]['firmware_status']))
    for item in basestation_data[0]['sensors']:
        try:
            if item['type'] not in ['cl01', 'ts01']:
                log(item['friendly_name'].ljust(17) + ' | ' + color(item['status'].ljust(8)) + ' | firmware ' + color(item['firmware_status']), 0, 0, 0)
                if item['type'] not in ['is01', 'sp01', 'sp02']:
                    print('| battery ' + color(item['battery']['state']), end=' ')
                if item['type'] in ['ds02', 'ds01', 'ws02']:
                    print('| position ' + color(item['position_status']), end=' ')
                if args.sensor > 1:
                    print('| ' + item['id'].upper(), end=' ')
                print()
        except KeyError:
            print()
    if sensor_exist['camera']:
        try:
            for cam in camera_data:
                print('[-] ' + cam['friendly_name'].ljust(17) + ' | ' + color(cam['status'].ljust(8)) + ' | firmware ' + color(cam['firmware_status']), end=' ')
                print(('| quality ' + color(cam['settings']['quality']) + ' | nightmode ' + color(cam['settings']['nightmode']) + ' | mic ' +
                       color(cam['settings']['mic'])), end=' ')
                print(('| motion detection ' + color(cam['motion_detection']['status']) + ' | connection ' + color(cam['settings']['connection'])), end=' ')
                if cam['settings']['connection'] == 'wifi':
                    print('| ssid ' + Fore.GREEN + str(cam['wifi_ssid']).upper(), end=' ')
                if args.sensor > 1:
                    print('| ' + cam['id'].upper(), end=' ')
                print()
        except KeyError:
            print()
    if sensor_exist['thermostat'] or sensor_exist['climate_sensor'] or sensor_exist['umos'] or sensor_exist['water_sensor']:
        try:
            for clm in elements_data["bs01"][0]["subelements"]:
                if clm['type'] in ['bs01.ts01', 'bs01.cl01', 'bs01.um01','bs01.wd01']:
                    print('[-] ' + clm['friendlyName'].ljust(17) + ' | ' + color(clm['connectionStatus'].ljust(8)) + ' | firmware ' + color(clm['firmwareStatus']) +
                        ' | battery ' + color(clm['batteryStatus']) + ' | temperature ' +str(round(clm['states']['temperature'], 1)) , end=' ')
                    if clm['type'] == 'bs01.ts01':
                        print('| setpoint ' +str(int(clm['states']['setPoint'])) , end=' ')
                    elif clm['type'] == 'bs01.um01':
                        print('| pressure ' +str(int(clm['states']['pressure'])) , end=' ')
                    elif clm['type'] in ['bs01.cl01','bs01.wd01']:
                        print('| humidity ' +str(round(clm['states']['humidity'], 1)) , end=' ')
                    else:
                        pass
                    if args.sensor > 1:
                        print('| ' + clm['id'].rsplit(".", 1)[1].upper(), end=' ')
                    print()
        except KeyError:
            print()
    return


def rules(basestation_data):
    """List custom rule(s)."""
    ruleset = rest(GET, URL_BASE + '/' + basestation_data[0]['id'] + '/rules?rules=custom')
    for item in ruleset:
        try:
            if item['active']:
                item['active'] = 'active'
            else:
                item['active'] = 'inactive'
            log(item['friendly_name'].ljust(17) + ' | ' + color(item['active'].ljust(8)) + ' | ' + item['friendly_description'])
        except KeyError:
            continue
    return


def notifications():
    """List notification settings per mobile device."""
    channels = rest(GET, URL_CHANNEL)
    for item in channels.get('gcm', ''):
        try:
            print(('[-] ' + item['friendlyName'].ljust(17) + ' | ' + color(item['status'].ljust(8)) + ' |'), end=' ')
            for item2 in item['notificationGroups']:
                print(item2, end=' ')
            print()
        except KeyError:
            continue
    return


def camera_stream(sensor_id, sensor_exist):
    """Show camera details and current state."""
    if not sensor_exist['camera']:
        log('Camera'.ljust(17) + ' | ' + 'ERROR'.ljust(8) + ' | Not found', 3, 1)
    if args.stream.upper() in sensor_id['yc01']:
        mac = args.stream.upper()
    else:
        mac = sensor_id['yc01'][0]
    stream_data = rest(GET, URL_CAMERA + '/' + mac + '/liveview/start')
    for stream in ('m3u8', 'rtsp'):
        log('Stream'.ljust(17) + ' | ' + stream.upper().ljust(8) + ' | ' + stream_data['uri'][stream])
    return


def record(sensor_id, sensor_exist):
    """Start or stop camera recording based on current state."""
    if not sensor_exist['camera']:
        log('Camera'.ljust(17) + ' | ' + 'ERROR'.ljust(8) + ' | Not found', 3, 1)
    if args.record.upper() in sensor_id['yc01']:
        mac = args.record.upper()
    else:
        mac = sensor_id['yc01'][0]
    camera_status = rest(GET, URL_CAMERA + '/' + mac + '/recording/status')
    if camera_status['description'] == 'Recording not started':
        rest(GET, URL_CAMERA + '/' + mac + '/recording/start')
        log('Camera recording'.ljust(17) + ' | ' + color('started'.ljust(8)) + ' | ' + mac)
    if camera_status['description'] == 'Recording already started':
        rest(GET, URL_CAMERA + '/' + mac + '/recording/stop')
        log('Camera recording'.ljust(17) + ' | ' + color('stopped'.ljust(8)) + ' | ' + mac)
    return


def getsnapshot(sensor_id, sensor_exist):
    """Download snapshot from camera."""
    if not sensor_exist['camera']:
        log('Camera'.ljust(17) + ' | ' + 'ERROR'.ljust(8) + ' | Not found', 3, 1)
    if args.snapshot.upper() in sensor_id['yc01']:
        mac = args.snapshot.upper()
    else:
        mac = sensor_id['yc01'][0]
    image_name = mac + '_' + time.strftime('%y%m%d') + '_' + time.strftime('%H%M%S') + '.jpg'
    if filewritable('Snapshot image', image_name, 0):
        log('Camera snapshot'.ljust(17) + ' | ' + color('download'.ljust(8)) + ' | ' + image_name)
        with open(image_name, 'wb') as image:
            image.write(rest(GET, URL_CAMERA + '/' + mac + '/snapshot?fresh=true'))
    return


def start_logger(logfile):
    """Setup log file handler."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    try:
        filehandle = logging.FileHandler(logfile, 'a')
    except IOError:
        print(Fore.RED + '[-] Unable to write log file ' + logfile)
        sys.exit('\n')
    filehandle.setLevel(logging.INFO)
    logger.addHandler(filehandle)
    logger.info('[' + time.strftime('%c') + '] ' + 'Gigaset Elements'.ljust(17) + ' | ' + 'CLI'.ljust(8) + ' | ' + _VERSION_ + ' | ' + ' '.join(sys.argv[1:]))
    return


def get_elements(elements_data):
    """Write elements json object."""
    if sys.version_info[0] < 3 or os.name == 'nt':
        elements_data = unicode(elements_data)
    if filewritable('JSON file', args.elements, 0):
        log('JSON file'.ljust(17) + ' | ' + color('write'.ljust(8)) + ' | ' + args.elements)
        with open(args.elements, 'w') as outfile:
            json.dump(elements_data, outfile, indent=4, sort_keys=False, ensure_ascii=False)
    return


def base():
    """Base program."""
    pb_body = None
    print('\n' + 'Gigaset Elements - Command-line Interface v' + _VERSION_ + '\n')
    try:
        if args.log:
            start_logger(args.log)

        if args.daemon:
            log('Run as background'.ljust(17) + ' | ' + color('daemon'.ljust(8)) + ' | ' + args.pid)

        if args.remove:
            remove_cron()

        if args.cronjob:
            add_cron()

        if not args.noupdate:
            check_version()

        auth_time = authenticate()

        basestation_data, status_data, camera_data, elements_data = systemstatus()

        sensor_id, sensor_exist = collect_hw(basestation_data, camera_data)

        if args.modus is not None and args.cronjob is None:
            modus_switch(basestation_data, status_data)
            if args.sensor is not True:
                pb_body = 'Status ' + status_data['system_health'].upper() + ' | Modus set from ' + \
                    basestation_data[0]['intrusion_settings']['active_mode'].upper() + ' to ' + args.modus.upper()

        if args.sensor:
            sensor(basestation_data, sensor_exist, camera_data, elements_data)
            if status_data['status_msg_id'] == '':
                status_data['status_msg_id'] = '\u2713'
            pb_body = 'Status ' + status_data['system_health'].upper() + ' | ' + status_data['status_msg_id'].upper() + \
                ' | Modus ' + basestation_data[0]['intrusion_settings']['active_mode'].upper()

        if args.delay is not None:
            set_delay(basestation_data)

        if args.privacy is not None:
            set_privacy(basestation_data)

        if args.stream:
            camera_stream(sensor_id, sensor_exist)

        if args.record:
            record(sensor_id, sensor_exist)

        if args.snapshot:
            getsnapshot(sensor_id, sensor_exist)

        if args.notifications:
            notifications()

        if args.rules:
            rules(basestation_data)

        if args.siren:
            siren(basestation_data, sensor_exist)

        if args.plug:
            plug(basestation_data, sensor_exist, sensor_id)

        if not args.quiet and None not in (args.notify, pb_body):
            pb_message(pb_body)

        if args.events is None and args.date is None:
            pass
        else:
            list_events()

        if args.elements:
            get_elements(elements_data)

        if args.panic:
            trigger_alarm()

        if args.end:
            end_alarm()

        if args.monitor:
            monitor(auth_time, basestation_data, status_data)
        print()
    except KeyboardInterrupt:
        log('Program'.ljust(17) + ' | ' + color('halted'.ljust(8)) + ' | ' + 'CTRL+C', 0, 1, 2)


def main():
    """Main program."""
    if args.daemon and os.name != 'nt':
        print()
        if filewritable('PID file', args.pid):
            daemon = Daemonize(app='gigasetelements-cli', pid=args.pid, action=base, auto_close_fds=False, chdir=os.path.dirname(os.path.abspath(sys.argv[0])))
            daemon.start()
    else:
        base()
