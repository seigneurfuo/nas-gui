APP_NAME=nas-gui
APP_VERSION=0.0.1

fpm \
-s dir -t deb \
\
--name "${APP_NAME}" \
--version "${APP_VERSION}" \
--description "" \
--maintainer "seigneurfuo@protonmail.com>" \
\
--architecture x86 \
--depends python3-pyqt6 \
\
nas-gui.py=/usr/bin/nas-gui.py \
changelog.txt=/usr/share/${pkgname}/changelog.txt" \
nas-gui-autostart.desktop=/usr/share/applications/${APP_NAME}.desktop" \
nas-gui.desktop="/usr/share/applications/${APP_NAME}.desktop"