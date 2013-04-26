# Dojima, a markets client.
# Copyright (C) 2012-2013 Emery Hemingway
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

import hashlib
import heapq
import hmac
import json
import logging
import time
import urllib.parse

from decimal import Decimal

import matplotlib.dates
import numpy as np
from PyQt4 import QtCore, QtGui, QtNetwork

import dojima.exchanges
import dojima.exchange
import dojima.data.account
import dojima.data.market
import dojima.data.offers
import dojima.markets
import dojima.network
import dojima.ui.wizard


PRETTY_NAME = "BTC-e"
HOSTNAME = "btc-e.com"
URL_BASE = "https://" + HOSTNAME + "/api/2/"
PLAIN_NAME = "btce"

logger = logging.getLogger(PLAIN_NAME)

MARKETS = ( 'btc_eur', 'btc_rur', 'btc_usd', 
            'eur_usd', 
            'ltc_btc', 'ltc_rur', 'ltc_usd', 
            'nmc_btc', 
            'nvc_btc', 
            'ppc_btc',
            'trc_btc', 
            'usd_rur', )

FACTORS = { 'btc':int(1e8),
            'eur':int(1e6),
            'ltc':100000000,
            'nmc':1000,
            'nvc':1000,
            'ppc':1000,
            'rur':1000,
            'trc':1000,
            'usd':int(1e6) }

POWERS = { 'btc':8,
           'eur':3,
           'ltc':8,
           'nmc':3,
           'nvc':3,
           'ppc':3,
           'rur':3,
           'trc':3,
           'usd':3 }

def get_symbols(pair):
    return pair.split('_')
    
def saveAccountSettings(key, secret):
    settings = QtCore.QSettings()
    settings.beginGroup(PLAIN_NAME)
    settings.setValue('API_key', key)
    settings.setValue('API_secret', secret)

def loadAccountSettings():
    settings = QtCore.QSettings()
    settings.beginGroup(PLAIN_NAME)
    key = settings.value('API_key')
    secret = settings.value('API_secret')
    return key, secret


class BtceExchangeProxy(dojima.exchange.ExchangeProxy):

    id = 'btce'
    name = PRETTY_NAME
    local_market_map = dict()
    remote_market_map = dict()

    def __init__(self):
        self.exchange_object = None

    def getExchangeObject(self):
        if self.exchange_object is None:
            self.exchange_object = BtceExchange()

        return self.exchange_object

    def getPrettyMarketName(self, remote_market_id):
        # TODO make the asset seperator (/) locale dependant
        s = remote_market_id.replace('_', '/')
        return s.upper()

    def getWizardPage(self, wizard):
        return BtceWizardPage(wizard)
        
    def refreshMarkets(self):
        for market_symbol in MARKETS:
            remote_base_id, remote_counter_id = market_symbol.split('_')
            local_counter_id = dojima.model.commodities.remote_model.getRemoteToLocalMap('btce-' + remote_counter_id)
            local_base_id = dojima.model.commodities.remote_model.getRemoteToLocalMap('btce-' + remote_base_id)
            if ((local_base_id is None) or
                (local_counter_id is None)) : continue

            local_pair = local_base_id + '_' + local_counter_id

            if local_pair in self.local_market_map:
                local_map = self.local_market_map[local_pair]
            else:
                local_map = list()
                self.local_market_map[local_pair] = local_map

            if market_symbol not in local_map:
                local_map.append(market_symbol)

            self.remote_market_map[market_symbol] = local_pair

            dojima.markets.container.addExchange(self, local_pair,
                                                 local_base_id, local_counter_id)

            
class BtceWizardPage(dojima.ui.wizard.ExchangeWizardPage):

    def __init__(self, parent):
        super(BtceWizardPage, self).__init__(parent)
        self.setTitle(PRETTY_NAME)
        self._is_complete = False

    def checkCompleteState(self):
        if self.base_combo.currentIndex() == self.counter_combo.currentIndex():
            is_complete = False
        else:
            is_complete = True

        if self._is_complete is not is_complete:
            self._is_complete = is_complete
            self.completeChanged.emit()

    def initializePage(self):
        self.key_edit = QtGui.QLineEdit()
        self.secret_edit = QtGui.QLineEdit()
        self.market_combo = QtGui.QComboBox()
        self.base_combo = QtGui.QComboBox()
        self.counter_combo = QtGui.QComboBox()

        new_local_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate(PRETTY_NAME, "New Commodity",
                                              "The label on the new commodity button in the "
                                              "new market wizard."))
        button_box = QtGui.QDialogButtonBox()
        button_box.addButton(new_local_button, button_box.ActionRole)

        layout = QtGui.QFormLayout()
        layout.addRow(QtCore.QCoreApplication.translate(PRETTY_NAME, "API Key"), self.key_edit)
        layout.addRow(QtCore.QCoreApplication.translate(PRETTY_NAME, "API Secret"), self.secret_edit)
        layout.addRow(QtCore.QCoreApplication.translate(PRETTY_NAME, "Market"), self.market_combo)
        layout.addRow(QtCore.QCoreApplication.translate(PRETTY_NAME, "Local Base Commodity"), self.base_combo)
        layout.addRow(QtCore.QCoreApplication.translate(PRETTY_NAME, "Local Counter Commodity"), self.counter_combo)
        layout.addRow(button_box)
        self.setLayout(layout)

        self.market_combo.addItems(MARKETS)
        self.base_combo.setModel(dojima.model.commodities.local_model)
        self.counter_combo.setModel(dojima.model.commodities.local_model)
                
        new_local_button.clicked.connect(self.showNewCommodityDialog)
        self.key_edit.textChanged.connect(self.checkCompleteState)
        self.secret_edit.textChanged.connect(self.checkCompleteState)
        self.base_combo.currentIndexChanged.connect(self.checkCompleteState)
        self.counter_combo.currentIndexChanged.connect(self.checkCompleteState)

        key, secret = loadAccountSettings()
        if key:
            self.key_edit.setText(key)
        if secret:
            self.secret_edit.setText(secret)

    def isComplete(self):
        return self._is_complete

    def nextId(self):
        return -1

    def validatePage(self):
        saveAccountSettings(self.key_edit.text(), self.secret_edit.text())
        
        base_symbol, counter_symbol = self.market_combo.currentText().split('_')
        base_symbol    = 'btce-' + base_symbol
        counter_symbol = 'btce-' + counter_symbol
        
        local_base_id    = self.base_combo.itemData(self.base_combo.currentIndex(), QtCore.Qt.UserRole)
        local_counter_id = self.base_combo.itemData(self.counter_combo.currentIndex(), QtCore.Qt.UserRole)

        dojima.model.commodities.remote_model.map(base_symbol,    local_base_id)
        dojima.model.commodities.remote_model.map(counter_symbol, local_counter_id)
        
        return dojima.model.commodities.remote_model.submit()


class BtceExchange(QtCore.QObject, dojima.exchange.Exchange):
    valueType = Decimal

    accountChanged = QtCore.pyqtSignal(str)
    exchange_error_signal = QtCore.pyqtSignal(str)

    def __init__(self, network_manager=None, parent=None):
        if not network_manager:
            network_manager = dojima.network.get_network_manager()
        super(BtceExchange, self).__init__(parent)

        self.network_manager = network_manager
        self.host_queue = self.network_manager.get_host_request_queue(HOSTNAME, 1000)
        self.requests = list()
        self.replies = set()

        self._key = None
        self._secret = None
        self._nonce = int(time.time() / 2)
        
        self.account_validity_proxies = dict()
        self.ticker_proxies = dict()
        self.ticker_clients = dict()
        self.balance_proxies = dict()
        self.depth_proxies = dict()
        self.trades_proxies = dict()

        self.offers_model = dojima.data.offers.Model()
        self.base_offers_proxies = dict()
        self.offers_proxies = dict()
        self.offers_proxies_asks = dict()
        self.offers_proxies_bids = dict()

        self._ticker_refresh_rate = 16
        self.ticker_timer = QtCore.QTimer(self)
        self.ticker_timer.timeout.connect(self._refresh_tickers)
        self.ticker_clients = dict()
        
        self.loadAccountCredentials()

    def cancelOffer(self, order_id, pair=None):
        params = {'order_id': order_id}
        request = BtceCancelOrderRequest(params, self)
        request.order_id = order_id
                
    cancelAskOffer = cancelOffer
    cancelBidOffer = cancelOffer

    def getBalanceBaseProxy(self, market_id):
        symbol = market_id.split('_')[0]
        if symbol not in self.balance_proxies:
            proxy = dojima.data.balance.BalanceProxyDecimal(self)
            self.balance_proxies[symbol] = proxy
            return proxy

        return self.balance_proxies[symbol]

    def getBalanceCounterProxy(self, market_id):
        symbol = market_id.split('_')[1]
        if symbol not in self.balance_proxies:
            proxy = dojima.data.balance.BalanceProxyDecimal(self)
            self.balance_proxies[symbol] = proxy
            return proxy

        return self.balance_proxies[symbol]

    def getDepthProxy(self, pair):
        if pair not in self.depth_proxies:
            proxy = dojima.data.market.DepthProxy(pair, self)
            self.depth_proxies[pair] = proxy
            return proxy

        return self.depth_proxies[pair]    

    def getMarketSymbols(self, pair):
        return pair.split('_')

    def getTradesProxy(self, pair):
        if pair not in self.trades_proxies:
            proxy = dojima.data.market.TradesProxy(pair, self)
            self.trades_proxies[pair] = proxy
            return proxy

        return self.trades_proxies[pair]
    
    def hasAccount(self, market_id=None):
        return bool(self._key and self._secret)
        
    def loadAccountCredentials(self):
        key, secret = loadAccountSettings()
        secret = bytes(secret, 'utf')
        if self._key != key or self._secret != secret:
            self._key = key
            self._secret = secret
            for pair in MARKETS:
                self.accountChanged.emit(pair)

    def placeAskLimitOffer(self, amount, price, pair):
        params = {'pair': pair,
                  'type': 'sell',
                  'rate': price,
                  'amount': amount}       
        request = BtceTradeRequest(params, self)
        request.pair = pair
        request.amount = amount
        request.price = price
        request.type_ = dojima.data.offers.ASK
    
    def placeBidLimitOffer(self, amount, price, pair):
        params = {'pair': pair,
                  'type': 'buy',
                  'rate': price,
                  'amount': amount}       
        request = BtceTradeRequest(params, self)
        request.pair = pair
        request.amount = amount
        request.price = price
        request.type_ = dojima.data.offers.BID

    def populateMenuBar(self, menu_bar, market_id):
        account_menu = menu_bar.getAccountMenu()
        edit_credentials_action = BtceEditCredentialsAction(account_menu)
        account_menu.addAction(edit_credentials_action)
        edit_credentials_action.accountSettingsChanged.connect(self.loadAccountCredentials)
        
    def refreshBalance(self, market_id=None):
        BtceInfoRequest(None, self)
                
    def refreshDepth(self, market_id):
        BtceDepthRequest(market_id, self)

    def refreshOffers(self, pair=None):
        if pair is None:
            param = None
        else:
            params = {'pair': pair}

        BtceOrdersRequest(params, self)

    def refreshTrades(self, market_id):
        BtceTradesRequest(market_id, self)
        
    def _refresh_tickers(self):
        for pair in list(self.ticker_clients.keys()):
            BtceTickerRequest(pair, self)


class _BtcePublicRequest(dojima.network.ExchangeGETRequest):

    def __init__(self, pair, parent):
        self.pair = pair
        self.parent = parent
        self.url = QtCore.QUrl(URL_BASE + pair + self.path)
        self.reply = None
        parent.requests.append( (self.priority, self,) )
        parent.host_queue.enqueue(self.parent, self.host_priority)


class BtceDepthRequest(_BtcePublicRequest):
    path = "/depth"

    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw)

        proxy = self.parent.getDepthProxy(self.pair)
        
        bids = data['bids']
        bids = np.array(bids).transpose()
        proxy.processBids(bids)
        
        asks = data['asks']
        asks = np.array(asks).transpose()
        proxy.processAsks(asks)       

        
class BtceTickerRequest(_BtcePublicRequest):
    path = "/ticker"
    
    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw, parse_float=Decimal, parse_int=Decimal)
        data = data['ticker']
        proxy = self.parent.ticker_proxies[self.pair]
        proxy.ask_signal.emit(data['buy'])
        proxy.last_signal.emit(data['last'])
        proxy.bid_signal.emit(data['sell'])

        
class BtceTradesRequest(_BtcePublicRequest):
    path = "/trades"

    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw)

        trades = np.empty( (3, len(data)) )

        for i, trade in enumerate(data):
            trades[0,i] = trade['date']
            trades[1,i] = trade['price']
            trades[2,i] = trade['amount']

        trades[0] = matplotlib.dates.epoch2num(trades[0])
        
        proxy = self.parent.getTradesProxy(self.pair)
        proxy.refreshed.emit(trades)
        

class _BtcePrivateRequest(dojima.network.ExchangePOSTRequest):
    priority = 1
    host_priority = 0
    url = QtCore.QUrl("https://" + HOSTNAME + "/tapi")

    def __init__(self, params, parent):
        self.params = params
        self.parent = parent
        self.reply = None
        parent.requests.append( (self.priority, self,) )
        parent.host_queue.enqueue(self.parent, self.host_priority)

    def _prepare_request(self):
        self.request = QtNetwork.QNetworkRequest(self.url)
        self.request.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader,
                               "application/x-www-form-urlencoded")
        params = {'method': self.method,
                  'nonce': str(self.parent._nonce)}
        self.parent._nonce += 1
        if self.params:
            params.update(self.params)
        self.query = urllib.parse.urlencode(params)
                
        h = hmac.new(self.parent._secret, bytes(self.query, 'utf'), hashlib.sha512)
        signature = h.hexdigest()
        
        self.request.setRawHeader('Key', self.parent._key)
        self.request.setRawHeader('Sign', signature)

    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw, parse_float=Decimal, parse_int=Decimal)
        if data['success'] == 0:
            logger.error("%s: %s", data['error'], self.query)
            return

        self.handle_reply(data['return'])
        

class BtceInfoRequest(_BtcePrivateRequest):
    method = 'getInfo'

    def handle_reply(self, data):
        for symbol, balance in list(data['funds'].items()):
            if symbol in self.parent.balance_proxies:
                proxy = self.parent.balance_proxies[symbol]
                proxy.balance_liquid.emit(balance)

                
class BtceCancelOrderRequest(_BtcePrivateRequest):
    method = 'CancelOrder'
    priority = 0

    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw, parse_float=Decimal, parse_int=Decimal)
        logger.debug(data)
        if data['success'] == 0:
            logger.error("%s: %s", data['error'], self.query)
            return
               
        search = self.parent.offers_model.findItems(self.order_id)
        for item in search:
            self.parent.offers_model.removeRows(item.row(), 1)

            
class BtceOrdersRequest(_BtcePrivateRequest):
    method = 'OrderList'

    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw, parse_float=Decimal, parse_int=Decimal)
        self.parent.offers_model.clear()

        if 'return' not in data:
            return

        row = 0
        for order_id, order in list(data['return'].items()):

            #id 
            item = QtGui.QStandardItem(order_id)
            self.parent.offers_model.setItem(row, dojima.data.offers.ID, item)

            # price
            item = QtGui.QStandardItem()
            item.setData(order['rate'], QtCore.Qt.UserRole)
            self.parent.offers_model.setItem(row, dojima.data.offers.PRICE, item)

            # offer outstanding
            item = QtGui.QStandardItem()
            item.setData(order['amount'], QtCore.Qt.UserRole)
            self.parent.offers_model.setItem(row, dojima.data.offers.OUTSTANDING, item)

            offer_type = order['type']
            if offer_type == 'sell':
                item = QtGui.QStandardItem(dojima.data.offers.ASK)
                self.parent.offers_model.setItem(row, dojima.data.offers.TYPE, item)
            elif offer_type == 'buy':
                item = QtGui.QStandardItem(dojima.data.offers.BID)
                self.parent.offers_model.setItem(row, dojima.data.offers.TYPE, item)
            else:
                logger.error("Unrecognized order type: %s", offer_type)

            base_symbol, counter_symbol = get_symbols(order['pair'])
            item = QtGui.QStandardItem(base_symbol)
            self.parent.offers_model.setItem(row, dojima.data.offers.BASE, item)
            item = QtGui.QStandardItem(counter_symbol)
            self.parent.offers_model.setItem(row, dojima.data.offers.COUNTER, item)            
            row += 1


class BtceTradeRequest(_BtcePrivateRequest):
    method = 'Trade'

    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw)
        if data['success'] == 0:
            logger.error("%s: %s", data['error'], self.query)
            return

        base_symbol, counter_symbol = get_symbols(self.pair)
        row = self.parent.offers_model.rowCount()

        item = QtGui.QStandardItem()
        item.setData(self.price, QtCore.Qt.UserRole)
        self.parent.offers_model.setItem(row, dojima.data.offers.PRICE, item)
        
        item = QtGui.QStandardItem()
        item.setData(self.amount, QtCore.Qt.UserRole)
        self.parent.offers_model.setItem(row, dojima.data.offers.OUTSTANDING, item)        

        item = QtGui.QStandardItem(self.type_)
        self.parent.offers_model.setItem(row, dojima.data.offers.TYPE, item)

        item = QtGui.QStandardItem(base_symbol)
        self.parent.offers_model.setItem(row, dojima.data.offers.BASE, item)
        item = QtGui.QStandardItem(counter_symbol)
        self.parent.offers_model.setItem(row, dojima.data.offers.COUNTER, item)
        
        if self.type_ is dojima.data.offers.ASK:
            total = (- self.amount)
            proxy = self.parent.balance_proxies[base_symbol]
            proxy.balance_liquid_changed.emit(total)
                
        elif self.type_ is dojima.data.offers.BID:
            total = (- (self.price * self.amount))
            proxy = self.parent.balance_proxies[counter_symbol]
            proxy.balance_liquid_changed.emit(total)

            
class BtceEditCredentialsAction(dojima.exchange.EditCredentialsAction):

    def show_dialog(self):
        dialog = BtceEditCredentialsDialog(self.parent())
        if dialog.exec_():
            self.accountSettingsChanged.emit()

        
class BtceEditCredentialsDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        super(BtceEditCredentialsDialog, self).__init__(parent)

        self.key_edit = QtGui.QLineEdit()
        self.secret_edit = QtGui.QLineEdit()
        button_box = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Save)
        button_box.accepted.connect(self.save)
        button_box.rejected.connect(self.reject)
        
        layout = QtGui.QFormLayout()
        layout.addRow(QtCore.QCoreApplication.translate(PRETTY_NAME, "API Key"), self.key_edit)
        layout.addRow(QtCore.QCoreApplication.translate(PRETTY_NAME, "API Secret"), self.secret_edit)
        layout.addRow(button_box)
        self.setLayout(layout)

        key, secret = loadAccountSettings()
        if key:
            self.key_edit.setText(key)
        if secret:
            self.secret_edit.setText(secret)      

    def save(self):
        saveAccountSettings(self.key_edit.text(), self.secret_edit.text())
        self.accept()
        
            
"""        
class BtceAccount:

    def _orderlist_handler(self, data):
        data = data['return']
        if not data:
            return
        asks = dict()
        bids = dict()
        for order_id, order in list(data.items()):
            price = order['rate']
            amount = order['amount']
            order_type = order['type']
            pair = order['pair']

            if order_type == 'sell':
                if pair not in asks:
                    asks[pair] = list()
                asks[pair].append((order_id, price, amount,))
            elif order_type == 'buy':
                if pair not in bids:
                    bids[pair] = list()
                bids[pair].append((order_id, price, amount,))
            else:
                logger.warning("unknown order type: %s", order_type)

        for pair, orders in list(asks.items()):
            if pair in self.orders_proxies:
                self.orders_proxies[pair].asks.emit(orders)
        for pair, orders in list(bids.items()):
            if pair in self.orders_proxies:
                self.orders_proxies[pair].bids.emit(orders)

    def place_ask_limit_order(self, remote, amount, price):
        self._place_order(remote, 'sell', amount, price)

    def place_bid_limit_order(self, remote, amount, price):
        self._place_order(remote, 'buy', amount, price)

    def _place_order(self, remote_pair, order_type, amount, price):
        params = {'pair': remote_pair,
                  'type': order_type,
                  'amount': str(amount),
                  'rate': str(price)}
        raise NotImplementedError

    def _trade_handler(self, data):
        order_id = data['return']['order_id']
        amount = data['return']['remains']
        price = data['query']['rate']
        pair = data['query']['pair']
        order_type = data['query']['type']
        if order_type == 'sell':
            logger.info("ask order %s in place", order_id)
            if pair in self.orders_proxies:
                self.orders_proxies[pair].ask.emit((order_id, price, amount,))
        elif order_type == 'buy':
            logger.info("bid order %s in place", order_id)
            if pair in self.orders_proxies:
                self.orders_proxies[pair].bid.emit((order_id, price, amount,))
        self._emit_funds(data['return']['funds'])


    def _emit_funds(self, data):
        for symbol, balance in list(data.items()):
            if symbol in self.funds_proxies:
                self.funds_proxies[symbol].balance.emit(Decimal(balance))
            else:
                logger.info("ignoring %s balance", symbol)

    def get_commission(self, amount, remote_market=None):
        return amount * self.commission
"""
    
def parse_markets():
    if PLAIN_NAME in dojima.exchanges.container: return

    exchange_proxy = BtceExchangeProxy()
    dojima.exchanges.container.addExchange(exchange_proxy)

parse_markets()
