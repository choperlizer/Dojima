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

import otapi
from PyQt4 import QtCore

import tulpenmanie.model.ot

class OTServersModel(tulpenmanie.model.ot.OTBaseModel):

    COLUMNS = 3
    ID, NAME, CONTRACT = range(COLUMNS)

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal:
            if section == self.ID:
                return QtCore.QCoreApplication.translate('OTServersModel',
                                                         "server id")
            if section == self.NAME:
                return QtCore.QCoreApplication.translate('OTServerssModel',
                                                         "name")
            if section == self.CONTRACT:
                return QtCore.QCoreApplication.translate('OTServersModel',
                                                         "contract")
        return section

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return 0
        if role == QtCore.Qt.TextAlignmentRole:
            return int(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        if role == QtCore.Qt.ToolTipRole:
            #TODO clean strip the base64 and return formatted XML
            ot_id = otapi.OT_API_GetServer_ID(index.row())
            return otapi.OT_API_GetServer_Contract(ot_id)
        elif role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            column = index.column()
            ot_id = otapi.OT_API_GetOt_id(index.row())
            if column == self.ID:
                return ot_id
            if column == self.NAME:
                return otapi.OT_API_GetServer_Name(ot_id)
            if column == self.CONTRACT:
                return otapi.OT_API_GetServer_Contract(ot_id)

    def setData(self, index, data, role=QtCore.Qt.EditRole):
        if not index.isValid() or role != QtCore.Qt.EditRole:
            return False
        if index.column() != self.NAME:
            return False
        ot_id = otapi.OT_API_GetServer_ID(index.row())
        otapi_OT_API_SetServer_Name(ot_id, str(data))
        self.dataChanged.emit(index, index)
        return True

    def rowCount(self, parent=None):
        if parent and parent.isValid():
            return 0
        return otapi.OT_API_GetServerCount()

    def columnCount(self, parent=None):
        if parent and parent.isValid():
            return 0
        return 2

    def parent(self):
        return QtCore.QModelIndex()

""" def flags(self, index):
        flags = super(_MyTableModel, self).flags(index)
        flags |= QtCore.Qt.ItemIsEditable
        return flags
"""
