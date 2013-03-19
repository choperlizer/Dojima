# Dojima, a markets client.
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

import otapi
from PyQt4 import QtCore, QtGui

import dojima.model.ot.servers
import dojima.model.ot.accounts
import dojima.ui.ot.views


class ServersDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        super(ServersDialog, self).__init__(parent)

        self.server_combo = dojima.ui.ot.views.ServerComboBox()
        self.accounts_model = dojima.model.ot.accounts.OTAccountsServerModel()

        accounts_view = QtGui.QTableView()
        accounts_view.setModel(self.accounts_model)
        #accounts_view.setColumnHidden(self.accounts_model.ACCOUNT, True)
        #accounts_view.setColumnHidden(self.accounts_model.ASSET, True)
        #accounts_view.setColumnHidden(self.accounts_model.NYM, True)
        #accounts_view.setColumnHidden(self.accounts_model.SERVER, True)

        button_box = QtGui.QDialogButtonBox()
        add_server_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate('ServersDialog',
                                              "&Add Server"))
        button_box.addButton(add_server_button, button_box.ActionRole)
        button_box.addButton(button_box.Ok)

        layout = QtGui.QFormLayout()
        layout.addRow(
            QtCore.QCoreApplication.translate('ServersDialog', "Server:"),
            self.server_combo)

        layout.addRow(accounts_view)
        layout.addRow(button_box)
        self.setLayout(layout)

        self.server_combo.serverIdChanged.connect(self.accounts_model.setFilterFixedString)
        add_server_button.clicked.connect(self.showAddServerDialog)
        button_box.accepted.connect(self.accept)

    def showAddServerDialog(self):
        dialog = dojima.ui.ot.contract.ServerContractImportDialog()
        if dialog.exec_():
            dojima.model.ot.servers.model.refresh()
