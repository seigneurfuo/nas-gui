#!/bin/bash
echo "----- PKGBUILD -----"
cd "packaging/PKGBUILD"
ln -s -v -f "../../src/nas-gui.py" .
ln -s -v -f "../../src/changelog.txt" .
cd ".."

echo "----- Debian -----"
cd "debian"
ln -s -v -f "../../src/nas-gui.py" .
ln -s -v -f "../../src/changelog.txt" .

# TODO FPM: https://fpm.readthedocs.io/en/latest/getting-started.html#understanding-the-basics-of-fpm ?