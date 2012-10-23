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

import logging

import otapi
from PyQt4 import QtCore, QtGui

import tulpenmanie.model.ot


logger = logging.getLogger(__name__)


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


class OTAssetsSettingsModel(QtGui.QStandardItemModel):

    COLUMNS = 3
    ASSET_ID, LOCAL_ID, FACTOR = range(COLUMNS)
    settings_group = "OT-assets"
    settings_map = (("commodity", LOCAL_ID), ("factor", FACTOR))

    def __init__(self, parent=None):
        super(OTAssetsSettingsModel, self).__init__(parent)
        self.load()

    def load(self):
        logger.debug("reverting OT assets settings")
        settings = QtCore.QSettings()
        settings.beginGroup(self.settings_group)
        for row, asset_id in enumerate(settings.childGroups()):
            item = QtGui.QStandardItem(asset_id)
            self.setItem(row, self.ASSET_ID, item)

            settings.beginGroup(asset_id)
            for key, column in self.settings_map:
                value = settings.value(key)
                item = QtGui.QStandardItem(value)
                self.setItem(row, column, item)
            settings.endGroup()
        return True

    def submit(self):
        logger.debug("submitting OT assets settings")
        settings = QtCore.QSettings()
        settings.beginGroup(self.settings_group)
        settings.remove('')
        for row in range(self.rowCount()):
            asset_id = self.item(row, self.ASSET_ID).text()
            settings.beginGroup(asset_id)
            for key, column in self.settings_map:
                value = self.item(row, column).text()
                settings.setValue(key, value)
            settings.endGroup()
        return True
