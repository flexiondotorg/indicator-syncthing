#!/usr/bin/env python3
#
#  utils.py
"""
Utility functions.
"""
# stdlib
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
import os
import re
import socket

# 3rd party
import appdirs
from apeye import URL
from domdf_python_tools.paths import PathPlus

__all__ = ["get_lock", "get_port", "human_readable", "shorten_path"]

listen_address_re = re.compile(r"<listenAddress>\s*(.*)\s*</listenAddress>")


def get_port() -> int:
	"""
	Returns the Syncthing port.
	"""

	config_dir = PathPlus(appdirs.user_config_dir("syncthing"))
	config_file = config_dir / "config.xml"

	for match in listen_address_re.findall(config_file.read_text()):
		if match != "default":
			netloc = URL(match).netloc
			if ':' in netloc:
				return int(netloc.split(':')[-1])
			else:
				return 80

	return 8384


def get_lock(process_name):
	"""
	Acquire a lock on the socket used to communicate with Syncthing.

	:param process_name:
	"""

	# Without holding a reference to our socket somewhere it gets garbage
	# collected when the function exits
	get_lock._lock_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)  # type: ignore

	try:
		get_lock._lock_socket.bind('\x00' + process_name)  # type: ignore
		print("Created lock for process:", process_name)
	except OSError:
		print("Lock exists. Process:", process_name, "is already running")
		exit()


def shorten_path(text: str, maxlength: int = 80) -> str:
	"""
	Shorten the path ``text`` to a max length of ``maxlength`` characters,
	adding ellipses to the middle if necessary.

	:param text:
	:param maxlength:
	"""  # noqa: D400

	if len(text) <= maxlength:
		return text

	head, tail = os.path.split(text)

	if len(tail) > maxlength:
		return tail[:maxlength]  # TODO: separate file extension

	while len(head) + len(tail) > maxlength:
		head = '/'.join(head.split('/')[:-1])
		if head == '':
			return f".../{tail}"

	return f"{head}/.../{tail}"


def human_readable(size: float):
	"""
	Return a human-readable representation of ``size``.

	:param size:
	"""

	# TODO: use humanfriendly?

	for unit in ['B', "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB"]:
		if abs(size) < 1024.0:
			f = f"{size:.1f}".rstrip('0').rstrip('.')
			return f"{f} {unit}"

		size = size / 1024.0

	return f"{size:.1f} {'YiB'}"
