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

from PyQt4 import QtCore

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

    def pop_request(self):
        request = heapq.heappop(self._requests)
        request.send()
        self._replies.add(request)

    def getAccountObject(self):
        raise NotImplementedError

    def getAccountValidityProxy(self, marketID):
        if marketID not in self.account_validity_proxies:
            validity_proxy = dojima.data.account.AccountValidityProxy(self)
            self.account_validity_proxies[marketID] = validity_proxy
            return validity_proxy
        return self.account_validity_proxies[marketID]

    def getFactors(self, remoteMarketID):
        raise NotImplementedError

    def getPower(self, remoteMarketID):
        raise NotImplementedError

    def getScale(self, remoteMarketID):
        return 1

    def getTickerProxy(self, market_id):
        if market_id not in self.ticker_proxies:
            ticker_proxy = dojima.data.market.TickerProxy(self)
            self.ticker_proxies[market_id] = ticker_proxy
            return ticker_proxy
        return self.ticker_proxies[market_id]

    def getDepthProxy(self, remoteMarketID):
        raise NotImplementedError

    def hasDefaultAccount(self, remoteMarketID):
        raise NotImplementedError

    def populateMenuBar(self, menu, remoteMarketID):
        pass

    def setTickerStreamState(self, state, remoteMarketID):
        raise NotImplementedError


class ExchangeAccount:

    def pop_request(self):
        request = heapq.heappop(self._requests)
        request.send()
        self._replies.add(request)

    def cancelAskOffer(self, offerId, remoteMarketID):
        raise NotImplementedError

    def cancelBidOffer(self, offerId, remoteMarketID):
        raise NotImplementedError

    def getCommission(self, remoteMarketID, amount):
        raise NotImplementedError

    def getBalanceProxy(self, symbol):
        if symbol not in self.funds_proxies:
            proxy = dojima.data.funds.BalanceProxy(self)
            self.funds_proxies[symbol] = proxy
            return proxy

        return self.funds_proxies[symbol]

    def getOffersProxy(self, remote_market):
        if remote_market not in self.offers_proxies:
            offers_proxy = dojima.data.offers.OffersProxy(self)
            self.offers_proxies[remote_market] = offers_proxy
            return offers_proxy

        return self.offers_proxies[remote_market]

    def refresh(self, marketId):
        self.refreshOffers()
        self.refreshBalance()

    def refreshBalance(self):
        raise NotImplementedError

    def refreshOffers(self):
        raise NotImplementedError

    def placeAskLimitOffer(self, remoteMarketID, amount, price):
        raise NotImplementedError

    def placeBidLimitOffer(self, remoteMarketID, amount, price):
        raise NotImplementedError
