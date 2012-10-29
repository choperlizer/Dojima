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
import logging
from Queue import Queue

import otapi
from PyQt4 import QtCore, QtGui

import tulpenmanie.markets
import tulpenmanie.exchange
import tulpenmanie.data.ticker
import tulpenmanie.model.ot.assets

# i don't really want to import gui stuff here
import tulpenmanie.ui.ot.account


logger = logging.getLogger(__name__)


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


class OTTickerTimer(QtCore.QObject):

    def __init__(self, market_id, parent):
        super(OTTickerTimer, self).__init__(parent)
        self.parent = parent
        self.market_id = market_id
        self.timer = QtCore.QBasicTimer()

    def timerEvent(self, event):
        self.parent.trades_queue.put(self.market_id)

    def start(self, timeout):
        self.timer.start(timeout, self)

    def stop(self):
        self.timer.stop()


class OTExchange(QtCore.QObject):

    exchange_error_signal = QtCore.pyqtSignal(str)
    funds_proxies = dict()

    def __init__(self, serverID, parent=None):
        super(OTExchange, self).__init__(parent)
        self.account_object = None

        self.server_id = serverID
        # TODO going to need this nym
        self.nym_id = None
        self.ticker_proxies = dict()
        self.ticker_clients = dict()
        # market_id -> [base_id, counter_id]
        self.assets = dict()
        # market_id -> [base_account_id, counter_account_id]
        self.accounts = dict()
        # market_id -> scale
        self.scales = dict()

        self.ml_store = otapi.QueryObject(otapi.STORED_OBJ_MARKET_LIST,
                                          'markets', self.server_id,
                                          'market_data.bin')
        self.market_list = otapi.MarketList.ot_dynamic_cast(self.ml_store)
        for i in range(self.market_list.GetMarketDataCount()):
            data = self.market_list.GetMarketData(i)
            market_id = data.market_id
            self.assets[market_id] = (data.asset_type_id, data.currency_type_id)
            self.scales[market_id] = data.scale
        self.nol_store = None

        # The request timer and queues
        self.request_timer = QtCore.QTimer(self)
        self.request_timer.timeout.connect(self.sendRequest)
        # Just start the timer at init()
        self.request_timer.start(2048)
        self.ticker_clients = 0
        self.ticker_timer = QtCore.QTimer(self)
        self.ticker_timer.timeout.connect(self.getMarketList)
        self.getaccount_queue = Queue()
        self.getnymoffers_queue = Queue()
        self.offer_queue = Queue()
        self.trades_queue = Queue()

    def readNymOfferList(self):
        # this would go into __init__ but the nym_id isn't there
        # it may be too much overhead to create the storable each time
        storable = otapi.QueryObject(otapi.STORED_OBJ_OFFER_LIST_NYM,
                                      'nyms', self.server_id, 'offers',
                                      self.nym_id + '.bin')
        if not storable: return

        nym_offers = otapi.OfferListNym.ot_dynamic_cast(storable)

        for i in range(nym_offers.GetOfferDataNymCount()):
            offer = nym_offers.GetOfferDataNym(i)
            print i, offer

    def getAccountObject(self):
        if self.account_object is None:
            self.account_object = OTExchangeAccount(self)

        return self.account_object

    def getTickerProxy(self, market_id):
        if market_id not in self.ticker_proxies:
            ticker_proxy = tulpenmanie.data.ticker.TickerProxy(self)
            self.ticker_proxies[market_id] = ticker_proxy
            return ticker_proxy
        return self.ticker_proxies[market_id]

    def getRemotePair(self, market_id):
        return self.assets[market_id]

    def getMarketList(self):
        otapi.OT_API_getMarketList(self.server_id, self.nym_id)
        for i in range(self.market_list.GetMarketDataCount()):
            data = self.market_list.GetMarketData(i)
            if data.market_id in self.ticker_proxies:
                proxy = self.ticker_proxies[data.market_id]
                proxy.ask_signal.emit(Decimal(data.current_ask))
                proxy.last_signal.emit(Decimal(data.last_sale_price))
                proxy.bid_signal.emit(Decimal(data.current_bid))

    def setTickerStreamState(self, state, market_id):
        if state is True:
            self.startTickerStream(market_id)
            return
        self.stopTickerStream(market_id)

    def startTickerStream(self, market_id=None):
        if self.ticker_clients == 0:
            logger.debug("starting ticker stream for %s", self.server_id)
            self.ticker_timer.start(16384)

        self.ticker_clients += 1

    def stopTickerStream(self, market_id=None):
        if self.ticker_clients == 1:
            logger.debug("stopping ticker stream for %s", self.server_id)
            self.ticker_timer.stop()

        self.ticker_clients -= 1
        assert self.ticker_clients >= 0

    def refresh_ticker(self, market_id):
        pass

    def getTicker(self, market_id):
        self.trades_queue.put(market_id)
        if not self.trades_timer.isActive():
            self.timer.start(self.request_pause)

    def hasDefaultAccount(self, marketId):
        if marketId in self.accounts:
            return True

        settings = QtCore.QSettings()
        settings.beginGroup('OT-defaults')

        settings.beginGroup(self.server_id)
        self.nym_id = str(settings.value('nym', self.nym_id))
        settings.endGroup()

        for group in settings.childGroups():
            if str(group) == str(marketId):

                settings.beginGroup(marketId)
                self.accounts[marketId] = (
                    str(settings.value('base_account')),
                    str(settings.value('counter_account')))
                return True

    def readTrades(self, market_id):
        logger.debug('reading %s trades', market_id)
        storable = otapi.QueryObject(otapi.STORED_OBJ_TRADE_LIST_MARKET,
                                     "markets", self.server_id,
                                     "recent", market_id + ".bin")
        trades = otapi.TradeListMarket.ot_dynamic_cast(storable)
        if not trades:
            return

    def setDefaultAccounts(self, marketId):
        # I guess we could just read from settings each time, but ram is cheap
        baseAccountId, counterAccountId = self.accounts[marketId]
        settings = QtCore.QSettings()
        settings.beginGroup('OT-defaults')
        settings.beginGroup(self.server_id)
        settings.setValue('nym', self.nym_id)
        settings.endGroup()
        settings.beginGroup(marketId)
        settings.setValue('base_account', baseAccountId)
        settings.setValue('counter_account', counterAccountId)

    def sendRequest(self):
        # if the timer is the only one to call this it shouldn't block
        if not self.offer_queue.empty():
            # MARKET_SCALE,	Defaults to minimum of 1. Market granularity.
            # MINIMUM_INCREMENT, This will be multiplied by the Scale. Min 1.
            # TOTAL_ASSETS_ON_OFFER, Total assets available for sale or purchase.
            # Will be multiplied by minimum increment.

            # SELLING == OT_TRUE, BUYING == OT_FALSE

            market_id, total, price, buy_sell = self.offer_queue.get()
            base_asset_id, counter_asset_id = self.assets[market_id]
            base_account_id, counter_account_id = self.accounts[market_id]
            scale = self.scales[market_id]
            increment = 1
            otapi.OT_API_issueMarketOffer(self.server_id, self.nym_id,
                                          base_asset_id, base_account_id,
                                          counter_asset_id, counter_account_id,
                                          str(scale), str(increment), str(total),
                                          str(price), buy_sell)
            return

        if not self.getaccount_queue.empty():
            account_id = self.getaccount_queue.get_nowait()
            otapi.OT_API_getAccount(self.server_id, self.nym_id, account_id)

            balance = Decimal(otapi.OT_API_GetAccountWallet_Balance(account_id))
            proxy = self.funds_proxies[account_id]
            proxy.balance.emit(balance)
            return

        if not self.getnymoffers_queue.empty():
            # TODO won't work if making offers with more than one nym
            self.getnymoffers_queue.get_nowait()
            logger.info('requesting nym %s offer list from %s',
                        self.nym_id, self.server_id)
            otapi.OT_API_getNym_MarketOffers(self.server_id, self.nym_id)
            # TODO now read the nym_offer_list

        if not self.trades_queue.empty():
            market_id = self.trades_queue.get_nowait()
            logger.info('requesting %s trade list from %s',
                        market_id, self.server_id)
            r = otapi.OT_API_getMarketRecentTrades(self.server_id, self.nym_id,
                                                   market_id)
            if r < 1:
                # no message was sent, don't retry, it was only a trades request
                return
            self.readTrades(market_id)

    def showAccountDialog(self, market_id, parent):
        base_id, counter_id = self.assets[market_id]
        dialog = tulpenmanie.ui.ot.account.MarketAccountsDialog(self.server_id,
                                                                base_id,
                                                                counter_id,
                                                                parent)
        if dialog.exec_():
            self.nym_id = str(dialog.getNymId())
            self.accounts[market_id] = (str(dialog.getBaseAccountId()),
                                        str(dialog.getCounterAccountId()))
            self.setDefaultAccounts(market_id)
            return True

        return False


class OTTradesRequest(QtCore.QObject):

    done_signal = QtCore.pyqtSignal()

    def __init__(self, server_id, nym_id, market_id):
        pass


# Things are going to get weird now, each market has two accounts,
# somethimes those account pairs overlap, sometimes they don't
# it seems I'll need a per account signal proxy to deal with balances and stuff

class OTExchangeAccount(QtCore.QObject, tulpenmanie.exchange.ExchangeAccount):

    exchange_error_signal = QtCore.pyqtSignal(str)

    def __init__(self, exchange):
        super(OTExchangeAccount, self).__init__(exchange)
        self.exchange = exchange
        # These are needed for the inherited get proxy methods
        self.orders_proxies = dict()

    def getAccountPair(self, market_id):
        return self.exchange.accounts[market_id]

    def getFundsProxy(self, account_id):
        if account_id not in self.exchange.funds_proxies:
            proxy = tulpenmanie.data.funds.FundsProxy(self)
            self.exchange.funds_proxies[account_id] = proxy
            return proxy

        return self.exchange.funds_proxies[account_id]

    def refresh(self, market_id):
        self.refreshFunds(market_id)
        self.refreshOrders()

    def refreshFunds(self, market_id):
        for account_id in self.exchange.accounts[market_id]:
            self.exchange.getaccount_queue.put(account_id)

    def refreshOrders(self, market_id=None):
        self.exchange.getnymoffers_queue.put(True)

    def placeAskLimitOrder(self, market_id, amount, price):
        # SELLING == OT_TRUE, BUYING == OT_FALSE
        self.exchange.offer_queue.put( (market_id, int(amount), int(price), 1) )

    def placeBidLimitOrder(self, market_id, amount, price):
        # SELLING == OT_TRUE, BUYING == OT_FALSE
        self.exchange.offer_queue.put( (market_id, int(amount), int(price), 0) )

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
