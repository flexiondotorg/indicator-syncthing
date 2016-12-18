#!/usr/bin/env python3

import argparse
import datetime
import dateutil.parser
import json
import logging as log
import os
import subprocess
import sys
import time
import urllib.parse
import webbrowser
import pytz
import requests   # used only to catch exceptions
import signal
import socket     # used only to catch exceptions
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')

from requests_futures.sessions import FuturesSession
from gi.repository import Gtk, Gio, GLib
from xml.dom import minidom

VERSION = 'v1.0.0'


def shorten_path(text, maxlength=80):
    if len(text) <= maxlength:
        return text
    head, tail = os.path.split(text)
    if len(tail) > maxlength:
        return tail[:maxlength]  # TODO: separate file extension
    while len(head) + len(tail) > maxlength:
        head = '/'.join(head.split('/')[:-1])
        if head == '':
            return '.../' + tail
    return head + '/.../' + tail


def human_readable(num):
    for unit in ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB']:
        if abs(num) < 1024.0:
            f = '{:.1f}'.format(num).rstrip('0').rstrip('.')
            return '{} {}'.format(f, unit)
        num = num / 1024.0
    return '{:.1f} {}'.format(num, 'YiB')


class Main(object):

    def __init__(self, args):
        log.info('Started main procedure')
        self.args = args
        self.wd = os.path.dirname(os.path.realpath(__file__))
        self.icon_path = os.path.join(self.wd, 'icons')
        if not self.args.text_only:
            from gi.repository import AppIndicator3 as appindicator
            self.ind = appindicator.Indicator.new_with_path(
                'syncthing-indicator',
                'syncthing-client-idle',
                appindicator.IndicatorCategory.APPLICATION_STATUS,
                self.icon_path)
            self.ind.set_status(appindicator.IndicatorStatus.ACTIVE)

        self.state = {'update_folders': True,
                      'update_devices': True,
                      'update_files': True,
                      'update_st_running': False,
                      'set_icon': 'paused'}
        self.set_icon()
        self.create_menu()

        self.downloading_files = []
        self.downloading_files_extra = {}  # map: file_details -> file_details_extra
        self.recent_files = []
        self.folders = []
        self.devices = []
        self.errors = []

        self.last_ping = None
        self.system_status = {}
        self.syncthing_base = 'http://localhost:8080'
        self.syncthing_version = ''
        self.device_name = ''
        self.last_seen_id = 0
        self.timeout_counter = 0
        self.count_connection_error = 0
        self.session = FuturesSession()
        self.current_action = (None, None)

        GLib.idle_add(self.load_config_begin)

    def create_menu(self):
        self.menu = Gtk.Menu()

        self.title_menu = Gtk.MenuItem('Syncthing')
        self.title_menu.show()
        self.title_menu.set_sensitive(False)
        self.menu.append(self.title_menu)

        self.syncthing_upgrade_menu = Gtk.MenuItem('Upgrade check')
        self.syncthing_upgrade_menu.connect(
            'activate', self.open_releases_page)
        self.menu.append(self.syncthing_upgrade_menu)

        self.mi_errors = Gtk.MenuItem('Errors: open web interface')
        self.mi_errors.connect('activate', self.open_web_ui)
        self.menu.append(self.mi_errors)

        sep = Gtk.SeparatorMenuItem()
        sep.show()
        self.menu.append(sep)

        self.devices_menu = Gtk.MenuItem('Devices')
        self.devices_menu.show()
        self.devices_menu.set_sensitive(False)
        self.menu.append(self.devices_menu)
        self.devices_submenu = Gtk.Menu()
        self.devices_menu.set_submenu(self.devices_submenu)

        self.folder_menu = Gtk.MenuItem('Folders')
        self.folder_menu.show()
        self.folder_menu.set_sensitive(False)
        self.menu.append(self.folder_menu)
        self.folder_menu_submenu = Gtk.Menu()
        self.folder_menu.set_submenu(self.folder_menu_submenu)

        sep = Gtk.SeparatorMenuItem()
        sep.show()
        self.menu.append(sep)

        self.current_files_menu = Gtk.MenuItem('Downloading files')
        self.current_files_menu.show()
        self.current_files_menu.set_sensitive(False)
        self.menu.append(self.current_files_menu)
        self.current_files_submenu = Gtk.Menu()
        self.current_files_menu.set_submenu(self.current_files_submenu)

        self.recent_files_menu = Gtk.MenuItem('Recently updated')
        self.recent_files_menu.show()
        self.recent_files_menu.set_sensitive(False)
        self.menu.append(self.recent_files_menu)
        self.recent_files_submenu = Gtk.Menu()
        self.recent_files_menu.set_submenu(self.recent_files_submenu)

        sep = Gtk.SeparatorMenuItem()
        sep.show()
        self.menu.append(sep)

        open_web_ui = Gtk.MenuItem('Open web interface')
        open_web_ui.connect('activate', self.open_web_ui)
        open_web_ui.show()
        self.menu.append(open_web_ui)

        self.more_menu = Gtk.MenuItem('More')
        self.more_menu.show()
        self.menu.append(self.more_menu)

        self.more_submenu = Gtk.Menu()
        self.more_menu.set_submenu(self.more_submenu)

        self.mi_start_syncthing = Gtk.MenuItem('Start Syncthing')
        self.mi_start_syncthing.connect('activate', self.syncthing_start)
        self.mi_start_syncthing.set_sensitive(False)
        self.more_submenu.append(self.mi_start_syncthing)

        self.mi_restart_syncthing = Gtk.MenuItem('Restart Syncthing')
        self.mi_restart_syncthing.connect('activate', self.syncthing_restart)
        self.mi_restart_syncthing.set_sensitive(False)
        self.more_submenu.append(self.mi_restart_syncthing)

        self.mi_shutdown_syncthing = Gtk.MenuItem('Shutdown Syncthing')
        self.mi_shutdown_syncthing.connect('activate', self.syncthing_shutdown)
        self.mi_shutdown_syncthing.set_sensitive(False)
        self.more_submenu.append(self.mi_shutdown_syncthing)

        sep = Gtk.SeparatorMenuItem()
        self.more_submenu.append(sep)

        if not self.args.no_shutdown:
            self.mi_start_syncthing.show()
            self.mi_restart_syncthing.show()
            self.mi_shutdown_syncthing.show()
            sep.show()

        self.about_menu = Gtk.MenuItem('About Indicator')
        self.about_menu.connect('activate', self.show_about)
        self.about_menu.show()
        self.more_submenu.append(self.about_menu)

        self.quit_button = Gtk.MenuItem('Quit Indicator')
        self.quit_button.connect('activate', self.leave)
        self.quit_button.show()
        self.more_submenu.append(self.quit_button)
        if not self.args.text_only:
            self.ind.set_menu(self.menu)

    def load_config_begin(self):
        # Read needed values from config file
        confdir = GLib.get_user_config_dir()
        if not confdir:
            confdir = os.path.expanduser('~/.config')
        conffile = os.path.join(confdir, 'syncthing', 'config.xml')
        if not os.path.isfile(conffile):
            log.error("Couldn't find config file {}".format(
                conffile))
            self.leave()
        f = Gio.file_new_for_path(conffile)
        f.load_contents_async(None, self.load_config_finish)
        return False

    def load_config_finish(self, fp, async_result):
        try:
            success, data, etag = fp.load_contents_finish(async_result)

            dom = minidom.parseString(data)

            conf = dom.getElementsByTagName('configuration')
            if not conf:
                raise Exception('No configuration element in config')

            gui = conf[0].getElementsByTagName('gui')
            if not gui:
                raise Exception('No gui element in config')

            # Find the local syncthing address
            address = gui[0].getElementsByTagName('address')
            if not address:
                raise Exception('No address element in config')
            if not address[0].hasChildNodes():
                raise Exception('No address specified in config')

            self.syncthing_base = 'http://%s' % address[0].firstChild.nodeValue

            # Find and fetch the api key
            api_key = gui[0].getElementsByTagName('apikey')
            if not api_key:
                raise Exception('No apikey element in config')
            if not api_key[0].hasChildNodes():
                raise Exception(
                    'No apikey specified in config, please create one via the web interface')
            self.api_key = api_key[0].firstChild.nodeValue

            # Read folders and devices from config
            for elem in conf[0].childNodes:
                if elem.nodeType != minidom.Node.ELEMENT_NODE:
                    continue
                if elem.tagName == 'device':
                    self.devices.append({
                        'id': elem.getAttribute('id'),
                        'name': elem.getAttribute('name'),
                        'state': '',
                        'connected': False,
                        'lastSeen': '',
                    })
                elif elem.tagName == 'folder':
                    self.folders.append({
                        'id': elem.getAttribute('id'),
                        'label': elem.getAttribute('label'),
                        'path': elem.getAttribute('path'),
                        'state': 'unknown',
                    })
            if not self.devices:
                raise Exception('No devices in config')
            if not self.folders:
                raise Exception('No folders in config')
        except Exception as e:
            log.error('Error parsing config file: {}'.format(e))
            self.leave()

        # Start processes
        GLib.idle_add(self.rest_get, '/rest/system/version')
        GLib.idle_add(self.rest_get, '/rest/system/connections')
        GLib.idle_add(self.rest_get, '/rest/system/status')
        GLib.idle_add(self.rest_get, '/rest/system/upgrade')
        GLib.idle_add(self.rest_get, '/rest/system/error')
        GLib.idle_add(self.rest_get, '/rest/events')
        GLib.timeout_add_seconds(self.args.timeout_gui, self.update)
        GLib.timeout_add_seconds(self.args.timeout_rest, self.timeout_rest)
        GLib.timeout_add_seconds(self.args.timeout_event, self.timeout_events)

    def syncthing_url(self, url):
        ''' Creates a url from given values and the address read from file '''
        return urllib.parse.urljoin(self.syncthing_base, url)

    def open_web_ui(self, *args):
        webbrowser.open(self.syncthing_url(''))

    def open_releases_page(self, *args):
        webbrowser.open('https://github.com/syncthing/syncthing/releases')

    def rest_post(self, rest_path):
        log.debug('rest_post {}'.format(rest_path))
        headers = {'X-API-Key': self.api_key}
        if rest_path in ['/rest/system/restart', '/rest/system/shutdown']:
            f = self.session.post(
                self.syncthing_url(rest_path), headers=headers)
        return False

    def rest_get(self, rest_path):
        params = ''
        if rest_path == '/rest/events':
            params = {'since': self.last_seen_id}

        log.info('rest_get {} {}'.format(rest_path, params))
        headers = {'X-API-Key': self.api_key}
        f = self.session.get(self.syncthing_url(rest_path),
                             params=params,
                             headers=headers,
                             timeout=9)
        f.add_done_callback(self.rest_receive_data)
        return False

    def rest_receive_data(self, future):
        try:
            r = future.result()
        except requests.exceptions.ConnectionError:
            log.error(
                "Couldn't connect to Syncthing at {}".format(
                    self.syncthing_base))
            self.count_connection_error += 1
            log.info('count_connection_error: {}'.format(
                self.count_connection_error))
            if self.current_action[0] == 'syncthing_shutdown':
                self.current_action = (None, None)
            if self.count_connection_error > 1:
                self.state['update_st_running'] = True
                self.set_state('paused')
            return
        except (requests.exceptions.Timeout, socket.timeout):
            log.debug('Timeout')
            # Timeout may be because Syncthing restarted and event ID reset.
            GLib.idle_add(self.rest_get, '/rest/system/status')
            return
        except Exception as e:
            log.error('exception: {}'.format(e))
            return

        rest_path = urllib.parse.urlparse(r.url).path
        rest_query = urllib.parse.urlparse(r.url).query
        if r.status_code != 200:
            log.warning('rest_receive_data: {0} failed ({1})'.format(
                rest_path, r.status_code))
            if rest_path == '/rest/system/upgrade':
                # Debian/Ubuntu Syncthing packages disable upgrade check
                pass
            else:
                self.set_state('error')
            if rest_path == '/rest/system/ping':
                # Basic version check: try the old REST path
                GLib.idle_add(self.rest_get, '/rest/ping')
            return

        try:
            json_data = r.json()
        except:
            log.warning('rest_receive_data: Cannot process REST data')
            self.set_state('error')
            return

        # Receiving data appears to have succeeded
        self.count_connection_error = 0
        if self.current_action[0]:
            self.current_action = (None, None)
            self.state['update_st_running'] = True
        self.set_state('idle')  # TODO: fix this
        log.debug('rest_receive_data: {} {}'.format(rest_path, rest_query))
        if rest_path == '/rest/events':
            try:
                for qitem in json_data:
                    self.process_event(qitem)
            except Exception as e:
                log.warning(
                    'rest_receive_data: error processing event ({})'.format(e))
                log.debug(qitem)
                self.set_state('error')
        else:
            fn = getattr(
                self,
                'process_{}'.format(rest_path.strip('/').replace('/', '_'))
            )(json_data)

    # Processing of the events coming from the event interface
    def process_event(self, event):
        if self.args.log_events:
            log.debug('EVENT: {}: {}'.format(event['type'], json.dumps(event)))

        t = event.get('type').lower()
        #log.debug('received event: '+str(event))
        if hasattr(self, 'event_{}'.format(t)):
            log.debug('received event: {} {}'.format(
                event.get('id'), event.get('type')))
            pass
        else:
            log.debug('ignoring event: {} {}'.format(
                event.get('id'), event.get('type')))

        #log.debug(json.dumps(event, indent=4))
        fn = getattr(self, 'event_{}'.format(
            t), self.event_unknown_event)(event)
        self.update_last_seen_id(event.get('id', 0))

    def event_downloadprogress(self, event):
        try:
            e = list(event['data'].values())
            e = list(e[0].keys())[0]
        except (ValueError, KeyError, IndexError):
            e = ""

        log.debug('download in progress: {}'.format(e))
        for folder_name in list(event['data'].keys()):
            for filename in event['data'][folder_name]:
                file_details = json.dumps({'folder': folder_name,
                                           'file': filename,
                                           'type': 'file',
                                           'direction': 'down'})

                must_be_added = False
                try:
                    v = self.downloading_files_extra[file_details]
                except KeyError:
                    v = {}
                    must_be_added = True  # not yet present in downloading_files_extra

                file = event["data"][folder_name][filename]
                if file["bytesTotal"] == 0:
                    pct = 0.0
                else:
                    pct = 100 * file["bytesDone"] / file["bytesTotal"]
                # TODO: convert bytes to kb, mb etc
                v["progress"] = " ({}/{}) - {:.2f}%".format(
                    file["bytesDone"], file["bytesTotal"], pct)
                if must_be_added:
                    self.downloading_files_extra[file_details] = v

            for elm in self.folders:
                if elm['id'] == folder_name:
                    elm['state'] = 'syncing'
                    # TODO: this is slow!
        self.state['update_files'] = True

    def event_unknown_event(self, event):
        pass

    def event_statechanged(self, event):
        for elem in self.folders:
            if elem['id'] == event['data']['folder']:
                elem['state'] = event['data']['to']
        self.state['update_folders'] = True
        self.set_state()

    def event_foldersummary(self, event):
        for elem in self.folders:
            if elem['id'] == event['data']['folder']:
                elem.update(event['data']['summary'])
        self.state['update_folders'] = True

    def event_foldercompletion(self, event):
        for dev in self.devices:
            if dev['id'] == event['data']['device']:
                if event['data']['completion'] < 100:
                    dev['state'] = 'syncing'
                else:
                    dev['state'] = ''
        self.state['update_devices'] = True

    def event_starting(self, event):
        self.set_state('paused')
        log.info('Received that Syncthing was starting at %s' % event['time'])
        # Check for added/removed devices or folders.
        GLib.idle_add(self.rest_get, '/rest/system/config')
        GLib.idle_add(self.rest_get, '/rest/system/version')

    def event_startupcomplete(self, event):
        self.set_state('idle')
        log.info('Syncthing startup complete at %s' %
                 self.convert_time(event['time']))
        if event['data'] != None:
            self.system_status['myID'] = event['data'].get('myID')
        log.info('myID: %s' % self.system_status.get('myID'))

    def event_ping(self, event):
        self.last_ping = dateutil.parser.parse(event['time'])

    def event_devicediscovered(self, event):
        found = False
        for elm in self.devices:
            if elm['id'] == event['data']['device']:
                elm['state'] = 'discovered'
                found = True
        if not found:
            log.warn('unknown device discovered')
            self.devices.append({
                'id': event['data']['device'],
                'name': 'new unknown device',
                'address': event['data']['addrs'],
                'state': 'unknown',
            })
        self.state['update_devices'] = True

    def event_deviceconnected(self, event):
        for dev in self.devices:
            if event['data']['id'] == dev['id']:
                dev['connected'] = True
                log.info('Device connected: %s' % dev['name'])
        self.state['update_devices'] = True

    def event_devicedisconnected(self, event):
        for dev in self.devices:
            if event['data']['id'] == dev['id']:
                dev['connected'] = False
                log.info('Device disconnected: %s' % dev['name'])
        self.state['update_devices'] = True

    def event_itemstarted(self, event):
        log.debug('item started: {}'.format(event['data']['item']))
        file_details = {'folder': event['data']['folder'],
                        'file': event['data']['item'],
                        'type': event['data']['type'],
                        'direction': 'down'}
        try:
            del self.downloading_files_extra[json.dumps(file_details)]
        except KeyError:
            pass

        if file_details not in self.downloading_files:
            self.downloading_files.append(file_details)
        for elm in self.folders:
            if elm['id'] == event['data']['folder']:
                elm['state'] = 'syncing'
        self.set_state()
        self.state['update_files'] = True

    def event_itemfinished(self, event):
        # TODO: test whether 'error' is null
        log.debug('item finished: {}'.format(event['data']['item']))
        file_details = {'folder': event['data']['folder'],
                        'file': event['data']['item'],
                        'type': event['data']['type'],
                        'direction': 'down'}
        try:
            del self.downloading_files_extra[json.dumps(file_details)]
        except KeyError:
            pass
        try:
            self.downloading_files.remove(file_details)
            # action: update, delete, or metadata.
            # versioning:
            # For the first hour, the most recent version is kept every 30 seconds.
            # For the first day, the most recent version is kept every hour.
            # For the first 30 days, the most recent version is kept every day.
            log.debug('file locally updated: %s (%s) at %s' % (
                file_details['file'], event['data']['action'], event['time']))
        except ValueError:
            log.debug('Completed a file we didn\'t know about: {}'.format(
                event['data']['item']))
        file_details['time'] = event['time']
        file_details['action'] = event['data']['action']
        self.recent_files.insert(0, file_details)
        self.recent_files = self.recent_files[:self.args.nb_recent_files]
        self.state['update_files'] = True
    # End of event processing

    # Begin REST processing functions
    def process_rest_system_connections(self, data):
        for elem in data['connections']:
            for dev in self.devices:
                if dev['id'] == elem:
                    dev['connected'] = True
        self.state['update_devices'] = True

    def process_rest_system_config(self, data):
        log.info('Processing /rest/system/config')
        self.api_key = data['gui']['apiKey']

        newfolders = []
        for elem in data['folders']:
            newfolders.append({
                'id': elem['id'],
                'label': elem['label'],
                'path': elem['path'],
                'state': 'unknown',
            })

        newdevices = []
        for elem in data['devices']:
            newdevices.append({
                'id': elem['deviceID'],
                'name': elem['name'],
                'state': '',
                'connected': False,
                'lastSeen': '',
            })

        self.folders = newfolders
        self.devices = newdevices

    def process_rest_system_status(self, data):
        if data['uptime'] < self.system_status.get('uptime', 0):
            # Means that Syncthing restarted
            self.last_seen_id = 0
            GLib.idle_add(self.rest_get, '/rest/system/version')
        self.system_status = data
        # TODO: check status of global announce
        self.state['update_st_running'] = True

    def process_rest_system_upgrade(self, data):
        self.syncthing_version = data['running']
        if data['newer']:
            self.syncthing_upgrade_menu.set_label(
                'New version available: %s' % data['latest'])
            self.syncthing_upgrade_menu.show()
        else:
            self.syncthing_upgrade_menu.hide()
        self.state['update_st_running'] = True

    def process_rest_system_version(self, data):
        self.syncthing_version = data['version']
        self.state['update_st_running'] = True

    def process_rest_system_ping(self, data):
        if data['ping'] == 'pong':
            log.info('Connected to Syncthing REST interface at {}'.format(
                self.syncthing_url('')))

    def process_rest_ping(self, data):
        if data['ping'] == 'pong':
            # Basic version check
            log.error('Detected running Syncthing version < v0.11')
            log.error('Syncthing v0.11 (or higher) required. Exiting.')
            self.leave()

    def process_rest_stats_device(self, data):
        for item in data:
            for dev in self.devices:
                if dev['id'] == item:
                    dev['lastSeen'] = data[item]['lastSeen']

    def process_rest_system_error(self, data):
        self.errors = data['errors']
        if self.errors:
            log.info('{}'.format(data['errors']))
            self.mi_errors.show()
            self.set_state('error')
        else:
            self.mi_errors.hide()
    # end of the REST processing functions

    def update(self):
        for func in self.state:
            if self.state[func]:
                log.debug('self.update {}'.format(func))
                start = getattr(self, '%s' % func)()
        return True

    def update_last_checked(self, isotime):
        #dt = dateutil.parser.parse(isotime)
        #self.last_checked_menu.set_label('Last checked: %s' % (dt.strftime('%H:%M'),))
        pass

    def update_last_seen_id(self, lsi):
        if lsi > self.last_seen_id:
            self.last_seen_id = lsi

    def update_devices(self):
        self.state['update_devices'] = False
        if not self.devices:
            self.devices_menu.set_label('No devices')
            self.devices_menu.set_sensitive(False)
            return

        # TODO: set icon if zero devices are connected
        self.devices_menu.set_label('Devices ({}/{})'.format(
            self.count_connected(), len(self.devices) - 1))
        self.devices_menu.set_sensitive(True)

        # TODO: use a better check here, in case devices changed but count
        # stayed the same
        if len(self.devices_submenu) != len(self.devices) - 1:
            # Repopulate the devices menu
            for child in self.devices_submenu.get_children():
                self.devices_submenu.remove(child)
            for elm in sorted(self.devices, key=lambda elm: elm['name']):
                if elm['id'] == self.system_status.get('myID', None):
                    self.device_name = elm['name']
                    self.state['update_st_running'] = True
                else:
                    mi = Gtk.MenuItem(elm['name'])
                    self.devices_submenu.append(mi)
                    mi.show()

        # Set menu item labels
        for mi in self.devices_submenu:
            for dev in self.devices:
                if mi.get_label().split()[0] == dev['name']:
                    if dev['connected']:
                        mi.set_label(dev['name'])
                    else:
                        # NOTE: This crashes when lastSeen = 0
                        if len(dev['lastSeen']) > 0:
                            mi.set_label('{} (Last seen {})'.format(
                                dev['name'],
                                self.convert_time(dev['lastSeen'])))
                        else:
                            mi.set_label(
                                '{} (Last seen Unknown)'.format(dev['name']))

                    mi.set_sensitive(dev['connected'])

    def update_files(self):
        self.current_files_menu.set_label('Downloading %s files' % (
            len(self.downloading_files)))

        if not self.downloading_files:
            self.current_files_menu.set_sensitive(False)
            # self.set_state('idle')
        else:
            # Repopulate the current files menu
            self.current_files_menu.set_sensitive(True)
            self.set_state('syncing')
            for child in self.current_files_submenu.get_children():
                self.current_files_submenu.remove(child)
            for f in self.downloading_files:
                fj = json.dumps(f)
                # mi = Gtk.MenuItem(u'\u2193 [{}] {}'.format(
                #    f['folder'],
                #    shorten_path(f['file'])))
                mi = Gtk.MenuItem('\u2193 [{}] {}{}'.format(
                    f['folder'],
                    shorten_path(f['file']),
                    self.downloading_files_extra[fj]["progress"] if fj in self.downloading_files_extra and "progress" in self.downloading_files_extra[fj] else ""))
                self.current_files_submenu.append(mi)
                mi.connect(
                    'activate',
                    self.open_file_browser,
                    os.path.split(
                        self.get_full_path(f['folder'], f['file']))[0])
                mi.show()
            self.current_files_menu.show()

        # Repopulate the recent files menu
        if not self.recent_files:
            self.recent_files_menu.set_sensitive(False)
        else:
            self.recent_files_menu.set_sensitive(True)
            for child in self.recent_files_submenu.get_children():
                self.recent_files_submenu.remove(child)
            icons = {'delete': '\u2612',    # [x]
                     'update': '\u2193',    # down arrow
                     'dir': '\U0001f4c1',   # folder
                     'file': '\U0001f4c4',  # file
                     }
            for f in self.recent_files:
                mi = Gtk.MenuItem(
                    '{icon} {time} [{folder}] {item}'.format(
                        icon=icons.get(f['action'], 'unknown'),
                        folder=f['folder'],
                        item=shorten_path(f['file']),
                        time=self.convert_time(f['time'])
                    )
                )
                self.recent_files_submenu.append(mi)
                mi.connect(
                    'activate',
                    self.open_file_browser,
                    os.path.split(
                        self.get_full_path(f['folder'], f['file']))[0])
                mi.show()
            self.recent_files_menu.show()
        self.state['update_files'] = False

    def update_folders(self):
        if self.folders:
            self.folder_menu.set_sensitive(True)
            folder_maxlength = 0
            if len(self.folders) == len(self.folder_menu_submenu):
                for mi in self.folder_menu_submenu:
                    for elm in self.folders:
                        folder_maxlength = max(
                            folder_maxlength, len(elm['id']))
                        if folder_maxlength < max(folder_maxlength, len(elm['label'])):
                            folder_maxlength = max(
                                folder_maxlength, len(elm['label']))
                        if str(mi.get_label()).split(' ', 1)[0] == elm['id']:
                            if elm['state'] == 'scanning':
                                #mi.set_label('{} (scanning)'.format(elm['id']))
                                mi.set_label('{} (scanning)'.format(
                                    elm['id'] or elm['label']))
                            elif elm['state'] == 'syncing':
                                if elm.get('needFiles') > 1:
                                    lbltext = '{fid} (syncing {num} files, {bytes})'
                                elif elm.get('needFiles') == 1:
                                    lbltext = '{fid} (syncing {num} file, {bytes})'
                                else:
                                    lbltext = '{fid} (syncing)'
                                mi.set_label(lbltext.format(
                                    #fid=elm['id'], num=elm.get('needFiles'),
                                    fid=elm['id'] or elm['label'], num=elm.get('needFiles'),
                                    bytes=human_readable(elm.get('needBytes', 0))))
                            else:
                                #mi.set_label(elm['id'].ljust(folder_maxlength + 20))
                                mi.set_label(elm['id'] or elm['label'].ljust(
                                    folder_maxlength + 20))
            else:
                for child in self.folder_menu_submenu.get_children():
                    self.folder_menu_submenu.remove(child)
                for elm in self.folders:
                    folder_maxlength = max(folder_maxlength, len(elm['id']))
                    if folder_maxlength < max(folder_maxlength, len(elm['label'])):
                        folder_maxlength = max(
                            folder_maxlength, len(elm['label']))
                    #mi = Gtk.MenuItem(elm['id'].ljust(folder_maxlength + 20))
                    mi = Gtk.MenuItem(
                        (elm['label'] or elm['id']).ljust(folder_maxlength + 20))
                    mi.connect('activate', self.open_file_browser, elm['path'])
                    self.folder_menu_submenu.append(mi)
                    mi.show()
        else:
            self.folder_menu.set_sensitive(False)
        self.state['update_folders'] = False

    def update_st_running(self):
        if self.current_action[0]:
            pass
        elif self.count_connection_error <= 1:
            if self.syncthing_version and self.device_name:
                self.title_menu.set_label('Syncthing {0}  \u2022  {1}'.format(
                    self.syncthing_version, self.device_name))
            else:
                self.title_menu.set_label('Syncthing')
            self.mi_start_syncthing.set_sensitive(False)
            self.mi_restart_syncthing.set_sensitive(True)
            self.mi_shutdown_syncthing.set_sensitive(True)
        else:
            self.title_menu.set_label('Syncthing is not running')
            for dev in self.devices:
                dev['connected'] = False
            self.state['update_devices'] = True
            for f in self.folders:
                f['state'] = 'unknown'
            self.state['update_folders'] = True
            self.errors = []
            self.mi_errors.hide()
            self.set_state()
            self.mi_start_syncthing.set_sensitive(True)
            self.mi_restart_syncthing.set_sensitive(False)
            self.mi_shutdown_syncthing.set_sensitive(False)

    def count_connected(self):
        # Prevent counting local running syncthing instance
        l = len([e for e in self.devices if e['connected']]) - 1
        if l >= 0:
            return l
        else:
            return 0

    def syncthing_start(self, *args):
        self.mi_start_syncthing.set_sensitive(False)
        self.mi_restart_syncthing.set_sensitive(False)
        self.mi_shutdown_syncthing.set_sensitive(False)
        self.current_action = ('syncthing_start', time.time())
        self.title_menu.set_label('Starting Syncthing...')
        self.syncthing_version = None

        #cmd = [os.path.join(self.wd, 'start-syncthing.sh')]
        #cmd = "syncthing -no-browser -no-restart -logflags=0"
        #log.info('Starting {}'.format(cmd))
        try:
            #proc = subprocess.Popen(cmd)
            log.info('Starting syncthing')
            proc = subprocess.Popen(
                "syncthing", "-no-browser", "-no-restart", "-logflags=0")
        except Exception as e:
            #log.error("Couldn't run {}: {}".format(cmd, e))
            log.error("Couldn't run syncthing: {}".format(e))
            return
        self.state['update_st_running'] = True

    def syncthing_restart(self, *args):
        self.mi_start_syncthing.set_sensitive(False)
        self.mi_restart_syncthing.set_sensitive(False)
        self.mi_shutdown_syncthing.set_sensitive(False)
        self.current_action = ('syncthing_restart', time.time())
        self.title_menu.set_label('Restarting Syncthing...')
        self.syncthing_version = None

        self.rest_post('/rest/system/restart')
        self.set_state('paused')
        self.state['update_st_running'] = True

    def syncthing_shutdown(self, *args):
        self.mi_start_syncthing.set_sensitive(False)
        self.mi_restart_syncthing.set_sensitive(False)
        self.mi_shutdown_syncthing.set_sensitive(False)
        self.current_action = ('syncthing_shutdown', time.time())
        self.title_menu.set_label('Shutting down Syncthing...')
        self.syncthing_version = None

        self.rest_post('/rest/system/shutdown')
        self.set_state('paused')
        self.state['update_st_running'] = True

    def convert_time(self, _time):
        return dateutil.parser.parse(_time).strftime(self.args.timeformat)

    def calc_speed(self, old, new):
        return old / (new * 10)

    def license(self):
        with open(os.path.join(self.wd, 'LICENSE'), 'r') as f:
            lic = f.read()
        return lic

    def show_about(self, widget):
        dialog = Gtk.AboutDialog()
        dialog.set_default_icon_from_file(
            os.path.join(self.icon_path, 'icon.png'))
        dialog.set_logo(None)
        dialog.set_program_name('Syncthing Ubuntu Indicator')
        dialog.set_version(VERSION)
        dialog.set_website(
            'https://github.com/icaruseffect/syncthing-ubuntu-indicator')
        dialog.set_comments('This menu applet for systems supporting AppIndicator'
                            '\ncan show the status of a Syncthing instance')
        dialog.set_license(self.license())
        dialog.run()
        dialog.destroy()

    def set_state(self, s=None):
        if not s:
            s = self.state['set_icon']

        if (s == 'error') or self.errors:
            self.state['set_icon'] = 'error'
        elif self.count_connection_error > 1:
            self.state['set_icon'] = 'paused'
        else:
            self.state['set_icon'] = self.folder_check_state()

    def folder_check_state(self):
        state = {'syncing': 0, 'idle': 0, 'cleaning': 0, 'scanning': 0,
                 'unknown': 0}
        for elem in self.folders:
            if elem['state'] in state:
                state[elem['state']] += 1

        if state['syncing'] > 0:
            return 'syncing'
        elif state['cleaning'] > 0:
            return 'scanning'
        else:
            return 'idle'

    def set_icon(self):
        icon = {
            'updating': {'name': 'syncthing-client-updating', 'descr': 'Updating'},
            'idle': {'name': 'syncthing-client-idle', 'descr': 'Nothing to do'},
            'syncing': {'name': 'syncthing-client-updown', 'descr': 'Transferring Data'},
            'error': {'name': 'syncthing-client-error', 'descr': 'Scotty, We Have A Problem!'},
            'paused': {'name': 'syncthing-client-paused', 'descr': 'Paused'},
            'scanning': {'name': 'syncthing-client-scanning', 'descr': 'Scanning Directories'},
            'cleaning': {'name': 'syncthing-client-scanning', 'descr': 'Cleaning Directories'},
        }

        if not self.args.text_only:
            self.ind.set_attention_icon(icon[self.state['set_icon']]['name'])
            self.ind.set_icon_full(icon[self.state['set_icon']]['name'],
                                   icon[self.state['set_icon']]['descr'])

    def leave(self, *args):
        Gtk.main_quit()

    def timeout_rest(self):
        self.timeout_counter = (self.timeout_counter + 1) % 10
        if self.count_connection_error <= 1:
            GLib.idle_add(self.rest_get, '/rest/system/connections')
            GLib.idle_add(self.rest_get, '/rest/system/status')
            GLib.idle_add(self.rest_get, '/rest/system/error')
            GLib.idle_add(self.rest_get, '/rest/stats/device')
            if self.timeout_counter == 0 or not self.syncthing_version:
                GLib.idle_add(self.rest_get, '/rest/system/upgrade')
                GLib.idle_add(self.rest_get, '/rest/system/version')
        else:
            GLib.idle_add(self.rest_get, '/rest/system/status')
        if self.current_action in ['syncthing_start', 'syncthing_restart']:
            GLib.idle_add(self.rest_get, '/rest/system/upgrade')
            GLib.idle_add(self.rest_get, '/rest/system/version')
        return True

    def timeout_events(self):
        if self.count_connection_error == 0:
            GLib.idle_add(self.rest_get, '/rest/events')
        return True

    def open_file_browser(self, menuitem, path):
        if not os.path.isdir(path):
            log.debug('Not a directory, or does not exist: {}'.format(path))
            return
        try:
            proc = subprocess.Popen(['xdg-open', path])
        except Exception as e:
            log.error("Couldn't open file browser for {} ({})".format(path, e))

    def get_full_path(self, folder, item):
        for elem in self.folders:
            a = ''
            if elem['id'] == folder:
                a = elem['path']
        return os.path.join(a, item)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    parser = argparse.ArgumentParser()
    parser.add_argument('--loglevel',
                        choices=['debug', 'info', 'warning', 'error'], default='info',
                        help='Filter logging by level. Default: %(default)s')
    parser.add_argument('--log-events', action='store_true',
                        help='Log every event')
    parser.add_argument('--timeout-event', type=int, default=10, metavar='N',
                        help='Interval for polling event interface, in seconds. Default: %(default)s')
    parser.add_argument('--timeout-rest', type=int, default=30, metavar='N',
                        help='Interval for polling REST interface, in seconds. Default: %(default)s')
    parser.add_argument('--timeout-gui', type=int, default=5, metavar='N',
                        help='Interval for refreshing GUI, in seconds. Default: %(default)s')
    parser.add_argument('--no-shutdown', action='store_true',
                        help='Hide Start, Restart, and Shutdown Syncthing menus')
    parser.add_argument('--timeformat', type=str, default='%x %X',
                        metavar='FORMAT',
                        help='Format to display date and time. See `man strftime` for help. '
                        "Default: '%(default)s'")
    parser.add_argument('--text-only', action='store_true',
                        help='Text only, no icon')
    parser.add_argument('--nb-recent-files', type=int, default=20, metavar='N',
                        help='Number of recent files entries to keep. Default: %(default)s')

    args, unknown = parser.parse_known_args()
    for arg in [args.timeout_event, args.timeout_rest, args.timeout_gui]:
        if arg < 1:
            sys.exit('Timeouts must be integers greater than 0')

    loglevels = {'debug': log.DEBUG, 'info': log.INFO,
                 'warning': log.WARNING, 'error': log.ERROR}
    log.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                    level=loglevels[args.loglevel])
    requests_log = log.getLogger('urllib3.connectionpool')
    requests_log.setLevel(log.WARNING)
    requests_log.propagate = True

    app = Main(args)
    Gtk.main()
