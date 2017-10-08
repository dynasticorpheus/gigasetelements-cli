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
    sys.exit(str(error) + '. Please install from PyPI: pip install --upgrade ' + str(error).rsplit(None, 1)[-1])

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
                os.path.expanduser('~/.config/gigasetelements-cli/gigasetelements-cli.conf'),
                os.path.expanduser('~/Library/Application Support/gigasetelements-cli/gigasetelements-cli.conf')]

_AUTHOR_ = 'dynasticorpheus@gmail.com'
_VERSION_ = '1.5.0b5'

LOGCL = {0: Fore.RESET, 1: Fore.GREEN, 2: Fore.YELLOW, 3: Fore.RED}
LEVEL = {'intrusion': '4', 'unusual': '3', 'button': '2', 'ok': '1', 'green': '1', 'orange': '3', 'red': '4', 'home': '10',
         'custom': '20', 'away': '30', 'night': '40'}

SENSOR_FRIENDLY = {'ws02': 'window_sensor', 'ps01': 'presence_sensor', 'ps02': 'presence_sensor', 'ds01': 'door_sensor', 'ds02': 'door_sensor',
                   'is01': 'indoor_siren', 'sp01': 'smart_plug', 'bn01': 'button', 'yc01': 'camera', 'sd01': 'smoke', 'um01': 'umos'}

AUTH_EXPIRE = 14400

URL_IDENTITY = 'https://im.gigaset-elements.de/identity/api/v1/user/login'
URL_AUTH = 'https://api.gigaset-elements.de/api/v1/auth/openid/begin?op=gigaset'
URL_EVENTS = 'https://api.gigaset-elements.de/api/v2/me/events'
URL_BASE = 'https://api.gigaset-elements.de/api/v1/me/basestations'
URL_CAMERA = 'https://api.gigaset-elements.de/api/v1/me/cameras'
URL_HEALTH = 'https://api.gigaset-elements.de/api/v2/me/health'
URL_CHANNEL = 'https://api.gigaset-elements.de/api/v1/me/notifications/users/channels'
URL_RELEASE = 'https://pypi.python.org/pypi/gigasetelements-cli/json'
URL_USAGE = 'https://goo.gl/oHJ565'

URL_SWITCH = '/json.htm?type=command&param=switchlight&switchcmd='
URL_ALERT = '/json.htm?type=command&param=udevice&idx='
URL_LOG = '/json.htm?type=command&param=addlogmessage&message='

parser = configargparse.ArgParser(description='Gigaset Elements - Command-line Interface by dynasticorpheus@gmail.com', default_config_files=CONFPATH)
parser.add_argument('-c', '--config', help='fully qualified name of configuration-file', required=False, is_config_file=True)
parser.add_argument('-u', '--username', help='username (email) in use with my.gigaset-elements.com', required=True)
parser.add_argument('-p', '--password', help='password in use with my.gigaset-elements.com', required=True)
parser.add_argument('-n', '--notify', help='pushbullet token', required=False, metavar='TOKEN')
parser.add_argument('-e', '--events', help='show last <number> of events', type=int, required=False)
parser.add_argument('-d', '--date', help='filter events on begin date - end date', required=False, nargs=2, metavar='DD/MM/YYYY')
parser.add_argument('-o', '--cronjob', help='schedule cron job at HH:MM (requires -m option)', required=False, metavar='HH:MM')
parser.add_argument('-x', '--remove', help='remove all cron jobs linked to this program', action='store_true', required=False)
parser.add_argument('-f', '--filter', help='filter events on type', required=False, choices=(
    'door', 'window', 'motion', 'siren', 'plug', 'button', 'homecoming', 'intrusion', 'systemhealth', 'camera', 'phone', 'smoke', 'umos'))
parser.add_argument('-m', '--modus', help='set modus', required=False, choices=('home', 'away', 'custom', 'night'))
parser.add_argument('-k', '--delay', help='set alarm timer delay in seconds (use 0 to disable)', type=int, required=False)
parser.add_argument('-D', '--daemon', help='daemonize during monitor/domoticz mode', action='store_true', required=False)
parser.add_argument('-z', '--notifications', help='show notification status', action='store_true', required=False)
parser.add_argument('-l', '--log', help='fully qualified name of log file', required=False)
parser.add_argument('-R', '--rules', help='show custom rules', action='store_true', required=False)
parser.add_argument('-P', '--pid', help='fully qualified name of pid file', default='/tmp/gigasetelements-cli.pid', required=False)
parser.add_argument('-s', '--sensor', help='''show sensor status (use -ss to include sensor id's)''', action='count', default=0, required=False)
parser.add_argument('-b', '--siren', help='arm/disarm siren', required=False, choices=('arm', 'disarm'))
parser.add_argument('-g', '--plug', help='switch plug on/off', required=False, choices=('on', 'off'))
parser.add_argument('-y', '--privacy', help='switch privacy mode on/off', required=False, choices=('on', 'off'))
parser.add_argument('-a', '--stream', help='start camera cloud based streams', action='store_true', required=False)
parser.add_argument('-r', '--record', help='switch camera recording on/off', action='store_true', required=False)
parser.add_argument('-A', '--snapshot', help='download camera snapshot', action='store_true', required=False)
parser.add_argument('-t', '--monitor', help='show events using monitor mode (use -tt to activate domoticz mode)', action='count', default=0, required=False)
parser.add_argument('-i', '--ignore', help='ignore configuration-file at predefined locations', action='store_true', required=False)
parser.add_argument('-N', '--noupdate', help='do not periodically check for updates', action='store_true', required=False)
parser.add_argument('-j', '--restart', help='automatically restart program in case of a connection error', action='store_true', required=False)
parser.add_argument('-q', '--quiet', help='do not send pushbullet message', action='store_true', required=False)
parser.add_argument('-I', '--insecure', help='disable SSL/TLS certificate verification', action='store_true', required=False)
parser.add_argument('-S', '--silent', help='suppress urllib3 warnings', action='store_true', required=False)
parser.add_argument('-U', '--url', help='url (domoticz)', required=False)
parser.add_argument('-X', '--sensorpairs', help='idx keypairs (domoticz)', required=False, action='append')
parser.add_argument('-v', '--version', help='show version', action='version', version='%(prog)s version ' + str(_VERSION_))

args = parser.parse_args()
init(autoreset=True)
s = requests.Session()
s.mount('http://', requests.adapters.HTTPAdapter(max_retries=3))
s.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))
POST, GET, HEAD = s.post, s.get, s.head


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
    if args.log is not None:
        logger = logging.getLogger(__name__)
        logger.info('[' + time.strftime('%c') + '] ' + logme)
    if newline is not None:
        newline = ' '
    print(LOGCL[rbg] + '[-] ' + logme, end=newline)
    if exitnow == 1:
        print()
        if args.restart:
            restart_program()
        sys.exit()
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
    green = ['ok', 'online', 'closed', 'up_to_date', 'home', 'auto', 'on', 'hd', 'cable', 'normal', 'daemon', 'wifi',
             'started', 'active', 'green', 'armed', 'pushed', 'verified', 'loaded', 'success', 'download']
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
            if request.status_code != requests.codes.ok:  # pylint: disable=no-member
                urlsplit = urlparse(request.url)
                log('HTTP ERROR'.ljust(17) + ' | ' + str(request.status_code).ljust(8) + ' | ' + request.reason + ' ' + str(urlsplit.path), 3, end)
        contenttype = request.headers.get('Content-Type', default='').split(';')[0]
        if contenttype == 'application/json':
            data = request.json()
        elif contenttype == 'image/jpeg':
            data = request.content
        else:
            data = request.text
    return data


def authenticate(reauthenticate=False):
    """Gigaset Elements API authentication."""
    auth_time = time.time()
    auth_type = 'Re-authentication'
    payload = {'password': args.password, 'email': args.username}
    commit_data = rest(POST, URL_IDENTITY, payload)
    if not reauthenticate:
        log('Identity'.ljust(17) + ' | ' + color('verified') + ' | ' + commit_data['message'])
        auth_type = auth_type[3:].title()
    rest(GET, URL_AUTH)
    log(auth_type.ljust(17) + ' | ' + color('success'.ljust(8)) + ' | ')
    rest(HEAD, URL_USAGE, None, False, 2, 0, True)
    return auth_time


def systemstatus():
    """Gigaset Elements system status retrieval."""
    basestation_data = rest(GET, URL_BASE)
    log('Basestation'.ljust(17) + ' | ' + color(basestation_data[0]['status'].ljust(8)) + ' | ' + basestation_data[0]['id'])
    camera_data = rest(GET, URL_CAMERA)
    status_data = rest(GET, URL_HEALTH)
    if status_data['system_health'] == 'green':
        status_data['status_msg_id'] = ''
    else:
        status_data['status_msg_id'] = ' | ' + status_data['status_msg_id']
    if args.modus is None:
        log('Status'.ljust(17) + ' | ' + color(status_data['system_health'].ljust(8)) +
            status_data['status_msg_id'].upper() + ' | Modus ' + color(basestation_data[0]['intrusion_settings']['active_mode']))
    return basestation_data, status_data, camera_data


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
        if 'id' in camera_data[0] and len(camera_data[0]['id']) == 12:
            sensor_id.update(dict.fromkeys(['yc01'], camera_data[0]['id']))
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
    rest(POST, URL_BASE + '/' + basestation_data[0]['id'] + '/endnodes/' + sensor_id['sp01'][0] + '/cmd', json.dumps(switch), True)
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
    """Add job to crontab to set alarm modus."""
    if args.modus is None:
        log('Cronjob'.ljust(17) + ' | ' + 'ERROR'.ljust(8) + ' | Specify modus using -m option', 3, 1)
    elif os.name == 'nt':
        log('Cronjob'.ljust(17) + ' | ' + 'ERROR'.ljust(8) + ' | Not supported on windows OS', 3, 1)
    if istimeformat(args.cronjob):
        cron = CronTab(user=True)
        now = datetime.datetime.now()
        timer = now.replace(hour=time.strptime(args.cronjob, '%H:%M')[3], minute=time.strptime(args.cronjob, '%H:%M')[4], second=0, microsecond=0)
        job = cron.new('gigasetelements-cli -u ' + args.username + ' -p ' + args.password + ' -m ' +
                       args.modus, comment='added by gigasetelements-cli on ' + str(now)[:16])
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
        log('Cronjob'.ljust(17) + ' | ' + color(args.modus.ljust(8)) + ' | ' + 'Modus on ' + timer.strftime('%A %d %B %Y %H:%M'), 0, 1)
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


def monitor(auth_time, basestation_data, status_data, url_domo, cfg_domo):
    """List events realtime optionally filtered by type."""
    health = modus = ''
    epoch = time.time() - 60
    if args.filter is None:
        url_monitor = URL_EVENTS + '?limit=10'
    else:
        url_monitor = URL_EVENTS + '?limit=10&group=' + args.filter
    if cfg_domo and args.monitor > 1:
        mode = 'Domoticz mode'
        rest(GET, url_domo + URL_LOG + 'Gigaset Elements - Command-line Interface: Domoticz mode started')
    else:
        mode = 'Monitor mode'
        args.monitor = 1
    log(mode.ljust(17) + ' | ' + color('started'.ljust(8)) + ' | ' + 'CTRL+C to exit')
    from_ts = str(int(time.time()) * 1000)
    print('\n')
    try:
        while 1:
            if args.monitor > 1 and time.time() - epoch > 59:
                status_data = rest(GET, URL_HEALTH)
                if health != status_data['system_health'].lower():
                    domoticz(status_data['system_health'].lower(), basestation_data[0]['id'].lower(),
                             basestation_data[0]['friendly_name'].lower(), basestation_data, url_domo, cfg_domo)
                    health = status_data['system_health'].lower()
                basestation_data = rest(GET, URL_BASE)
                if modus != basestation_data[0]['intrusion_settings']['active_mode']:
                    domoticz(basestation_data[0]['intrusion_settings']['active_mode'].lower(), basestation_data[0]['id'].lower(),
                             basestation_data[0]['friendly_name'].lower(), basestation_data, url_domo, cfg_domo)
                    modus = basestation_data[0]['intrusion_settings']['active_mode']
                epoch = time.time()
            lastevents = rest(GET, url_monitor + '&from_ts=' + from_ts)
            for item in reversed(lastevents['events']):
                try:
                    if 'type' in item['o']:
                        log(time.strftime('%m/%d/%y %H:%M:%S', time.localtime(int(item['ts']) / 1000)) + ' | ' + item['o'][
                            'type'].ljust(8) + ' | ' + item['type'] + ' ' + item['o'].get('friendly_name', item['o']['type']))
                        if args.monitor > 1:
                            if item['o']['type'] == 'ycam':
                                domoticz(item['type'][5:].lower(), item['source_id'].lower(), 'ycam', basestation_data, url_domo, cfg_domo)
                            else:
                                domoticz(item['type'].lower(), item['o']['id'].lower(), item['o'].get('friendly_name', 'basestation').lower(),
                                         basestation_data, url_domo, cfg_domo)
                    else:
                        log(time.strftime('%m/%d/%y %H:%M:%S', time.localtime(int(item['ts']) / 1000)) +
                            ' | ' + 'system'.ljust(8) + ' | ' + item['source_type'] + ' ' + item['type'])
                        domoticz(item['type'].lower(), basestation_data[0]['id'].lower(), item['source_type'].lower(), basestation_data, url_domo, cfg_domo)
                    from_ts = str(int(item['ts']) + 1)
                except KeyError:
                    continue
            if time.time() - auth_time >= AUTH_EXPIRE:
                auth_time = authenticate(reauthenticate=True)
            else:
                time.sleep(1)
    except KeyboardInterrupt:
        if args.monitor > 1:
            rest(GET, url_domo + URL_LOG + 'Gigaset Elements - Command-line Interface: Domoticz mode halted')
        log('Program'.ljust(17) + ' | ' + color('halted'.ljust(8)) + ' | ' + 'CTRL+C')
    return


def domoticz(event, sid, friendly, basestation_data, url_domo, cfg_domo):
    """Push events to domoticz server."""
    if event in ['open', 'close', 'sirenon', 'sirenoff', 'on', 'off', 'movement', 'motion']:
        if event in ['close', 'sirenoff', 'off']:
            cmd = 'off'
        else:
            cmd = 'on'
        rest(GET, url_domo + URL_SWITCH + cmd.title() + '&idx=' + cfg_domo[sid])
    elif event in ['button1', 'button2', 'button3', 'button4']:
        rest(GET, url_domo + URL_ALERT + cfg_domo[sid] + '&nvalue=1' + '&svalue=' + event[-1:] + '0')
    elif event in ['home', 'custom', 'away', 'night']:
        rest(GET, url_domo + URL_ALERT + cfg_domo[basestation_data[0]['id'].lower()].split(',')[1] + '&nvalue=1' + '&svalue=' + LEVEL.get(event))
    else:
        status_data = rest(GET, URL_HEALTH)
        rest(GET, url_domo + URL_ALERT + cfg_domo[basestation_data[0]['id'].lower()].split(',')[0] + '&nvalue=' +
             LEVEL.get(status_data['system_health'], '3') + '&svalue=' + friendly + ' | ' + event)
    sys.stdout.write('\033[F')
    sys.stdout.write('\033[K')
    return


def sensor(basestation_data, sensor_exist, camera_data):
    """Show sensor details and current state."""
    log(basestation_data[0]['friendly_name'].ljust(17) + ' | ' + color(basestation_data[0]
                                                                       ['status'].ljust(8)) + ' | firmware ' + color(basestation_data[0]['firmware_status']))
    for item in basestation_data[0]['sensors']:
        try:
            log(item['friendly_name'].ljust(17) + ' | ' + color(item['status'].ljust(8)) + ' | firmware ' + color(item['firmware_status']), 0, 0, 0)
            if item['type'] not in ['is01', 'sp01']:
                print('| battery ' + color(item['battery']['state']), end=' ')
            if item['type'] in ['ds02', 'ds01']:
                print('| position ' + color(item['position_status']), end=' ')
            if args.sensor > 1:
                print('| ' + item['id'].upper(), end=' ')
            print()
        except KeyError:
            print()
            continue
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


def camera_stream(camera_data, sensor_exist):
    """Show camera details and current state."""
    if not sensor_exist['camera']:
        log('Camera'.ljust(17) + ' | ' + 'ERROR'.ljust(8) + ' | Not found', 3, 1)
    try:
        for cam in camera_data:
            stream_data = rest(GET, URL_CAMERA + '/' + cam['id'] + '/liveview/start')
            for stream in ('m3u8', 'rtmp', 'rtsp'):
                log(cam['friendly_name'].ljust(17) + ' | ' + stream.upper().ljust(8) + ' | ' + stream_data['uri'][stream])
    except KeyError:
        print()
    return


def record(camera_data, sensor_exist):
    """Start or stop camera recording based on current state."""
    if not sensor_exist['camera']:
        log('Camera'.ljust(17) + ' | ' + 'ERROR'.ljust(8) + ' | Not found', 3, 1)
    camera_status = rest(GET, URL_CAMERA + '/' + str(camera_data[0]['id']) + '/recording/status')
    if camera_status['description'] == 'Recording not started':
        rest(GET, URL_CAMERA + '/' + str(camera_data[0]['id']) + '/recording/start')
        log('Camera recording'.ljust(17) + ' | ' + color('started'.ljust(8)) + ' | ')
    if camera_status['description'] == 'Recording already started':
        rest(GET, URL_CAMERA + '/' + str(camera_data[0]['id']) + '/recording/stop')
        log('Camera recording'.ljust(17) + ' | ' + color('stopped'.ljust(8)) + ' | ')
    return


def getsnapshot(camera_data, sensor_exist):
    """Download snapshot from camera."""
    if not sensor_exist['camera']:
        log('Camera'.ljust(17) + ' | ' + 'ERROR'.ljust(8) + ' | Not found', 3, 1)
    image_name = 'snapshot_' + time.strftime('%y%m%d') + '_' + time.strftime('%H%M%S') + '.jpg'
    if filewritable('Snapshot image', image_name, 0):
        log('Camera snapshot'.ljust(17) + ' | ' + color('download'.ljust(8)) + ' | ' + image_name)
        with open(image_name, 'wb') as image:
            image.write(rest(GET, URL_CAMERA + '/' + str(camera_data[0]['id']) + '/snapshot?fresh=true'))
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
        print()
        sys.exit()
    filehandle.setLevel(logging.INFO)
    logger.addHandler(filehandle)
    logger.info('[' + time.strftime('%c') + '] ' + 'Gigaset Elements'.ljust(17) + ' | ' + 'CLI'.ljust(8) + ' | ' + _VERSION_ + ' | ' + ' '.join(sys.argv[1:]))
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

        basestation_data, status_data, camera_data = systemstatus()

        sensor_id, sensor_exist = collect_hw(basestation_data, camera_data)

        if args.modus is not None and args.cronjob is None:
            modus_switch(basestation_data, status_data)
            if args.sensor is not True:
                pb_body = 'Status ' + status_data['system_health'].upper() + ' | Modus set from ' + \
                    basestation_data[0]['intrusion_settings']['active_mode'].upper() + ' to ' + args.modus.upper()

        if args.sensor:
            sensor(basestation_data, sensor_exist, camera_data)
            if status_data['status_msg_id'] == '':
                status_data['status_msg_id'] = '\u2713'
            pb_body = 'Status ' + status_data['system_health'].upper() + ' | ' + status_data['status_msg_id'].upper() + \
                ' | Modus ' + basestation_data[0]['intrusion_settings']['active_mode'].upper()

        if args.delay is not None:
            set_delay(basestation_data)

        if args.privacy is not None:
            set_privacy(basestation_data)

        if args.stream:
            camera_stream(camera_data, sensor_exist)

        if args.record:
            record(camera_data, sensor_exist)

        if args.snapshot:
            getsnapshot(camera_data, sensor_exist)

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

        if args.monitor:
            if args.monitor > 1 and args.sensorpairs:
                try:
                    for keypair in args.sensorpairs:
                        cfg_domo = {key: value for key, value in (rule.split(":") for rule in keypair.lower().split(';'))}
                except ValueError:
                    log('Config'.ljust(17) + ' | ' + 'ERROR'.ljust(8) + ' | check sensor pairing value format', 3, 1)
            else:
                cfg_domo = None
            monitor(auth_time, basestation_data, status_data, args.url, cfg_domo)
        print()
    except KeyboardInterrupt:
        log('Program'.ljust(17) + ' | ' + color('halted'.ljust(8)) + ' | ' + 'CTRL+C')


def main():
    """Main program."""
    if args.daemon and os.name != 'nt':
        print()
        if filewritable('PID file', args.pid):
            daemon = Daemonize(app='gigasetelements-cli', pid=args.pid, action=base, auto_close_fds=False, chdir=os.path.dirname(os.path.abspath(sys.argv[0])))
            daemon.start()
    else:
        base()
