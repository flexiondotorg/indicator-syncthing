#!/usr/bin/env python
# This file is managed by `repo_helper`. Don't edit it directly
"""Setup script"""

# 3rd party
from setuptools import find_packages, setup

# this package
from __pkginfo__ import *  # pylint: disable=wildcard-import

# Create .desktop file
with open(f'indicator-syncthing.desktop', 'w') as desktop:
	desktop.write(f"""[Desktop Entry]
Version={__version__}
Name={modname}
Comment={short_desc}
Exec=indicator-syncthing
Icon=syncthing
Terminal=false
Type=Application
Categories=Utility;
""")

setup(
		author=author,
		author_email=author_email,
		classifiers=classifiers,
		description=short_desc,
		entry_points=entry_points,
		extras_require=extras_require,
		include_package_data=True,
		install_requires=install_requires,
		keywords=keywords,
		license=__license__,
		long_description=long_description,
		name=pypi_name,
		packages=find_packages(exclude=("tests", "doc-source")),
		project_urls=project_urls,
		py_modules=py_modules,
		python_requires=">=3.6",
		url=web,
		version=__version__,
		zip_safe=False,
		data_files=[('share/applications', ['indicator-syncthing.desktop'])],
		)
