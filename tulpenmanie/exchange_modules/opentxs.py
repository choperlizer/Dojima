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


otapi.OT_API_Init()


class OpenTransactionsExchangeItem(tulpenmanie.model.exchanges.DynamicExchangeItem):

    # OT can handle most of this stuff, we can just cache the labels and
    # stuff that the API passes


class OpenTransactionsExchangeMarket(QtCore.QObject):


    def __init__(self, parent=None):
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
