# Copyright (C) 2019-2020 Dominic Davis-Foster <dominic@davis-foster.co.uk>

import pathlib

from indicator_syncthing import APPINDICATOR_ID

modname = APPINDICATOR_ID
py_modules = ["indicator_syncthing"]
entry_points = {
	'console_scripts': [
		f'{APPINDICATOR_ID}=indicator_syncthing:main',
			]}
# Credit: https://stackoverflow.com/a/12514470/3092681

license = 'Apache Software License'

short_desc = 'Syncthing status indicator'

classifiers = [
		'Development Status :: 4 - Beta',
		'Intended Audience :: End Users/Desktop',
		"License :: OSI Approved :: Apache Software License",
		'Operating System :: POSIX :: Linux',
		'Programming Language :: Python',
		'Programming Language :: Python :: 3.6',
		'Programming Language :: Python :: 3.7',
		'Programming Language :: Python :: 3.8',
		"Topic :: Utilities",
		]

author = "Dominic Davis-Foster"
author_email = "dominic@davis-foster.co.uk"
github_username = "domdfcoding"
web = github_url = f"https://github.com/{github_username}/{modname}"


# Get info from files; set: long_description
if pathlib.Path.cwd().name == "doc-source":
	print(pathlib.Path.cwd().parent / "README.rst")
	install_requires = (pathlib.Path.cwd().parent / "requirements.txt").read_text().split("\n")
	long_description = (pathlib.Path.cwd().parent / "README.rst").read_text() + '\n'
else:
	print(pathlib.Path("README.rst"))
	install_requires = pathlib.Path("requirements.txt").read_text().split("\n")
	long_description = pathlib.Path("README.rst").read_text() + '\n'


data_files = [
		('share/applications', [f'{APPINDICATOR_ID}.desktop']),
		]
