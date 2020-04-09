#!/bin/bash
cd "PKGBUILD"
ln -s "../src/nas-gui.py" .
PKGDEST=".." makepkg --clean --cleanbuild --force --syncdeps --rmdeps