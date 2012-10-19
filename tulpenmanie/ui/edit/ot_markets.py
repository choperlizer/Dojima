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

        markets_view = QtGui.QTreeView()
        model = tulpenmanie.model.ot.servers.OTServersTreeModel()
        markets_view.setModel(model)
        #TODO make a loop to resize past column 0
        markets_view.resizeColumnToContents(1)
        markets_view.resizeColumnToContents(2)
        markets_view.resizeColumnToContents(3)

        layout = QtGui.QGridLayout()
        layout.addWidget(markets_view)

        self.setLayout(layout)
