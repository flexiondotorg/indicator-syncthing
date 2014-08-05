from gi.repository import Gtk, Gio, GLib
from gi.repository import AppIndicator3 as appindicator
from xml.dom import minidom
import json, os, webbrowser, datetime, urlparse
import pytz
import dateutil.parser

class Main(object):
    def __init__(self):
        icon_path = os.path.normpath(os.path.abspath(os.path.split(__file__)[0]))
        icon_path = os.path.join(icon_path, "icons")
        self.ind = appindicator.Indicator.new_with_path (
                            "syncthing-indicator",
                            "syncthing-client-idle",
                            appindicator.IndicatorCategory.APPLICATION_STATUS,
                            icon_path)
        self.ind.set_attention_icon ("syncthing-client-updating")
        self.ind.set_status (appindicator.IndicatorStatus.ACTIVE)
        
        self.connected_nodes = []
        self.downloading_files = []
        self.uploading_files = []
        self.recent_files = []
        self.node_dict = {}

        self.menu = Gtk.Menu()
        
        self.last_checked_menu = Gtk.MenuItem("Last checked: ?")
        self.last_checked_menu.show()
        self.last_checked_menu.set_sensitive(False)
        self.menu.append(self.last_checked_menu)
        self.update_last_checked(datetime.datetime.now(pytz.utc).isoformat())

        self.connected_nodes_menu = Gtk.MenuItem("Connected to: ?")
        self.connected_nodes_menu.show()
        self.connected_nodes_menu.set_sensitive(False)
        self.menu.append(self.connected_nodes_menu)
        self.update_connected_nodes()
        self.connected_nodes_submenu = Gtk.Menu()
        self.connected_nodes_menu.set_submenu(self.connected_nodes_submenu)

        self.current_files_menu = Gtk.MenuItem("Current files")
        self.current_files_menu.show()
        self.menu.append(self.current_files_menu)
        self.current_files_submenu = Gtk.Menu()
        self.current_files_menu.set_submenu(self.current_files_submenu)


        self.recent_files_menu = Gtk.MenuItem("Recently synced")
        self.menu.append(self.recent_files_menu)
        self.recent_files_submenu = Gtk.Menu()
        self.recent_files_menu.set_submenu(self.recent_files_submenu)
        self.update_current_files()

        open_web_ui = Gtk.MenuItem("Open web interface")
        open_web_ui.connect("activate", self.open_web_ui)
        open_web_ui.show()
        self.menu.append(open_web_ui)
        self.ind.set_menu(self.menu)

        self.syncthing_update_menu = Gtk.MenuItem("Update check")
        self.syncthing_update_menu.connect("activate", self.open_releases_page)
        self.menu.append(self.syncthing_update_menu)

        self.syncthing_base = "http://localhost:8080"
        GLib.idle_add(self.start_load_config)
        GLib.idle_add(self.check_for_syncthing_update)
        self.last_seen_id= int(0)

    def start_load_config(self):
        confdir = GLib.get_user_config_dir()
        if not confdir: confdir = os.path.expanduser("~/.config")
        conffile = os.path.join(confdir, "syncthing", "config.xml")
        if not os.path.isfile(conffile):
            print "Couldn't find config file."
        f = Gio.file_new_for_path(conffile)
        f.load_contents_async(None, self.finish_load_config)
    
    def finish_load_config(self, fp, async_result):
        try:
            success, data, etag = fp.load_contents_finish(async_result)
        except:
            return self.bail_releases("Couldn't open config file")
        try:
            dom = minidom.parseString(data)
        except:
            return self.bail_releases("Couldn't parse config file")
        conf = dom.getElementsByTagName("configuration")
        if not conf: return self.bail_releases("No configuration element in config")
        gui = conf[0].getElementsByTagName("gui")
        if not gui: return self.bail_releases("No gui element in config")
        address = gui[0].getElementsByTagName("address")
        if not address: return self.bail_releases("No address element in config")
        if not address[0].hasChildNodes():
            return self.bail_releases("No address specified in config")
        self.syncthing_base = "http://%s" % address[0].firstChild.nodeValue
        
        #read node names from config 
        nodeids = conf[0].getElementsByTagName("node")
        try:
            for elem in nodeids:
                if elem.hasAttribute("name"):
                    node_id = elem.getAttribute("id")
                    node_name = elem.getAttribute("name")
                    self.node_dict[node_id] = node_name
        except:
            "config has no nodes configured"

        GLib.idle_add(self.start_poll)
        GLib.idle_add(self.check_for_syncthing_update)
        
    def syncthing(self, url):
        return urlparse.urljoin(self.syncthing_base, url)

    def open_web_ui(self, *args):
        webbrowser.open(self.syncthing(""))

    def open_releases_page(self, *args):
        webbrowser.open('https://github.com/syncthing/syncthing/releases')

    def check_for_syncthing_update(self):
        f = Gio.file_new_for_uri("https://github.com/syncthing/syncthing/releases.atom")
        f.load_contents_async(None, self.fetch_releases)

    def bail_releases(self, message):
        print message
        GLib.timeout_add_seconds(600, self.check_for_syncthing_update)

    def fetch_releases(self, fp, async_result):
        try:
            success, data, etag = fp.load_contents_finish(async_result)
        except:
            return self.bail_releases("Request for github releases list failed: error")
        try:
            dom = minidom.parseString(data)
        except:
            return self.bail_releases("Couldn't parse github release xml")
        entries = dom.getElementsByTagName("entry")
        if not entries:
            return self.bail_releases("Github release list had no entries")
        title = entries[0].getElementsByTagName("title")
        if not title:
            return self.bail_releases("Github release list first entry had no title")
        title = title[0]
        if not title.hasChildNodes():
            return self.bail_releases("Github release list first entry had empty title")
        title = title.firstChild.nodeValue
        f = Gio.file_new_for_uri(self.syncthing("/rest/version"))
        f.load_contents_async(None, self.fetch_local_version, title)

    def fetch_local_version(self, fp, async_result, most_recent_release):
        try:
            success, local_version, etag = fp.load_contents_finish(async_result)
        except:
            return self.bail_releases("Request for local version failed")
        if most_recent_release != local_version:
            self.syncthing_update_menu.set_label("New version %s available!" % 
                (most_recent_release,))
            self.syncthing_update_menu.show()
        else:
            self.syncthing_update_menu.hide()
        GLib.timeout_add_seconds(28800, self.check_for_syncthing_update)


    def start_poll(self):
        #connection command for testserver
        #f = Gio.file_new_for_uri("http://localhost:5115")
        #connection command for a "real" server
        f = Gio.file_new_for_uri(self.syncthing("/rest/events?since=%s") % self.last_seen_id)
        f.load_contents_async(None, self.fetch_poll)

    def fetch_poll(self, fp, async_result):
        try:
            success, data, etag = fp.load_contents_finish(async_result)
        except:
            print "request failed: error"
            GLib.timeout_add_seconds(10, self.start_poll)
            self.ind.set_icon_full("syncthing-client-error", "Couldn't connect to syncthing")
            return
        if success:
            try:
                queue = json.loads(data)
                for qitem in queue:
                    self.process_event(qitem)
            except ValueError:
                print "request failed to parse json: error"
                GLib.timeout_add_seconds(10, self.start_poll)
                self.ind.set_icon_full("syncthing-client-error", "Couldn't connect to syncthing")
 
        else:
            print "request failed"

        if self.downloading_files or self.uploading_files:
            self.ind.set_icon_full("syncthing-client-updating", 
                "Updating %s files" % (
                    len(self.downloading_files) + len(self.uploading_files)))
        else:
            self.ind.set_icon_full("syncthing-client-idle", "Up to date")
        GLib.idle_add(self.start_poll)

    def process_event(self, event):
        t = event.get("type", "unknown_event").lower()
        fn = getattr(self, "event_%s" % t, self.event_unknown_event)(event)
        self.update_last_checked(event["time"])
        self.update_last_seen_id( event["id"] )


    def event_unknown_event(self, event):
        print "got unknown event", event 

    def event_statechanged(self,event):
        if event["data"]["to"] == "syncing" :
            self.ind.set_attention_icon ("syncthing-client-updating")
        else:
            self.ind.set_icon_full("syncthing-client-idle", "Up to date")
        
    def event_remoteindexupdated(self,event):
        pass

    
    def event_starting(self,event):
        time = self.convert_time( event["time"] )
        print "Syncthing is starting at " +   time
        pass

    def event_startupcomplete(self,event):
        time = self.convert_time( event["time"] )
        print "startup done at " + time
        pass
    
    
    def event_ping(self,event):
        print "a ping was send at %s" %self.convert_time( event["time"] )
        pass

    def event_nodediscovered(self,event):
        pass

    def event_nodeconnected(self, event):
        self.connected_nodes.append(event["data"]["id"])
        self.update_connected_nodes()

    def event_nodedisconnected(self, event):
        try:
           self.connected_nodes.remove(self.translate_node_id( event["data"]["id"] ))
        except ValueError:
            print "A node %s disconnected but we didn't know about it" % event["data"]["id"]
        self.update_connected_nodes()

    def event_itemstarted(self, event):
        print "item started", event
        file_details = {"repo": event["params"].get("repo"), "file": event["params"].get("item")}
        self.downloading_files.append(file_details)
        self.update_current_files()

    def event_localindexupdated(self, event):
        file_details = {"repo": event["data"]["repo"], "file": event["data"]["name"]}
        try:
            self.downloading_files.remove(file_details)
        except ValueError:
            print "Completed a file %s which we didn't know about" % (event["data"]["name"],)
        
        self.recent_files.append({"file": event["data"]["name"], 
            "direction": "down", "time":  event["data"]["modified"] })  
        self.recent_files = self.recent_files[-5:] 
        self.update_current_files()
    
    def event_pull_error(self, event):
        print "Pull error"

    def update_last_checked(self, isotime):
        dt = dateutil.parser.parse(isotime)
        self.last_checked_menu.set_label("Last checked: %s" % (dt.strftime("%H:%M"),))
    
    def update_last_seen_id(self, lsi):
        if lsi > self.last_seen_id:
            self.last_seen_id= lsi
            
    def translate_node_id(self, reqid):
        if self.node_dict.has_key(reqid) == False:
            return "Unknown Node: " + str(reqid)
        else:
            return self.node_dict[reqid]

    def update_connected_nodes(self):
        self.connected_nodes_menu.set_label("Connected machines: %s" % (
            len(self.connected_nodes),))
        if (len(self.connected_nodes))== 0 :
            self.connected_nodes_menu.set_sensitive(False)			
        else:
            # repopulate the connected nodes menu
            self.connected_nodes_menu.set_sensitive(True)
            for child in self.connected_nodes_submenu.get_children():
                self.connected_nodes_submenu.remove(child)
            for nid in self.connected_nodes:
                mi = Gtk.MenuItem(self.translate_node_id(nid))	#add node name
                self.connected_nodes_submenu.append(mi)
                mi.show()

    def convert_time(self, time):
        time=time[:time.index('.')]
        time = datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S")
        time = time.strftime("%d.%m. %H:%M")
        return time
        
    def update_current_files(self):
        self.current_files_menu.set_label(u"Syncing \u21d1 %s  \u21d3 %s" % (
            len(self.uploading_files), len(self.downloading_files)))
        if (len(self.uploading_files), len(self.downloading_files)) == (0,0):
            self.current_files_menu.hide()
        else:
            # repopulate the current files menu
            for child in self.current_files_submenu.get_children():
                self.current_files_submenu.remove(child)
            for f in self.uploading_files:
                mi = Gtk.MenuItem(u"\u21d1 %s" % f["file"])
                self.current_files_submenu.append(mi)
                mi.show()
            for f in self.downloading_files:
                mi = Gtk.MenuItem(u"\u21d3 %s" % f["file"])
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
                updown = u"\u21d3" u"\u21d1"
                mi = Gtk.MenuItem(u"%s %s (%s)" % (
                    updown, f["file"],  f["time"] ))
                self.recent_files_submenu.append(mi)
                mi.show()
            self.recent_files_menu.show()

if __name__ == "__main__":
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = Main()
    Gtk.main()

