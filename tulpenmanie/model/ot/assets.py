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

class OTAssetsModel(tulpenmanie.model.ot.OTBaseModel):

    COLUMNS = 3
    ID, NAME, CONTRACT = range(COLUMNS)

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal:
            if section == self.ID:
                return QtCore.QCoreApplication.translate('OTAssetsModel',
                                                         "asset id")
            if section == self.NAME:
                return QtCore.QCoreApplication.translate('OTAssetsModel',
                                                         "name")
            if section == self.CONTRACT:
                return QtCore.QCoreApplication.translate('OTAssetsModel',
                                                         "contract")
        return section

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return 0
        if role == QtCore.Qt.TextAlignmentRole:
            return int(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        if role == QtCore.Qt.ToolTipRole:
            #TODO clean strip the base64 and return formatted XML
            ot_id = otapi.OT_API_GetAssetType_ID(index.row())
            return otapi.OT_API_GetAssetType_Contract(ot_id)
        elif role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            column = index.column()
            ot_id = otapi.OT_API_GetAssetType_ID(index.row())
            if column == 0:
                return ot_id
            if column == 1:
                return otapi.OT_API_GetAssetType_Name(ot_id)
            if column == 2:
                return otapi.OT_API_GetAssetType_Contract(ot_id)

    def setData(self, index, data, role=QtCore.Qt.EditRole):
        if not index.isValid() or role != QtCore.Qt.EditRole:
            return False
        if index.column() != 1:
            return False
        ot_id = otapi.OT_API_GetAssetType_ID(index.row())
        otapi_OT_API_SetAssetType_Name(ot_id, str(data))
        self.dataChanged.emit(index, index)
        return True

    def rowCount(self, parent=None):
        if parent and parent.isValid():
            return 0
        return otapi.OT_API_GetAssetTypeCount()

    def flags(self, index):

        flags = super(OTAssetsModel, self).flags(index)
        if index.column() == self.NAME:
            flags |= QtCore.Qt.ItemIsEditable
        return flags


class LocalOTAssetMappingModel(tulpenmanie.model.TreeModel):

    def __init__(self, parent):
        super(LocalOTAssetMappingModel, self).__init__(parent)
        self.asset_ids = list()

    def columnCount(self, parent):
        return 2

    def data(self, index, role):
        if role != QtCore.Qt.DisplayRole:
            return
        column = index.column()
        asset_id = self.asset_ids[index.row()]
        if column == 0:
            return asset_id
        if column == 1:
            return otapi.OT_API_GetAssetType_Name(asset_id)

    def insertRows(self, row, count, index):
        asset_id = otapi.OT_API_GetAssetType_ID(index.row())
        count = len(self.asset_ids)
        self.beginInsertRows(QtCore.QModelIndex(), count, count)
        self.asset_ids.append(asset_id)
        self.endInsertRows()

    def supportedDropActions(self):
        return QtCore.Qt.CopyAction

    def rowCount(self, parent):
        return len(self.asset_ids)

    def appendAsset(self, asset_id):
        current_count = len(self.asset_ids)
        self.beginInsertRows(QtCore.QModelIndex(), current_count, current_count)
        self.asset_ids.append(asset_id)
        self.endInsertRows()

    def popRow(self, row):
        self.beginRemoveRows(QtCore.QModelIndex(), row, row)
        asset_id = self.asset_ids.pop(row)
        self.endRemoveRows()
        return asset_id
