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

from PyQt4 import QtCore

import tulpenmanie.data.funds
import tulpenmanie.data.orders


class Exchange:

    def pop_request(self):
        request = heapq.heappop(self._requests)
        request.send()
        self._replies.add(request)

    def getAccountObject(self):
        raise NotImplementedError

    def getTickerProxy(self, remoteMarketID):
        raise NotImplementedError

    def hasDefaultAccount(self, remoteMarketID):
        raise NotImplementedError

    def setTickerStreamState(self, remoteMarketID):
        raise NotImplementedError


class ExchangeAccount:

    def pop_request(self):
        request = heapq.heappop(self._requests)
        request.send()
        self._replies.add(request)


    def cancelAskOrder(self, remoteMarketID, orderID):
        raise NotImplementedError

    def cancelBidOrder(self, remoteMarketID, orderID):
        raise NotImplementedError

    def getCommission(self, remoteMarketID, amount):
        raise NotImplementedError

    def getFundsProxy(self, symbol):
        if symbol not in self.funds_proxies:
            proxy = tulpenmanie.data.funds.FundsProxy(self)
            self.funds_proxies[symbol] = proxy
            return proxy

        return self.funds_proxies[symbol]

    def getOrdersProxy(self, remote_market):
        if remote_market not in self.orders_proxies:
            orders_proxy = tulpenmanie.data.orders.OrdersProxy(self)
            self.orders_proxies[remote_market] = orders_proxy
            return orders_proxy

        return self.orders_proxies[remote_market]

    def refresh(self):
        self.refresh_orders()
        self.refresh_funds()

    def refreshFunds(self):
        raise NotImplementedError

    def refreshOrders(self):
        raise NotImplementedError

    def placeAskLimitOrder(self, remoteMarketID, amount, price):
        raise NotImplementedError

    def placeBidLimitOrder(self, remoteMarketID, amount, price):
        raise NotImplementedError
