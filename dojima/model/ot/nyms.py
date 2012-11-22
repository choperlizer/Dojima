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

import otapi
from PyQt4 import QtCore, QtGui

import dojima.model.ot


class OTNymsModel(QtGui.QStandardItemModel):

    def __init__(self, parent=None):
        super(OTNymsModel, self).__init__(parent)
        self.nym_ids = list()
        for i in range(otapi.OT_API_GetNymCount()):
            nym_id = otapi.OT_API_GetNym_ID(i)
            self.addNym(nym_id)

        self.setHorizontalHeaderLabels(
            QtCore.QCoreApplication.translate('OTNymsModel', "Nym"
                                              "this is the display "
                                              "header for a nym list"),)

    def addNym(self, nym_id):
        item = QtGui.QStandardItem(otapi.OT_API_GetNym_Name(nym_id))
        item.setData(nym_id, QtCore.Qt.UserRole)
        self.appendRow(item)
        self.nym_ids.append(nym_id)

    def refresh(self):
        for i in range(otapi.OT_API_GetNymCount()):
            nym_id = otapi.OT_API_GetNym_ID(i)
            if not nym_id in self.nym_ids:
                self.addNym(nym_id)


    # TODO need to overide something so the nym label can be changed
    # also, I guess there will be nyms that aren't ours floating around too

model = OTNymsModel()
