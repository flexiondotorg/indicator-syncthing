#!/usr/bin/env python
# This file is managed by 'repo_helper'. Don't edit it directly.

# stdlib
import sys

# 3rd party
from setuptools import setup

sys.path.append('.')

# this package
from __pkginfo__ import *  # pylint: disable=wildcard-import

# Create .desktop file
with open(f'indicator-syncthing.desktop', 'w') as desktop:
	desktop.write(
			f"""[Desktop Entry]
Version={__version__}
Name={modname}
Comment={short_desc}
Exec=indicator-syncthing
Icon=syncthing
Terminal=false
Type=Application
Categories=Utility;
"""
			)

setup(
		data_files=[("share/applications", ["indicator-syncthing.desktop"])],
		description="A Syncthing status menu for Unity and other desktops that support AppIndicator.",
		extras_require=extras_require,
		install_requires=install_requires,
		py_modules=[],
		version=__version__,
		)
