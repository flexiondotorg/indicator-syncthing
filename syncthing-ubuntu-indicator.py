#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import argparse
import datetime
import dateutil.parser
import json
import logging as log
import os
import subprocess
import sys
import urlparse
import webbrowser

import pytz
import requests
from requests_futures.sessions import FuturesSession
from gi.repository import Gtk, Gio, GLib
from gi.repository import AppIndicator3 as appindicator
from xml.dom import minidom

VERSION = 'v0.3.0'

class Main(object):
    def __init__(self):
        log.info('Started main procedure')
        self.wd = os.path.normpath(os.path.abspath(os.path.split(__file__)[0]))
        self.icon_path = os.path.join(self.wd, 'icons')
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
                      'set_icon': 'idle'}
        self.set_icon()
        self.create_menu()

        self.downloading_files = []
        self.uploading_files = []
        self.recent_files = []
        self.folders = []
        self.devices = []
        self.last_ping = None
        self.system_data = {}
        self.syncthing_base = 'http://localhost:8080'
        self.syncthing_version = ''
        self.device_name = ''
        self.last_seen_id = int(0)
        self.rest_connected = False
        self.timeout_counter = 0
        self.ping_counter = 0

        self.session = FuturesSession()

        GLib.idle_add(self.load_config_begin)


    def create_menu(self):
        self.menu = Gtk.Menu()

        #self.last_checked_menu = Gtk.MenuItem('Last checked: ?')
        #self.last_checked_menu.show()
        #self.last_checked_menu.set_sensitive(False)
        #self.menu.append(self.last_checked_menu)
        #self.update_last_checked(datetime.datetime.now(pytz.utc).isoformat())

        self.title_menu = Gtk.MenuItem('Syncthing')
        self.title_menu.show()
        self.title_menu.set_sensitive(False)
        self.menu.append(self.title_menu)

        self.syncthing_upgrade_menu = Gtk.MenuItem('Update check')
        self.syncthing_upgrade_menu.connect('activate', self.open_releases_page)
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

        self.current_files_menu = Gtk.MenuItem('Current files')
        self.menu.append(self.current_files_menu)
        self.current_files_submenu = Gtk.Menu()
        self.current_files_menu.set_submenu(self.current_files_submenu)

        self.recent_files_menu = Gtk.MenuItem('Recently synced')
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
        self.mi_start_syncthing.show()
        self.more_submenu.append(self.mi_start_syncthing)

        self.mi_restart_syncthing = Gtk.MenuItem('Restart Syncthing')
        self.mi_restart_syncthing.connect('activate', self.syncthing_restart)
        self.mi_restart_syncthing.set_sensitive(False)
        self.mi_restart_syncthing.show()
        self.more_submenu.append(self.mi_restart_syncthing)

        self.mi_shutdown_syncthing = Gtk.MenuItem('Shutdown Syncthing')
        self.mi_shutdown_syncthing.connect('activate', self.syncthing_shutdown)
        self.mi_shutdown_syncthing.set_sensitive(False)
        self.mi_shutdown_syncthing.show()
        self.more_submenu.append(self.mi_shutdown_syncthing)

        sep = Gtk.SeparatorMenuItem()
        sep.show()
        self.more_submenu.append(sep)

        self.about_menu = Gtk.MenuItem('About Indicator')
        self.about_menu.connect('activate', self.show_about)
        self.about_menu.show()
        self.more_submenu.append(self.about_menu)

        self.quit_button = Gtk.MenuItem('Quit Indicator')
        self.quit_button.connect('activate', self.leave)
        self.quit_button.show()
        self.more_submenu.append(self.quit_button)

        self.ind.set_menu(self.menu)


    def load_config_begin(self):
        ''' read needed values from config file '''
        confdir = GLib.get_user_config_dir()
        if not confdir:
            confdir = os.path.expanduser('~/.config')
        conffile = os.path.join(confdir, 'syncthing', 'config.xml')
        if not os.path.isfile(conffile):
            log.error('load_config_begin: Couldn\'t find config file.')
        f = Gio.file_new_for_path(conffile)
        f.load_contents_async(None, self.load_config_finish)
        return False


    def load_config_finish(self, fp, async_result):
        try:
            success, data, etag = fp.load_contents_finish(async_result)
        except:
            log.error('Couldn\'t open config file')
            self.leave()

        try:
            dom = minidom.parseString(data)
        except:
            log.error('Couldn\'t parse config file')
            self.leave()

        conf = dom.getElementsByTagName('configuration')
        if not conf:
            log.error('No configuration element in config')
            self.leave()

        gui = conf[0].getElementsByTagName('gui')
        if not gui:
            log.error('No gui element in config')
            self.leave()

        # find the local syncthing address
        address = gui[0].getElementsByTagName('address')
        if not address:
            log.error('No address element in config')
            self.leave()
        if not address[0].hasChildNodes():
            log.error('No address specified in config')
            self.leave()

        self.syncthing_base = 'http://%s' % address[0].firstChild.nodeValue

        # find and fetch the api key
        api_key = gui[0].getElementsByTagName('apikey')
        if not api_key:
            log.error('No api-key element in config')
            self.leave()
        if not api_key[0].hasChildNodes():
            log.error('No api-key specified in config, please create one via the web interface')
            self.leave()
        self.api_key = api_key[0].firstChild.nodeValue

        # read device names from config
        deviceids = conf[0].getElementsByTagName('device')
        try:
            for elem in deviceids:
                if elem.hasAttribute('name') and elem.hasAttribute('id'):
                    self.devices.append({
                        'id': elem.getAttribute('id'),
                        'name': elem.getAttribute('name'),
                        'compression': elem.getAttribute('compression'),
                        'state': 'disconnected',
                        })
        except:
            log.error('config has no devices configured')
            self.leave()

        # read folders from config
        folders = conf[0].getElementsByTagName('folder')
        try:
            for elem in folders:
                if elem.hasAttribute('id') and elem.hasAttribute('path'):
                    self.folders.append({
                        'id': elem.getAttribute('id'),
                        'path': elem.getAttribute('path'),
                        'state': 'unknown',
                        })
        except:
            log.error('config has no folders configured')
            self.leave()

        # Start processes
        GLib.idle_add(self.rest_get, '/rest/system/ping')
        GLib.idle_add(self.rest_get, '/rest/system/version')
        GLib.idle_add(self.rest_get, '/rest/system/connections')
        GLib.idle_add(self.rest_get, '/rest/system/status')
        GLib.idle_add(self.rest_get, '/rest/system/upgrade')
        GLib.idle_add(self.rest_get, '/rest/system/error')
        GLib.idle_add(self.rest_get, '/rest/events')
        GLib.timeout_add_seconds(TIMEOUT_GUI, self.update)
        GLib.timeout_add_seconds(TIMEOUT_REST, self.timeout_rest)
        GLib.timeout_add_seconds(TIMEOUT_EVENT, self.timeout_events)


    def syncthing_url(self, url):
        ''' creates a url from given values and the address read from file '''
        return urlparse.urljoin(self.syncthing_base, url)


    def open_web_ui(self, *args):
        webbrowser.open(self.syncthing_url(''))


    def open_releases_page(self, *args):
        webbrowser.open('https://github.com/syncthing/syncthing/releases')


    def rest_post(self, rest_path):
        log.debug('rest_post {}'.format(rest_path))
        headers = {'X-API-Key': self.api_key}
        if rest_path in ['/rest/system/restart', '/rest/system/shutdown']:
            f = self.session.post(self.syncthing_url(rest_path), headers=headers)
        return False


    def rest_get(self, rest_path):
        log.debug('rest_get {}'.format(rest_path))
        # url for the included testserver: http://localhost:5115
        headers = {'X-API-Key': self.api_key}
        params = {}
        if rest_path == '/rest/events':
            params = {'since': self.last_seen_id}
        f = self.session.get(self.syncthing_url(rest_path),
                             params=params,
                             headers=headers,
                             timeout=8)
        f.add_done_callback(self.rest_receive_data)
        return False


    def rest_receive_data(self, future):
        try:
            r = future.result()
        except requests.exceptions.ConnectionError:
            log.error("Couldn't connect to Syncthing REST interface at {}".format(
                self.syncthing_url('')))
            self.rest_connected = False
            self.state['update_st_running'] = True
            if self.ping_counter > 1:
                self.set_state('error')
            return
        except requests.exceptions.Timeout:
            log.warning('Connection timeout')
            return
        except Exception as e:
            log.error('exception: {}'.format(e))
            return

        rest_path = urlparse.urlparse(r.url).path
        if r.status_code != 200:
            log.warning('rest_receive_data: {0} failed ({1})'.format(
                rest_path, r.status_code))
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

        self.set_state('idle')
        log.debug('rest_receive_data: {}'.format(rest_path))
        if rest_path == '/rest/events':
            try:
                for qitem in json_data:
                    self.process_event(qitem)
            except ValueError as e:
                log.warning('rest_receive_data: error processing event ({})'.format(e))
                log.debug(qitem)
                self.set_state('error')
        else:
            fn = getattr(
                self,
                'process_{}'.format(rest_path.strip('/').replace('/','_'))
                )(json_data)


    # processing of the events coming from the event interface
    def process_event(self, event):
        t = event.get('type').lower()
        if hasattr(self, 'event_{}'.format(t)):
            log.debug('received event: {}'.format(event.get('type')))
        else:
            log.debug('ignoring unknown event: {}'.format(event.get('type')))

        #log.debug(json.dumps(event, indent=4))
        fn = getattr(self, 'event_{}'.format(t), self.event_unknown_event)(event)
        self.update_last_seen_id(event.get('id', 0))


    def event_unknown_event(self, event):
        pass


    def event_statechanged(self, event):
        for elem in self.folders:
            if elem['id'] == event['data']['folder']:
                elem['state'] = event['data']['to']
                self.state['update_folders'] = True
        self.set_state()


    def event_starting(self, event):
        self.set_state('paused')
        log.info('Received that Syncthing was starting at %s' % event['time'])


    def event_startupcomplete(self, event):
        self.set_state('idle')
        time = self.convert_time(event['time'])
        log.debug('Startup done at %s' % time)


    def event_ping(self, event):
        self.last_ping = dateutil.parser.parse(event['time'])
        log.debug('A ping was sent at %s' % self.last_ping.strftime('%H:%M'))


    def event_devicediscovered(self, event):
        found = False
        for elm in self.devices:
            if elm['id'] == event['data']['device']:
                elm['state'] = 'discovered'
                found = True
        if found == False:
            log.warn('unknown device discovered')
            self.devices.append({
                'id': event['data']['device'],
                'name': 'new unknown device',
                'address': event['data']['addrs'],
                'state': 'unknown',
                })
        self.state['update_devices'] = True


    def event_deviceconnected(self, event):
        for elem in self.devices:
            if event['data']['id'] == elem['id']:
                elem['state'] = 'connected'
                log.debug('device %s connected' % elem['name'])
        self.state['update_devices'] = True


    def event_devicedisconnected(self, event):
        for elem in self.devices:
            if event['data']['id'] == elem['id']:
                elem['state'] = 'disconnected'
                log.debug('device %s disconnected' % elem['name'])
        self.state['update_devices'] = True


    def event_itemstarted(self, event):
        log.debug(u'item started: {}'.format(event['data']['item']))
        file_details = {'folder': event['data']['folder'],
                        'file': event['data']['item'],
                        'direction': 'down'}
        self.downloading_files.append(file_details)
        for elm in self.folders:
            if elm['id'] == event['data']['folder']:
                elm['state'] = 'syncing'
        self.set_state()
        self.state['update_files'] = True


    def event_itemfinished(self, event):
        # TODO: test whether 'error' is null
        log.debug(u'item finished: {}'.format(event['data']['item']))
        file_details = {'folder': event['data']['folder'],
                        'file': event['data']['item'],
                        'direction': 'down'}
        try:
            self.downloading_files.remove(file_details)
            log.debug('file locally updated: %s' % file_details['file'])
        except ValueError:
            log.debug('Completed a file we didn\'t know about: {}'.format(
                event['data']['item']))
        file_details['time'] = event['time']
        file_details['action'] = event['data']['action']
        self.recent_files.append(file_details)
        self.recent_files = self.recent_files[-5:]
        self.state['update_files'] = True

    # end of the event processing dings


    # begin REST processing functions

    def process_rest_system_connections(self, data):
        for elem in data['connections'].iterkeys():
            for nid in self.devices:
                if nid['id'] == elem:
                    nid['state'] = 'connected'
                    self.state['update_devices'] = True


    def process_rest_system_status(self, data):
        self.system_data = data
        self.state['update_st_running'] = True


    def process_rest_system_upgrade(self, data):
        if data['newer']:
            self.syncthing_upgrade_menu.set_label(
                'New version available: {}'.format(data['latest']))
            self.syncthing_upgrade_menu.show()
        else:
            self.syncthing_upgrade_menu.hide()


    def process_rest_system_version(self, data):
        self.syncthing_version = data['version']
        self.state['update_st_running'] = True


    def process_rest_system_ping(self, data):
        if data['ping'] == 'pong':
            log.info('Connected to Syncthing REST interface at {}'.format(
                self.syncthing_url('')))
            self.rest_connected = True
            self.ping_counter = 0


    def process_rest_ping(self, data):
        if data['ping'] == 'pong':
            # Basic version check
            log.error('Detected running Syncthing version < v0.11')
            log.error('Syncthing v0.11.0-beta (or higher) required. Exiting.')
            self.leave()


    def process_rest_system_error(self, data):
        if data['errors'] != []:
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
        elif lsi < self.last_seen_id:
            log.warning('received event id {} less than last_seen_id {}'.format(
                lsi, self.last_seen_id))


    def update_devices(self):
        self.devices_menu.set_label('Devices (%s connected)' % self.count_connected())
        if len(self.devices) == 0:
            self.devices_menu.set_label('Devices (0 connected)')
            self.devices_menu.set_sensitive(False)
        else:
            self.devices_menu.set_sensitive(True)

            if len(self.devices) == len(self.devices_submenu) + 1:
                # this updates the devices menu
                for mi in self.devices_submenu:
                    for elm in self.devices:
                        if mi.get_label() == elm['name']:
                            mi.set_label(elm['name'])
                            mi.set_sensitive(elm['state'] == 'connected')

            else:
                # this populates the devices menu with devices from config
                for child in self.devices_submenu.get_children():
                    self.devices_submenu.remove(child)

                for nid in sorted(self.devices, key=lambda nid: nid['name']):
                    if nid['id'] == self.system_data.get('myID', None):
                        self.device_name = nid['name']
                        self.state['update_st_running'] = True
                        continue

                    mi = Gtk.MenuItem(nid['name'])
                    mi.set_sensitive(nid['state'] == 'connected')
                    self.devices_submenu.append(mi)
                    mi.show()
        self.state['update_devices'] = False


    def update_files(self):
        self.current_files_menu.set_label(u'Syncing \u2191 %s  \u2193 %s' % (
            len(self.uploading_files), len(self.downloading_files)))

        if (len(self.uploading_files), len(self.downloading_files)) == (0,0):
            self.current_files_menu.hide()
            #self.set_state('idle')
        else:
            # repopulate the current files menu
            self.set_state('syncing')
            for child in self.current_files_submenu.get_children():
                self.current_files_submenu.remove(child)
            for f in self.uploading_files:
                mi = Gtk.MenuItem(u'\u2191 [{}] {}'.format(f['folder'], f['file']))
                self.current_files_submenu.append(mi)
                mi.show()
            for f in self.downloading_files:
                mi = Gtk.MenuItem(u'\u2193 [{}] {}'.format(f['folder'], f['file']))
                self.current_files_submenu.append(mi)
                mi.show()
            self.current_files_menu.show()

        # repopulate the recent files menu
        if not self.recent_files:
            self.recent_files_menu.hide()
        else:
            for child in self.recent_files_submenu.get_children():
                self.recent_files_submenu.remove(child)
            for f in self.recent_files:
                updown = u'\u2193' u'\u2191'
                if f['action'] == 'delete':
                    action = '(Del)'
                else:
                    action = updown
                mi = Gtk.MenuItem(
                    u'{time} [{folder}] {action} {item}'.format(
                        action=action,
                        folder=f['folder'],
                        item=f['file'],
                        time=self.convert_time(f['time'])
                        )
                    )
                self.recent_files_submenu.append(mi)
                mi.show()
            self.recent_files_menu.show()
        self.state['update_files'] = False


    def update_folders(self):
        if len(self.folders) == 0:
            self.folder_menu.set_sensitive(False)
        else:
            self.folder_menu.set_sensitive(True)
            folder_maxlength = 0
            if len(self.folders) == len(self.folder_menu_submenu):
                for mi in self.folder_menu_submenu:
                    for elm in self.folders:
                        folder_maxlength = max(folder_maxlength, len(elm['id']))
                        if str(mi.get_label()).split(' ', 1)[0] == elm['id']:
                            if elm['state'] in ['scanning', 'syncing']:
                                mi.set_label('{0}   ({1})'.format(elm['id'], elm['state']))
                            else:
                                mi.set_label(elm['id'].ljust(folder_maxlength + 20))
            else:
                for child in self.folder_menu_submenu.get_children():
                    self.folder_menu_submenu.remove(child)
                for elm in self.folders:
                    folder_maxlength = max(folder_maxlength, len(elm['id']))
                    mi = Gtk.MenuItem(elm['id'].ljust(folder_maxlength + 20))
                    self.folder_menu_submenu.append(mi)
                    mi.show()
        self.state['update_folders'] = False


    def update_st_running(self):
        if self.rest_connected:
            self.title_menu.set_label(u'Syncthing {0}  \u2022  {1}'.format(
                self.syncthing_version, self.device_name))
            self.mi_start_syncthing.set_sensitive(False)
            self.mi_restart_syncthing.set_sensitive(True)
            self.mi_shutdown_syncthing.set_sensitive(True)
        else:
            self.title_menu.set_label('Syncthing: not running?')
            self.mi_start_syncthing.set_sensitive(True)
            self.mi_restart_syncthing.set_sensitive(False)
            self.mi_shutdown_syncthing.set_sensitive(False)


    def count_connected(self):
        return len([e for e in self.devices if e['state'] == 'connected'])


    def syncthing_start(self, *args):
        cmd = os.path.join(self.wd, 'start-syncthing.sh')
        log.info('Starting {}'.format(cmd))
        try:
            proc = subprocess.Popen([cmd])
        except Exception as e:
            log.error("Couldn't run {}: {}".format(cmd, e))
            return
        self.state['update_st_running'] = True
        self.last_seen_id = int(0)


    def syncthing_restart(self, *args):
        self.rest_post('/rest/system/restart')
        self.last_seen_id = int(0)


    def syncthing_shutdown(self, *args):
        self.rest_post('/rest/system/shutdown')
        self.last_seen_id = int(0)


    def convert_time(self, time):
        return dateutil.parser.parse(time).strftime('%x %X')


    def calc_speed(self, old, new):
        return old / (new * 10)


    def license(self):
        with open(os.path.join(self.wd, 'LICENSE'), 'r') as f:
            lic = f.read()
        return lic


    def show_about(self, widget):
        dialog = Gtk.AboutDialog()
        dialog.set_default_icon_from_file(os.path.join(self.icon_path, 'syncthing-client-idle.svg'))
        dialog.set_logo(None)
        dialog.set_program_name('Syncthing Ubuntu Indicator')
        dialog.set_version(VERSION)
        dialog.set_website('http://www.syncthing.net')
        dialog.set_comments('This menu applet for systems supporting AppIndicator can show the status of a Syncthing instance')
        dialog.set_license(self.license())
        dialog.run()
        dialog.destroy()


    def set_state(self, s=None):
        if not s:
            s = self.state['set_icon']

        if s == 'error':
            self.state['set_icon'] = s
        else:
            self.state['set_icon'] = self.folder_check_state()


    def folder_check_state(self):
        state = {'syncing': 0, 'idle': 0, 'cleaning': 0, 'scanning': 0, 'unknown': 0}
        for elem in self.folders:
            state[elem['state']] += 1

        if state['syncing'] > 0:
            return 'syncing'
        elif state['scanning'] > 0 or state['cleaning'] > 0:
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

        self.ind.set_attention_icon(icon[self.state['set_icon']]['name'])
        self.ind.set_icon_full(icon[self.state['set_icon']]['name'], icon[self.state['set_icon']]['descr'])
        #GLib.timeout_add_seconds(1, self.set_icon)


    def leave(self, widget):
        Gtk.main_quit()


    def timeout_rest(self):
        self.timeout_counter = (self.timeout_counter + 1) % 10
        if self.rest_connected:
            GLib.idle_add(self.rest_get, '/rest/system/connections')
            GLib.idle_add(self.rest_get, '/rest/system/status')
            GLib.idle_add(self.rest_get, '/rest/system/error')
            if self.timeout_counter == 0:
                GLib.idle_add(self.rest_get, '/rest/system/upgrade')
                GLib.idle_add(self.rest_get, '/rest/system/version')
        else:
            self.ping_counter += 1
            log.debug('ping counter {}'.format(self.ping_counter))
            GLib.idle_add(self.rest_get, '/rest/system/ping')
        return True


    def timeout_events(self):
        if self.rest_connected:
            GLib.idle_add(self.rest_get, '/rest/events')
        return True



if __name__ == '__main__':
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    parser = argparse.ArgumentParser()
    parser.add_argument('--loglevel', choices=['debug', 'info', 'warning', 'error'], default='info')
    parser.add_argument('--timeout-event', type=int, default=5)
    parser.add_argument('--timeout-rest', type=int, default=30)
    parser.add_argument('--timeout-gui', type=int, default=5)

    args = parser.parse_args()
    for arg in [args.timeout_event, args.timeout_rest, args.timeout_gui]:
        if arg < 1:
            sys.exit('Timeouts must be integers greater than 0')
    TIMEOUT_EVENT = args.timeout_event
    TIMEOUT_REST = args.timeout_rest
    TIMEOUT_GUI = args.timeout_gui

    # setup debugging:
    loglevels = {'debug': log.DEBUG, 'info': log.INFO, 'warning': log.WARNING, 'error': log.ERROR}
    log.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=loglevels[args.loglevel])

    app = Main()
    Gtk.main()
