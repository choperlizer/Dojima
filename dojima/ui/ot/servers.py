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


class ServersDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        super(ServersDialog, self).__init__(parent)
        self.servers = list()

        _accounts_model = dojima.model.ot.accounts.OTAccountsModel()
        self.accounts_model = QtGui.QSortFilterProxyModel()
        self.accounts_model.setSourceModel(_accounts_model)
        self.accounts_model.setFilterKeyColumn(_accounts_model.SERVER_ID)

        self.server_combo = QtGui.QComboBox()
        for row in range(otapi.OT_API_GetServerCount()):
            server_id = otapi.OT_API_GetServer_ID(row)
            self.servers.append(server_id)
            self.server_combo.addItem(otapi.OT_API_GetServer_Name(server_id))

        accounts_view = QtGui.QTableView()
        accounts_view.setModel(self.accounts_model)
        accounts_view.setColumnHidden(_accounts_model.ID, True)
        accounts_view.setColumnHidden(_accounts_model.ASSET_ID, True)
        accounts_view.setColumnHidden(_accounts_model.NYM_ID, True)
        accounts_view.setColumnHidden(_accounts_model.SERVER_ID, True)
        accounts_view.setColumnHidden(_accounts_model.SERVER_NAME, True)

        button_box = QtGui.QDialogButtonBox()
        add_server_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate('ServersDialog',
                                              "&Add Server"))
        button_box.addButton(add_server_button, button_box.ActionRole)
        button_box.addButton(button_box.Ok)

        top_form_layout = QtGui.QFormLayout()
        top_form_layout.addRow(QtCore.QCoreApplication.translate('ServersDialog',
                                                                 "Server:"),
                               self.server_combo)

        layout = QtGui.QVBoxLayout()
        layout.addLayout(top_form_layout)
        layout.addWidget(accounts_view)
        layout.addWidget(button_box)
        self.setLayout(layout)

        self.server_combo.currentIndexChanged.connect(self.serverChanged)
        add_server_button.clicked.connect(self.showAddServerDialog)
        button_box.accepted.connect(self.accept)

        self.serverChanged(0)

    def refreshServers(self):
        for row in range(otapi.OT_API_GetServerCount()):
            server_id = otapi.OT_API_GetServer_ID(row)
            if server_id in self.servers: continue
            self.servers.append(server_id)
            self.server_combo.addItem(otapi.OT_API_GetServer_Name(server_id))

    def serverChanged(self, row):
        server_id = self.servers[row]
        self.accounts_model.setFilterFixedString(server_id)

    def showAddServerDialog(self):
        dialog = dojima.ui.ot.contract.ServerContractImportDialog()
        if dialog.exec_():
            self.refreshServers()
