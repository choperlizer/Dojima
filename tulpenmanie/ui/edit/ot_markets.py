# Tulpenmanie, a markets client.
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

from PyQt4 import QtCore, QtGui

import tulpenmanie.model.ot.servers

class EditWidget(QtGui.QWidget):

    def __init__(self, parent=None):
        super(EditWidget, self).__init__(parent)

        self.markets_view = QtGui.QTreeView()
        self.markets_view.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.servers_model = tulpenmanie.model.ot.servers.OTServersTreeModel()
        self.markets_view.setModel(self.servers_model)
        #TODO make a loop to resize past column 0
        self.markets_view.resizeColumnToContents(1)
        self.markets_view.resizeColumnToContents(2)
        self.markets_view.resizeColumnToContents(3)

        map_to_commodity_action = QtGui.QAction(
            QtCore.QCoreApplication.translate('EditWidget', "map to..."),
            self, triggered=self.map_to_commodity)

        self.markets_view.addAction(map_to_commodity_action)
        self.markets_view.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

        layout = QtGui.QGridLayout()
        layout.addWidget(self.markets_view)

        self.setLayout(layout)

    def map_to_commodity(self):
        index = self.markets_view.currentIndex()
        asset_id = self.servers_model.data(index, QtCore.Qt.UserRole)
        dialog = tulpenmanie.ui.edit.ot_assets.AssetMappingDialog(asset_id, self)
        dialog.exec_()
