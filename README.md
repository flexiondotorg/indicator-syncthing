syncthing-ubuntu-indicator
==========================

A [Syncthing] status menu for Ubuntu,
using Syncthings event interface to display informations about what's going on.

This is a fork from Stuart Langridges [syncthing-ubuntu-indicator].

The project is in an early stage and contributions are welcome.

dependencies
==========================
python2 AppIndicator3
python2 gtk 
& the python2 versions of:
python-dateutil
python-tz



(I'm running Arch Linux so somebody maybe can fill the dependencies for other distributions, if there are some?)

installation
==========================
just run via terminal ./syncthing-ubuntu-indicator.sh

When you are using GNOME3 you can move the icon with the [gnome-shell-extension-appindicator] in the upper notification bar. 


[Syncthing]: https://github.com/syncthing/syncthing

[syncthing-ubuntu-indicator]: https://github.com/stuartlangridge/syncthing-ubuntu-indicator

[gnome-shell-extension-appindicator]: https://github.com/rgcjonas/gnome-shell-extension-appindicator
