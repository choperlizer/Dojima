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
#from tulpenmanie.model.exchanges import exchanges_model
import tulpenmanie.model.ot.assets


class OTExchangeProxy(object):

    # make a dict that returns the market_id for a given pair

    def __init__(self, serverId, marketList):
        self.server_id = serverId
        # TODO find out if this market_list thing is dynamic
        self.market_list = marketList
        self.exchange_object = None
        self.market_map = dict()

    def getExchangeObject(self):
        if self.exchange_object is None:
            self.exchange_object = OTExchangeObject(self.server_id)

        return self.exchange_object

    @property
    def name(self):
        return otapi.OT_API_GetServer_Name(self.server_id)


class OpenTransactionsExchangeMarket(QtCore.QObject):


    def __init__(self, serverID, parent=None):
        super(OpenTransactionsExchangeMarket, self).__init__(parent)
        self.ticker_proxies = dict()
        self.ticker_clients = dict()


    def get_ticker_proxy(self, market_id):
        if market_id not in self.ticker_proxies:
            ticker_proxy = tulpenmanie.data.ticker.TickerProxy(self)
            self.ticker_proxies[market_id] = ticker_proxy
            return ticker_proxy
        return self.ticker_proxies[market_id]


    def set_ticker_stream_state(self, state, market_id):
        pass

    def refresh_ticker(self, market_id):
        pass

    def getTicker(self, server_id, market_id, nym_id):
        pass

class OpenTransactionsExchangeAccount(QtCore.QObject):

    def get_funds_proxy(self, asset_id):
        # This is available in the ExchangeAccount superclass
        pass

    def get_orders_proxy(self, market_id):
        # This is available in the ExchangeAccount superclass
        pass

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
