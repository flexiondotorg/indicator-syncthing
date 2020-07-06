#!/usr/bin/env python3
#
#  __init__.py
"""
A Syncthing status menu for Unity and other desktops that support AppIndicator.
"""
#
#  Copyright (c) 2020 Dominic Davis-Foster <dominic@davis-foster.co.uk>
#  Based on syncthing-ubuntu-indicator.
#  https://github.com/stuartlangridge/syncthing-ubuntu-indicator
#  Copyright (c) 2014 Stuart Langridge
#
#  With modifications by https://github.com/0xBADEAFFE and https://github.com/icaruseffect
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
#  or implied. See the License for the specific language governing
#  permissions and limitations under the License.
#

# stdlib
import json
import logging as log
import os
import socket  # used only to catch exceptions
import subprocess
import time
import webbrowser as wb
from urllib.parse import urljoin, urlparse
from xml.dom import minidom

# 3rd party
import gi  # type: ignore
import requests  # used only to catch exceptions
from dateutil.parser import parse
from requests_futures.sessions import FuturesSession  # type: ignore

gi.require_version("Gtk", "3.0")
gi.require_version("AppIndicator3", "0.1")

# 3rd party
from gi.repository import AppIndicator3 as appindicator  # type: ignore
from gi.repository import Gio as gio
from gi.repository import GLib as glib
from gi.repository import Gtk as gtk

__author__ = "Dominic Davis-Foster"
__copyright__ = "2020 Dominic Davis-Foster"

__license__ = "Apache Software License"
__version__ = VERSION = "0.1.0"
__email__ = "dominic@davis-foster.co.uk"

APPINDICATOR_ID = "indicator-syncthing"


def get_lock(process_name):
	# Without holding a reference to our socket somewhere it gets garbage
	# collected when the function exits
	get_lock._lock_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)

	try:
		get_lock._lock_socket.bind("\0" + process_name)
		print("Created lock for process:", process_name)
	except OSError:
		print("Lock exists. Process:", process_name, "is already running")
		exit()


def shorten_path(text, maxlength=80):
	if len(text) <= maxlength:
		return text
	head, tail = os.path.split(text)
	if len(tail) > maxlength:
		return tail[:maxlength]  # TODO: separate file extension
	while len(head) + len(tail) > maxlength:
		head = "/".join(head.split("/")[:-1])
		if head == "":
			return ".../" + tail
	return head + "/.../" + tail


def human_readable(size):
	for unit in ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB"]:
		if abs(size) < 1024.0:
			f = f"{size:.1f}".rstrip("0").rstrip(".")
			return f"{f} {unit}"
		size = size / 1024.0
	return f"{size:.1f} {'YiB'}"


class IndicatorSyncthing:

	def __init__(self, args):
		log.info("Started main procedure")
		self.args = args
		self.wd = os.path.dirname(os.path.realpath(__file__))
		self.icon_path = os.path.join(self.wd, "icons")

		if not self.args.text_only:
			self.ind = appindicator.Indicator.new_with_path(
					APPINDICATOR_ID,
					"syncthing-client-idle",
					appindicator.IndicatorCategory.APPLICATION_STATUS,
					self.icon_path,
					)
			self.ind.set_status(appindicator.IndicatorStatus.ACTIVE)

		self.state = {
				"update_folders": True,
				"update_devices": True,
				"update_files": True,
				"update_st_running": False,
				"set_icon": "paused",
				}

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
		self.syncthing_base = "http://localhost:8080"
		self.syncthing_version = ""
		self.device_name = ""
		self.last_seen_id = 0
		self.timeout_counter = 0
		self.count_connection_error = 0
		self.session = FuturesSession()
		self.current_action = (None, None)

		glib.idle_add(self.load_config_begin)

	def create_menu(self):
		self.menu = gtk.Menu()

		self.title_menu = gtk.MenuItem("Syncthing")
		self.title_menu.show()
		self.title_menu.set_sensitive(False)
		self.menu.append(self.title_menu)

		self.syncthing_upgrade_menu = gtk.MenuItem("Upgrade check")
		self.syncthing_upgrade_menu.connect("activate", self.open_releases_page)
		self.menu.append(self.syncthing_upgrade_menu)

		self.mi_errors = gtk.MenuItem("Errors: open web interface")
		self.mi_errors.connect("activate", self.open_web_ui)
		self.menu.append(self.mi_errors)

		sep = gtk.SeparatorMenuItem()
		sep.show()
		self.menu.append(sep)

		self.devices_menu = gtk.MenuItem("Devices")
		self.devices_menu.show()
		self.devices_menu.set_sensitive(False)
		self.menu.append(self.devices_menu)
		self.devices_submenu = gtk.Menu()
		self.devices_menu.set_submenu(self.devices_submenu)

		self.folder_menu = gtk.MenuItem("Folders")
		self.folder_menu.show()
		self.folder_menu.set_sensitive(False)
		self.menu.append(self.folder_menu)
		self.folder_menu_submenu = gtk.Menu()
		self.folder_menu.set_submenu(self.folder_menu_submenu)

		sep = gtk.SeparatorMenuItem()
		sep.show()
		self.menu.append(sep)

		self.current_files_menu = gtk.MenuItem("Downloading files")
		self.current_files_menu.show()
		self.current_files_menu.set_sensitive(False)
		self.menu.append(self.current_files_menu)
		self.current_files_submenu = gtk.Menu()
		self.current_files_menu.set_submenu(self.current_files_submenu)

		self.recent_files_menu = gtk.MenuItem("Recently updated")
		self.recent_files_menu.show()
		self.recent_files_menu.set_sensitive(False)
		self.menu.append(self.recent_files_menu)
		self.recent_files_submenu = gtk.Menu()
		self.recent_files_menu.set_submenu(self.recent_files_submenu)

		sep = gtk.SeparatorMenuItem()
		sep.show()
		self.menu.append(sep)

		open_web_ui = gtk.MenuItem("Open web interface")
		open_web_ui.connect("activate", self.open_web_ui)
		open_web_ui.show()
		self.menu.append(open_web_ui)

		self.more_menu = gtk.MenuItem("More")
		self.more_menu.show()
		self.menu.append(self.more_menu)

		self.more_submenu = gtk.Menu()
		self.more_menu.set_submenu(self.more_submenu)

		self.mi_start_syncthing = gtk.MenuItem("Start Syncthing")
		self.mi_start_syncthing.connect("activate", self.syncthing_start)
		self.mi_start_syncthing.set_sensitive(False)
		self.more_submenu.append(self.mi_start_syncthing)

		self.mi_restart_syncthing = gtk.MenuItem("Restart Syncthing")
		self.mi_restart_syncthing.connect("activate", self.syncthing_restart)
		self.mi_restart_syncthing.set_sensitive(False)
		self.more_submenu.append(self.mi_restart_syncthing)

		self.mi_shutdown_syncthing = gtk.MenuItem("Shutdown Syncthing")
		self.mi_shutdown_syncthing.connect("activate", self.syncthing_shutdown)
		self.mi_shutdown_syncthing.set_sensitive(False)
		self.more_submenu.append(self.mi_shutdown_syncthing)

		sep = gtk.SeparatorMenuItem()
		self.more_submenu.append(sep)

		if not self.args.no_shutdown:
			self.mi_start_syncthing.show()
			self.mi_restart_syncthing.show()
			self.mi_shutdown_syncthing.show()
			sep.show()

		self.about_menu = gtk.MenuItem("About Indicator")
		self.about_menu.connect("activate", self.show_about)
		self.about_menu.show()
		self.more_submenu.append(self.about_menu)

		self.quit_button = gtk.MenuItem("Quit Indicator")
		self.quit_button.connect("activate", self.quit)
		self.quit_button.show()
		self.more_submenu.append(self.quit_button)
		if not self.args.text_only:
			self.ind.set_menu(self.menu)

	def load_config_begin(self):
		# Read needed values from config file
		confdir = glib.get_user_config_dir()
		if not confdir:
			confdir = os.path.expanduser("~/.config")
		conffile = os.path.join(confdir, "syncthing", "config.xml")
		if not os.path.isfile(conffile):
			log.error(f"Couldn't find config file: {conffile}")
			self.quit()
		f = gio.file_new_for_path(conffile)
		f.load_contents_async(None, self.load_config_finish)
		return False

	def load_config_finish(self, fp, async_result):
		try:
			success, data, etag = fp.load_contents_finish(async_result)

			dom = minidom.parseString(data)

			conf = dom.getElementsByTagName("configuration")
			if not conf:
				raise Exception("No configuration element in config")

			gui = conf[0].getElementsByTagName("gui")
			if not gui:
				raise Exception("No gui element in config")

			# Find the local syncthing address
			address = gui[0].getElementsByTagName("address")
			if not address:
				raise Exception("No address element in config")
			if not address[0].hasChildNodes():
				raise Exception("No address specified in config")

			self.syncthing_base = f"http://{address[0].firstChild.nodeValue}"

			# Find and fetch the api key
			api_key = gui[0].getElementsByTagName("apikey")
			if not api_key:
				raise Exception("No apikey element in config")
			if not api_key[0].hasChildNodes():
				raise Exception("No apikey specified in config, please create one via the web interface")
			self.api_key = api_key[0].firstChild.nodeValue

			# Read folders and devices from config
			for elem in conf[0].childNodes:
				if elem.nodeType != minidom.Node.ELEMENT_NODE:
					continue
				if elem.tagName == "device":
					self.devices.append({
							"id": elem.getAttribute("id"),
							"name": elem.getAttribute("name"),
							"state": "",
							"connected": False,
							"lastSeen": "",
							})
				elif elem.tagName == "folder":
					self.folders.append({
							"id": elem.getAttribute("id"),
							"label": elem.getAttribute("label"),
							"path": elem.getAttribute("path"),
							"state": "unknown",
							})
			if not self.devices:
				raise Exception("No devices in config")
			if not self.folders:
				raise Exception("No folders in config")
		except Exception as e:
			log.error(f"Error parsing config file: {e}")
			self.quit()

		# Start processes
		glib.idle_add(self.rest_get, "/rest/system/version")
		glib.idle_add(self.rest_get, "/rest/system/connections")
		glib.idle_add(self.rest_get, "/rest/system/status")
		glib.idle_add(self.rest_get, "/rest/system/upgrade")
		glib.idle_add(self.rest_get, "/rest/system/error")
		glib.idle_add(self.rest_get, "/rest/events")
		glib.timeout_add_seconds(self.args.timeout_gui, self.update)
		glib.timeout_add_seconds(self.args.timeout_rest, self.timeout_rest)
		glib.timeout_add_seconds(self.args.timeout_event, self.timeout_events)

	def syncthing_url(self, url):
		# Creates a url from given values and the address read from file
		return urljoin(self.syncthing_base, url)

	def open_web_ui(self, *_):
		wb.open(self.syncthing_url(''))

	@staticmethod
	def open_releases_page(*_):
		wb.open("https://github.com/syncthing/syncthing/releases")

	def rest_post(self, rest_path):
		log.debug(f"rest_post: {rest_path}")
		headers = {"X-API-Key": self.api_key}
		if rest_path in ["/rest/system/restart", "/rest/system/shutdown"]:
			f = self.session.post(self.syncthing_url(rest_path), headers=headers)
		return False

	def rest_get(self, rest_path):
		params = ""
		if rest_path == "/rest/events":
			params = {"since": self.last_seen_id}

		log.info(f"rest_get: {rest_path} {params}")
		headers = {"X-API-Key": self.api_key}
		f = self.session.get(
				self.syncthing_url(rest_path),
				params=params,
				headers=headers,
				timeout=9,
				)

		f.add_done_callback(self.rest_receive_data)
		return False

	def rest_receive_data(self, future):
		try:
			r = future.result()
		except requests.exceptions.ConnectionError:
			log.error(f"Couldn't connect to Syncthing at: {self.syncthing_base}")
			self.count_connection_error += 1
			log.info(f"count_connection_error: {self.count_connection_error}")
			if self.current_action[0] == "syncthing_shutdown":
				self.current_action = (None, None)
			if self.count_connection_error > 1:
				self.state["update_st_running"] = True
				self.set_state("paused")
			return
		except (requests.exceptions.Timeout, socket.timeout):
			log.debug("Timeout")
			# Timeout may be because Syncthing restarted and event ID reset.
			glib.idle_add(self.rest_get, "/rest/system/status")
			return
		except Exception as e:
			log.error(f"exception: {e}")
			return

		rest_path = urlparse(r.url).path
		rest_query = urlparse(r.url).query
		if r.status_code != 200:
			log.warning(f"rest_receive_data: {rest_path} failed ({r.status_code})")
			if rest_path == "/rest/system/upgrade":
				# Debian/Ubuntu Syncthing packages disable upgrade check
				pass
			else:
				self.set_state("error")
			if rest_path == "/rest/system/ping":
				# Basic version check: try the old REST path
				glib.idle_add(self.rest_get, "/rest/ping")
			return

		try:
			json_data = r.json()
		except:
			log.warning("rest_receive_data: Cannot process REST data")
			self.set_state("error")
			return

		# Receiving data appears to have succeeded
		self.count_connection_error = 0
		if self.current_action[0]:
			self.current_action = (None, None)
			self.state["update_st_running"] = True
		self.set_state("idle")  # TODO: fix this
		log.debug(f"rest_receive_data: {rest_path} {rest_query}")
		if rest_path == "/rest/events":
			try:
				for qitem in json_data:
					self.process_event(qitem)
			except Exception as e:
				log.warning(f"rest_receive_data: error processing event ({e})")
				log.debug(f"qitem: {qitem}")
				self.set_state("error")
		else:
			fn = getattr(self, f"process_{rest_path.strip('/').replace('/', '_')}")(json_data)

	# Processing of the events coming from the event interface
	def process_event(self, event):
		if self.args.log_events:
			log.debug(f"EVENT: {event['type']}: {json.dumps(event)}")

		t = event.get("type").lower()
		# log.debug("received event: "+str(event))
		if hasattr(self, f"event_{t}"):
			log.debug(f"Received event: {event.get('id')} {event.get('type')}")
			pass
		else:
			log.debug(f"Ignoring event: {event.get('id')} {event.get('type')}")

		# log.debug(json.dumps(event, indent=4))
		fn = getattr(self, f"event_{t}", self.event_unknown_event)(event)
		self.update_last_seen_id(event.get("id", 0))

	def event_downloadprogress(self, event):
		try:
			e = list(event["data"].values())
			e = list(e[0].keys())[0]
		except (ValueError, KeyError, IndexError):
			e = ""

		log.debug(f"Download in progress: {e}")
		for folder_name in list(event["data"].keys()):
			for filename in event["data"][folder_name]:
				file_details = json.dumps({
						"folder": folder_name,
						"file": filename,
						"type": "file",
						"direction": "down",
						})

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
				v["progress"] = f"({file['bytesDone']}/{file['bytesTotal']}) - {pct:.2f}%"
				if must_be_added:
					self.downloading_files_extra[file_details] = v

			for elm in self.folders:
				if elm["id"] == folder_name:
					elm["state"] = "syncing"
			# TODO: this is slow!
		self.state["update_files"] = True

	def event_unknown_event(self, event):
		pass

	def event_statechanged(self, event):
		for elem in self.folders:
			if elem["id"] == event["data"]["folder"]:
				elem["state"] = event["data"]["to"]
		self.state["update_folders"] = True
		self.set_state()

	def event_foldersummary(self, event):
		for elem in self.folders:
			if elem["id"] == event["data"]["folder"]:
				elem.update(event["data"]["summary"])
		self.state["update_folders"] = True

	def event_foldercompletion(self, event):
		for dev in self.devices:
			if dev["id"] == event["data"]["device"]:
				if event["data"]["completion"] < 100:
					dev["state"] = "syncing"
				else:
					dev["state"] = ""
		self.state["update_devices"] = True

	def event_starting(self, event):
		self.set_state("paused")
		log.info(f"Received that Syncthing was starting at: {event['time']}")
		# Check for added/removed devices or folders.
		glib.idle_add(self.rest_get, "/rest/system/config")
		glib.idle_add(self.rest_get, "/rest/system/version")

	def event_startupcomplete(self, event):
		self.set_state("idle")
		log.info(f"Syncthing startup complete at: {self.convert_time(event['time'])}")
		if event["data"] is None:
			self.system_status["myID"] = event["data"].get("myID")
		log.info(f"myID: {self.system_status.get('myID')}")

	def event_ping(self, event):
		self.last_ping = parse(event["time"])

	def event_devicediscovered(self, event):
		found = False
		for elm in self.devices:
			if elm["id"] == event["data"]["device"]:
				elm["state"] = "discovered"
				found = True
		if not found:
			log.warn("Unknown device discovered")
			self.devices.append({
					"id": event["data"]["device"],
					"name": "new unknown device",
					"address": event["data"]["addrs"],
					"state": "unknown",
					})
		self.state["update_devices"] = True

	def event_deviceconnected(self, event):
		for dev in self.devices:
			if event["data"]["id"] == dev["id"]:
				dev["connected"] = True
				log.info(f"Device connected: {dev['name']}")
		self.state["update_devices"] = True

	def event_devicedisconnected(self, event):
		for dev in self.devices:
			if event["data"]["id"] == dev["id"]:
				dev["connected"] = False
				log.info(f"Device disconnected: {dev['name']}")
		self.state["update_devices"] = True

	def event_itemstarted(self, event):
		log.debug(f"Item started: {event['data']['item']}")
		file_details = {
				"folder": event["data"]["folder"],
				"file": event["data"]["item"],
				"type": event["data"]["type"],
				"direction": "down",
				}
		try:
			del self.downloading_files_extra[json.dumps(file_details)]
		except KeyError:
			pass

		if file_details not in self.downloading_files:
			self.downloading_files.append(file_details)
		for elm in self.folders:
			if elm["id"] == event["data"]["folder"]:
				elm["state"] = "syncing"
		self.set_state()
		self.state["update_files"] = True

	def event_itemfinished(self, event):
		# TODO: test whether "error" is null
		log.debug(f"Item finished: {event['data']['item']}")
		file_details = {
				"folder": event["data"]["folder"],
				"file": event["data"]["item"],
				"type": event["data"]["type"],
				"direction": "down",
				}
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
			log.debug(
					f"File locally updated: {file_details['file']} ({event['data']['action']}) at {event['time']}"
					)
		except ValueError:
			log.debug(f"Completed a file we didn't know about: {event['data']['item']}")

		file_details["time"] = event["time"]
		file_details["action"] = event["data"]["action"]
		self.recent_files.insert(0, file_details)
		self.recent_files = self.recent_files[:self.args.nb_recent_files]
		self.state["update_files"] = True

	# End of event processing

	# Begin REST processing functions
	def process_rest_system_connections(self, data):
		for elem in data["connections"]:
			for dev in self.devices:
				if dev["id"] == elem:
					dev["connected"] = True
		self.state["update_devices"] = True

	def process_rest_system_config(self, data):
		log.info("Processing: /rest/system/config")
		self.api_key = data["gui"]["apiKey"]

		newfolders = []
		for elem in data["folders"]:
			newfolders.append({
					"id": elem["id"],
					"label": elem["label"],
					"path": elem["path"],
					"state": "unknown",
					})

		newdevices = []
		for elem in data["devices"]:
			newdevices.append({
					"id": elem["deviceID"],
					"name": elem["name"],
					"state": "",
					"connected": False,
					"lastSeen": "",
					})

		self.folders = newfolders
		self.devices = newdevices

	def process_rest_system_status(self, data):
		if data["uptime"] < self.system_status.get("uptime", 0):
			# Means that Syncthing restarted
			self.last_seen_id = 0
			glib.idle_add(self.rest_get, "/rest/system/version")
		self.system_status = data
		# TODO: check status of global announce
		self.state["update_st_running"] = True

	def process_rest_system_upgrade(self, data):
		self.syncthing_version = data["running"]
		if data["newer"]:
			self.syncthing_upgrade_menu.set_label(f"New version available: {data['latest']}")
			self.syncthing_upgrade_menu.show()
		else:
			self.syncthing_upgrade_menu.hide()
		self.state["update_st_running"] = True

	def process_rest_system_version(self, data):
		self.syncthing_version = data["version"]
		self.state["update_st_running"] = True

	def process_rest_system_ping(self, data):
		if data["ping"] == "pong":
			log.info(f"Connected to Syncthing REST interface at {self.syncthing_url('')}")

	def process_rest_ping(self, data):
		if data["ping"] == "pong":
			# Basic version check
			log.error("Detected running Syncthing version < v0.11")
			log.error("Syncthing v0.11 (or higher) required. Exiting.")
			self.quit()

	def process_rest_stats_device(self, data):
		for item in data:
			for dev in self.devices:
				if dev["id"] == item:
					dev["lastSeen"] = data[item]["lastSeen"]

	def process_rest_system_error(self, data):
		self.errors = data["errors"]
		if self.errors:
			log.info(f"{data['errors']}")
			self.mi_errors.show()
			self.set_state("error")
		else:
			self.mi_errors.hide()

	# end of the REST processing functions

	def update(self):
		for func in self.state:
			if self.state[func]:
				log.debug(f"self.update {func}")
				start = getattr(self, "%s" % func)()
		return True

	def update_last_checked(self, isotime):
		# dt = parse(isotime)
		# self.last_checked_menu.set_label("Last checked: %s" % (dt.strftime("%H:%M"),))
		pass

	def update_last_seen_id(self, lsi):
		if lsi > self.last_seen_id:
			self.last_seen_id = lsi

	def update_devices(self):
		self.state["update_devices"] = False
		if not self.devices:
			self.devices_menu.set_label("No devices")
			self.devices_menu.set_sensitive(False)
			return

		# TODO: set icon if zero devices are connected
		self.devices_menu.set_label(f"Devices ({self.count_connected()}/{len(self.devices) - 1})")
		self.devices_menu.set_sensitive(True)

		# TODO: use a better check here, in case devices changed but count
		# stayed the same
		if len(self.devices_submenu) != len(self.devices) - 1:
			# Repopulate the devices menu
			for child in self.devices_submenu.get_children():
				self.devices_submenu.remove(child)
			for elm in sorted(self.devices, key=lambda elm: elm["name"]):
				if elm["id"] == self.system_status.get("myID", None):
					self.device_name = elm["name"]
					self.state["update_st_running"] = True
				else:
					mi = gtk.MenuItem(elm["name"])
					self.devices_submenu.append(mi)
					mi.show()

		# Set menu item labels
		for mi in self.devices_submenu:
			for dev in self.devices:
				if mi.get_label().split()[0] == dev["name"]:
					if dev["connected"]:
						mi.set_label(dev["name"])
					else:
						# NOTE: This crashes when lastSeen = 0
						if len(dev["lastSeen"]) > 0:
							mi.set_label(f"{dev['name']} (Last seen {self.convert_time(dev['lastSeen'])})")
						else:
							mi.set_label(f"{dev['name']} (Last seen Unknown)")

					mi.set_sensitive(dev["connected"])

	def update_files(self):
		self.current_files_menu.set_label(f"Downloading {len(self.downloading_files)} files")

		if not self.downloading_files:
			self.current_files_menu.set_sensitive(False)
		# self.set_state("idle")
		else:
			# Repopulate the current files menu
			self.current_files_menu.set_sensitive(True)
			self.set_state("syncing")
			for child in self.current_files_submenu.get_children():
				self.current_files_submenu.remove(child)
			for f in self.downloading_files:
				fj = json.dumps(f)
				# mi = gtk.MenuItem(f"\u2193 [{f['folder']}] {shorten_path(f['file'])}")
				mi = gtk.MenuItem(
						"\u2193 [{}] {}{}".format(
								f["folder"],
								shorten_path(f["file"]),
								self.downloading_files_extra[fj]["progress"] if fj in self.downloading_files_extra
								and "progress" in self.downloading_files_extra[fj] else ""
								)
						)
				self.current_files_submenu.append(mi)
				mi.connect(
						"activate",
						self.open_file_browser,
						os.path.split(self.get_full_path(f["folder"], f["file"]))[0]
						)
				mi.show()
			self.current_files_menu.show()

		# Repopulate the recent files menu
		if not self.recent_files:
			self.recent_files_menu.set_sensitive(False)
		else:
			self.recent_files_menu.set_sensitive(True)
			for child in self.recent_files_submenu.get_children():
				self.recent_files_submenu.remove(child)
			icons = {
					"delete": "\u2612",  # [x]
					"update": "\u2193",  # down arrow
					"dir": "\u0001f4c1",  # folder
					"file": "\u0001f4c4",  # file
					}
			for f in self.recent_files:
				mi = gtk.MenuItem(
						f"{icons.get(f['action'], 'unknown')} {self.convert_time(f['time'])} [{f['folder']}] {shorten_path(f['file'])}"
						)
				self.recent_files_submenu.append(mi)
				mi.connect(
						"activate",
						self.open_file_browser,
						os.path.split(self.get_full_path(f["folder"], f["file"]))[0]
						)
				mi.show()
			self.recent_files_menu.show()
		self.state["update_files"] = False

	def update_folders(self):
		if self.folders:
			self.folder_menu.set_sensitive(True)
			folder_maxlength = 0
			if len(self.folders) == len(self.folder_menu_submenu):
				for mi in self.folder_menu_submenu:
					for elm in self.folders:
						folder_maxlength = max(folder_maxlength, len(elm["id"]))
						if folder_maxlength < max(folder_maxlength, len(elm["label"])):
							folder_maxlength = max(folder_maxlength, len(elm["label"]))
						if str(mi.get_label()).split(" ", 1)[0] == elm["id"]:
							if elm["state"] == "scanning":
								# mi.set_label(f"{elm['id']} (scanning)")
								mi.set_label(f"{elm['id'] or elm['label']} (scanning)")
							elif elm["state"] == "syncing":
								if elm.get("needFiles") > 1:
									lbltext = "{fid} (syncing {num} files, {bytes})"
								elif elm.get("needFiles") == 1:
									lbltext = "{fid} (syncing {num} file, {bytes})"
								else:
									lbltext = "{fid} (syncing)"
								mi.set_label(
										lbltext.format(
												# fid=elm["id"], num=elm.get("needFiles"),
												fid=elm["id"] or elm["label"],
												num=elm.get("needFiles"),
												bytes=human_readable(elm.get("needBytes", 0))
												)
										)
							else:
								# mi.set_label(elm["id"].ljust(folder_maxlength + 20))
								mi.set_label(elm["id"] or elm["label"].ljust(folder_maxlength + 20))
			else:
				for child in self.folder_menu_submenu.get_children():
					self.folder_menu_submenu.remove(child)
				for elm in self.folders:
					folder_maxlength = max(folder_maxlength, len(elm["id"]))
					if folder_maxlength < max(folder_maxlength, len(elm["label"])):
						folder_maxlength = max(folder_maxlength, len(elm["label"]))
					# mi = gtk.MenuItem(elm["id"].ljust(folder_maxlength + 20))
					mi = gtk.MenuItem((elm["label"] or elm["id"]).ljust(folder_maxlength + 20))
					mi.connect("activate", self.open_file_browser, elm["path"])
					self.folder_menu_submenu.append(mi)
					mi.show()
		else:
			self.folder_menu.set_sensitive(False)
		self.state["update_folders"] = False

	def update_st_running(self):
		if self.current_action[0]:
			pass
		elif self.count_connection_error <= 1:
			if self.syncthing_version and self.device_name:
				self.title_menu.set_label(f"Syncthing {self.syncthing_version} \u2022 {self.device_name}")
			else:
				self.title_menu.set_label("Syncthing")
			self.mi_start_syncthing.set_sensitive(False)
			self.mi_restart_syncthing.set_sensitive(True)
			self.mi_shutdown_syncthing.set_sensitive(True)
		else:
			self.title_menu.set_label("Syncthing is not running")
			for dev in self.devices:
				dev["connected"] = False
			self.state["update_devices"] = True
			for f in self.folders:
				f["state"] = "unknown"
			self.state["update_folders"] = True
			self.errors = []
			self.mi_errors.hide()
			self.set_state()
			self.mi_start_syncthing.set_sensitive(True)
			self.mi_restart_syncthing.set_sensitive(False)
			self.mi_shutdown_syncthing.set_sensitive(False)

	def count_connected(self):
		return len([e for e in self.devices if e['connected']])

	def syncthing_start(self, *_):
		self.mi_start_syncthing.set_sensitive(False)
		self.mi_restart_syncthing.set_sensitive(False)
		self.mi_shutdown_syncthing.set_sensitive(False)
		self.current_action = ("syncthing_start", time.time())
		self.title_menu.set_label("Starting Syncthing...")
		self.syncthing_version = None

		try:
			log.info("Starting syncthing")
			subprocess.run(["syncthing", "-no-browser", "-no-restart", "-logflags=0"], shell=True, check=True)
		except Exception as e:
			log.error(f"Couldn't run syncthing: {e}")
			return
		self.state["update_st_running"] = True

	def syncthing_restart(self, *_):
		self.mi_start_syncthing.set_sensitive(False)
		self.mi_restart_syncthing.set_sensitive(False)
		self.mi_shutdown_syncthing.set_sensitive(False)
		self.current_action = ("syncthing_restart", time.time())
		self.title_menu.set_label("Restarting Syncthing...")
		self.syncthing_version = None

		self.rest_post("/rest/system/restart")
		self.set_state("paused")
		self.state["update_st_running"] = True

	def syncthing_shutdown(self, *_):
		self.mi_start_syncthing.set_sensitive(False)
		self.mi_restart_syncthing.set_sensitive(False)
		self.mi_shutdown_syncthing.set_sensitive(False)
		self.current_action = ("syncthing_shutdown", time.time())
		self.title_menu.set_label("Shutting down Syncthing...")
		self.syncthing_version = None

		self.rest_post("/rest/system/shutdown")
		self.set_state("paused")
		self.state["update_st_running"] = True

	def convert_time(self, t):
		return parse(t).strftime(self.args.timeformat)

	@staticmethod
	def calc_speed(old, new):
		return old / (new * 10)

	def license(self):
		with open(os.path.join(self.wd, "LICENSE")) as f:
			lic = f.read()
		return lic

	def show_about(self, _):
		dialog = gtk.AboutDialog()
		dialog.set_default_icon_from_file(os.path.join(self.icon_path, "icon.png"))
		dialog.set_logo(None)
		dialog.set_program_name("Indicator Syncthing")
		dialog.set_version(VERSION)
		dialog.set_website("https://github.com/vincent-t/indicator-syncthing")
		dialog.set_comments(
				"This menu applet for systems supporting AppIndicator\ncan show the status of a Syncthing instance"
				)
		dialog.set_license(self.license())
		dialog.run()
		dialog.destroy()

	def set_state(self, s=None):
		if not s:
			s = self.state["set_icon"]

		if (s == "error") or self.errors:
			self.state["set_icon"] = "error"
		elif self.count_connection_error > 1:
			self.state["set_icon"] = "paused"
		else:
			self.state["set_icon"] = self.folder_check_state()

	def folder_check_state(self):
		state = {"syncing": 0, "idle": 0, "cleaning": 0, "scanning": 0, "unknown": 0}
		for elem in self.folders:
			if elem["state"] in state:
				state[elem["state"]] += 1

		if state["syncing"] > 0:
			return "syncing"
		elif state["cleaning"] > 0:
			return "scanning"
		else:
			return "idle"

	def set_icon(self):
		icon = {
				"updating": {"name": "syncthing-client-updating", "descr": "Updating"},
				"idle": {"name": "syncthing-client-idle", "descr": "Nothing to do"},
				"syncing": {"name": "syncthing-client-updown", "descr": "Transferring Data"},
				"error": {"name": "syncthing-client-error", "descr": "Scotty, We Have A Problem!"},
				"paused": {"name": "syncthing-client-paused", "descr": "Paused"},
				"scanning": {"name": "syncthing-client-scanning", "descr": "Scanning Directories"},
				"cleaning": {"name": "syncthing-client-scanning", "descr": "Cleaning Directories"},
				}

		if not self.args.text_only:
			self.ind.set_attention_icon(icon[self.state["set_icon"]]["name"])
			self.ind.set_icon_full(icon[self.state["set_icon"]]["name"], icon[self.state["set_icon"]]["descr"])

	@staticmethod
	def run():
		gtk.main()

	@staticmethod
	def quit(*_):
		log.shutdown()
		gtk.main_quit()

	def timeout_rest(self):
		self.timeout_counter = (self.timeout_counter + 1) % 10
		if self.count_connection_error <= 1:
			glib.idle_add(self.rest_get, "/rest/system/connections")
			glib.idle_add(self.rest_get, "/rest/system/status")
			glib.idle_add(self.rest_get, "/rest/system/error")
			glib.idle_add(self.rest_get, "/rest/stats/device")
			if self.timeout_counter == 0 or not self.syncthing_version:
				glib.idle_add(self.rest_get, "/rest/system/upgrade")
				glib.idle_add(self.rest_get, "/rest/system/version")
		else:
			glib.idle_add(self.rest_get, "/rest/system/status")
		if self.current_action in ["syncthing_start", "syncthing_restart"]:
			glib.idle_add(self.rest_get, "/rest/system/upgrade")
			glib.idle_add(self.rest_get, "/rest/system/version")
		return True

	def timeout_events(self):
		if self.count_connection_error == 0:
			glib.idle_add(self.rest_get, "/rest/events")
		return True

	@staticmethod
	def open_file_browser(menuitem, path):
		if not os.path.isdir(path):
			log.debug(f"Not a directory, or does not exist: {path}")
			return
		try:
			subprocess.run(["xdg-open", path], check=True)
		except Exception as e:
			log.error(f"Couldn't open file browser for: {path} ({e})")

	def get_full_path(self, folder, item):
		for elem in self.folders:
			a = ""
			if elem["id"] == folder:
				a = elem["path"]
		return os.path.join(a, item)
