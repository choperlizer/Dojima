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


class OTMarketsModel(QtGui.QStandardItemModel):

    BASE = 0
    COUNTER = 1
    SCALE = 2
    VOLUME = 3

    unknown_asset_string = QtCore.QCoreApplication.translate("OTMarketsModel",
                                                             "Unknown Asset",
                                                             "This is placeholder text for "
                                                             "when a contract is found in "
                                                             "markets model but a local copy "
                                                             "of the contract does not exist.")

    def __init__(self, server_id, parent=None):
        super(OTMarketsModel, self).__init__(parent)
        self.server_id = server_id
        self.market_ids = list()

        storable = otapi.QueryObject(otapi.STORED_OBJ_MARKET_LIST, 'markets',
                                     self.server_id, 'market_data.bin')
        if not storable: return

        market_list = otapi.MarketList.ot_dynamic_cast(storable)
        for i in range(market_list.GetMarketDataCount()):
            data = market_list.GetMarketData(i)
            self.addRow(data, i)

    def addRow(self, data, row=None):
        if not row:
            row = self.rowCount()

        self.market_ids.append(data.market_id)

        asset_name = otapi.OTAPI_Basic_GetAssetType_Name(data.asset_type_id)
        if not asset_name:
            asset_name = self.unknown_asset_string
        item = QtGui.QStandardItem(asset_name)
        item.setData(data.asset_type_id, QtCore.Qt.UserRole)
        self.setItem(row, self.BASE, item)

        asset_name = otapi.OTAPI_Basic_GetAssetType_Name(data.currency_type_id)
        if not asset_name:
            asset_name = self.unknown_asset_string
        item = QtGui.QStandardItem(asset_name)
        item.setData(data.currency_type_id, QtCore.Qt.UserRole)
        self.setItem(row, self.COUNTER, item)

        item = QtGui.QStandardItem(data.scale)
        self.setItem(row, self.SCALE, item)

        item = QtGui.QStandardItem(data.volume_assets)
        self.setItem(row, self.VOLUME, item)

    def getMarketId(self, row):
        return self.market_ids[row]

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                if section == self.BASE:
                    return QtCore.QCoreApplication.translate('OTMarketsModel',
                                                             "Base")
                if section == self.COUNTER:
                    return QtCore.QCoreApplication.translate('OTMarketsModel',
                                                             "Counter")
                if section == self.SCALE:
                    return QtCore.QCoreApplication.translate('OTMarketsModel',
                                                             "Scale")
                if section == self.VOLUME:
                    return QtCore.QCoreApplication.translate('OTMarketsModel',
                                                             "Volume")
    def refresh(self, nym_id):
        pass
        """
        # TODO error handling
        assert nym_id
        msg = objEasy.get_market_list(self.server_id, nym_id)
        if objEasy.VerifyMessageSuccess(msg) < 1:
            logger.error("Failed to refresh markets from server %s", self.server_id)
            return

        storable = otapi.QueryObject(otapi.STORED_OBJ_MARKET_LIST, 'markets',
                                     self.server_id, 'market_data.bin')
        if not storable: return

        market_list = otapi.MarketList.ot_dynamic_cast(storable)
        for i in range(market_list.GetMarketDataCount()):
            data = market_list.GetMarketData(i)
            if data.market_id not in self.market_ids:
                self.addRow(data)
        """

    def setData(self, index, data, role=QtCore.Qt.EditRole):
        # more that account label could be edited but it'd have to sync across
        # multiplie items
        if not index.isValid() or role != QtCore.Qt.EditRole:
            return False
        #if index.column() != self.ACCOUNT:
        #    return False

        #row = index.row()
        #account_id = self.item(row, self.ID).text()
        #signer_nym = self.item(row, self.NYM_ID).text()
        #otapi.OTAPI_Basic_SetAccountWallet_Name(account_id,
        #                                        signer_nym,
        #                                        data)
        #self.item(row, self.ACCOUNT).setText(data)
        #self.dataChanged.emit(index, index)
        #return True
