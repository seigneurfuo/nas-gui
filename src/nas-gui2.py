#!/bin/env python

import sys
import os
import configparser

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon, QMenu, QAction

from os import system
from time import sleep
from threading import Thread
from psutil import process_iter
from subprocess import check_output
from webbrowser import open_new_tab

changelogMessage = """
<b>2019-07-20</b>
 - Ajout d'une entrée "changements"
 - Création automatique des répertoires de montage s'il n'existent pas
 - Ajout d'un choix qui permet d'afficher l'espace utilisé pour chaque partage
 - Ajout d'un lien pour acceder à la page DSM
"""

class App(QSystemTrayIcon):
    def __init__(self):
        super().__init__(QIcon.fromTheme("favorites"))

        self.isPackageMount = False

        self.config = configparser.ConfigParser()
        self.config.read("/home/seigneurfuo/nas-gui.ini")

        self.dsm_url = self.config["common"]["dsm_url"]
        self.nas_ip = self.config["common"]["ip"]
        self.nasBaseFolder = "{}:/volume1/".format(self.nas_ip)

        self.shares = [share for share in self.config.sections() if share.startswith("share")]
        self.shares_menu_list = list()

        self.initUI()

        Thread(target=self.daemon).start()

    def daemon(self):
        running = True
        while running:
            for proc in process_iter():
                if proc.name() == "pamac-manager":
                    self.mount_share("Packages")
                    running = False

            sleep(1)


    def initUI(self):
        self.menu = QMenu()

        for share in self.shares:
            name = self.config[share]["name"]
            icon = self.config[share]["icon"]

            print(icon, " - ", name)

            # On est (obligé ?) de faire ça en deux étapes en passant par une liste pour l'affectation dynamique
            action = QAction(QIcon.fromTheme(icon), name)
            action.triggered.connect(lambda: self.mount_share(name))
            self.shares_menu_list.append(action)
            self.menu.addAction(self.shares_menu_list[-1])


        # self.menu.addSeparator()
        #
        # self.actionUnmountAll = QAction(QIcon.fromTheme("window-close"), "Démonter TOUS les partages")
        # self.actionUnmountAll.triggered.connect(self.umount_all)
        # self.menu.addAction(self.actionUnmountAll)
        #
        # self.menu.addSeparator()
        #
        # self.actionUsage= QAction(QIcon.fromTheme(""), "Utilisation ...")
        # self.actionUsage.triggered.connect(self.usage_dialog)
        #
        # self.action_open_dsm = QAction(QIcon.fromTheme(""), "Ouvrir DSM ...")
        # self.action_open_dsm.triggered.connect(self.open_DSM)
        # self.menu.addAction(self.action_open_dsm)
        #
        # self.menu.addSeparator()
        #
        # self.actionChangements = QAction(QIcon.fromTheme(""), "Liste des changements")
        # self.actionChangements.triggered.connect(self.show_changements)
        # self.menu.addAction(self.actionChangements)
        #
        #
        # self.menu.addSeparator()
        #

        self.actionQuit = QAction(QIcon.fromTheme("window-close"), "Quitter")
        self.actionQuit.triggered.connect(self.close)
        self.menu.addAction(self.actionQuit)

        self.setContextMenu(self.menu)
        self.setVisible(True)

    @pyqtSlot()
    def mount_share(self, share_name):
        """Commandes pour monter un partage grace à son nom"""

        print(self.sender())
        exit(0)

        if share_name == "Packages":
            remote_path = "{}/{}/manjaro/officiels".format(self.nasBaseFolder, share_name)
            local_path = "/var/cache/pacman/pkg"
            self.mount(remote_path, local_path)

        remote_path = self.config[share_name]["remote"] #"{}/{}".format(self.nasBaseFolder, shareName)
        local_path = self.config[share_name]["local"] #"{}/{}".format(self.mountpoint, shareName)

        if not os.path.exists(local_path):
            os.makedirs(local_path)

        self.mount(remote_path, local_path)

    def mount(self, remotePath, localPath):
        if os.path.ismount(localPath):
            self.showMessage("Partage déja monté", "Le partage selectionné est déja monté")

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
        open_new_tab(self.dsm_url)

    def umount_all(self):
        command = "pkexec umount {}/*".format(self.mountpoint)
        system(command)

    def close(self):
        self.setVisible(False)
        exit(0)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainwindow = App()
    mainwindow.show()
    sys.exit(app.exec_())
