# Tulpenmanie, a graphical speculation platform.
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


class OTAssetsModel(QtCore.QAbstractTableModel):

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal:
            if section == 0:
                return QtCore.QCoreApplication.translate('OTAssetsModel',
                                                         "asset id")
            if section == 1:
                return QtCore.QCoreApplication.translate('OTAssetsModel',
                                                         "name")
            if section == 2:
                return QtCore.QCoreApplication.translate('OTAssetsModel',
                                                         "contract")
        return section


    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return 0
        if role == QtCore.Qt.TextAlignmentRole:
            return int(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        elif role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            column = index.column()
            asset_id = otapi.OT_API_GetAssetType_ID(index.row())
            if column == 0:
                return asset_id
            if column == 1:
                return otapi.OT_API_GetAssetType_Name(asset_id)
            if column == 2:
                return otapi.OT_API_GetAssetType_Contract(asset_id)

    def setData(self, index, data, role=QtCore.Qt.EditRole):
        if not index.isValid() or role != QtCore.Qt.EditRole:
            return False
        if index.column() != 1:
            return False
        asset_id = otapi.OT_API_GetAssetType_ID(index.row())
        otapi_OT_API_SetAssetType_Name(asset_id, str(data))
        self.dataChanged.emit(index, index)
        return True

    def rowCount(self, parent=None):
        if parent and parent.isValid():
            return 0
        return otapi.OT_API_GetAssetTypeCount()

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
