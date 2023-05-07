#!/bin/env python3

import sys
import os
import configparser
import shutil

from pathlib import Path
from webbrowser import open_new_tab

from PyQt5.Qt import pyqtSlot
from PyQt5.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon, QMenu
from PyQt5.QtGui import QIcon

class SystemTrayApplication(QSystemTrayIcon):
    def __init__(self):
        super().__init__()

        self.read_config_file()

        # Chemin de base des partages sur le NAS
        self.nas_sshfs_base_folder = "{nas_ip}:".format(nas_ip=self.config["Settings"]["ip"])
        self.nas_nfs_base_folder = "{nas_ip}:".format(nas_ip=self.config["Settings"]["ip"])

        # Point de montage par défaut
        self.mountpoint = self.config["Settings"]["default_mountpoint"]

        # Protocole de montage par défaut
        self.protocols = ["nfs", "sshfs"]
        self.protocol_index = 0
        self.current_protocol = self.protocols[self.protocol_index]
        self.mount_as_read_only = True

        # On veut récupérer la liste des partages. Chaque partage est definit en tant que section dans le fichier.
        # Seule la section Settings est à retirer
        self.folders = [section for section in self.config.sections() if section != "Settings"]

        # Actions du menu
        self.actions = [
            {"name": "Ouvrir DSM ...",
             "icon": "",
             "action": self.open_dsm,
             "separator": "before"},

            {"name": "Changements",
             "icon": "",
             "action": self.show_changelog,
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
        self.config_file_path = os.path.join(Path.home(), ".config", "nas-gui.conf")

        if not os.path.isfile(self.config_file_path):
            msg = "Fichier de configuration inexistant ! <br> Veuillez renseigner la configuration dans le fichier: <br><b>{}</b>".format(
                self.config_file_path)
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

        # Bouton de modification du protocole
        self.menu.addSeparator()

        protocol_change_checkbox = self.menu.addAction(QIcon(), "")
        protocol_change_checkbox.setCheckable(False)
        protocol_change_checkbox.triggered.connect(self.on_protocol_change_checkbox_clicked)
        self.protocol_label_set_text(protocol_change_checkbox)

        # Bouton de modification de lecture seule
        read_only_mount_checkbox = self.menu.addAction(QIcon(), "")
        read_only_mount_checkbox.setCheckable(False)
        read_only_mount_checkbox.triggered.connect(self.on_mount_as_read_only_option_change_checkbox_clicked)
        self.mount_as_read_only_label_set_text(read_only_mount_checkbox)

        self.menu.addSeparator()

        # Entrées de différents partages
        for folder in self.folders:
            share_name = self.config[folder]["name"]
            volume = "volume1" if "volume" not in self.config[folder] else self.config[folder]["volume"]
            protocol = "{nfs}{separator}{sshfs}".format(
                nfs=("nfs" if self.config[folder]["nfs"] == "1" else ""),
                sshfs=("sshfs" if self.config[folder]["sshfs"] == "1" else ""),
                separator=(" / " if self.config[folder]["nfs"] == "1" and self.config[folder]["sshfs"] == "1" else "")
            )

            icon = QIcon.fromTheme(self.config[folder]["icon"])
            label = "{name} ({protocol})".format(name=share_name, protocol=protocol.upper())

            menu_action = self.menu.addAction(icon, label)
            menu_action.setCheckable(False)
            menu_action.triggered.connect(
                lambda lamdba, share_name=share_name, volume=volume,
                       menu_action=menu_action: self.mount_share(share_name, volume, menu_action))

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

    @pyqtSlot()
    def on_protocol_change_checkbox_clicked(self):
        """
        Action lorsque le bouton du protocole est cliqué

        :return: None
        """

        menu_action = self.sender()

        # Si 0 alors 1 et si 1 alors 0
        self.protocol_index = int(not self.protocol_index)
        self.current_protocol = self.protocols[self.protocol_index]

        self.protocol_label_set_text(menu_action)

        # Permet de réafficher le menu (en tant normal, le menu se ferme si l'on clique sur une des actions)
        #self.contextMenu().show()

    def protocol_label_set_text(self, menu_action):
        """
        Fonction qui permet de changer le texte du protocol utilisé dans le menu

        :param menu_action:
        :return: None
        """

        msg = "Protocole actuel: {protocol}".format(protocol=self.current_protocol)
        menu_action.setText(msg)

    @pyqtSlot()
    def on_mount_as_read_only_option_change_checkbox_clicked(self):
        menu_action = self.sender()
        self.mount_as_read_only = not self.mount_as_read_only

        self.mount_as_read_only_label_set_text(menu_action)

    def mount_as_read_only_label_set_text(self, menu_action):
        msg = "Lecture seule" if self.mount_as_read_only else "Lecture / Ecriture"
        menu_action.setText(msg)

    def get_changelog_message(self):
        files = [os.path.join(os.path.dirname(__file__), "changelog.txt"),
                 "/usr/share/nas-gui/changelog.txt"]

        for filepath in files:
            if os.path.isfile(filepath):
                with open(filepath, "r") as changelog_file:
                    return changelog_file.read()
        return ""

    def show_changelog(self):
        """
        Affiche la fenêtre des changements

        :return: None
        """

        changelog_message = self.get_changelog_message()

        msg = "<p>" + changelog_message.replace("\n", "<br>") + "</p>"
        dialog = QMessageBox(QMessageBox.Information, "Liste des changements", msg)
        dialog.exec_()

    def open_dsm(self):
        """
        Ouvre l'interface de DSM dans le navigateur par défaut

        :return: None
        """

        open_new_tab(self.config["Settings"]["DSM_url"])

    def umount(self, local_path):
        """
        Fonction qui permet de démonter le partage sélectionné

        :return: None
        """

        command = "pkexec umount {path}".format(path=local_path)
        os.system(command)

    def umount_all(self):
        """
        Fonction qui permet de démonter tous les partages

        :return: None
        """

        command = "pkexec umount {path}/*".format(path=self.mountpoint)
        os.system(command)

    def mount_share(self, share_name, volume, menu_action):
        """
        Fonction pour monter un partage grace à son nom

        :param share_name: Nom du partage à monter
        :return: None
        """

        # Pour le partage, on monte un dossier qui n'est pas conventionnel en terme de chemin
        if share_name == "Packages":
            remote_path = "{}/{}/{}/manjaro/x86_64".format(self.nas_nfs_base_folder, volume, share_name)
            local_path = "/var/cache/pacman/pkg"
            self.mount_nfs(remote_path, local_path)

        local_path = "{}/{}".format(self.mountpoint, share_name)

        # Création automatique du dossier de partage
        if not os.path.exists(local_path):
            os.makedirs(local_path)

        # FIXME: Changer le type de véfiriccation. Il est impossible pour le moment de passer de NFS à SSHDS et inversement s'il le partage est déja monté
        # Si déja monté
        if os.path.ismount(local_path):
            self.umount(local_path)

            # msg = "Le partage {} est déja monté".format(local_path)
            # self.showMessage("Partage déja monté", msg, 1000)

        # On choisi le protocol actuel pour monter le dossier. Si le partage ne peut pas etre monté avec le protocol actuel,
        # alors on repasse le monte avec l'autre protocole

        # On regarde si on peut monter le dossier avec le protocol actuel ou non
        if self.config[share_name][self.current_protocol] == "1":
            if self.current_protocol == "nfs":
                remote_path = "{}/{}/{}".format(self.nas_nfs_base_folder, volume, share_name)
                self.mount_nfs(remote_path, local_path, menu_action)

            elif self.current_protocol == "sshfs":
                remote_path = "{}/{}/{}".format(self.nas_sshfs_base_folder, volume, share_name)
                self.mount_sshfs(remote_path, local_path, menu_action)

        # Sinon, on le monte avec l'un ou l'autre

        # NFS
        elif self.config[share_name]["nfs"] == "1":
            remote_path = "{}/{}/{}".format(self.nas_nfs_base_folder, volume, share_name)
            self.mount_nfs(remote_path, local_path, menu_action)

        # sshfs
        elif self.config[share_name]["sshfs"] == "1":
            remote_path = "{}/{}/{}".format(self.nas_sshfs_base_folder, volume, share_name)
            self.mount_sshfs(remote_path, local_path, menu_action)

    def mount_nfs(self, remote_path, local_path, menu_action=None):
        """
        Fonction pour monter les partages NFS

        :param remote_path: Chemin distant
        :param local_path: Chemin local
        :menuaction: Passe le menuaction correspondant: si on à un chemin qui est bien monté, alors on coche la case
        :return: None
        """

        if os.path.ismount(local_path):
            self.showMessage("Partage déja monté", "Le partage selectionné est déja monté", msecs=5000)

        else:
            options = " -o ro " if  self.mount_as_read_only else " "
            command = "pkexec mount{options}{remote_path} {local_path}".format(options=options, remote_path=remote_path, local_path=local_path)

            # command = "mount -t cifs {} {} -o username={},password={}".format(remotePath, localPath, user, password) #,uid=1000,gid=1000
            print(command)
            return_code = os.system(command)
            if return_code == 0:
                msg_title = ""
                msg_content = "Partage: {local_path} monté via NFS\n{command}".format(local_path=local_path, command=command)

                # On coche l'action dans le menu pour indique le dossier est bien monté
                if menu_action:  # Pour contourner Package qui monte sans action
                    menu_action.setCheckable(True)
                    menu_action.setChecked(True)

            else:
                msg_title = "Erreur"
                msg_content = "Une erreur est survenue lors du montage de: {remote_path} (monté avec NFS)".format(remote_path=remote_path, local_path=local_path)

            self.showMessage(msg_title, msg_content, msecs=5000)

    def mount_sshfs(self, remote_path, local_path, menu_action):
        """
        Fonction pour monter les partages SSHFS

        :param remote_path: Chemin distant
        :param local_path: Chemin local
        :param menu_action:
        :return: None
        """
        if not shutil.which("sshfs"):
            msg = "Le montage <b>{local_path}</b> est configuré pour etre monté avec sshfs. <br>Cependant l'executable sshfs n'est pas installé.".format(
                local_path=local_path)
            qmessagebox = QMessageBox(QMessageBox.Critical, "Executable inexistant", msg)
            qmessagebox.show()
            qmessagebox.exec_()
            exit(0)

        else:
            command = "sshfs {username}@{remote_path} {local_path} -o ro".format(
                username=self.config["Settings"]["sshfs_user"], remote_path=remote_path, local_path=local_path)
            print(command)
            os.system(command)
            msg = "Partage: {local_path} monté avec SSHFS".format(local_path=local_path)
            self.showMessage("Commande", msg, msecs=5000)

        # On coche l'action dans le menu pour indique le dossier est bien monté
        if menu_action:  # Pour contourner Package qui monte sans action
            menu_action.setCheckable(True)
            menu_action.setChecked(True)

    def close(self):
        self.setVisible(False)
        exit(0)


if __name__ == '__main__':
    import cgitb
    cgitb.enable(format='text')

    app = QApplication(sys.argv)
    app.setApplicationName("NAS-Gui")
    app.setQuitOnLastWindowClosed(False)

    system_tray_application = SystemTrayApplication()
    system_tray_application.show()

    sys.exit(app.exec_())
