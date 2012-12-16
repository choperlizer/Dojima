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

import dojima.model.ot


logger = logging.getLogger(__name__)


class OTAssetsModel(QtGui.QStandardItemModel):

    def __init__(self, parent=None):
        super(OTAssetsModel, self).__init__(parent)
        self.asset_ids = list()
        for i in range(otapi.OTAPI_Basic_GetAssetTypeCount()):
            asset_id = otapi.OTAPI_Basic_GetAssetType_ID(i)
            self.addAsset(asset_id)

    def addAsset(self, asset_id):
        item = QtGui.QStandardItem(otapi.OTAPI_Basic_GetAssetType_Name(asset_id))
        item.setData(asset_id, QtCore.Qt.UserRole)
        self.appendRow(item)
        self.asset_ids.append(asset_id)

    def refresh(self):
        for i in range(otapi.OTAPI_Basic_GetAssetTypeCount()):
            asset_id = otapi.OTAPI_Basic_GetAssetType_ID(i)
            if asset_id not in self.asset_ids:
                self.addAsset(asset_id)


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
