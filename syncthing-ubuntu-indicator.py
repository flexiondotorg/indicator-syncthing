#!/usr/bin/env python2
# -*- coding: utf-8 -*-s
#Syncthing Ubuntu Indicator v0
LICENSE = """Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   1. Definitions.

      "License" shall mean the terms and conditions for use, reproduction,
      and distribution as defined by Sections 1 through 9 of this document.

      "Licensor" shall mean the copyright owner or entity authorized by
      the copyright owner that is granting the License.

      "Legal Entity" shall mean the union of the acting entity and all
      other entities that control, are controlled by, or are under common
      control with that entity. For the purposes of this definition,
      "control" means (i) the power, direct or indirect, to cause the
      direction or management of such entity, whether by contract or
      otherwise, or (ii) ownership of fifty percent (50%) or more of the
      outstanding shares, or (iii) beneficial ownership of such entity.

      "You" (or "Your") shall mean an individual or Legal Entity
      exercising permissions granted by this License.

      "Source" form shall mean the preferred form for making modifications,
      including but not limited to software source code, documentation
      source, and configuration files.

      "Object" form shall mean any form resulting from mechanical
      transformation or translation of a Source form, including but
      not limited to compiled object code, generated documentation,
      and conversions to other media types.

      "Work" shall mean the work of authorship, whether in Source or
      Object form, made available under the License, as indicated by a
      copyright notice that is included in or attached to the work
      (an example is provided in the Appendix below).

      "Derivative Works" shall mean any work, whether in Source or Object
      form, that is based on (or derived from) the Work and for which the
      editorial revisions, annotations, elaborations, or other modifications
      represent, as a whole, an original work of authorship. For the purposes
      of this License, Derivative Works shall not include works that remain
      separable from, or merely link (or bind by name) to the interfaces of,
      the Work and Derivative Works thereof.

      "Contribution" shall mean any work of authorship, including
      the original version of the Work and any modifications or additions
      to that Work or Derivative Works thereof, that is intentionally
      submitted to Licensor for inclusion in the Work by the copyright owner
      or by an individual or Legal Entity authorized to submit on behalf of
      the copyright owner. For the purposes of this definition, "submitted"
      means any form of electronic, verbal, or written communication sent
      to the Licensor or its representatives, including but not limited to
      communication on electronic mailing lists, source code control systems,
      and issue tracking systems that are managed by, or on behalf of, the
      Licensor for the purpose of discussing and improving the Work, but
      excluding communication that is conspicuously marked or otherwise
      designated in writing by the copyright owner as "Not a Contribution."

      "Contributor" shall mean Licensor and any individual or Legal Entity
      on behalf of whom a Contribution has been received by Licensor and
      subsequently incorporated within the Work.

   2. Grant of Copyright License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      copyright license to reproduce, prepare Derivative Works of,
      publicly display, publicly perform, sublicense, and distribute the
      Work and such Derivative Works in Source or Object form.

   3. Grant of Patent License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      (except as stated in this section) patent license to make, have made,
      use, offer to sell, sell, import, and otherwise transfer the Work,
      where such license applies only to those patent claims licensable
      by such Contributor that are necessarily infringed by their
      Contribution(s) alone or by combination of their Contribution(s)
      with the Work to which such Contribution(s) was submitted. If You
      institute patent litigation against any entity (including a
      cross-claim or counterclaim in a lawsuit) alleging that the Work
      or a Contribution incorporated within the Work constitutes direct
      or contributory patent infringement, then any patent licenses
      granted to You under this License for that Work shall terminate
      as of the date such litigation is filed.

   4. Redistribution. You may reproduce and distribute copies of the
      Work or Derivative Works thereof in any medium, with or without
      modifications, and in Source or Object form, provided that You
      meet the following conditions:

      (a) You must give any other recipients of the Work or
          Derivative Works a copy of this License; and

      (b) You must cause any modified files to carry prominent notices
          stating that You changed the files; and

      (c) You must retain, in the Source form of any Derivative Works
          that You distribute, all copyright, patent, trademark, and
          attribution notices from the Source form of the Work,
          excluding those notices that do not pertain to any part of
          the Derivative Works; and

      (d) If the Work includes a "NOTICE" text file as part of its
          distribution, then any Derivative Works that You distribute must
          include a readable copy of the attribution notices contained
          within such NOTICE file, excluding those notices that do not
          pertain to any part of the Derivative Works, in at least one
          of the following places: within a NOTICE text file distributed
          as part of the Derivative Works; within the Source form or
          documentation, if provided along with the Derivative Works; or,
          within a display generated by the Derivative Works, if and
          wherever such third-party notices normally appear. The contents
          of the NOTICE file are for informational purposes only and
          do not modify the License. You may add Your own attribution
          notices within Derivative Works that You distribute, alongside
          or as an addendum to the NOTICE text from the Work, provided
          that such additional attribution notices cannot be construed
          as modifying the License.

      You may add Your own copyright statement to Your modifications and
      may provide additional or different license terms and conditions
      for use, reproduction, or distribution of Your modifications, or
      for any such Derivative Works as a whole, provided Your use,
      reproduction, and distribution of the Work otherwise complies with
      the conditions stated in this License.

   5. Submission of Contributions. Unless You explicitly state otherwise,
      any Contribution intentionally submitted for inclusion in the Work
      by You to the Licensor shall be under the terms and conditions of
      this License, without any additional terms or conditions.
      Notwithstanding the above, nothing herein shall supersede or modify
      the terms of any separate license agreement you may have executed
      with Licensor regarding such Contributions.

   6. Trademarks. This License does not grant permission to use the trade
      names, trademarks, service marks, or product names of the Licensor,
      except as required for reasonable and customary use in describing the
      origin of the Work and reproducing the content of the NOTICE file.

   7. Disclaimer of Warranty. Unless required by applicable law or
      agreed to in writing, Licensor provides the Work (and each
      Contributor provides its Contributions) on an "AS IS" BASIS,
      WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
      implied, including, without limitation, any warranties or conditions
      of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A
      PARTICULAR PURPOSE. You are solely responsible for determining the
      appropriateness of using or redistributing the Work and assume any
      risks associated with Your exercise of permissions under this License.

   8. Limitation of Liability. In no event and under no legal theory,
      whether in tort (including negligence), contract, or otherwise,
      unless required by applicable law (such as deliberate and grossly
      negligent acts) or agreed to in writing, shall any Contributor be
      liable to You for damages, including any direct, indirect, special,
      incidental, or consequential damages of any character arising as a
      result of this License or out of the use or inability to use the
      Work (including but not limited to damages for loss of goodwill,
      work stoppage, computer failure or malfunction, or any and all
      other commercial damages or losses), even if such Contributor
      has been advised of the possibility of such damages.

   9. Accepting Warranty or Additional Liability. While redistributing
      the Work or Derivative Works thereof, You may choose to offer,
      and charge a fee for, acceptance of support, warranty, indemnity,
      or other liability obligations and/or rights consistent with this
      License. However, in accepting such obligations, You may act only
      on Your own behalf and on Your sole responsibility, not on behalf
      of any other Contributor, and only if You agree to indemnify,
      defend, and hold each Contributor harmless for any liability
      incurred by, or claims asserted against, such Contributor by reason
      of your accepting any such warranty or additional liability.

   END OF TERMS AND CONDITIONS

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License."""


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
        self.last_ping = None
        self.sytem_data = {}

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
        
        self.about_menu = Gtk.MenuItem("About")
        self.about_menu.connect("activate", self.show_about)
        self.about_menu.show()
        self.menu.append(self.about_menu)



    """ read needed values from config file """
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
        
        """find the local syncthing address"""
        address = gui[0].getElementsByTagName("address")
        if not address: return self.bail_releases("No address element in config")
        if not address[0].hasChildNodes():
            return self.bail_releases("No address specified in config")
        self.syncthing_base = "http://%s" % address[0].firstChild.nodeValue
        
        """find and fetch the api key"""
        api_key = gui[0].getElementsByTagName("apikey")
        if not api_key: return self.bail_releases("No api-key element in config")
        if not api_key[0].hasChildNodes():
            return self.bail_releases("No api-key specified in config, please create one via the web interface")
        self.api_key =  api_key[0].firstChild.nodeValue
        
        
        """read node names from config"""
        nodeids = conf[0].getElementsByTagName("node")
        try:
            for elem in nodeids:
                if elem.hasAttribute("name"):
                    node_id = elem.getAttribute("id")
                    node_name = elem.getAttribute("name")
                    self.node_dict[node_id] = node_name
        except:
            self.bail_releases("config has no nodes configured")
        
        """ Start fetching information from Syncthing """
        GLib.idle_add(self.start_poll)
        GLib.idle_add(self.start_rest)
        GLib.idle_add(self.check_for_syncthing_update)
     
    """ creates a url from given values and the address read from file """
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
    
    """this attaches the rest interface """
    def start_rest(self):
        def create_fetch_rest(param):
            f = Gio.file_new_for_uri(self.syncthing("/rest/" + param + "?x-api-key=" + self.api_key) )
            f.load_contents_async(None, self.fetch_rest, param)
        
        ## save the best for beer...
        #create_fetch_rest("system")
        #create_fetch_rest("connections")
        
    
    def fetch_rest(self, fp, async_result, param):
        #try:
            success, data, etag = fp.load_contents_finish(async_result)
            self.ind.set_icon_full("syncthing-client-idle", "Up to date")
            GLib.timeout_add_seconds(5, self.start_rest)
            if success:
                self.process_event( {"type":"rest_"+param, "data":data} )
            else:
                print "Scotty, we have a problem with REST"
        #except:
        #    print "Couldn't connect to syncthing (rest interface)"
        #    GLib.timeout_add_seconds(10, self.start_rest)
        #    self.ind.set_icon_full("syncthing-client-error", "Couldn't connect to syncthing (rest interface) waiting now 10 seconds")
        
    """this attaches the event interface """
    def start_poll(self):
        #this is the connection command for the included testserver
        #f = Gio.file_new_for_uri("http://localhost:5115")
        #this is the connection command for a "real" server:
        f = Gio.file_new_for_uri(self.syncthing("/rest/events?since=%s") % self.last_seen_id)
        f.load_contents_async(None, self.fetch_poll)
    

    def fetch_poll(self, fp, async_result):
        try:
            success, data, etag = fp.load_contents_finish(async_result)
            self.ind.set_icon_full("syncthing-client-idle", "Up to date")
        except:
            print "Couldn't connect to syncthing (event interface)"
            GLib.timeout_add_seconds(5, self.start_poll)
            self.ind.set_icon_full("syncthing-client-error", "Couldn't connect to syncthing (event interface)")
            ##add a check if syncthing restarted here. for now it just resets the last_seen_id
            self.last_seen_id = 0
            self.connected_nodes = []
            return
        if success:
            try:
                queue = json.loads(data)
                for qitem in queue:
                    self.process_event(qitem)
            except ValueError:
                print "request failed to parse json: error"
                GLib.timeout_add_seconds(5, self.start_poll)
                self.ind.set_icon_full("syncthing-client-error", "Couldn't connect to syncthing")
 
        else:
            if datetime.datetime.now(pytz.utc).isoformat() > self.last_ping:
                return
            else:
                print "request failed"

        if self.downloading_files or self.uploading_files:
            self.ind.set_icon_full("syncthing-client-updating", 
                "Updating %s files" % (
                    len(self.downloading_files) + len(self.uploading_files)))
        else:
            self.ind.set_icon_full("syncthing-client-idle", "Up to date")
        GLib.idle_add(self.start_poll)
    
    
    """ processing of the events coming from the event interface"""
    def process_event(self, event):
        t = event.get("type", "unknown_event").lower()
        fn = getattr(self, "event_%s" % t, self.event_unknown_event)(event)
        ####replace this ugly try by an if statement
        try:
            self.update_last_checked(event["time"])
            self.update_last_seen_id( event["id"] )
        except:
            pass


    def event_unknown_event(self, event):
        print "got unknown event", event 

    def event_statechanged(self,event):
        self.ind.set_attention_icon ("syncthing-client-updating")
        """if event["data"]["to"] == "syncing" :
            self.ind.set_attention_icon ("syncthing-client-updating")
            #self.ind.set_icon_full("syncthing-client-updating", "Updating")
        else:
            self.ind.set_icon_full("syncthing-client-idle", "Up to date")
        """
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
        self.last_ping = dateutil.parser.parse(event["time"])
        #print "a ping was send at %s" % self.last_ping.strftime("%H:%M")
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
        file_details = {"repo": event["data"].get("repo"), "file": event["data"].get("item")}
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
    
    def event_rest_connections(self, event):
        #print event["data"]
        print "got connections info"
        
    def event_rest_system(self, event):
        print "got system info"
        
    """end of the event processing dings """
    
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
                node_id = self.translate_node_id(nid)
                mi = Gtk.MenuItem(node_id)	#add node name
                self.connected_nodes_submenu.append(mi)
                mi.show()

    def convert_time(self, time):
        time = dateutil.parser.parse(time)
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
    
    def update_system_information(self):
        pass

    def show_about(self, widget):
        dialog = Gtk.AboutDialog()
        dialog.set_program_name("Syncthing Ubuntu Indicator")
        dialog.set_version("0.1")
        dialog.set_website('http://www.syncthing.net')
        dialog.set_comments("This menu applet for systems supporting AppIndicator can show the status of a syncthing instance")
        dialog.set_license(LICENSE)
        dialog.run()
        dialog.destroy()

if __name__ == "__main__":
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = Main()
    Gtk.main()

