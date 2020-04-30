#!/bin/env python

import configparser
import sys
import os

from pathlib import Path
from subprocess import check_output
from time import sleep

from webbrowser import open_new_tab
from os import system
from threading import Thread

from psutil import process_iter
from PyQt5.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon


changelogMessage = """
<b>2020-04-30</b>
 - Déplacement de quelques informations de configuration dans un fichier<br>de configuration: ~/.config/nas-gui.ini
 - Désactivation de la demande de montage quand pamac est ouvert

<b>2020-04-09</b>
 - Modification du chemin pour les paquets Manjaro: x86_64

<b>2020-03-18</b>
 - Ajout d'un nouveau partage "Sauvegarde Web"
 - Correction de la fermeture de l'application

<b>2020-03-15</b>
 - Ajout d'un .desktop pour lance rl'application à chaque démarrage

<b>2019-07-20</b>
 - Ajout d'une entrée "changements"
 - Création automatique des répertoires de montage s'il n'existent pas
 - Ajout d'un choix qui permet d'afficher l'espace utilisé pour chaque partage
 - Ajout d'un lien pour acceder à la page DSM
"""

class TrayIcon(QSystemTrayIcon):
    def __init__(self):
        super().__init__()

        self.config = configparser.ConfigParser()
        self.read_config_file()

        self.init_ui()

        self.nasBaseFolder = "{}:/volume1/".format(self.config["NAS"]["ip"])
        self.mountpoint = self.config["Shares"]["default_mountpoint"]
        self.isPackageMount = False
        self.shares = ["Fichiers", "Echange", "Packages", "Sauvegarde", "Temporaire", "Torrents", "Vidéos"]

        #self.pamac_thread = Thread(target=self.daemon)
        #self.pamac_thread.start()

    def read_config_file(self):
        config_file_path = os.path.join(Path.home(),".config", "nas-gui.ini")
        if not os.path.isfile(config_file_path):
            exit(0)

        self.config.read(config_file_path)


    def daemon(self):
        self.daemon_running = True
        while self.daemon_running:
            for proc in process_iter():
                if proc.name() == "pamac-manager":
                    self.mount_share("Packages")
                    running = False

            sleep(1)


    def init_ui(self):
        self.menu = QMenu()

        self.actionFichiers = QAction(QIcon.fromTheme("folder"), "Fichiers")
        self.actionFichiers.triggered.connect(lambda: self.mount_share("Fichiers"))
        self.menu.addAction(self.actionFichiers)

        self.actionEchange = QAction(QIcon.fromTheme("fitwidth"), "Echange")
        self.actionEchange.triggered.connect(lambda: self.mount_share("Echange"))
        self.menu.addAction(self.actionEchange)

        self.actionPackages = QAction(QIcon.fromTheme("package"), "Packages")
        self.actionPackages.triggered.connect(lambda: self.mount_share("Packages"))
        self.menu.addAction(self.actionPackages)

        self.actionSauvegarde = QAction(QIcon.fromTheme("folder-backup"), "Sauvegarde")
        self.actionSauvegarde.triggered.connect(lambda: self.mount_share("Sauvegarde"))
        self.menu.addAction(self.actionSauvegarde)

        self.actionSauvegardeWeb = QAction(QIcon.fromTheme("web-browser"), "Sauvegarde Web")
        self.actionSauvegardeWeb.triggered.connect(lambda: self.mount_share("Sauvegarde-web"))
        self.menu.addAction(self.actionSauvegardeWeb)

        self.actionTemporaire = QAction(QIcon.fromTheme("folder-temp"), "Temporaire")
        self.actionTemporaire.triggered.connect(lambda: self.mount_share("Temporaire"))
        self.menu.addAction(self.actionTemporaire)

        self.actionTorrents = QAction(QIcon.fromTheme("folder-download"), "Torrents")
        self.actionTorrents.triggered.connect(lambda: self.mount_share("Torrents"))
        self.menu.addAction(self.actionTorrents)

        self.actionVideos = QAction(QIcon.fromTheme("folder-videos"), "Vidéos")
        self.actionVideos.triggered.connect(lambda: self.mount_share("Vidéos"))
        self.menu.addAction(self.actionVideos)

        self.menu.addSeparator()
        self.actionUnmountAll = QAction(QIcon.fromTheme("window-close"), "Démonter TOUS les partages")
        self.actionUnmountAll.triggered.connect(self.umount_all)
        self.menu.addAction(self.actionUnmountAll)

        self.menu.addSeparator()
        self.actionUsage = QAction(QIcon.fromTheme(""), "Utilisation ...")
        self.actionUsage.triggered.connect(self.usage_dialog)
        #self.menu.addAction(self.actionUsage)

        self.actionOpenDSM = QAction(QIcon.fromTheme(""), "Ouvrir DSM ...")
        self.actionOpenDSM.triggered.connect(self.open_DSM)
        self.menu.addAction(self.actionOpenDSM)

        self.menu.addSeparator()
        self.actionChangements = QAction(QIcon.fromTheme(""), "Liste des changements")
        self.actionChangements.triggered.connect(self.show_changements)
        self.menu.addAction(self.actionChangements)


        self.menu.addSeparator()
        self.actionQuit = QAction(QIcon.fromTheme("window-close"), "Quitter")
        self.actionQuit.triggered.connect(self.close)
        self.menu.addAction(self.actionQuit)

        self.setContextMenu(self.menu)

        self.setIcon(QIcon.fromTheme("favorites"))
        self.setVisible(True)

    def mount_share(self, shareName):
        """Commande pour monter un partage grace à son nom"""

        # Identifiant et mot de passe
        #user, password = self.get_credentials()

        if shareName == "Packages":
            remotePath = "{}/{}/manjaro/x86_64".format(self.nasBaseFolder, shareName)
            localPath = "/var/cache/pacman/pkg"
            self.mount(remotePath, localPath)

        remotePath = "{}/{}".format(self.nasBaseFolder, shareName)
        localPath = "{}/{}".format(self.mountpoint, shareName)

        if not os.path.exists(localPath):
            os.makedirs(localPath)

        self.mount(remotePath, localPath)

    def mount(self, remotePath, localPath):
        if os.path.ismount(localPath): self.showMessage("Partage déja monté", "Le partage selectionné est déja monté")
        else:
            command = "pkexec mount {} {}".format(remotePath, localPath)
            #command = "mount -t cifs {} {} -o username={},password={}".format(remotePath, localPath, user, password) #,uid=1000,gid=1000
            system(command)
            self.showMessage("Commande", command)

    def show_changements(self):
        dialog = QMessageBox()
        dialog.setWindowTitle("Liste des changements")
        dialog.setText("<p>" + changelogMessage.replace("\n", "<br>") + "</p>")
        dialog.exec()

    def usage_dialog(self):
        text = "<p>"
        for index, share in enumerate(self.shares):
            localPath = "{}/{}".format(self.mountpoint, share)

            # Si le dossier n'est pas vide (donc que le partage est monté)
            if os.listdir(localPath):
                size = check_output(['du', '-sh', localPath]).split()[0].decode('utf-8')
            else:
                size = "Déconnecté"

            text += "<b>{}:</b> {}<br>".format(share, size)

        text += "</p>"

        dialog = QMessageBox()
        dialog.setWindowTitle("Liste des changements")
        dialog.setText("<p>" + text + "</p>")
        dialog.exec()

    def open_DSM(self):
        open_new_tab(self.config["NAS"]["DSM_url"])

    def umount_all(self):
        command = "pkexec umount {}/*".format(self.mountpoint)
        system(command)

    def close(self):
        self.setVisible(False)
        self.daemon_running = False
        exit(0)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName("NAS-Gui")

    tray = TrayIcon()
    tray.show()

    sys.exit(app.exec_())
