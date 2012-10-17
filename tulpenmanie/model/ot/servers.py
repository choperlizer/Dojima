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


class OTServersSimpleModel(tulpenmanie.model.ot.OTBaseModel):
    """A stateless server model"""

    COLUMNS = 2
    ID, NAME = range(COLUMNS)

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal:
            if section == self.ID:
                return QtCore.QCoreApplication.translate('OTServersSimlpeModel',
                                                         "server id")
            if section == self.NAME:
                return QtCore.QCoreApplication.translate('OTServersSimpleModel',
                                                         "name")
        return section

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return 0

        if role == QtCore.Qt.TextAlignmentRole:
            return int(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        elif role == QtCore.Qt.ToolTipRole:
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

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if not index.isValid() or role != QtCore.Qt.EditRole:
            return False
        if index.column() != self.NAME:
            return False
        ot_id = otapi.OT_API_GetServer_ID(index.row())
        if otapi_OT_API_SetServer_Name(ot_id, str(value)) == 1:
            self.parentItem.dataChanged(index, index)
            return True
        return False

    def rowCount(self, parent=None):
        if parent and parent.isValid():
            return 0
        return otapi.OT_API_GetServerCount()


class OTServersComplexModel(QtCore.QAbstractItemModel):

    def __init__(self, parent=None):
        super(OTServersComplexModel, self).__init__(parent)

        self.root_item = RootItem(self)
        self.revert()

    def columnCount(self, parent):
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self.root_item.columnCount()

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None

        item = index.internalPointer()
        return item.data(index.column(), role)

    # This might need to ask the items for their flags in the future
    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        item = index.internalPointer()
        return item.flags()

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.root_item.data(section)
        return None

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            parentItem = self.root_item
        else:
            parentItem = parent.internalPointer()

        child_item = parentItem.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        else:
            return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        child_item = index.internalPointer()
        parentItem = child_item.parent()
        if parentItem == self.root_item:
            return QtCore.QModelIndex()
        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.root_item
        else:
            parentItem = parent.internalPointer()
        return parentItem.childCount()

    def revert(self):
        for i in range(otapi.OT_API_GetServerCount()):
            server_id = otapi.OT_API_GetServer_ID(i)
            if server_id not in self.root_item.childIndexes:
                server_item = ServerItem(server_id, self.root_item)
                self.root_item.appendChild(server_id, server_item)

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if not index.isValid():
            return False

        item = index.internalPointer()
        return item.setData(index, value, role)


class RootItem(object):
    def __init__(self, parent):
        self.parentItem = parent
        self.childIndexes = list()
        self.childItems = list()

    def appendChild(self, item_id, item):
        self.childIndexes.append(item_id)
        self.childItems.append(item)

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def columnCount(self):
        # This is hardcoded to the amount of columns in the biggest child
        return 4

    def data(self, column, role=None):
        return None

    def dataChanged(self, topLeft, bottomRight):
        self.parentItem.dataChanged.emit(topLeft, bottomRight)

    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)

        return 0

class ServerItem(object):

    COLUMNS = 4
    ID, NAME = 0, 1

    def __init__(self, server_id, parent):
        self.server_id = server_id
        self.name = otapi.OT_API_GetServer_Name(server_id)
        self.parentItem = parent
        self.childIndexes = list()
        self.childItems = list()
        # Try and make it so that we can subclass this item and then change
        # revert or init for different models, like accounts

        # TODO, this has not been checked to make sure it works, it needs to
        # be tested with a clean wallet
        if otapi.Exists('markets', self.server_id, 'market_data.bin'):
            self.storable = otapi.QueryObject(otapi.STORED_OBJ_MARKET_LIST,
                                              'markets', self.server_id,
                                              'market_data.bin')
        else:
            self.storable = otapi.CreateObject(otapi.STORED_OBJ_MARKET_LIST)
        self.market_list = otapi.MarketList.ot_dynamic_cast(self.storable)
        self.revert()

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def columnCount(self):
        return self.COLUMNS

    def data(self, column, role=QtCore.Qt.DisplayRole):
        if role != QtCore.Qt.DisplayRole:
            return None
        if column == self.ID:
            return self.server_id
        if column == self.NAME:
            return self.name

    def dataChanged(self, topLeft, bottomRight):
        self.parentItem.dataChanged(topLeft, bottomRight)

    def flags(self):
        return QtCore.Qt.ItemIsEnabled

    def row(self):
        return self.parentItem.childIndexes.index(self.server_id)

    def parent(self):
        return self.parentItem

    def revert(self):
        for i in range(self.market_list.GetMarketDataCount()):
            market_data = self.market_list.GetMarketData(i)
            market_id = market_data.market_id
            if market_id not in self.childIndexes:
                market_item = MarketItem(market_data, self)
                self.childItems.append(market_item)
                self.childIndexes.append(market_data.market_id)

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if not index.isValid() or role != QtCore.Qt.EditRole:
            return False
        if index.column() != self.NAME:
            return False
        server_id = otapi.OT_API_GetServer_ID(self.row)
        if otapi_OT_API_SetServer_Name(self.server_id, str(value)) == 1:
            self.dataChanged.emit(index, index)
            return True
        return False


class MarketItem(object):

    COLUMNS = 4
    ID, BASE, COUNTER, ENABLE = range(COLUMNS)
    # Maybe add an volume column
    #TODO disable markets with unknown currencies/assets/commodities

    def __init__(self, market_data, parent):
        self.market_data = market_data
        self.parentItem = parent
        self.check_state = QtCore.Qt.Checked

    def checkState(self):
        return self.check_state

    def setCheckState(self, state):
        self.check_state = state

    def childCount(self):
        return 0

    def columnCount(self):
        return self.COLUMNS

    def data(self, column, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if column == self.ID:
                return self.market_data.asset_type_id

            if column == self.BASE:
                return otapi.OT_API_GetAssetType_Name(
                    self.market_data.asset_type_id)

            if column == self.COUNTER:
                return otapi.OT_API_GetAssetType_Name(
                    self.market_data.currency_type_id)

        elif column == self.ENABLE and role == QtCore.Qt.CheckStateRole:
            return self.checkState()

    def flags(self):
        return (QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable)

    def row(self):
        return self.parent.childIndexes.index(self.server_data.market_id)

    def setData(self, index, value, role=QtCore.Qt.CheckStateRole):
        if index.column() != self.ENABLE or role != QtCore.Qt.CheckStateRole:
            print "setData was not the right role"
            return False
        self.check_state = value
        self.parentItem.dataChanged(index, index)
        print "we've emmitted and stuff"
        print value
        return True

    def parent(self):
        return self.parentItem
