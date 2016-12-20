indicator-syncthing
==========================

A [Syncthing] status menu for systems that support AppIndicator,
using Syncthing's event interface to display information about what's going on.

Syncthing v0.11.0 and higher are supported.

This is a fork from Stuart Langridge's [syncthing-ubuntu-indicator].

The project is in an early stage and contributions are welcome.

dependencies
==========================

_On Ubuntu:_
* python3-dateutil
* python3-gi
* python3-requests
* python3-requests-futures

installation
==========================

    git clone https://github.com/vincent-t/syncthing-ubuntu-indicator.git
    cd syncthing-ubuntu-indicator
    python3 ./indicator-syncthing.py

[Syncthing]: https://github.com/syncthing/syncthing

[syncthing-ubuntu-indicator]: https://github.com/stuartlangridge/syncthing-ubuntu-indicator
