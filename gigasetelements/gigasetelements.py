#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""Main code for gigasetelements command-line interface."""


import gc
import os
import sys
import time
import datetime
import argparse
import json
import ConfigParser
import unidecode


_AUTHOR_ = 'dynasticorpheus@gmail.com'
_VERSION_ = '1.4.0'

parser = argparse.ArgumentParser(description='Gigaset Elements - Command-line Interface by dynasticorpheus@gmail.com')
parser.add_argument('-c', '--config', help='fully qualified name of configuration-file', required=False)
parser.add_argument('-u', '--username', help='username (email) in use with my.gigaset-elements.com', required=False)
parser.add_argument('-p', '--password', help='password in use with my.gigaset-elements.com', required=False)
parser.add_argument('-n', '--notify', help='pushbullet token', required=False, metavar='TOKEN')
parser.add_argument('-e', '--events', help='show last <number> of events', type=int, required=False)
parser.add_argument('-d', '--date', help='filter events on begin date - end date', required=False, nargs=2, metavar='DD/MM/YYYY')
parser.add_argument('-o', '--cronjob', help='schedule cron job at HH:MM (requires -m option)', required=False, metavar='HH:MM')
parser.add_argument('-x', '--remove', help='remove all cron jobs linked to this program', action='store_true', required=False)
parser.add_argument('-f', '--filter', help='filter events on type', required=False, choices=(
    'door', 'motion', 'siren', 'plug', 'button', 'homecoming', 'intrusion', 'systemhealth', 'camera'))
parser.add_argument('-m', '--modus', help='set modus', required=False, choices=('home', 'away', 'custom'))
parser.add_argument('-k', '--delay', help='set alarm timer delay in seconds (use 0 to disable)', type=int, required=False)
parser.add_argument('-D', '--daemon', help='daemonize during monitor/domoticz mode', action='store_true', required=False)
parser.add_argument('-z', '--notifications', help='show notification status', action='store_true', required=False)
parser.add_argument('-l', '--log', help='fully qualified name of log file', required=False)
parser.add_argument('-R', '--rules', help='show custom rules', action='store_true', required=False)
parser.add_argument('-P', '--pid', help='fully qualified name of pid file', default='/tmp/gigasetelements-cli.pid', required=False)
parser.add_argument('-s', '--sensor', help='''show sensor status (use -ss to include sensor id's)''', action='count', default=0, required=False)
parser.add_argument('-b', '--siren', help='arm/disarm siren', required=False, choices=('arm', 'disarm'))
parser.add_argument('-g', '--plug', help='switch plug on/off', required=False, choices=('on', 'off'))
parser.add_argument('-a', '--camera', help='show camera status', action='store_true', required=False)
parser.add_argument('-r', '--record', help='switch camera recording on/off', action='store_true', required=False)
parser.add_argument('-t', '--monitor', help='show events using monitor mode (use -tt to activate domoticz mode)', action='count', default=0, required=False)
parser.add_argument('-i', '--ignore', help='ignore configuration-file at predefined locations', action='store_true', required=False)
parser.add_argument('-j', '--restart', help='automatically restart program in case of a connection error', action='store_true', required=False)
parser.add_argument('-q', '--quiet', help='do not send pushbullet message', action='store_true', required=False)
parser.add_argument('-I', '--insecure', help='disable SSL/TLS certificate verification', action='store_true', required=False)
parser.add_argument('-w', '--warning', help='suppress urllib3 warnings', action='store_true', required=False)
parser.add_argument('-v', '--version', help='show version', action='version', version='%(prog)s version ' + str(_VERSION_))

gc.disable()
args = parser.parse_args()

print
print 'Gigaset Elements - Command-line Interface'
print

if os.name == 'nt':
    import colorama
    colorama.init()
    args.cronjob = None
    args.remove = False

if args.daemon and os.name != 'nt':
    from daemonize import Daemonize
    try:
        target = open(args.pid, 'w')
        target.close()
    except IOError:
        print('\033[91m' + '[-] Unable to write pid file ' + args.pid + '\033[0m')
        print
        sys.exit()

if args.log is not None:
    import logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    try:
        fh = logging.FileHandler(args.log, 'a')
    except IOError:
        print('\033[91m' + '[-] Unable to write log file ' + args.log + '\033[0m')
        print
        sys.exit()
    fh.setLevel(logging.INFO)
    logger.addHandler(fh)
    logger.info('[' + time.strftime("%c") + '] Gigaset Elements - Command-line Interface')

if args.cronjob is None and args.remove is False:
    import requests
    s = requests.Session()
    s.mount("http://", requests.adapters.HTTPAdapter(max_retries=3))
    s.mount("https://", requests.adapters.HTTPAdapter(max_retries=3))


URL_IDENTITY = 'https://im.gigaset-elements.de/identity/api/v1/user/login'
URL_AUTH = 'https://api.gigaset-elements.de/api/v1/auth/openid/begin?op=gigaset'
URL_EVENTS = 'https://api.gigaset-elements.de/api/v2/me/events'
URL_BASE = 'https://api.gigaset-elements.de/api/v1/me/basestations'
URL_CAMERA = 'https://api.gigaset-elements.de/api/v1/me/cameras'
URL_HEALTH = 'https://api.gigaset-elements.de/api/v2/me/health'
URL_CHANNEL = 'https://api.gigaset-elements.de/api/v1/me/notifications/users/channels'
URL_USAGE = 'https://goo.gl/wjLswA'

URL_SWITCH = '/json.htm?type=command&param=switchlight&switchcmd='
URL_ALERT = '/json.htm?type=command&param=udevice&idx='
URL_LOG = '/json.htm?type=command&param=addlogmessage&message='

LEVEL = {'intrusion': '4', 'unusual': '3', 'button': '2', 'ok': '1', 'green': '1', 'orange': '3', 'red': '4'}

AUTH_EXPIRE = 21540


class bcolors:
    """Define color classes."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARN = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def restart_program():
    """Restarts the current program."""
    python = sys.executable
    os.execl(python, python, * sys.argv)
    return


def log(logme, rbg=0, exitnow=0, newline=1):
    """Print output in selected color and provide program exit on critical error."""
    if os.name == 'nt':
        logme = unidecode.unidecode(unicode(logme))
    if args.log is not None:
        logger.info('[' + time.strftime("%c") + '] ' + unidecode.unidecode(unicode(logme)))
    if rbg == 1:
        print bcolors.OKGREEN + '[-] ' + logme.encode('utf-8') + bcolors.ENDC
    elif rbg == 2:
        print bcolors.WARN + '[-] ' + logme.encode('utf-8') + bcolors.ENDC
    elif rbg == 3:
        print bcolors.FAIL + '[-] ' + logme.encode('utf-8') + bcolors.ENDC
    else:
        if newline == 1:
            print '[-] ' + logme.encode('utf-8')
        else:
            print '[-] ' + logme.encode('utf-8'),
    if exitnow == 1 and args.restart:
        print
        restart_program()
    if exitnow == 1:
        print
        sys.exit()
    return


def color(txt):
    """Add color to string based on presence in list and return in uppercase."""
    green = ['ok', 'online', 'closed', 'up_to_date', 'home', 'auto', 'on', 'hd', 'cable', 'normal', 'daemon',
             'wifi', 'started', 'active', 'green', 'armed', 'pushed', 'verified', 'loaded', 'success']
    orange = ['orange', 'warning']
    if args.log is not None:
        txt = txt.upper()
    else:
        if txt.lower().strip() in green:
            txt = bcolors.OKGREEN + txt.upper() + bcolors.ENDC
        elif txt.lower().strip() in orange:
            txt = bcolors.WARN + txt.upper() + bcolors.ENDC
        else:
            txt = bcolors.FAIL + txt.upper() + bcolors.ENDC
    return txt


def configure():
    """Load variables based on command line arguments and config file."""
    global dconfig
    global url_domo
    global credfromfile
    global pem
    credfromfile = False
    authstring = ''
    if args.insecure:
        pem = False
    else:
        try:
            import certifi
            pem = certifi.old_where()
        except Exception:
            pem = True
    if args.config is None:
        locations = ['/opt/etc/gigasetelements-cli.conf', '/usr/local/etc/gigasetelements-cli.conf', '/usr/etc/gigasetelements-cli.conf',
                     '/etc/gigasetelements-cli.conf', os.path.expanduser('~/.gigasetelements-cli/gigasetelements-cli.conf'),
                     os.path.expanduser('~/Library/Application Support/gigasetelements-cli/gigasetelements-cli.conf')]
        for i in locations:
            if os.path.exists(i):
                args.config = i
        if args.ignore:
            args.config = None
    else:
        if not os.path.exists(args.config):
            log('Configuration'.ljust(17) + ' | ' + 'ERROR'.ljust(8) + ' | File does not exist ' + args.config, 3, 1)
    if args.config is not None:
        config = ConfigParser.ConfigParser()
        config.read(args.config)
        if args.monitor > 1:
            try:
                dconfig = dict(config.items('domoticz'))
                if dconfig['username'] != '':
                    authstring = dconfig['username'] + ':' + dconfig['password'] + '@'
                url_domo = 'http://' + authstring + dconfig['ip'] + ':' + dconfig['port']
            except Exception:
                log('Configuration'.ljust(17) + ' | ' + 'ERROR'.ljust(8) + ' | Domoticz setting(s) incorrect and/or missing', 3, 1)
        log('Configuration'.ljust(17) + ' | ' + color('loaded'.ljust(8)) + ' | ' + args.config)
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
    if None in (args.username, args.password):
        log('Configuration'.ljust(17) + ' | ' + 'ERROR'.ljust(8) + ' | Username and/or password missing', 3, 1)
    return


def restget(url, head=0, seconds=90, end=1):
    """REST interaction using GET or HEAD."""
    try:
        if head == 1:
            header = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'}
            r = s.head(url, timeout=seconds, headers=header, allow_redirects=True, verify=pem)
        else:
            r = s.get(url, timeout=seconds, stream=False, verify=pem)
    except requests.exceptions.RequestException as e:
        log('ERROR'.ljust(17) + ' | ' + 'UNKNOWN'.ljust(8) + ' | ' + str(time.strftime('%m/%d/%y %H:%M:%S')) + ' ' + str(e.message), 3, end)
    if r.status_code != requests.codes.ok:
        log('HTTP ERROR'.ljust(17) + ' | ' + str(r.status_code).ljust(8) + ' | ' + str(time.strftime('%m/%d/%y %H:%M:%S')), 3, end)
    try:
        data = r.json()
    except ValueError:
        data = r.text
    return data


def restpost(url, payload, head=None):
    """REST interaction using POST."""
    try:
        if head is not None:
            r = s.post(url, data=payload, timeout=90, stream=False, headers=head, verify=pem)
        else:
            r = s.post(url, data=payload, timeout=90, stream=False, verify=pem)
    except requests.exceptions.RequestException as e:
        log('ERROR'.ljust(17) + ' | ' + 'UNKNOWN'.ljust(8) + ' | ' + str(time.strftime('%m/%d/%y %H:%M:%S')) + ' ' + str(e.message), 3, 1)
    if r.status_code != requests.codes.ok:
        log('HTTP ERROR'.ljust(17) + ' | ' + str(r.status_code).ljust(8) + ' | ' + str(time.strftime('%m/%d/%y %H:%M:%S')), 3, 1)
    try:
        commit_data = r.json()
    except ValueError:
        commit_data = r.text
    return commit_data


def connect():
    """Gigaset Elements API authentication and status retrieval."""
    global basestation_data
    global status_data
    global camera_data
    global auth_time
    if args.warning:
        try:
            requests.packages.urllib3.disable_warnings()
        except Exception:
            pass
    payload = {'password': args.password, 'email': args.username}
    commit_data = restpost(URL_IDENTITY, payload)
    log('Identity'.ljust(17) + ' | ' + color('verified') + ' | ' + commit_data['message'])
    auth_time = time.time()
    restget(URL_AUTH)
    log('Authentication'.ljust(17) + ' | ' + color('success'.ljust(8)) + ' | ')
    restget(URL_USAGE, 1, 3, 0)
    basestation_data = restget(URL_BASE)
    log('Basestation'.ljust(17) + ' | ' + color(basestation_data[0]['status'].ljust(8)) + ' | ' + basestation_data[0]['id'])
    camera_data = restget(URL_CAMERA)
    status_data = restget(URL_HEALTH)
    if status_data['system_health'] == 'green':
        status_data['status_msg_id'] = ''
    else:
        status_data['status_msg_id'] = ' | ' + status_data['status_msg_id']
    if args.modus is None:
        log('Status'.ljust(17) + ' | ' + color(status_data['system_health'].ljust(8)) +
            status_data['status_msg_id'].upper() + ' | Modus ' + color(basestation_data[0]['intrusion_settings']['active_mode']))
    return


def collect_hw():
    """Retrieve sensor list and details."""
    global sensor_id
    global sensor_exist
    sensor_id = {}
    sensor_exist = dict.fromkeys(['button', 'camera', 'door_sensor', 'indoor_siren', 'presence_sensor', 'smart_plug'], False)
    for item in basestation_data[0]['sensors']:
        sensor_id.setdefault(item['type'], []).append(item['id'])
    try:
        if 'id' in camera_data[0] and len(camera_data[0]['id']) == 12:
            sensor_id.update(dict.fromkeys(['yc01'], camera_data[0]['id']))
    except IndexError:
        pass
    if 'is01' in sensor_id:
        sensor_exist.update(dict.fromkeys(['indoor_siren'], True))
    if 'sp01' in sensor_id:
        sensor_exist.update(dict.fromkeys(['smart_plug'], True))
    if 'bn01' in sensor_id:
        sensor_exist.update(dict.fromkeys(['button'], True))
    if 'yc01' in sensor_id:
        sensor_exist.update(dict.fromkeys(['camera'], True))
    if 'ws02' in sensor_id:
        sensor_exist.update(dict.fromkeys(['window_sensor'], True))
    if 'ps01' in sensor_id or 'ps02' in sensor_id:
        sensor_exist.update(dict.fromkeys(['presence_sensor'], True))
    if 'ds01' in sensor_id or 'ds02' in sensor_id:
        sensor_exist.update(dict.fromkeys(['door_sensor'], True))
    return


def modus_switch():
    """Switch alarm modus."""
    switch = {'intrusion_settings': {'active_mode': args.modus}}
    restpost(URL_BASE + '/' + basestation_data[0]['id'], json.dumps(switch))
    log('Status'.ljust(17) + ' | ' + color(status_data['system_health'].ljust(8)) + status_data['status_msg_id'].upper() +
        ' | Modus set from ' + color(basestation_data[0]['intrusion_settings']['active_mode']) + ' to ' + color(args.modus))
    return


def set_delay():
    """Set alarm trigger delay."""
    linfo = ''
    delay = str(args.delay * 1000)
    if args.delay > 0:
        sinfo = 'delayed'
        linfo = str(args.delay) + ' seconds'
    else:
        sinfo = 'normal'
        linfo = 'No delay'
    switch = {"intrusion_settings": {"modes": [{"away": {"trigger_delay": delay}}]}}
    restpost(URL_BASE + '/' + basestation_data[0]['id'], json.dumps(switch))
    log('Alarm timer'.ljust(17) + ' | ' + color((sinfo).ljust(8)) + ' | ' + linfo)
    return


def siren():
    """Dis(arm) siren."""
    if not sensor_exist['indoor_siren']:
        log('Siren'.ljust(17) + ' | ' + 'ERROR'.ljust(8) + ' | Not found', 3, 1)
    modus = ['home', 'away', 'custom']
    if args.siren == 'disarm':
        for m in modus:
            switch = {"intrusion_settings": {"modes": [{m: {"sirens_on": False}}]}}
            restpost(URL_BASE + '/' + basestation_data[0]['id'], json.dumps(switch))
    else:
        for m in modus:
            switch = {"intrusion_settings": {"modes": [{m: {"sirens_on": True}}]}}
            restpost(URL_BASE + '/' + basestation_data[0]['id'], json.dumps(switch))
    log('Siren'.ljust(17) + ' | ' + color((args.siren + 'ED').ljust(8)) + ' | ')
    return


def plug():
    """Switch Plug on or off."""
    if not sensor_exist['smart_plug']:
        log('Plug'.ljust(17) + ' | ' + 'ERROR'.ljust(8) + ' | Not found', 3, 1)
    switch = {"name": args.plug}
    header = {'content-type': 'application/json; charset=UTF-8'}
    restpost(URL_BASE + '/' + basestation_data[0]['id'] + '/endnodes/' + sensor_id['sp01'][0] + '/cmd', json.dumps(switch), header)
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
    from crontab import CronTab
    if args.modus is None:
        log('Cronjob'.ljust(17) + ' | ' + 'ERROR'.ljust(8) + ' | Specify modus using -m option', 3, 1)
    if istimeformat(args.cronjob):
        cron = CronTab(user=True)
        now = datetime.datetime.now()
        timer = now.replace(hour=time.strptime(args.cronjob, '%H:%M')[3], minute=time.strptime(args.cronjob, '%H:%M')[4], second=0, microsecond=0)
        if credfromfile:
            job = cron.new('gigasetelements-cli -m ' + args.modus, comment='added by gigasetelements-cli on ' + str(now)[:16])
        else:
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
        log('Cronjob'.ljust(17) + ' | ' + color(args.modus.ljust(8)) + ' | ' + 'Modus on ' + timer.strftime('%A %d %B %Y %H:%M'))
    else:
        log('Cronjob'.ljust(17) + ' | ' + 'ERROR'.ljust(8) + ' | Use valid time (00:00 - 23:59)', 3, 1)
    return


def remove_cron():
    """Remove all jobs from crontab setting alarm modus."""
    from crontab import CronTab
    cron = CronTab(user=True)
    existing = cron.find_command('gigasetelements-cli')
    count = 0
    for i in existing:
        log('Cronjob'.ljust(17) + ' | ' + color('removed'.ljust(8)) + ' | ' + str(i))
        count += 1
    cron.remove_all(comment='gigasetelements-cli')
    if count == 0:
        log('Cronjob'.ljust(17) + ' | ' + color('warning'.ljust(8)) + ' | ' + 'No items found for removal')
    else:
        cron.write()
    return


def pb_message(pbmsg):
    """Send message using pushbullet module."""
    if args.notify is not None and args.quiet is not True:
        from pushbullet import PushBullet, InvalidKeyError, PushbulletError
        try:
            pb = PushBullet(args.notify)
        except InvalidKeyError:
            log('Notification'.ljust(17) + ' | ' + color('token'.ljust(8)) + ' | ')
        except PushbulletError:
            log('Notification'.ljust(17) + ' | ' + color('error'.ljust(8)) + ' | ')
        else:
            pb.push_note('Gigaset Elements', pbmsg)
            log('Notification'.ljust(17) + ' | ' + color('pushed'.ljust(8)) + ' | ')
    return


def list_events():
    """List past events optionally filtered by date and/or type."""
    if args.filter is None and args.date is None:
        log('Event(s)'.ljust(17) + ' | ' + str(args.events).ljust(8) + ' | ' + 'No filter')
        event_data = restget(URL_EVENTS + '?limit=' + str(args.events))
    if args.filter is not None and args.date is None:
        log('Event(s)'.ljust(17) + ' | ' + str(args.events).ljust(8) + ' | ' + args.filter.title())
        event_data = restget(URL_EVENTS + '?limit=' + str(args.events) + '&group=' + str(args.filter))
    if args.date is not None:
        try:
            from_ts = str(int(time.mktime(time.strptime(args.date[0], '%d/%m/%Y'))) * 1000)
            to_ts = str(int(time.mktime(time.strptime(args.date[1], '%d/%m/%Y'))) * 1000)
        except Exception:
            log('Event(s)'.ljust(17) + ' | ' + 'ERROR'.ljust(8) + ' | ' + 'Date(s) filter not in DD/MM/YYYY format', 3, 1)
    if args.filter is None and args.date is not None:
        log('Event(s)'.ljust(17) + ' | ' + 'DATE'.ljust(8) + ' | ' + args.date[0] + ' - ' + args.date[1])
        event_data = restget(URL_EVENTS + '?from_ts=' + from_ts + '&to_ts=' + to_ts + '&limit=999')
    if args.filter is not None and args.date is not None:
        log('Event(s)'.ljust(17) + ' | ' + '*'.ljust(8) + ' | ' + args.filter.title() + ' | ' + args.date[0] + ' - ' + args.date[1])
        event_data = restget(URL_EVENTS + '?from_ts=' + from_ts + '&to_ts=' + to_ts + '&group=' + str(args.filter) + '&limit=999')
    for item in event_data['events']:
        try:
            if 'type' in item['o']:
                log(time.strftime('%m/%d/%y %H:%M:%S', time.localtime(int(item['ts']) / 1000)) + ' | ' + item['o']
                    ['type'].ljust(8) + ' | ' + item['type'] + ' ' + item['o'].get('friendly_name', item['o']['type']))
        except KeyError:
            log(time.strftime('%m/%d/%y %H:%M:%S', time.localtime(int(item['ts']) / 1000)) + ' | ' + item['type'].ljust(8) + ' | ' + item['source_type'])
            continue
    return


def monitor():
    """List events realtime optionally filtered by type."""
    global auth_time
    if args.filter is None:
        url_monitor = URL_EVENTS + '?limit=10'
    else:
        url_monitor = URL_EVENTS + '?limit=10&group=' + args.filter
    if args.monitor > 1:
        mode = 'Domoticz mode'
        print
        restget(url_domo + URL_LOG + 'Gigaset Elements - Command-line Interface: Domoticz mode started')
        domoticz(status_data['system_health'].lower(), basestation_data[0]['id'].lower(), basestation_data[0]['friendly_name'].lower())
    else:
        mode = 'Monitor mode'
    log(mode.ljust(17) + ' | ' + color('started'.ljust(8)) + ' | ' + 'CTRL+C to exit')
    from_ts = str(int(time.time())*1000)
    try:
        while 1:
            lastevents = restget(url_monitor + '&from_ts=' + from_ts)
            for item in reversed(lastevents['events']):
                try:
                    if 'type' in item['o']:
                        log(time.strftime('%m/%d/%y %H:%M:%S', time.localtime(int(item['ts']) / 1000)) + ' | ' + item['o'][
                            'type'].ljust(8) + ' | ' + item['type'] + ' ' + item['o'].get('friendly_name', item['o']['type']))
                        if args.monitor > 1:
                            if item['o']['type'] == 'ycam':
                                domoticz(item['type'][5:].lower(), item['source_id'].lower(), 'ycam')
                            else:
                                domoticz(item['type'].lower(), item['o']['id'].lower(), item['o'].get('friendly_name', 'basestation').lower())
                    else:
                        log(time.strftime('%m/%d/%y %H:%M:%S', time.localtime(int(item['ts']) / 1000)) +
                            ' | ' + 'system'.ljust(8) + ' | ' + item['source_type'] + ' ' + item['type'])
                        domoticz(item['type'].lower(), basestation_data[0]['id'].lower(), item['source_type'].lower())
                    from_ts = str(int(item['ts']) + 1)
                except KeyError:
                    continue
            if time.time() - auth_time >= AUTH_EXPIRE:
                auth_time = time.time()
                restget(URL_AUTH)
            else:
                time.sleep(1)
    except KeyboardInterrupt:
        if args.monitor > 1:
            restget(url_domo + URL_LOG + 'Gigaset Elements - Command-line Interface: Domoticz mode halted')
        log('Program'.ljust(17) + ' | ' + color('halted'.ljust(8)) + ' | ' + 'CTRL+C')
    return


def domoticz(event, sid, friendly):
    """Push events to domoticz server."""
    global status_data
    if event in ['open', 'close', 'sirenon', 'sirenoff', 'on', 'off', 'movement', 'motion', 'button1', 'button2', 'button3', 'button4']:
        if event in ['close', 'sirenoff', 'off']:
            cmd = 'off'
        else:
            cmd = 'on'
        restget(url_domo + URL_SWITCH + cmd.title() + '&idx=' + dconfig[sid])
    else:
        status_data = restget(URL_HEALTH)
        restget(url_domo + URL_ALERT + dconfig[basestation_data[0]['id'].lower()] + '&nvalue=' +
                LEVEL.get(status_data['system_health'], '3') + '&svalue=' + friendly + ' | ' + event)
    sys.stdout.write("\033[F")
    sys.stdout.write("\033[K")
    return


def sensor():
    """Show sensor details and current state."""
    log(basestation_data[0]['friendly_name'].ljust(17) + ' | ' + color(basestation_data[0]
                                                                       ['status'].ljust(8)) + ' | firmware ' + color(basestation_data[0]['firmware_status']))
    for item in basestation_data[0]['sensors']:
        try:
            log(item['friendly_name'].ljust(17) + ' | ' + color(item['status'].ljust(8)) + ' | firmware ' + color(item['firmware_status']), 0, 0, 0)
            if item['type'] not in ['is01', 'sp01']:
                print '| battery ' + color(item['battery']['state']),
            if item['type'] in ['ds02', 'ds01']:
                print '| position ' + color(item['position_status']),
            if args.sensor > 1:
                print '| ' + item['id'].upper(),
            print
        except KeyError:
            print
            continue
    return


def rules():
    """List custom rule(s)."""
    rules = restget(URL_BASE + '/' + basestation_data[0]['id'] + '/rules?rules=custom')
    for item in rules:
        try:
            if item['active']:
                item['active'] = 'active'
            else:
                item['active'] = 'inactive'
            if item['parameter']['start_time'] == 0 and item['parameter']['end_time'] == 86400:
                timer = '00:00 - 00:00'.ljust(13)
            else:
                timer = str(datetime.timedelta(seconds=int(item['parameter']['start_time']))).rjust(8, '0')[
                    0:5] + ' - ' + str(datetime.timedelta(seconds=int(item['parameter']['end_time']))).rjust(8, '0')[0:5]
            if item['parameter']['repeater']['frequency'] == 'daily':
                days = '1, 2, 3, 4, 5, 6, 7'
            else:
                days = str(item['parameter']['repeater']['at']).replace('[', '').replace(']', '').ljust(19)
            log(item['friendly_name'].ljust(17) + ' | ' + color(item['active'].ljust(8)) + ' | ' + item['parameter']['repeater']
                ['frequency'].ljust(7) + ' | ' + timer + ' | ' + days + ' | ' + item['recipe'].replace('_', ' ') + ' | ' + item['id'])
        except KeyError:
            continue
    return


def notifications():
    """List notification settings per mobile device."""
    channels = restget(URL_CHANNEL)
    for item in channels.get('gcm', ''):
        try:
            print('[-] ' + item['friendlyName'].ljust(17) + ' | ' + color(item['status'].ljust(8)) + ' |'),
            for item2 in item['notificationGroups']:
                print item2,
            print
        except KeyError:
            continue
    return


def camera_info():
    """Show camera details and current state."""
    if not sensor_exist['camera']:
        log('Camera'.ljust(17) + ' | ' + 'ERROR'.ljust(8) + ' | Not found', 3, 1)
    try:
        print '[-] ' + camera_data[0]['friendly_name'].ljust(
            17) + ' | ' + color(camera_data[0]['status'].ljust(8)) + ' | firmware ' + color(camera_data[0]['firmware_status']),
        print('| quality ' + color(camera_data[0]['settings']['quality']) + ' | nightmode ' +
              color(camera_data[0]['settings']['nightmode']) + ' | mic ' + color(camera_data[0]['settings']['mic'])),
        print('| motion detection ' + color(camera_data[0]['motion_detection']['status']) + ' | connection ' + color(camera_data[0]['settings']['connection'])),
        if camera_data[0]['settings']['connection'] == 'wifi':
            print '| ssid ' + bcolors.OKGREEN + str(camera_data[0]['wifi_ssid']).upper() + bcolors.ENDC
    except KeyError:
        print
    stream_data = restget(URL_CAMERA + '/' + camera_data[0]['id'] + '/liveview/start')
    for stream in ('m3u8', 'rtmp', 'rtsp'):
        log('Camera stream'.ljust(17) + ' | ' + stream.upper().ljust(8) + ' | ' + stream_data['uri'][stream])
    return


def record():
    """Start or stop camera recording based on current state."""
    if not sensor_exist['camera']:
        log('Camera'.ljust(17) + ' | ' + 'ERROR'.ljust(8) + ' | Not found', 3, 1)
    camera_status = restget(URL_CAMERA + '/' + str(camera_data[0]['id']) + '/recording/status')
    if camera_status['description'] == 'Recording not started':
        restget(URL_CAMERA + '/' + str(camera_data[0]['id']) + '/recording/start')
        log('Camera recording'.ljust(17) + ' | ' + color('started'.ljust(8)) + ' | ')
    if camera_status['description'] == 'Recording already started':
        restget(URL_CAMERA + '/' + str(camera_data[0]['id']) + '/recording/stop')
        log('Camera recording'.ljust(17) + ' | ' + color('stopped'.ljust(8)) + ' | ')
    return


def main():
    """Main program."""

    pb_body = None

    try:
        configure()

        if args.cronjob is not None:
            add_cron()
            print
            sys.exit()

        if args.remove and args.cronjob is None:
            remove_cron()
            print
            sys.exit()

        connect()

        collect_hw()

        if args.modus is not None and args.cronjob is None:
            modus_switch()
            if args.sensor is not True:
                pb_body = 'Status ' + status_data['system_health'].upper() + ' | Modus set from ' + \
                    basestation_data[0]['intrusion_settings']['active_mode'].upper() + ' to ' + args.modus.upper()

        if args.sensor:
            sensor()
            if status_data['status_msg_id'] == '':
                status_data['status_msg_id'] = u'\u2713'
            pb_body = 'Status ' + status_data['system_health'].upper() + ' | ' + status_data['status_msg_id'].upper() + \
                ' | Modus ' + basestation_data[0]['intrusion_settings']['active_mode'].upper()

        if args.delay is not None:
            set_delay()

        if args.camera:
            camera_info()

        if args.record:
            record()

        if args.notifications:
            notifications()

        if args.rules:
            rules()

        if args.siren:
            siren()

        if args.plug:
            plug()

        if pb_body is not None:
            pb_message(pb_body)

        if args.events is None and args.date is None:
            pass
        else:
            list_events()

        if args.monitor:
            if args.daemon and os.name != 'nt':
                log('Run as background'.ljust(17) + ' | ' + color('daemon'.ljust(8)) + ' | ' + args.pid)
                print
                daemon = Daemonize(app="gigasetelements-cli", pid=args.pid, action=monitor, auto_close_fds=False)
                daemon.start()
            else:
                monitor()

        print

    except KeyboardInterrupt:
        log('Program'.ljust(17) + ' | ' + color('halted'.ljust(8)) + ' | ' + 'CTRL+C')
