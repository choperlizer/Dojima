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

from decimal import Decimal

import otapi
from PyQt4 import QtCore, QtGui

import tulpenmanie.markets
import tulpenmanie.exchange
import tulpenmanie.data.ticker
import tulpenmanie.model.ot.assets

# i don't really want to import gui stuff here
import tulpenmanie.ui.ot.account


class OTExchangeProxy(object):

    def __init__(self, serverId, marketList):
        self.id = serverId
        # TODO find out what this market list thing does
        self.market_list = marketList
        self.exchange_object = None
        self.market_map = dict()

    def getExchangeObject(self):
        if self.exchange_object is None:
            self.exchange_object = OTExchange(self.id)

        return self.exchange_object

    @property
    def name(self):
        return otapi.OT_API_GetServer_Name(self.id)

    def getMapping(self, key):
        return self.market_map[key]


class OTExchange(QtCore.QObject):

    exchange_error_signal = QtCore.pyqtSignal(str)

    def __init__(self, serverID, parent=None):
        super(OTExchange, self).__init__(parent)
        self.account_object = None

        self.server_id = serverID
        self.ticker_proxies = dict()
        self.ticker_clients = dict()
        # market_id -> [base_id, counter_id]
        self.markets = dict()
        # market_id -> [base_account_id, counter_account_id]
        self.accounts = dict()

        # this storable and list may go out of scope
        storable = otapi.QueryObject(otapi.STORED_OBJ_MARKET_LIST,
                                     'markets', self.server_id,
                                     'market_data.bin')
        self.market_list = otapi.MarketList.ot_dynamic_cast(storable)
        for i in range(self.market_list.GetMarketDataCount()):
            data = self.market_list.GetMarketData(i)
            self.markets[data.market_id] = (data.asset_type_id,
                                            data.currency_type_id)

    def getAccountObject(self):
        if self.account_object is None:
            self.account_object = OTExchangeAccount(self.server_id, self)

        return self.account_object

    def getTickerProxy(self, market_id):
        if market_id not in self.ticker_proxies:
            ticker_proxy = tulpenmanie.data.ticker.TickerProxy(self)
            self.ticker_proxies[market_id] = ticker_proxy
            return ticker_proxy
        return self.ticker_proxies[market_id]

    def getRemotePair(self, market_id):
        return self.markets[market_id]

    def setTickerStreamState(self, state, market_id):
        pass

    def refresh_ticker(self, market_id):
        pass

    def getTicker(self, server_id, market_id, nym_id):
        pass

    def hasDefaultAccount(self, marketId):
        if marketId in self.accounts:
            return True

        settings = QtCore.QSettings()
        settings.beginGroup('OT-default_accounts')
        for group in settings.childGroups():
            if str(group) == str(marketId):
                settings.beginGroup(marketId)
                self.accounts[marketId] = (
                    str(settings.value('base_account')),
                    str(settings.value('counter_account')))
                return True

    def setDefaultAccounts(self, marketId, baseAccountId, counterAccountId):
        # I guess we could just read from settings each time, but ram is cheap
        self.accounts[marketId] = (baseAccountId, counterAccountId)
        settings = QtCore.QSettings()
        settings.beginGroup('OT-default_accounts')
        settings.beginGroup(marketId)
        settings.setValue('base_account', baseAccountId)
        settings.setValue('counter_account', counterAccountId)

    def showAccountDialog(self, market_id, parent):
        base_id, counter_id = self.markets[market_id]
        dialog = tulpenmanie.ui.ot.account.MarketAccountsDialog(self.server_id,
                                                                base_id,
                                                                counter_id,
                                                                parent)
        if dialog.exec_():
            self.setDefaultAccounts(market_id,
                                    dialog.getBaseAccountId(),
                                    dialog.getCounterAccountId())
            return True

        return False

# Things are going to get weird now, each market has two accounts,
# somethimes those account pairs overlap, sometimes they don't
# it seems I'll need a per account signal proxy to deal with balances and stuff

class OTExchangeAccount(QtCore.QObject, tulpenmanie.exchange.ExchangeAccount):

    exchange_error_signal = QtCore.pyqtSignal(str)
    
    def __init__(self, serverId, parent):
        super(OTExchangeAccount, self).__init__(parent)
        self.server_id = serverId
        # These are needed for the inherited get proxy methods
        self.funds_proxies = dict()
        self.orders_proxies = dict()

    def refresh(self):
        pass

    def refresh_funds(self):
        pass

    def refresh_orders(self):
        pass

    def place_ask_limit_order(self, market_id, amount, price):
        pass

    def place_bid_limit_order(self, market_id, amount, price):
        pass

    def cancel_ask_order(self, market_id, order_id):
        pass

    def cancel_bid_order(self, market_id, order_id):
        pass

    def get_commission(self, amount, market_id):
        return Decimal(0)


def parse_servers():
    assets_mapping_model = tulpenmanie.model.ot.assets.OTAssetsSettingsModel()

    for i in range(otapi.OT_API_GetServerCount()):
        server_id = otapi.OT_API_GetServer_ID(i)
        if otapi.Exists('markets', server_id, 'market_data.bin'):
            storable = otapi.QueryObject(otapi.STORED_OBJ_MARKET_LIST,
                                         'markets', server_id,
                                         'market_data.bin')
        else:
            storable = otapi.CreateObject(otapi.STORED_OBJ_MARKET_LIST)

        market_list = otapi.MarketList.ot_dynamic_cast(storable)
        if not market_list.GetMarketDataCount():
            continue

        # we'll just make an item here and then stick it the bigger model
        # wherever a supported market may be
        exchange_proxy = None

        for j in range(market_list.GetMarketDataCount()):
            market_data = market_list.GetMarketData(j)

            search = assets_mapping_model.findItems(market_data.asset_type_id)
            if not search: continue
            row = search[0].row()
            local_base_id = assets_mapping_model.item(
                row, assets_mapping_model.LOCAL_ID).text()

            search = assets_mapping_model.findItems(market_data.currency_type_id)
            if not search: continue
            row = search[0].row()
            local_counter_id = assets_mapping_model.item(
                row, assets_mapping_model.LOCAL_ID).text()

            local_pair = local_base_id + '_' + local_counter_id

            if exchange_proxy is None:
                exchange_proxy = OTExchangeProxy(server_id, market_list)

            exchange_proxy.market_map[local_pair] = market_data.market_id
            # may not need this reverse map but whatever
            exchange_proxy.market_map[market_data.market_id] = local_pair
            tulpenmanie.markets.container.addExchange(exchange_proxy,
                                                       local_pair)

parse_servers()
