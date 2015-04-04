#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import argparse
import datetime
import dateutil.parser
import json
import logging as log
import os
import urlparse
import webbrowser

import pytz
from requests_futures.sessions import FuturesSession
from gi.repository import Gtk, Gio, GLib
from gi.repository import AppIndicator3 as appindicator
from xml.dom import minidom

VERSION = 'v0.2.1'

TIMEOUT_EVENT = 5
TIMEOUT_REST = 30
TIMEOUT_GUI = 5

class Main(object):
    def __init__(self):
        log.info('Started main procedure')
        icon_path = os.path.normpath(os.path.abspath(os.path.split(__file__)[0]))
        icon_path = os.path.join(icon_path, 'icons')
        self.ind = appindicator.Indicator.new_with_path(
                            'syncthing-indicator',
                            'syncthing-client-idle',
                            appindicator.IndicatorCategory.APPLICATION_STATUS,
                            icon_path)
        self.ind.set_status(appindicator.IndicatorStatus.ACTIVE)
        
        self.state = {'update_folders': True, 'update_devices': True, 'update_files': True, 'set_icon': 'idle'}
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
        
        self.session = FuturesSession()

        GLib.idle_add(self.start_load_config)
        

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

        sep = Gtk.SeparatorMenuItem()
        sep.show()
        self.menu.append(sep)
        
        self.connected_devices_menu = Gtk.MenuItem('Devices')
        self.connected_devices_menu.show()
        self.connected_devices_menu.set_sensitive(False)
        self.menu.append(self.connected_devices_menu)
        self.connected_devices_submenu = Gtk.Menu()
        self.connected_devices_menu.set_submenu(self.connected_devices_submenu)
        
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
                
        restart_syncthing = Gtk.MenuItem('Restart Syncthing')
        restart_syncthing.connect('activate', self.restart)
        restart_syncthing.show()
        self.more_submenu.append(restart_syncthing)
        
        self.about_menu = Gtk.MenuItem('About Indicator')
        self.about_menu.connect('activate', self.show_about)
        self.about_menu.show()
        self.more_submenu.append(self.about_menu)
        
        self.quit_button = Gtk.MenuItem('Quit Indicator')
        self.quit_button.connect('activate', self.leave)
        self.quit_button.show()
        self.more_submenu.append(self.quit_button)

        self.ind.set_menu(self.menu)


    def start_load_config(self):
        ''' read needed values from config file '''
        log.debug('start_load_config')
        confdir = GLib.get_user_config_dir()
        if not confdir:
            confdir = os.path.expanduser('~/.config')
        conffile = os.path.join(confdir, 'syncthing', 'config.xml')
        if not os.path.isfile(conffile):
            log.error('start_load_config: Couldn\'t find config file.')
        f = Gio.file_new_for_path(conffile)
        f.load_contents_async(None, self.finish_load_config)
        return False

    
    def finish_load_config(self, fp, async_result):
        try:
            success, data, etag = fp.load_contents_finish(async_result)
        except:
            return self.bail_releases('Couldn\'t open config file')

        try:
            dom = minidom.parseString(data)
        except:
            return self.bail_releases('Couldn\'t parse config file')

        conf = dom.getElementsByTagName('configuration')
        if not conf:
            return self.bail_releases('No configuration element in config')

        gui = conf[0].getElementsByTagName('gui')
        if not gui:
            return self.bail_releases('No gui element in config')
        
        # find the local syncthing address
        address = gui[0].getElementsByTagName('address')
        if not address:
            return self.bail_releases('No address element in config')
        if not address[0].hasChildNodes():
            return self.bail_releases('No address specified in config')

        self.syncthing_base = 'http://%s' % address[0].firstChild.nodeValue
        
        # find and fetch the api key
        api_key = gui[0].getElementsByTagName('apikey')
        if not api_key:
            return self.bail_releases('No api-key element in config')
        if not api_key[0].hasChildNodes():
            return self.bail_releases('No api-key specified in config, please create one via the web interface')
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
            self.bail_releases('config has no devices configured')
                
        # read folders from config
        folders = conf[0].getElementsByTagName('folder')
        try:
            for elem in folders:
                if elem.hasAttribute('id') and elem.hasAttribute('path'):
                    self.folders.append({
                        'folder': elem.getAttribute('id'),
                        'directory':  elem.getAttribute('path'),
                        'state': 'unknown',
                        })
        except:
            self.bail_releases('config has no folders configured')
        
        # Start processes
        GLib.idle_add(self.query_rest, 'events')
        GLib.idle_add(self.query_rest, 'connections')
        GLib.idle_add(self.query_rest, 'upgrade')
        GLib.idle_add(self.query_rest, 'system')
        GLib.timeout_add_seconds(TIMEOUT_GUI, self.update)
     
     
    def syncthing(self, url):
        ''' creates a url from given values and the address read from file '''
        return urlparse.urljoin(self.syncthing_base, url)


    def open_web_ui(self, *args):
        webbrowser.open(self.syncthing(''))


    def open_releases_page(self, *args):
        webbrowser.open('https://github.com/syncthing/syncthing/releases')


    def query_rest(self, param):
        log.debug('query_rest {}'.format(param))
        # this is the connection command for the included testserver
        # f = Gio.file_new_for_uri('http://localhost:5115')
        if param == 'upgrade':
            f = self.session.get(self.syncthing('/rest/{0}?x-api-key={1}'.format(param, self.api_key)))
            f.add_done_callback(self.finish_upgrade_check)
        elif param == 'events':
            f = self.session.get(self.syncthing('/rest/events?since={}'.format(self.last_seen_id)))
            f.add_done_callback(self.fetch_poll)
        elif param == 'connections':
            f = self.session.get(self.syncthing('/rest/{0}?x-api-key={1}'.format(param, self.api_key)))
            f.add_done_callback(self.fetch_rest_connections)
        elif param == 'system':
            f = self.session.get(self.syncthing('/rest/{0}?x-api-key={1}'.format(param, self.api_key)))
            f.add_done_callback(self.fetch_rest_system)
        return False


    def bail_releases(self, message):
        log.error(message)
        GLib.timeout_add_seconds(600, self.query_rest, 'upgrade')


    def finish_upgrade_check(self, future):
        try:
            r = future.result()
        except:
            log.error('finish_upgrade_check: Request for upgrade check failed')
            self.set_state('error')
            GLib.timeout_add_seconds(15, self.query_rest, 'upgrade')
            return
            
        if r.status_code != 200:
            return self.bail_releases('Request for upgrade check failed')

        upgrade_data = r.json()
        self.syncthing_version = upgrade_data['running']
        self.update_title_menu()
        
        if upgrade_data['newer']:
            self.syncthing_upgrade_menu.set_label('New version {} available!'.format(upgrade_data['latest']))
            self.syncthing_upgrade_menu.show()
        else:
            self.syncthing_upgrade_menu.hide()
        GLib.timeout_add_seconds(28800, self.query_rest, 'upgrade')


    def fetch_rest_system(self, future):
        param = 'system'
        log.debug('fetch_rest ' + param)
        try:
            r = future.result()
        except:
            log.error('fetch_rest: Couldn\'t connect to syncthing (rest interface)')
            GLib.timeout_add_seconds(15, self.query_rest, param)
            self.set_state('error')
            return
            
        if r.status_code == 200:
            GLib.timeout_add_seconds(TIMEOUT_REST, self.query_rest, param)
            try:
                self.process_event({'type': 'rest_' + param, 'data': r.json()})
            except:
                self.set_state('error')
                log.error('fetch_rest: Scotty, we have a problem with REST: I cannot process the data')
        else:
            log.error('fetch_rest: Couldn\'t connect to syncthing (rest interface)')
            GLib.timeout_add_seconds(15, self.query_rest, param)
            self.set_state('error')
            
            
    def fetch_rest_connections(self, future):
        param = 'connections'
        log.debug('fetch_rest ' + param)
        try:
            r = future.result()
        except:
            log.error('fetch_rest_connections: Couldn\'t connect to syncthing (rest interface)')
            GLib.timeout_add_seconds(15, self.query_rest, 'connections')
            self.set_state('error')
            return
            
        if r.status_code == 200:
            GLib.timeout_add_seconds(TIMEOUT_REST, self.query_rest, param)
            try:
                self.process_event({'type': 'rest_' + param, 'data': r.json()})
            except:
                set_state('error')
                log.error('fetch_rest: Scotty, we have a problem with REST: I cannot process the data')
        else:
            log.error('fetch_rest: Couldn\'t connect to syncthing (rest interface)')
            GLib.timeout_add_seconds(15, self.query_rest, param)
            self.set_state('error')
        

    def fetch_poll(self, future):
        log.debug('fetch_poll')
        try:
            r = future.result()
        except:
            log.error('fetch_poll: Couldn\'t connect to syncthing (rest interface)')
            GLib.timeout_add_seconds(15, self.query_rest, 'events')
            self.set_state('error')
            return
            
        if r.status_code == 200:
            self.set_state('idle')
            try:
                queue = r.json()
                for qitem in queue:
                    self.process_event(qitem)
            except ValueError:
                log.warning('fetch_poll: request failed to parse json: error')
                GLib.timeout_add_seconds(10, self.query_rest, 'events')
                self.set_state('error')
        else:
            log.error('fetch_poll: Couldn\'t connect to syncthing (event interface)')
            log.exception('Logging an uncaught exception')
            GLib.timeout_add_seconds(15, self.query_rest, 'events')
            self.set_state('error')
            # add a check if syncthing restarted here. for now it just resets the last_seen_id
            self.last_seen_id = 0 #self.last_seen_id - 30
            return
 
        #else:
        #    if datetime.datetime.now(pytz.utc).isoformat() > self.last_ping:
        #        return
        #    else:
        #        log.error('fetch_poll: request failed')
        #        self.set_state('error')
                
#        ''' if self.downloading_files or self.uploading_files:
#            self.set_state('update') 
#                    #'Updating %s files' % (
#                    #len(self.downloading_files) + len(self.uploading_files)))
#        #else:
#            #self.set_state('idle')
#            '''
        GLib.timeout_add_seconds(TIMEOUT_EVENT, self.query_rest, 'events')
   
    
    # processing of the events coming from the event interface
    def process_event(self, event):
        log.debug('processing event %s' % event.get('type'))
        t = event.get('type', 'unknown_event').lower()
        fn = getattr(self, 'event_%s' % t, self.event_unknown_event)(event)
        # replace this ugly try by an if statement
        try:
            #self.update_last_checked(event['time'])
            self.update_last_seen_id(event['id'])
        except:
            pass


    def event_unknown_event(self, event):
        log.debug('got unknown event {}'.format(event['type']))


    def event_statechanged(self,event): # adapt for folders
        for elem in self.folders:
            if elem['folder'] == event['data']['folder']:
                elem['state'] = event['data']['to']
                self.state['update_folders']=True
        self.set_state()
        
        
    def event_remoteindexupdated(self,event):
        pass


    def event_starting(self,event):
        self.set_state('paused')
        log.info('Received that Syncthing was starting at %s' % event['time'])


    def event_startupcomplete(self,event):
        self.set_state('idle')
        time = self.convert_time(event['time'])
        log.debug('startup done at %s' % time)
    
    
    def event_ping(self,event):
        self.last_ping = dateutil.parser.parse(event['time'])
        log.debug('a ping was sent at %s' % self.last_ping.strftime('%H:%M'))


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
        log.debug('item started', event)
        file_details = {'folder': event['data']['folder'], 'file': event['data']['item'], 'direction': 'down'}
        self.downloading_files.append(file_details)
        for elm in self.folders:
            if elm['folder'] == event['data']['folder']:
                elm['state'] = 'syncing'
                self.set_state()
        self.state['update_files'] = True


    def event_localindexupdated(self, event):
        # move this to update_files
        file_details = {'folder': event['data']['folder'], 'file': event['data']['name'], 'direction': 'down'}
        try:
            self.downloading_files.remove(file_details)
            log.debug('file locally updated %s' % file_details['file'])
        except ValueError:
            log.debug ('Completed a file %s which we didn\'t know about' % event['data']['name'])
        
        self.recent_files.append({
            'file': event['data']['name'], 
            'direction': 'down',
            'time': event['data']['modified'],
            })  
        self.recent_files = self.recent_files[-5:] 
        self.state['update_files'] = True
    
    
    def event_rest_connections(self, event):
        for elem in event['data'].iterkeys():
            if elem != 'total':
                for nid in self.devices:
                    if nid['id'] == elem:
                        nid['state'] = 'connected'
                        self.state['update_devices'] = True
        return


    def event_rest_system(self, event):
        log.debug('event_rest_system got system info')
        self.system_data = event['data']
        
    # end of the event processing dings
    
    
    def update_last_checked(self, isotime):
        #dt = dateutil.parser.parse(isotime)
        #self.last_checked_menu.set_label('Last checked: %s' % (dt.strftime('%H:%M'),))
        pass
        
    
    def update_last_seen_id(self, lsi):
        if lsi > self.last_seen_id:
            self.last_seen_id = lsi


    def update_devices(self):
        self.connected_devices_menu.set_label('Devices (%s connected)' % self.count_connected() )
        if len(self.devices) == 0:
            self.connected_devices_menu.set_label('Devices (0 connected)')
            self.connected_devices_menu.set_sensitive(False)
        else:
            self.connected_devices_menu.set_sensitive(True)
            
            if len(self.devices) == len(self.connected_devices_submenu) + 1:
                # this updates the connected devices menu
                for mi in self.connected_devices_submenu:
                    for elm in self.devices:
                        if str(mi.get_label()).split(' ', 1)[0] == elm['name']:
                            mi.set_label('%s   [%s]' % (elm['name'], elm['state'])) 
                            if elm['state'] == ('connected'):
                                mi.set_sensitive(True)
                            else:
                                mi.set_sensitive(False)
            
            else:
                # this populates the connected devices menu with devices from config
                for child in self.connected_devices_submenu.get_children():
                    self.connected_devices_submenu.remove(child)

                for nid in self.devices:
                    if nid['id'] == self.system_data.get('myID', None):
                        self.device_name = nid['name']
                        self.update_title_menu()
                        continue
                        
                    mi = Gtk.MenuItem('%s   [%s]' % (nid['name'], nid['state'])) #add device name
                    
                    if nid['state'] == 'connected':
                        mi.set_sensitive(True)
                    else:
                        mi.set_sensitive(False)
                    self.connected_devices_submenu.append(mi)
                    mi.show()
        self.state['update_devices'] = False


    def update_title_menu(self):
        self.title_menu.set_label('Syncthing {0} - {1}'.format(self.syncthing_version, self.device_name))


    def count_connected(self):
        return len([e for e in self.devices if e['state'] == 'connected']) 
     
     
    def restart(self, *args):
        self.start_rest('restart')
        
        
    def convert_time(self, time):
        time = dateutil.parser.parse(time)
        time = time.strftime('%d.%m. %H:%M')
        return time
        
        
    def update_files(self):
        self.current_files_menu.set_label(u'Syncing \u21d1 %s  \u21d3 %s' % (
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
                mi = Gtk.MenuItem(u'\u21d1 %s' % f['file'])
                self.current_files_submenu.append(mi)
                mi.show()
            for f in self.downloading_files:
                mi = Gtk.MenuItem(u'\u21d3 %s' % f['file'])
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
                updown = u'\u21d3' u'\u21d1'
                mi = Gtk.MenuItem(u'%s %s (%s)' % (updown, f['file'], f['time']))
                self.recent_files_submenu.append(mi)
                mi.show()
            self.recent_files_menu.show()
        self.state['update_files'] = False
   
   
    def update_folders(self):
        ''' this populates the folders menu with folders from config '''
        if len(self.folders) == 0 :
            self.folder_menu.set_sensitive(False)
        else:
            self.folder_menu.set_sensitive(True)
            
            if len(self.folders) == len(self.folder_menu_submenu):
                for mi in self.folder_menu_submenu:
                    for elm in self.folders:
                        if str(mi.get_label()).split(' ', 1)[0] == elm['folder']:
                            mi.set_label('%s   [%s]' % (elm['folder'], elm['state'])) 
                            if elm['state'] == ('idle' or 'scanning' or 'syncing'):
                                mi.set_sensitive(True)
                            else:
                                mi.set_sensitive(False)
            else:
                for child in self.folder_menu_submenu.get_children():
                    self.folder_menu_submenu.remove(child)
    
                for rid in self.folders:
                    mi = Gtk.MenuItem('%s   [%s]' % (rid['folder'], rid['state'])) # add device name
                    self.folder_menu_submenu.append(mi)
                    mi.show()
        self.state['update_folders'] = False
  
  
    def update_system_information(self): # to do
        pass
    
    
    def calc_speed(self,old,new):
        return old / (new * 10)


    def license(self):
        with open('LICENSE', 'r') as f:
            license = f.read()
        return license


    def show_about(self, widget):
        dialog = Gtk.AboutDialog()
        dialog.set_logo(None)
        dialog.set_program_name('Syncthing Ubuntu Indicator')
        dialog.set_version(VERSION)
        dialog.set_website('http://www.syncthing.net')
        dialog.set_comments('This menu applet for systems supporting AppIndicator can show the status of a syncthing instance')
        dialog.set_license(self.license())
        dialog.run()
        dialog.destroy()


    def update(self):
        for func in self.state:
            if self.state[func]:
                log.debug('self.update {}'.format(func))
                start = getattr(self, '%s' % func)()
        return True


    def set_state(self, s=None):
        if not s:
            s = self.state['set_icon']

        if s == 'error':
            self.state['set_icon'] = s
        else:
            rc = self.folder_check_state()
            if rc != 'unknown':
                self.state['set_icon'] = rc
            else:
                self.state['set_icon'] = s
    
    
    def folder_check_state(self):
        state = {'syncing': 0, 'idle': 0, 'cleaning': 0, 'scanning': 0, 'unknown': 0}
        for elem in self.folders:
            state[elem['state']] += 1

        if state['syncing'] > 0:
            return 'syncing'
        else:
            if state['scanning'] or state['cleaning'] > 0:
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
        
        self.ind.set_attention_icon(icon[self.state['set_icon'] ]['name'])
        self.ind.set_icon_full(icon[self.state['set_icon']]['name'], icon[self.state['set_icon']]['descr'])
        #GLib.timeout_add_seconds(1, self.set_icon)


    def leave(self, widget):
        exit()



if __name__ == '__main__':
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--loglevel', choices=['debug', 'info', 'error'], default='info')
    args = parser.parse_args()
    if args.loglevel == 'debug':
        loglevel = log.DEBUG
    elif args.loglevel == 'info':
        loglevel = log.INFO
    elif args.loglevel == 'error':
        loglevel = log.ERROR
    
    # setup debugging:
    log.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=loglevel)
    
    app = Main()
    Gtk.main()

