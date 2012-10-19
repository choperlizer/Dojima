# -*- coding: utf-8 -*-
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

import tulpenmanie.model.base


logger = logging.getLogger(__name__)
SETTINGS_GROUP= 'commodities'


class CommoditiesModel(tulpenmanie.model.TreeModel):

    ID, NAME, PREFIX, SUFFIX, PRECISION = range(5)

    def __init__(self, parent=None):
        super(CommoditiesModel, self).__init__(parent)
        self.indexes = list()
        self.objects = list()
        self.rootItem = CommoditiesRootItem(self)
        self.revert()

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        item = index.internalPointer()
        return item.flags(index)

    def revert(self):
        logger.debug("reverting commodities settings")
        settings = QtCore.QSettings()
        settings.beginGroup(SETTINGS_GROUP)
        commodity_ids = settings.childGroups()
        for commodity_id in commodity_ids:
            settings.beginGroup(commodity_id)
            name = settings.value('name')
            prefix = settings.value('prefix')
            suffix = settings.value('suffix')
            precision = settings.value('precision').toInt()
            if precision[1] is True:
                precision = precision[0]
            else:
                precision = 4
            settings.endGroup()
            commodity_item = CommodityItem(commodity_id, self.rootItem,
                                           name, prefix, suffix, precision)
            self.rootItem.appendChild(commodity_id, commodity_item)
        return True

    def submit(self):
        logger.debug("submitting commodities settings")
        settings = QtCore.QSettings()
        settings.beginGroup(SETTINGS_GROUP)
        settings.remove('')
        for item in self.rootItem.childItems:
            settings.beginGroup(item.id)
            settings.setValue('name', item.name)
            settings.setValue('prefix', item.prefix)
            settings.setValue('prefix', item.prefix)
            settings.setValue('suffix', item.suffix)
            settings.setValue('precision', item.precision)
            settings.endGroup()
        return True

    def new_commodity(self):
        uuid = QtCore.QUuid.createUuid().toString()[1:-1]
        item = CommodityItem(uuid, self.rootItem)
        self.rootItem.appendChild(uuid, item)
        return item.row()


class CommoditiesRootItem(tulpenmanie.model.RootItem):

    def columnCount(self):
        return 5


class CommodityItem(tulpenmanie.model.TreeItem):

    def __init__(self, identifier, parent,
                 name="", prefix="", suffix="", precision=4):
        self.id = identifier
        self.name = name
        self.prefix = prefix
        self.suffix = suffix
        self.precision = precision
        self.parentItem = parent
        self.childIndexes = list()
        self.childItems = list()

    def appendAsset(self, asset_id):
        asset_item = AssetItem(asset_id, self)
        count = len(self.childIndexes)
        self.beginInsertRows(count, count)
        self.appendChild(asset_id, asset_item)
        self.endInsertColumns()

    def columnCount(self):
        return self.parentItem.columnCount()

    def flags(self, index):
        return (QtCore.Qt.ItemIsSelectable |
                QtCore.Qt.ItemIsEditable |
                QtCore.Qt.ItemIsEnabled)

    def data(self, column, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            if column == 0:
                return self.id
            elif column == 1:
                return self.name
            elif column == 2:
                return self.prefix
            elif column == 3:
                return self.suffix
            elif column == 4:
                return self.precision

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        column = index.column()
        if column == 0:   self.id = value
        elif column == 1: self.name = value
        elif column == 2: self.prefix = value
        elif column == 3: self.suffix = value
        elif column == 4: self.precision = value
        else: return False

        return True


class AssetItem(tulpenmanie.model.TreeItem):

    def __init__(self, asset_id, parent):
        self.asset_id = asset_id
        self.parentItem = parent

    def data(self, column, role=QtCore.Qt.DisplayRole):
        if role != QtCore.Qt.DisplayRole:
            return None
        if column == 0: return asset_id
        if column == 1:
            return otapi.OT_API_GetAssetType_Name(self.asset_id)

    def flags(self, index):
        return (QtCore.Qt.ItemIsSelectable |
                QtCore.Qt.ItemIsEnabled)


#can't instantiate until after we have an app
commodities_model = CommoditiesModel()
