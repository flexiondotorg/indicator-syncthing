==========================
indicator-syncthing
==========================

.. start short_desc

**A Syncthing status menu for Unity and other desktops that support AppIndicator.**

.. end short_desc

Syncthing_ v0.11.0 and higher are supported.

This is a fork of Stuart Langridge's syncthing-ubuntu-indicator_.


.. _Syncthing: https://github.com/syncthing/syncthing

.. _syncthing-ubuntu-indicator: https://github.com/stuartlangridge/syncthing-ubuntu-indicator

.. start shields

.. list-table::
	:stub-columns: 1
	:widths: 10 90

	* - Docs
	  - |docs| |docs_check|
	* - Tests
	  - |travis| |codefactor|
	* - PyPI
	  - |pypi-version| |supported-versions| |supported-implementations| |wheel|
	* - Activity
	  - |commits-latest| |commits-since| |maintained|
	* - Other
	  - |license| |language| |requires|

.. |docs| image:: https://img.shields.io/readthedocs/indicator-syncthing/latest?logo=read-the-docs
	:target: https://indicator-syncthing.readthedocs.io/en/latest/?badge=latest
	:alt: Documentation Status

.. |docs_check| image:: https://github.com/domdfcoding/indicator-syncthing/workflows/Docs%20Check/badge.svg
	:target: https://github.com/domdfcoding/indicator-syncthing/actions?query=workflow%3A%22Docs+Check%22
	:alt: Docs Check Status

.. |travis| image:: https://img.shields.io/travis/com/domdfcoding/indicator-syncthing/master?logo=travis
	:target: https://travis-ci.com/domdfcoding/indicator-syncthing
	:alt: Travis Build Status

.. |requires| image:: https://requires.io/github/domdfcoding/indicator-syncthing/requirements.svg?branch=master
	:target: https://requires.io/github/domdfcoding/indicator-syncthing/requirements/?branch=master
	:alt: Requirements Status

.. |codefactor| image:: https://img.shields.io/codefactor/grade/github/domdfcoding/indicator-syncthing?logo=codefactor
	:target: https://www.codefactor.io/repository/github/domdfcoding/indicator-syncthing
	:alt: CodeFactor Grade

.. |pypi-version| image:: https://img.shields.io/pypi/v/indicator-syncthing
	:target: https://pypi.org/project/indicator-syncthing/
	:alt: PyPI - Package Version

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/indicator-syncthing
	:target: https://pypi.org/project/indicator-syncthing/
	:alt: PyPI - Supported Python Versions

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/indicator-syncthing
	:target: https://pypi.org/project/indicator-syncthing/
	:alt: PyPI - Supported Implementations

.. |wheel| image:: https://img.shields.io/pypi/wheel/indicator-syncthing
	:target: https://pypi.org/project/indicator-syncthing/
	:alt: PyPI - Wheel

.. |license| image:: https://img.shields.io/github/license/domdfcoding/indicator-syncthing
	:target: https://github.com/domdfcoding/indicator-syncthing/blob/master/LICENSE
	:alt: License

.. |language| image:: https://img.shields.io/github/languages/top/domdfcoding/indicator-syncthing
	:alt: GitHub top language

.. |commits-since| image:: https://img.shields.io/github/commits-since/domdfcoding/indicator-syncthing/v1.0.1
	:target: https://github.com/domdfcoding/indicator-syncthing/pulse
	:alt: GitHub commits since tagged version

.. |commits-latest| image:: https://img.shields.io/github/last-commit/domdfcoding/indicator-syncthing
	:target: https://github.com/domdfcoding/indicator-syncthing/commit/master
	:alt: GitHub last commit

.. |maintained| image:: https://img.shields.io/maintenance/yes/2020
	:alt: Maintenance

.. end shields

Dependencies
==========================

.. code-block:: bash

	python3_dateutil>=2.8.1
	requests_futures>=1.0.0
	requests>=2.18.4
	PyGObject>=3.34.0


Installation
==========================

.. start installation

``indicator-syncthing`` can be installed from PyPI.

To install with ``pip``:

.. code-block:: bash

	$ python -m pip install indicator-syncthing

.. end installation
