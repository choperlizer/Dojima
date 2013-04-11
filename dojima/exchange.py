# Dojima, a markets client.
# Copyright (C) 2012-2013  Emery Hemingway
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

from PyQt4 import QtCore, QtGui

import dojima.data.account
import dojima.data.balance
#import dojima.data.orders


class ExchangeProxy:

    def getLocaltoRemote(self, key):
        return self.local_market_map[key]

    def getPrettyInterMarketName(self, remoteMarketID):
        raise NotImplementedError

    def getRemoteMapping(self, key):
        return self.remote_market_map[key]

    def getRemoteMarketIDs(self, localPair):
        return self.local_market_map[localPair]

    def getRemoteToLocal(self, marketID):
        return self.remote_market_map[marketID]

    def refreshMarkets(self):
        raise NotImplementedError

    def nextPage(self, wizard):
        raise NotImplementedError

    
class Exchange:

    def echoTicker(self, remoteMarketID):
        pass

    def getAccountValidityProxy(self, marketID):
        if marketID not in self.account_validity_proxies:
            validity_proxy = dojima.data.account.AccountValidityProxy(self)
            self.account_validity_proxies[marketID] = validity_proxy
            return validity_proxy
        return self.account_validity_proxies[marketID]

    def getBalanceProxy(self, symbol):
        if symbol not in self.funds_proxies:
            proxy = dojima.data.funds.BalanceProxy(self)
            self.funds_proxies[symbol] = proxy
            return proxy

        return self.funds_proxies[symbol]

    def getOffersModelAsks(self, market_id):
        if market_id in self.offers_proxies_asks:
            return self.offers_proxies_asks[market_id]

        base_model = self.getOffersModel(market_id)
        asks_model = dojima.data.offers.FilterAsksModel(base_model)
        self.offers_proxies_asks[market_id] = asks_model
        return asks_model

    def getOffersModelBids(self, market_id):
        if market_id in self.offers_proxies_bids:
            return self.offers_proxies_bids[market_id]

        base_model = self.getOffersModel(market_id)
        bids_model = dojima.data.offers.FilterBidsModel(base_model)
        self.offers_proxies_bids[market_id] = bids_model
        return bids_model
        
    def getScale(self, remoteMarketID):
        return 1

    def getTickerProxy(self, market_id):
        if market_id not in self.ticker_proxies:
            ticker_proxy = dojima.data.market.TickerProxy(self)
            self.ticker_proxies[market_id] = ticker_proxy
            return ticker_proxy
        return self.ticker_proxies[market_id]

    def getTickerRefreshRate(self, market=None):
        return self._ticker_exchange_rate

    def getOffersModel(self, market_id):
        if self.offers_model is None:
            self.offers_model = dojima.data.offers.Model()

        if market_id in self.offers_proxies:
            return self.offers_proxies[market_id]

        base_symbol, counter_symbol = self.getMarketSymbols(market_id)
        if base_symbol in self.base_offers_proxies:
            base_proxy = self.base_offers_proxies[base_symbol]
        else:
            base_proxy = QtGui.QSortFilterProxyModel()
            base_proxy.setSourceModel(self.offers_model)
            base_proxy.setFilterKeyColumn(dojima.data.offers.BASE)
            base_proxy.setFilterFixedString(base_symbol)
            base_proxy.setDynamicSortFilter(True)
            self.base_offers_proxies[base_symbol] = base_proxy

        proxy = QtGui.QSortFilterProxyModel()
        proxy.setSourceModel(base_proxy)
        proxy.setFilterKeyColumn(dojima.data.offers.COUNTER)
        proxy.setFilterFixedString(counter_symbol)
        proxy.setDynamicSortFilter(True)
        self.offers_proxies[market_id] = proxy
        return proxy

    def pop_request(self):
        request = heapq.heappop(self._requests)
        request.send()
        self._replies.add(request)

    def populateMenuBar(self, menu, remoteMarketID):
        pass
        
    def refresh(self, market_id):
        self.refreshOffers()
        self.refreshBalance(market_id)
        
    def setTickerRefreshRate(self, rate):
        self._ticker_refresh_rate = rate
        if self.ticker_timer.isActive():
            self.ticker_timer.setInterval(self._ticker_refresh_rate * 1000)


        
