syncthing-ubuntu-indicator
==========================

A [Syncthing] status menu for systems that support AppIndicator,
using Syncthing's event interface to display information about what's going on.

Syncthing v0.11.0 and higher are supported.

This is a fork from Stuart Langridge's [syncthing-ubuntu-indicator].

The project is in an early stage and contributions are welcome.

dependencies
==========================

* python2 AppIndicator3
* python2 gtk 
* python-dateutil (python2 version)
* python-tz (python2 version)
* requests-futures (python2 version)


(I'm running Arch Linux so somebody maybe can fill the dependencies for other distributions, if there are some?)

installation
==========================
Tldr:
in a directory of your choice:

    git clone https://github.com/icaruseffect/syncthing-ubuntu-indicator.git
  
    cd syncthing-ubuntu-indicator
  
    python2 ./syncthing-ubuntu-indicator.py

When you are using GNOME3 you can move the icon with the [gnome-shell-extension-appindicator] in the upper notification bar. 


_On Ubuntu 14.04:_

    sudo apt-get install python-pip python-tz 
  
    sudo pip install python-dateutil requests-futures

  this should result in the installation of the following packages:
  * python-colorama
  * python-distlib
  * python-html5lib
  * python-pip
  * python-requests
  * python-setuptools
  * python-urllib3
  * python-dateutil

  then go to [gnome-extensions-appindicator] and install "AppIndicator support"





[Syncthing]: https://github.com/syncthing/syncthing

[syncthing-ubuntu-indicator]: https://github.com/stuartlangridge/syncthing-ubuntu-indicator

[gnome-shell-extension-appindicator]: https://github.com/rgcjonas/gnome-shell-extension-appindicator

[gnome-extensions-appindicator]: https://extensions.gnome.org/extension/615/appindicator-support/

