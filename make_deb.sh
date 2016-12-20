#!/bin/bash

PACKAGENAME=indicator-syncthing
VERSION=1.0.0
MAINTAINER=
EMAIL=

echo "Build $PACKAGENAME.deb"

mkdir -p "$PACKAGENAME/usr/bin" "$PACKAGENAME/etc/xdg/autostart" "$PACKAGENAME/usr/bin" "$PACKAGENAME/usr/share/$PACKAGENAME"

wget -nc -O - "https://github.com/vincent-t/indicator-syncthing/archive/master.tar.gz" | tar -xvzf - -C "$PACKAGENAME/usr/share/$PACKAGENAME" --strip-components=1 --exclude='README.md' --exclude='make_deb.sh' --exclude="*.gitignore" --exclude="*.svg"

tee "$PACKAGENAME/etc/xdg/autostart/$PACKAGENAME.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=$PACKAGENAME
Comment=AppIndicator for Syncthing
Exec=$PACKAGENAME --loglevel warning
StartupNotify=false
X-GNOME-Autostart-enabled=true
EOF

#Create softlink
ln -s "/usr/share/$PACKAGENAME/$PACKAGENAME.py" "$PACKAGENAME/usr/bin/$PACKAGENAME"

PACKAGESIZE=$(du -c $PACKAGENAME | egrep -i 'total|insgesamt' | cut -f1)

mkdir "$PACKAGENAME/DEBIAN"
tee "$PACKAGENAME/DEBIAN/control" << EOF
Package: $PACKAGENAME
Version: $VERSION
Architecture: all
Maintainer: $MAINTAINER <$EMAIL>
Installed-Size: $PACKAGESIZE
Depends: python3-dateutil, python3-gi, python3-requests, python3-requests-futures
Section: python
Priority: optional
Homepage: https://github.com/vincent-t/indicator-syncthing
Description: syncthing-ubuntu-indicator
 Provides an AppIndicator for Syncthing
EOF

chmod 0644 "$PACKAGENAME/DEBIAN/control"

fakeroot dpkg-deb --build "$PACKAGENAME"
rm -rf "$PACKAGENAME"
echo "$PACKAGENAME.deb successfully build!"
