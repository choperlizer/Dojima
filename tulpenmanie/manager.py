# Tulpenmanie, a commodities market client.
# Copyright (C) 2012  Emery Hemingway
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
from PyQt4 import QtCore, QtGui

import tulpenmanie.network

from tulpenmanie.ui.mainwindow import MainWindow

class Manager(QtGui.QApplication):

    __instance = None

    def __init__(self, args):
        QtGui.QApplication.__init__(self, args)
        self.__class__.__instance = self
        logger = logging.getLogger(__name__)
        QtCore.QObject.manager = self

        self.setOrganizationName("Emery Hemingway")
        self.setApplicationName("tulpenmanie")
        self.setApplicationVersion('0.3.0')

        # Network stuff
        self.network_manager = tulpenmanie.network.NetworkAccessManager()

        # Start the gui
        self.window = MainWindow()

    def run(self):
        self.window.show()
        res = self.exec_()
        self.exit()
        return res