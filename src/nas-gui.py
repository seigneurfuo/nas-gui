#!/bin/env python3

import sys
import os
import configparser

from pathlib import Path
from webbrowser import open_new_tab

# PyQt5
from PyQt5.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon

changelog_message = """
<b>2020-05-31</b>
 - Possibilité de configurer le mode de montage (SMB ou NFS dans le fichier<br>de configuration

<b>2020-05-01</b>
 - Ajout d'un nouveau système dynamique pour la création des entrées dans le menu
 - Déplacement de toutes les informations en dur dans le fichier de configuration<br>(le seul encore en dur est le cache de pacman
 - Nettoyage du code

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
 - Création automatique des répertoires de montage s'ils n'existent pas
 - Ajout d'un choix qui permet d'afficher l'espace utilisé pour chaque partage
 - Ajout d'un lien pour acceder à la page DSM
"""


class TrayIcon(QSystemTrayIcon):
    def __init__(self):
        super().__init__()

        self.read_config_file()

        # Chemin de base des partages sur le NAS
        self.nas_smb_base_folder = ""
        self.nas_nfs_base_folder = "{nas_ip}:/volume1".format(nas_ip=self.config["Settings"]["ip"])

        # Point de montage par défaut
        self.mountpoint = self.config["Settings"]["default_mountpoint"]

        # On veut récupérer la liste des partages. Chaque partage est definit en tant que section dans le fichier.
        # Seule la section Settings est à retirer
        self.folders = [section for section in self.config.sections() if section != "Settings"]

        # Actions du menu
        self.actions = [
            {"name":"Ouvrir DSM ...",
                "icon": "",
                "action": self.open_DSM,
                "separator": "before"},

            {"name": "Changements",
                 "icon": "",
                 "action": self.show_changements,
                 "separator": None},

            {"name": "Démonter TOUS les partages",
                 "icon": "window-close",
                 "action": self.umount_all,
                 "separator": "before"},

            {"name": "Quitter",
                 "icon": "window-close",
                 "action": self.close,
                 "separator": "before"}
        ]

        self.init_ui()


    def read_config_file(self):
        self.config = configparser.ConfigParser()
        self.config_file_path = os.path.join(Path.home(),".cdonfig", "nas-gui.conf")

        if not os.path.isfile(self.config_file_path):
            msg = "Fichier de configuration inexistant ! <br> Veuillez renseigner la configuration dans le fichier: <br><b>{}</b>".format(self.config_file_path)
            qmessagebox = QMessageBox(QMessageBox.Critical, "Fichier de configuration inexistant", msg)
            qmessagebox.show()
            qmessagebox.exec_()
            exit(0)

        self.config.read(self.config_file_path)


    def init_ui(self):
        """
        Fonction d'initialisation de l'interface

        :return: None
        """

        self.menu = QMenu()

        # Entrées de différents partages
        for folder in self.folders:
            share_name = self.config[folder]["name"]
            protocol = self.config[folder]["protocol"]
            icon = QIcon.fromTheme(self.config[folder]["icon"])
            label = "{name} ({protocol})".format(name=share_name, protocol=protocol.upper())

            menu_action = self.menu.addAction(icon, label)
            menu_action.triggered.connect(lambda lamdba, share_name=share_name: self.mount_share(share_name))

        self.menu.addSeparator()

        # Entrées des différentes actions
        for action in self.actions:
            if action["separator"] == "before":
                self.menu.addSeparator()

            menu_action = self.menu.addAction(QIcon.fromTheme(action["icon"]), action["name"])
            menu_action.triggered.connect(action["action"])

            if action["separator"] == "after":
                self.menu.addSeparator()

        # Application des élements au menu
        self.setContextMenu(self.menu)

        self.setIcon(QIcon.fromTheme(self.config["Settings"]["tray_icon"]))
        self.setVisible(True)


    def show_changements(self):
        """
        Affiche la fenêtre des changements

        :return: None
        """

        dialog = QMessageBox()
        dialog.setWindowTitle("Changements")
        dialog.setText("<p>" + changelog_message.replace("\n", "<br>") + "</p>")
        dialog.exec()


    def open_DSM(self):
        """
        Ouvre l'interface de DSM dans le navigateur par défaut

        :return: None
        """

        open_new_tab(self.config["Settings"]["DSM_url"])


    def umount_all(self):
        """
        Fonction qui permet de démonter tous les partages

        :return: None
        """

        command = "pkexec umount {path}/*".format(path=self.mountpoint)
        os.system(command)


    def mount_share(self, share_name):
        """
        Fonction pour monter un partage grace à son nom

        :param share_name: Nom du partage à monter
        :return: None
        """

        # Identifiant et mot de passe
        #user, password = self.get_credentials()

        # Pour le partage, on monte un dossier qui n'est pas conventionnel en terme de chemin
        if share_name == "Packages":
            remote_path = "{}/{}/manjaro/x86_64".format(self.nas_nfs_base_folder, share_name)
            local_path = "/var/cache/pacman/pkg"
            self.mount_nfs(remote_path, local_path)


        local_path = "{}/{}".format(self.mountpoint, share_name)
        # Création automatique du dossier de partage
        if not os.path.exists(local_path):
            os.makedirs(local_path)

        # SMB
        if  self.config[share_name]["protocol"] == "smb":
            remote_path = "{}/{}".format(self.nas_smb_base_folder, share_name)
            self.mount_smb(remote_path, local_path)

        # NFS
        else:
            remote_path = "{}/{}".format(self.nas_nfs_base_folder, share_name)
            self.mount_nfs(remote_path, local_path)


    def mount_nfs(self, remote_path, local_path):
        """
        Fonction qui permet de monter un chemin distant

        :param remote_path: Chemin distant
        :param local_path: Chemin local
        :return: None
        """

        if os.path.ismount(local_path):
            self.showMessage("Partage déja monté", "Le partage selectionné est déja monté", 1000)

        else:
            command = "pkexec mount {} {}".format(remote_path, local_path)
            #command = "mount -t cifs {} {} -o username={},password={}".format(remotePath, localPath, user, password) #,uid=1000,gid=1000
            os.system(command)
            self.showMessage("Commande", command, 1000)

    def mount_smb(self, remote_path, local_path):
        pass


    def close(self):
        self.setVisible(False)
        exit(0)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName("NAS-Gui")

    tray = TrayIcon()
    tray.show()

    sys.exit(app.exec_())