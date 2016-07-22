#!/bin/bash

PACKAGENAME=syncthing-ubuntu-indicator
VERSION=0.3.1
MAINTAINER=
EMAIL=

echo "Build $PACKAGENAME.deb"

mkdir -p $PACKAGENAME/etc/xdg/autostart
mkdir -p $PACKAGENAME/usr/bin
mkdir -p $PACKAGENAME/usr/share/syncthing-ubuntu-indicator

wget -nc -O - "https://github.com/vincent-t/syncthing-ubuntu-indicator/archive/master.tar.gz" | tar -xvzf - -C $PACKAGENAME/usr/share/syncthing-ubuntu-indicator --strip-components=1 --exclude='testserver.py' --exclude='README.md' --exclude='build_syncthing-ubuntu-indicator_deb.sh'

tee "$PACKAGENAME/etc/xdg/autostart/syncthing-ubuntu-indicator.desktop" << 'EOF'
[Desktop Entry]
Type=Application
Name=syncthing-ubuntu-indicator
Exec=syncthing-ubuntu-indicator
StartupNotify=false
Comment=AppIndicator for Syncthing
X-GNOME-Autostart-enabled=true
EOF

ln -s /usr/share/syncthing-ubuntu-indicator/syncthing-ubuntu-indicator.py $PACKAGENAME/usr/bin/syncthing-ubuntu-indicator

PACKAGESIZE=`du -c $PACKAGENAME | egrep -i 'total|insgesamt' | cut -f1`

mkdir $PACKAGENAME/DEBIAN
tee "$PACKAGENAME/DEBIAN/control" << EOF
Package: $PACKAGENAME
Version: $VERSION
Architecture: all
Maintainer: $MAINTAINER <$EMAIL>
Installed-Size: $PACKAGESIZE
Depends: python-gobject, python-pip, python-tz
Section: python
Priority: optional
Homepage: https://github.com/vincent-t/syncthing-ubuntu-indicator
Description: syncthing-ubuntu-indicator
 Provides an AppIndicator for Syncthing
EOF

fakeroot dpkg-deb --build $PACKAGENAME
rm -rf $PACKAGENAME
echo "$PACKAGENAME.deb successfully build!"

