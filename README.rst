indicator-syncthing
==========================

A Syncthing_ status menu for systems that support AppIndicator,
using Syncthing's event interface to display information about what's going on.

Syncthing v0.11.0 and higher are supported.

This is a fork from Stuart Langridge's syncthing-ubuntu-indicator_.

The project is in an early stage and contributions are welcome.

Dependencies
==========================

.. code-block:: bash

	python3_dateutil>=2.8.1
	requests_futures>=1.0.0
	requests>=2.18.4
	PyGObject>=3.34.0


Installation
==========================

.. code-block:: bash

	git clone https://github.com/domdfcoding/indicator-syncthing.git
	cd indicator-syncthing
	python3 ./indicator-syncthing.py

.. _Syncthing: https://github.com/syncthing/syncthing

.. _syncthing-ubuntu-indicator: https://github.com/stuartlangridge/syncthing-ubuntu-indicator
