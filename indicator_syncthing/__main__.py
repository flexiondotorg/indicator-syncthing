#!/usr/bin/env python3
#
#  __main__.py
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
import argparse
import logging as log
import os
import signal

# this package
from indicator_syncthing import IndicatorSyncthing, get_lock


def main():
	signal.signal(signal.SIGINT, signal.SIG_DFL)

	scriptname = os.path.basename(__file__)
	get_lock(scriptname)

	parser = argparse.ArgumentParser()
	parser.add_argument(
			"--loglevel",
			choices=["debug", "info", "warning", "error"],
			default="info",
			help="Filter logging by level. Default: %(default)s"
			)
	parser.add_argument("--log-events", action="store_true", help="Log every event")
	parser.add_argument(
			"--timeout-event",
			type=int,
			default=10,
			metavar="N",
			help="Interval for polling event interface, in seconds. Default: %(default)s"
			)
	parser.add_argument(
			"--timeout-rest",
			type=int,
			default=30,
			metavar="N",
			help="Interval for polling REST interface, in seconds. Default: %(default)s"
			)
	parser.add_argument(
			"--timeout-gui",
			type=int,
			default=5,
			metavar="N",
			help="Interval for refreshing GUI, in seconds. Default: %(default)s"
			)
	parser.add_argument(
			"--no-shutdown", action="store_true", help="Hide Start, Restart, and Shutdown Syncthing menus"
			)
	parser.add_argument(
			"--timeformat",
			type=str,
			default="%x %X",
			metavar="FORMAT",
			help="Format to display date and time. See 'man strftime' for help. Default: %(default)s"
			)
	parser.add_argument("--text-only", action="store_true", help="Text only, no icon")
	parser.add_argument(
			"--nb-recent-files",
			type=int,
			default=20,
			metavar="N",
			help="Number of recent files entries to keep. Default: %(default)s"
			)

	args, unknown = parser.parse_known_args()
	for arg in [args.timeout_event, args.timeout_rest, args.timeout_gui]:
		if arg < 1:
			print("Timeouts must be integers greater than 0")
			exit()

	loglevels = {"debug": log.DEBUG, "info": log.INFO, "warning": log.WARNING, "error": log.ERROR}
	log.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=loglevels[args.loglevel])

	# set log level of requests library
	log.getLogger("urllib3.connectionpool").setLevel(log.WARNING)

	indicator = IndicatorSyncthing(args)
	indicator.run()


if __name__ == "__main__":
	main()
