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

import base64
import heapq
import hashlib
import hmac
import json
import logging
import time

from decimal import Decimal

import matplotlib.dates
import numpy as np
from PyQt4 import QtCore, QtGui, QtNetwork

import dojima.exchange
import dojima.exchanges
import dojima.data.offers
import dojima.data.market
import dojima.network
import dojima.ui.wizard


PRETTY_NAME = "MtGox"
PLAIN_NAME = 'mtgox'
HOSTNAME = "mtgox.com"
URL_BASE = "https://data." + HOSTNAME + "/api/2/"

logger = logging.getLogger(PLAIN_NAME)

market_list = ( 'BTCAUD', 'BTCCAD', 'BTCCHF', 'BTCCNY', 'BTCDKK',
                'BTCEUR', 'BTCGBP', 'BTCHKD', 'BTCJPY', 'BTCNZD',
                'BTCPLN', 'BTCRUB', 'BTCSEK', 'BTCSGD', 'BTCTHB',
                'BTCUSD' )

factors = {'BTC':100000000,
           'AUD':100000,
           'CAD':100000,
           'CHF':100000,
           'CNY':100000,
           'DKK':100000,
           'EUR':100000,
           'GBP':100000,
           'HKD':100000,
           'JPY':1000,
           'NDZ':100000,
           'PLN':100000,
           'RUB':100000,
           'SEK':1000,
           'SGD':100000,
           'THB':100000,
           'USD':100000}

powers = {'BTC':8,
           'AUD':5,
           'CAD':5,
           'CHF':5,
           'CNY':5,
           'DKK':5,
           'EUR':5,
           'GBP':5,
           'HKD':5,
           'JPY':3,
           'NDZ':5,
           'PLN':5,
           'RUB':5,
           'SEK':3,
           'SGD':5,
           'THB':5,
           'USD':5}

def _object_hook(dct):
    if 'value' in dct:
        return int(dct['value_int'])
    else:
        return dct

def get_symbols(pair):
    return pair[:3], pair[3:]
    
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


class MtgoxExchangeProxy(dojima.exchange.ExchangeProxy):

    id = PLAIN_NAME
    name = PRETTY_NAME
    local_market_map = dict()
    remote_market_map = dict()

    def getExchangeObject(self):
        if self.exchange_object is None:
            self.exchange_object = MtgoxExchange()

        return self.exchange_object

    def getPrettyMarketName(self, remote_market_id):
        return remote_market_id

    def getWizardPage(self, wizard):
        return MtgoxWizardPage(wizard)

    def refreshMarkets(self):
        local_base_id = dojima.model.commodities.remote_model.getRemoteToLocalMap('mtgox-BTC')
        for market_symbol in market_list:
            local_counter_id = dojima.model.commodities.remote_model.getRemoteToLocalMap('mtgox-' + market_symbol[3:])
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


class MtgoxWizardPage(dojima.ui.wizard.ExchangeWizardPage):

    def __init__(self, parent):
        super(MtgoxWizardPage, self).__init__(parent)
        self.setTitle(PRETTY_NAME)
        self.setSubTitle(QtCore.QCoreApplication.translate(PRETTY_NAME, 
                                                           "Only one API key/secret pair may be used at a time, thus changing "
                                                           "the key here shall change the key for all MtGox markets."))
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
            QtCore.QCoreApplication.translate('MtGox', "New Commodity",
                                              "The label on the new "
                                              "commodity button in the "
                                              "new market wizard."))

        button_box = QtGui.QDialogButtonBox()
        button_box.addButton(new_local_button, button_box.ActionRole)

        layout = QtGui.QFormLayout()
        layout.addRow(QtCore.QCoreApplication.translate(PRETTY_NAME, "API Key"), self.key_edit)
        layout.addRow(QtCore.QCoreApplication.translate(PRETTY_NAME, "API Secret"),self.secret_edit)
        layout.addRow(QtCore.QCoreApplication.translate(PRETTY_NAME, "Market"), self.market_combo)
        layout.addRow(QtCore.QCoreApplication.translate(PRETTY_NAME, "Local Base Commodity"), self.base_combo)
        layout.addRow(QtCore.QCoreApplication.translate(PRETTY_NAME, "Local Counter Commodity"), self.counter_combo)
        layout.addRow(button_box)
        self.setLayout(layout)

        self.market_combo.addItems(market_list)
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

        self.checkCompleteState()

    def validatePage(self):
        saveAccountSettings(self.key_edit.text(), self.secret_edit.text())
        counter_tla = self.market_combo.currentText()[3:]
        counter_tla = 'mtgox-' + counter_tla

        local_base_id = self.base_combo.itemData(self.base_combo.currentIndex(), QtCore.Qt.UserRole)
        local_counter_id = self.counter_combo.itemData(self.counter_combo.currentIndex(), QtCore.Qt.UserRole)

        dojima.model.commodities.remote_model.map('mtgox-BTC', local_base_id)
        dojima.model.commodities.remote_model.map(counter_tla, local_counter_id)
        return dojima.model.commodities.remote_model.submit()


class MtgoxExchange(QtCore.QObject, dojima.exchange.Exchange):
    valueType = int

    accountChanged = QtCore.pyqtSignal(str)
    exchange_error_signal = QtCore.pyqtSignal(str)

    def __init__(self, network_manager=None, parent=None):
        if not network_manager:
            network_manager = dojima.network.get_network_manager()
        super(MtgoxExchange, self).__init__(parent)
        
        self.network_manager = network_manager
        self.host_queue = self.network_manager.get_host_request_queue(HOSTNAME, 5000)
        self.requests = list()
        self.replies = set()
        #self.factors = dict()

        self._key = None
        self._secret = None
        self._nonce = int(time.time() / 2)     

        self.account_validity_proxies = dict()
        self.balance_proxies = dict()
        self.depth_proxies = dict()
        self.ticker_proxies = dict()
        self.ticker_clients = dict()
        self.trades_proxies = dict()

        self.ticker_timer = QtCore.QTimer(self)
        self.ticker_timer.timeout.connect(self._refresh_tickers)
        self._ticker_refresh_rate = 16

        self.offers_model = dojima.data.offers.Model()
        self.base_offers_proxies = dict()
        self.offers_proxies = dict()
        self.offers_proxies_asks = dict()
        self.offers_proxies_bids = dict()
        
        self.loadAccountCredentials()

    def cancelOffer(self, order_id, pair=None):
        params = {"oid": order_id}
        request = MtgoxCancelOrderRequest(params, self)
        request.order_id = order_id
        
    cancelAskOffer = cancelOffer
    cancelBidOffer = cancelOffer

    def getBalanceBaseProxy(self, pair):
        symbol = pair[:3]
        if symbol not in self.balance_proxies:
            proxy = dojima.data.balance.BalanceProxy(self)
            self.balance_proxies[symbol] = proxy
            return proxy

        return self.balance_proxies[symbol]

    def getBalanceCounterProxy(self, pair):
        symbol = pair[3:]
        if symbol not in self.balance_proxies:
            proxy = dojima.data.balance.BalanceProxy(self)
            self.balance_proxies[symbol] = proxy
            return proxy

        return self.balance_proxies[symbol]

    def getBitcoinDepositAddress(self):
        if self._bitcoin_deposit_address:
            self.bitcoinDepositAddress.emit(self._bitcoin_deposit_address)
            return

        MtgoxBitcoinAddressRequest(None, self)        

    def getDepthProxy(self, pair):
        if pair not in self.depth_proxies:
            proxy = dojima.data.market.DepthProxy(pair, self)
            self.depth_proxies[pair] = proxy
            return proxy

        return self.depth_proxies[pair]        

    def getFactors(self, pair):
        base, counter = get_symbols(pair)
        return factors[base], factors[counter]

    def getMarketSymbols(self, pair):
        return pair[:3], pair[3:]
    
    def getPowers(self, pair):
        base, counter = get_symbols(pair)
        return powers[base], powers[counter]

    def getTradesProxy(self, pair):
        if pair not in self.trades_proxies:
            proxy = dojima.data.market.TradesProxy(pair, self)
            self.trades_proxies[pair] = proxy
            return proxy

        return self.trades_proxies[pair]    

    def hasAccount(self, pair=None):
        return bool(self._key and self._secret)

    def loadAccountCredentials(self):
        key, secret = loadAccountSettings()
        if len(key) + len(secret) != 124:
             self._key, self._secret = None, None
             return

        secret = base64.b64decode(bytes(secret, 'utf'))
        if self._key != key or self._secret != secret:
            self._key = key
            self._secret = secret

            for pair in market_list:
                self.accountChanged.emit(pair)       

    def placeAskLimitOffer(self, amount, price, pair):
        params = {'type':   "ask",
                  'amount': amount,
                  'price':  price }
        request = MtgoxOrderRequest(params, self)
        request.pair = pair
        rquest.pricy = price
        request.amount = amount
        request.type_ = dojima.data.offers.ASK

    def placeBidLimitOffer(self, amount, price, pair):
        params = {'type':   "bid",
                  'amount': amount,
                  'price':  price }
        request = MtgoxOrderRequest(params, self)
        request.pair = pair
        rquest.pricy = price
        request.amount = amount
        request.type_ = dojima.data.offers.BID
        
    def populateMenuBar(self, menu_bar, market_id):
        account_menu = menu_bar.getAccountMenu()
        edit_credentials_action = MtgoxEditCredentialsAction(account_menu)
        account_menu.addAction(edit_credentials_action)
        edit_credentials_action.accountSettingsChanged.connect(self.loadAccountCredentials)
        
    def refreshBalance(self, pair):
        MtgoxInfoRequest(pair, None, self)

    def refreshDepth(self, pair):
        MtgoxDepthRequest(pair, self)

    def refreshOffers(self, pair):
        MtgoxOrdersRequest(pair, None, self)

    def refreshTrades(self, pair):
        MtgoxTradesRequest(pair, self)

    def _refresh_tickers(self):
        for pair in list(self.ticker_clients.keys()):
            MtgoxTickerRequest(pair, self)


class _MtgoxPublicRequest(dojima.network.ExchangeGETRequest):

    def __init__(self, pair, parent):
        self.pair = pair
        self.parent = parent
        self.url = QtCore.QUrl(URL_BASE + pair + self.path)
        self.reply = None
        parent.requests.append( (self.priority, self,) )
        parent.host_queue.enqueue(self.parent, self.host_priority)

        
class MtgoxDepthRequest(_MtgoxPublicRequest):
    path = "/money/depth/fetch"

    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw)
        proxy = self.parent.getDepthProxy(self.pair)

        offers = data['data']['asks']
        a = np.empty((2, len(offers)))
        for i, offer in enumerate(offers):
            a[0,i] = offer["price"]
            a[1,i] = offer["amount"]
        
        proxy.processAsks(a)
        
        offers = data['data']['bids']
        offers.reverse()
        a = np.empty((2, len(offers)))
        for i, offer in enumerate(offers):
            a[0,i] = offer["price"]
            a[1,i] = offer["amount"]

        
        proxy.processBids(a)


class MtgoxTickerRequest(_MtgoxPublicRequest):
    path = "/money/ticker_fast"

    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw, object_hook=_object_hook)
        data = data['data']
        proxy = self.parent.ticker_proxies[self.pair]
        proxy.last_signal.emit(data['last_local'])
        proxy.bid_signal.emit(data['buy'])
        proxy.ask_signal.emit(data['sell'])

        
class MtgoxTradesRequest(_MtgoxPublicRequest):
    path = "/money/trades/fetch"

    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw)["data"]
        
        trades = np.empty((3, len(data),))

        for i, trade in enumerate(data):
            trades[0,i] = trade['date']
            trades[1,i] = trade['price']
            trades[2,i] = trade['amount']

        trades[0] = matplotlib.dates.epoch2num(trades[0])
                                  
        proxy = self.parent.getTradesProxy(self.pair)
        proxy.refreshed.emit(trades)

        
class _MtgoxPrivateRequest(dojima.network.ExchangePOSTRequest):
    priority = 1
    host_priority = 0

    def __init__(self, pair, params, parent):
        self.pair = pair
        self.params = params
        self.parent = parent
        self.reply = None
        parent.requests.append( (self.priority, self,) )
        parent.host_queue.enqueue(self.parent, self.host_priority)
        
    def _prepare_request(self):
        path = self.pair + self.method
        self.url = QtCore.QUrl(URL_BASE + path)
        path = bytes(path, 'utf')
        
        self.request = QtNetwork.QNetworkRequest(self.url)
        self.request.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader,
                          "application/x-www-form-urlencoded")
        query = QtCore.QUrl()
        query.addQueryItem('nonce', str(self.parent._nonce))
        self.parent._nonce += 1
        if self.params:
            for key, value in list(self.params.items()):
                query.addQueryItem(key, value)
        self.query = query.encodedQuery()
        
        h = hmac.new(self.parent._secret, path + b'\0' + bytes(self.query), hashlib.sha512)
        signature =  base64.b64encode(h.digest())

        self.request.setRawHeader('Rest-Key', self.parent._key)
        self.request.setRawHeader('Rest-Sign', signature)

    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw, object_hook=_object_hook)
        if data['result'] != "success":
            logger.error("%s: %s", data['result'], self.query)
            return

        self.handle_reply(data['data'])

            
class MtgoxInfoRequest(_MtgoxPrivateRequest):
    method = "/money/info"
    priority = 2
        
    def handle_reply(self, data):
            for symbol, dict_ in list(data["Wallets"].items()):
                if symbol in self.parent.balance_proxies:
                    proxy = self.parent.balance_proxies[symbol]
                    total_balance = dict_["Balance"]
                    proxy.balance_total.emit(total_balance)
                    proxy.balance_liquid.emit(total_balance - dict_['Open_Orders'])
                else:
                    logger.info("ignoring %s balance", symbol)
                
            #self.parent.commission = Decimal(data['return']['Trade_Fee']) / 100

            
class MtgoxCancelOrderRequest(_MtgoxPrivateRequest):
    method = "/money/order/cancel"
    priority = 0

    def handle_reply(self, data):
        search = self.parent.offers_model.findItems(data["oid"])
        for item in search:
            self.parent.offers_model.removeRows(item.row(), 1)

        
class MtgoxOrdersRequest(_MtgoxPrivateRequest):
    method = "/money/orders"

    def handle_reply(self, data):
        self.parent.offers_model.clear()
        if not data:
            return

        row = 0
        for order in data:
            #id
            item = QtGui.QStandardItem(order["oid"])
            self.parent.offer_model.setItem(row, dojima.data.offer.ID, item)
                                       
            # price
            item = QtGui.QStandardItem()
            item.setData(order["price"], QtCore.Qt.UserRole)
            self.parent.offer_model.setItem(row, dojima.data.PRICE, item)
            
            # outstanding
            item = QtGui.QStandardItem()
            item.setData(order["amount"], QtCore.Qt.UserRole)
            self.parent.offer_model.setItem(row, dojima.data.OUTSTANDING, item)

            # type
            order_type = order["type"]
            if offer_type == "ask":
                item = QtGui.QStandardItem(dojima.data.offers.ASK)
                self.parent.offers_model.setItem(row, dojima.data.offers.TYPE, item)
            elif offer_type == "bid":
                item = QtGui.QStandardItem(dojima.data.offers.BID)
                self.parent.offers_model.setItem(row, dojima.data.offers.TYPE, item)
            else:
                logger.error("Unrecognized order type: %s", offer_type)

            # base
            item = QtGui.QStandardItem(order["item"])
            self.parent.offers_model.setItem(row, dojima.data.offers.BASE, item)

            item = QtGui.QStandardItem(order["currency"])
            self.parent.offers_model.setItem(row, dojima.data.offers.COUNTER, item)

            row += 1


class MtgoxOrderRequest(_MtgoxPrivateRequest):
    method = "/money/order/add"
    priority = 1

    def handle_reply(self, order_id):
        row = self.parent.offers_model.rowCount()
        
        #id
        item = QtGui.QStandardItem(order_id)
        self.parent.offer_model.setItem(row, dojima.data.offer.ID, item)
                                       
        # price
        item = QtGui.QStandardItem()
        item.setData(self.price, QtCore.Qt.UserRole)
        self.parent.offer_model.setItem(row, dojima.data.PRICE, item)
            
        # outstanding
        item = QtGui.QStandardItem()
        item.setData(self.amount, QtCore.Qt.UserRole)
        self.parent.offer_model.setItem(row, dojima.data.OUTSTANDING, item)

        # type
        item = QtGui.QStandardItem(self.type_)
        self.parent.offers_model.setItem(row, dojima.data.offers.TYPE, item)

        base, counter = get_symbols(self.pair)
        # base
        item = QtGui.QStandardItem(base)
        self.parent.offers_model.setItem(row, dojima.data.offers.BASE, item)

        # counter
        item = QtGui.QStandardItem(counter)
        self.parent.offers_model.setItem(row, dojima.data.offers.COUNTER, item)

        
class MtgoxEditCredentialsAction(dojima.exchange.EditCredentialsAction):

    def show_dialog(self):
        dialog = MtgoxEditCredentialsDialog(self.parent())
        if dialog.exec_():
            self.accountSettingsChanged.emit()

        
class MtgoxEditCredentialsDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        super(MtgoxEditCredentialsDialog, self).__init__(parent)

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

        
def parse_markets():
    if 'mtgox' in dojima.exchanges.container: return
    exchange_proxy = MtgoxExchangeProxy()
    dojima.exchanges.container.addExchange(exchange_proxy)

parse_markets()
