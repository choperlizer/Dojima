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
from PyQt4 import QtCore

import dojima.model
import dojima.model.ot


class OTServersSimpleModel(dojima.model.ot.OTBaseModel):
    """A stateless server model"""

    COLUMNS = 2
    ID, NAME = list(range(COLUMNS))

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal:
            if section == self.ID:
                return QtCore.QCoreApplication.translate('OTServersSimpleModel',
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
            ot_id = otapi.OTAPI_Basic_GetServer_ID(index.row())
            return otapi.OTAPI_Basic_GetServer_Contract(ot_id)

        elif role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            column = index.column()
            ot_id = otapi.OTAPI_Basic_GetServer_ID(index.row())
            if column == self.ID:
                return ot_id
            if column == self.NAME:
                return otapi.OTAPI_Basic_GetServer_Name(ot_id)

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if not index.isValid() or role != QtCore.Qt.EditRole:
            return False
        if index.column() != self.NAME:
            return False
        ot_id = otapi.OTAPI_Basic_GetServer_ID(index.row())
        if otapi_OTAPI_Basic_SetServer_Name(ot_id, value) == 1:
            self.parentItem.dataChanged(index, index)
            return True
        return False

    def rowCount(self, parent=None):
        if parent and parent.isValid():
            return 0
        return otapi.OTAPI_Basic_GetServerCount()


class OTServersTreeModel(dojima.model.TreeModel):

    def __init__(self, parent=None):
        super(OTServersTreeModel, self).__init__(parent)
        self.rootItem = RootItem(None, self)
        self.rootItem.revert()

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return ("ID", "base", "counter")
        return None


class RootItem(dojima.model.TreeItem):

    def revert(self):
        # TODO handle missing servers
        for i in range(otapi.OTAPI_Basic_GetServerCount()):
            server_id = otapi.OTAPI_Basic_GetServer_ID(i)
            if server_id not in self.childIndexes:
                server_item = ServerItem(server_id, self)
                self.appendChild(server_id, server_item)
        return True

    def columnCount(self):
        return 4


class ServerItem(object):

    COLUMNS = 3
    ID, NAME = 0, 1

    def __init__(self, server_id, parent):
        self.server_id = server_id
        self.name = otapi.OTAPI_Basic_GetServer_Name(server_id)
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
        return 5

    def data(self, column, role=QtCore.Qt.DisplayRole):
        if role != QtCore.Qt.DisplayRole:
            return None
        if column == self.ID:
            return self.server_id
        if column == self.NAME:
            return self.name

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
        server_id = otapi.OTAPI_Basic_GetServer_ID(self.row)
        if otapi_OTAPI_Basic_SetServer_Name(self.server_id, value) == 1:
            return True
        return False


class MarketItem(object):

    COLUMNS = 3
    ID, BASE, COUNTER = list(range(COLUMNS))
    # Maybe add an volume column

    def __init__(self, market_data, parent):
        self.market_data = market_data
        self.parentItem = parent

    def childCount(self):
        return 0

    def columnCount(self):
        return self.COLUMNS

    def data(self, column, role=QtCore.Qt.DisplayRole):
        if column == self.ID:
            if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.UserRole:
                return self.market_data.market_id

        if column == self.BASE:
            if role == QtCore.Qt.DisplayRole:
                return otapi.OTAPI_Basic_GetAssetType_Name(
                    self.market_data.asset_type_id)
            if role == QtCore.Qt.UserRole:
                return self.market_data.asset_type_id

        if column == self.COUNTER:
            if role == QtCore.Qt.DisplayRole:
                return otapi.OTAPI_Basic_GetAssetType_Name(
                    self.market_data.currency_type_id)
            if role == QtCore.Qt.UserRole:
                return self.market_data.currency_type_id
                    
    def flags(self):
        return (QtCore.Qt.ItemIsEnabled)

    def row(self):
        return self.parent.childIndexes.index(self.server_data.market_id)

    def setData(self, index, value, role=QtCore.Qt.CheckStateRole):
        if index.column() != self.ENABLE or role != QtCore.Qt.CheckStateRole:
            return False
        self.check_state = value
        return True

    def submit(self):
        # find our market id, our server id, and set that in the markets_model

        # first resolve the base and counter to local uuids
        pass

    def parent(self):
        return self.parentItem
