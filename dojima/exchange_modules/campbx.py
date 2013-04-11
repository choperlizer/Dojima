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

import heapq
import json
import logging
from decimal import Decimal

import numpy as np
from PyQt4 import QtCore, QtGui, QtNetwork


import dojima.exchange
import dojima.exchanges
import dojima.data.market
import dojima.data.offers
import dojima.network


logger = logging.getLogger(__name__)

PRETTY_NAME = "CampBX"
HOSTNAME = "campbx.com"
URL_BASE = "https://" + HOSTNAME + "/api/"

def _reply_has_errors(reply):
    if reply.error():
        logger.error(reply.errorString())

def saveAccountSettings(username, password):
    settings = QtCore.QSettings()
    settings.beginGroup(__name__)
    settings.setValue('username', username)
    settings.setValue('password', password)

def loadAccountSettings():
    settings = QtCore.QSettings()
    settings.beginGroup(__name__)
    username = settings.value('username')
    password = settings.value('password')
    return username, password


class CampbxExchangeProxy(dojima.exchange.ExchangeProxy):

    id = __name__
    name = PRETTY_NAME
    local_market_map = dict()
    remote_market_map = dict()

    def __init__(self):
        self.exchange_object = None

    def getExchangeObject(self):
        if self.exchange_object is None:
            self.exchange_object = CampbxExchange()

        return self.exchange_object

    def getPrettyMarketName(self, market_id):
        return market_id

    def getWizardPage(self, wizard):
        return CampbxWizardPage(wizard)

    def refreshMarkets(self):
        local_base_id = dojima.model.commodities.remote_model.getRemoteToLocalMap('campbx-BTC')
        local_counter_id = dojima.model.commodities.remote_model.getRemoteToLocalMap('campbx-USD')

        if ((local_base_id is None) or
            (local_counter_id is None)): return

        local_pair = local_base_id + '_' + local_counter_id

        if local_pair in self.local_market_map:
            local_map = self.local_market_map[local_pair]
        else:
            local_map = list()
            self.local_market_map[local_pair] = local_map

        if 'BTCUSD' not in local_map:
            local_map.append('BTCUSD')

        self.remote_market_map['BTCUSD'] = local_pair

        dojima.markets.container.addExchange(self, local_pair,
                                             local_base_id, local_counter_id)


class CampbxWizardPage(QtGui.QWizardPage):

    def __init__(self, parent):
        super(CampbxWizardPage, self).__init__(parent)
        self.setTitle(PRETTY_NAME)
        self._is_complete = False

    def checkCompleteState(self):
        if ( len(self.username_edit.text()) < 4 or
             len(self.password_edit.text())   < 4 or
             self.base_combo.currentIndex() == self.counter_combo.currentIndex() ):
            is_complete = False
            
        else:
            is_complete = True

        if self._is_complete is not is_complete:
            self._is_complete = is_complete
            self.completeChanged.emit()

    def initializePage(self):
        self.username_edit = QtGui.QLineEdit()
        self.password_edit = QtGui.QLineEdit(echoMode=QtGui.QLineEdit.Password)
        self.base_combo = QtGui.QComboBox()
        self.counter_combo = QtGui.QComboBox()

        new_local_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate(PRETTY_NAME, "New Commodity",
                                              "The label on the new "
                                              "commodity button in the "
                                              "new market wizard."))

        button_box = QtGui.QDialogButtonBox()
        button_box.addButton(new_local_button, button_box.ActionRole)

        layout = QtGui.QFormLayout()
        layout.addRow(QtCore.QCoreApplication.translate(PRETTY_NAME, "Username"), self.username_edit)
        layout.addRow(QtCore.QCoreApplication.translate(PRETTY_NAME, "Password"), self.password_edit)
        layout.addRow(QtCore.QCoreApplication.translate(PRETTY_NAME, "Local Bitcoin Commodity"), self.base_combo)
        layout.addRow(QtCore.QCoreApplication.translate(PRETTY_NAME, "Local US Dollar Commodity"), self.counter_combo)
        layout.addRow(button_box)
        self.setLayout(layout)

        self.base_combo.setModel(dojima.model.commodities.local_model)
        self.counter_combo.setModel(dojima.model.commodities.local_model)

        self.username_edit.editingFinished.connect(self.checkCompleteState)
        self.password_edit.editingFinished.connect(self.checkCompleteState)

        new_local_button.clicked.connect(self.showNewCommodityDialog)
        self.username_edit.textChanged.connect(self.checkCompleteState)
        self.password_edit.textChanged.connect(self.checkCompleteState)
        self.base_combo.currentIndexChanged.connect(self.checkCompleteState)
        self.counter_combo.currentIndexChanged.connect(self.checkCompleteState)

        username, password = loadAccountSettings()
        if username:
            self.username_edit.setText(username)
        if password:
            self.password_edit.setText(password)

        self.checkCompleteState()

    def isComplete(self):
        return self._is_complete

    def nextId(self):
        return -1

    def showNewCommodityDialog(self):
        dialog = dojima.ui.edit.commodity.NewCommodityDialog(self)
        dialog.exec_()

    def validatePage(self):
        saveAccountSettings(self.username_edit.text(), self.password_edit.text())

        local_base_id    = self.base_combo.itemData(self.base_combo.currentIndex(), QtCore.Qt.UserRole)
        local_counter_id = self.counter_combo.itemData(self.counter_combo.currentIndex(), QtCore.Qt.UserRole)

        dojima.model.commodities.remote_model.map('campbx-BTC', local_base_id)
        dojima.model.commodities.remote_model.map('campbx-USD', local_counter_id)
        return dojima.model.commodities.remote_model.submit()


class CampbxExchange(QtCore.QObject, dojima.exchange.Exchange):
    valueType = Decimal

    accountChanged = QtCore.pyqtSignal(str)
    exchange_error_signal = QtCore.pyqtSignal(str)
    
    def __init__(self, network_manager=None, parent=None):
        if network_manager is None:
            network_manager = dojima.network.get_network_manager()
        super(CampbxExchange, self).__init__(parent)

        self.network_manager = network_manager
        self.host_queue = self.network_manager.get_host_request_queue(HOSTNAME, 500)
        self.requests = list()
        self.replies = set()

        self._ticker_refresh_rate = 16

        self.account_validity_proxies = dict()
        self.balance_proxies = dict()
        self.ticker_proxy = dojima.data.market.TickerProxy(self)
        self.depth_proxy = dojima.data.market.DepthProxy(self, 'BTCUSD')
        self.ticker_clients = 0
        self.ticker_timer = QtCore.QTimer(self)
        self.ticker_timer.timeout.connect(self.refreshTicker)

        self.account_validity_proxy = dojima.data.account.AccountValidityProxy(self)

        self.base_balance_proxy = dojima.data.balance.BalanceProxy(self)
        self.counter_balance_proxy = dojima.data.balance.BalanceProxy(self)

        self.offers_model = dojima.data.offers.Model()
        self.offer_proxy_asks = dojima.data.offers.FilterAsksModel(self.offers_model)
        self.offer_proxy_bids = dojima.data.offers.FilterBidsModel(self.offers_model)
                
        self.loadAccountCredentials()

    def cancelAskOffer(self, order_id, market_id=None):
        self._cancel_offer(order_id, 'Sell')
    
    def cancelBidOffer(self, order_id, market_id=None):
        self._cancel_offer(order_id, 'Buy')

    def _cancel_offer(self, order_id, order_type):
        params = {'Type' : order_type, 'OrderID' : order_id}
        CampbxCancelOrderRequest(params, self)
        
    def getBalanceBaseProxy(self, market=None):
        return self.base_balance_proxy

    def getBalanceCounterProxy(self, market=None):
        return self.counter_balance_proxy

    def getDepthProxy(self, market=None):
        return self.depth_proxy

    def getOffersModelAsks(self, market=None):
        return self.offer_proxy_asks

    def getOffersModelBids(self, market=None):
        return self.offer_proxy_bids
    
    def getTickerProxy(self, market=None):
        return self.ticker_proxy

    def getTickerRefreshRate(self):
        return self._ticker_refresh_rate

    def hasAccount(self, market=None):
        return (self._username and self._password)

    def loadAccountCredentials(self):
        self._username, self._password = loadAccountSettings()

    def placeAskLimitOffer(self, amount, price, market=None):
         self._place_order(dojima.data.offers.ASK, "QuickSell", amount, price)

    def placeBidLimitOffer(self, amount, price, market=None):
        self._place_order(dojima.data.offers.BID, "QuickBuy", amount, price)

    def _place_order(self, type_, mode, quantity, price):
        params = {'TradeMode': mode, 'Quantity': str(quantity), 'Price': str(price)}
        request = CampbxTradeRequest(params, self)
        request.type_ = type_
        request.price = price
        request.quantity = quantity

    def pop_request(self):
        request = heapq.heappop(self.requests)[1]
        request.send()

    def refreshBalance(self, market=None):
        CampbxFundsRequest(None, self)
    
    def refreshDepth(self, market=None):
        CampbxDepthRequest(self)

    def refreshTicker(self, market=None):
        CampbxTickerRequest(self)

    def refreshOffers(self, market=None):
        CampbxOrdersRequest(None, self)

    def setTickerStreamState(self, state, market=None):
        if state:
            self.ticker_clients += 1
            if self.ticker_timer.isActive():
                self.ticker_timer.setInterval(self._ticker_refresh_rate * 1000)
                return
            logger.info("starting ticker stream")
            self.ticker_timer.start(self._ticker_refresh_rate * 1000)
        else:
            if self.ticker_clients >1:
                self.ticker_clients -= 1
                return
            if self.ticker_clients == 0:
                return
            self.ticker_clients = 0
            logger.info("stopping ticker stream")
            self.ticker_timer.stop()


class _CampbxRequest(dojima.network.ExchangePOSTRequest):
    priority = 3
    host_priority = None

    query = QtCore.QUrl().encodedQuery()
    
    def __init__(self, parent):
        self.parent = parent
        self.reply = None
        parent.requests.append( (self.priority, self,) )
        parent.host_queue.enqueue(self.parent, self.host_priority)

    def _prepare_request(self):
        self.request = dojima.network.NetworkRequest(self.url)
        self.request.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader,
                               "application/x-www-form-urlencoded")
        
        
class _CampbxPrivateRequest(_CampbxRequest):
    priority = 2

    def __init__(self, params, parent):
        self.params = params
        self.parent = parent
        self.reply = None
        parent.requests.append( (self.priority, self,) )
        parent.host_queue.enqueue(self.parent, self.host_priority)

    def _prepare_request(self):
        self.request = dojima.network.NetworkRequest(self.url)
        self.request.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader,
                               "application/x-www-form-urlencoded")
        query = QtCore.QUrl()
        query.addQueryItem('user', self.parent._username)
        query.addQueryItem('pass', self.parent._password)
        if self.params:
            for key, value in list(self.params.items()):
                query.addQueryItem(key, value)
        self.query = query.encodedQuery()

        
class CampbxDepthRequest(_CampbxRequest):
    url = QtCore.QUrl(URL_BASE + 'xdepth.php')
    
    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw)
        asks = np.array(data['Asks']).transpose()
        bids = np.array(data['Bids']).transpose()
        
        self.parent.depth_proxy.processDepth(asks, bids)


class CampbxTickerRequest(_CampbxRequest):
    url = QtCore.QUrl(URL_BASE + 'xticker.php')

    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw, object_pairs_hook=self.object_pairs_hook)
        logger.debug(data)
        
        self.parent.ticker_proxy.last_signal.emit(data['Last Trade'])
        self.parent.ticker_proxy.ask_signal.emit(data['Best Ask'])
        self.parent.ticker_proxy.bid_signal.emit(data['Best Bid'])

    def object_pairs_hook(self, pairs):
        d = dict()
        for key, value in pairs:
            d[key] = Decimal(value)
        return d
        
        
"""
class CampbxExchangeAccount(_Campbx, dojima.exchange.ExchangeAccount):

    accountChanged = QtCore.pyqtSignal(str)

    _myfunds_url = QtCore.QUrl(_BASE_URL + "myfunds.php")
    _myorders_url = QtCore.QUrl(_BASE_URL + "myorders.php")
    _tradeenter_url = QtCore.QUrl(_BASE_URL + "tradeenter.php")
    _tradeadv_url = QtCore.QUrl(_BASE_URL + "tradeadv.php")
    _tradecancel_url = QtCore.QUrl(_BASE_URL + "tradecancel.php")
    _getbtcaddr_url = QtCore.QUrl(_BASE_URL + "getbtcaddr.php")
    _sendbtc_url = QtCore.QUrl(_BASE_URL + "sendbtc.php")

    bitcoin_deposit_address_signal = QtCore.pyqtSignal(str)
    withdraw_bitcoin_reply_signal = QtCore.pyqtSignal(str)

    commission = Decimal('0.0055')

    def __init__(self, exchangeObj, network_manager=None):
        if network_manager is None:
            network_manager = dojima.network.get_network_manager()
        super(CampbxExchangeAccount, self).__init__(exchangeObj)
        self.base_query = QtCore.QUrl()
        self.network_manager = network_manager
        self.host_queue = self.network_manager.get_host_request_queue(
            HOSTNAME, 500)
        self.requests = list()
        self.replies = set()

        self.offers_model = dojima.data.offers.Model()

        self._bitcoin_deposit_address = None

        settings = QtCore.QSettings()
        settings.beginGroup('CampBX')
        self._username = settings.value('username')
        self._password = settings.value('password')

    def hasAccount(self, market=None):
        return (self._username and self._password)

    def getOffersModel(self, market=None):
        return self.offers_model


    def _place_order(self, trade_type, amount, price=None):


    def get_bitcoin_deposit_address(self):
        if self._bitcoin_deposit_address:
            self.bitcoin_deposit_address_signal.emit(
                self._bitcoin_deposit_address)
        else:
            request = CampbxBitcoinAddressRequest(
                self._getbtcaddr_url, self)

    def withdraw_bitcoin(self, address, amount):
        data = {'query':
                {'BTCTo': address,
                 'BTCAmt': amount}}
        CampbxWithdrawBitcoinRequest(self._sendbtc_url, self, data)

    def get_commission(self, amount, remote_market=None):
        return amount * self.commission
"""


class CampbxFundsRequest(_CampbxPrivateRequest):
    url = QtCore.QUrl(URL_BASE + 'myfunds.php')
    priority = 2
    
    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw)

        value = data['Total USD']
        value = Decimal(value)
        self.parent.counter_balance_proxy.balance_total.emit(value)
        
        value = data['Total BTC']
        value = Decimal(value)
        self.parent.base_balance_proxy.balance_total.emit(value)

        value = data['Liquid USD']
        value = Decimal(value)
        self.parent.counter_balance_proxy.balance_liquid.emit(value)

        value = data['Liquid BTC']
        value = Decimal(value)
        self.parent.base_balance_proxy.balance_liquid.emit(value)
        

class CampbxOrdersRequest(_CampbxPrivateRequest):
    url = QtCore.QUrl(URL_BASE + 'myorders.php')
    
    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw)

        self.parent.offers_model.clear()
        row = 0

        if not 'Info' in data['Buy'][0]:
            for order in data['Buy']:
                self.addOrder(row, order, dojima.data.offers.BID)
                row += 1

        if not 'Info' in data['Sell'][0]:
            for order in data['Sell']:
                self.addOrder(row, order, dojima.data.offers.ASK)
                row += 1

    def addOrder(self, row, order, type_):
        item = QtGui.QStandardItem(order['Order ID'])
        self.parent.offers_model.setItem(row, dojima.data.offers.ID, item)

        item = QtGui.QStandardItem()
        item.setData(Decimal(order['Price']), QtCore.Qt.UserRole)
        self.parent.offers_model.setItem(row, dojima.data.offers.PRICE, item)

        assert order['Quantity']
        item = QtGui.QStandardItem()
        item.setData(Decimal(order['Quantity']), QtCore.Qt.UserRole)
        self.parent.offers_model.setItem(row, dojima.data.offers.OUTSTANDING, item)
            
        item = QtGui.QStandardItem(type_)
        self.parent.offers_model.setItem(row, dojima.data.offers.TYPE, item)


class CampbxTradeRequest(_CampbxPrivateRequest):
    url = QtCore.QUrl(URL_BASE + 'tradeenter.php')
    priority = 1

    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw)
        
        order_id = int(data['Success'])

        #TODO commissions will throw off these balance estimates
        
        if self.type_ is dojima.data.offers.ASK:
            total = (- self.quantity)
            self.parent.base_balance_proxy.balance_liquid_changed.emit(total)

            if not order_id:
                self.parent.base_balance_proxy.balance_total_changed.emit(total)
                
        elif self.type_ is dojima.data.offers.BID:
            total = (- (self.price * self.quantity))
            self.parent.counter_balance_proxy.balance_liquid_changed.emit(total)

            if not order_id:
                self.parent.counte_balance_proxy.balance_total_changed.emit(total)

        if order_id:
            row = self.parent.offers_model.rowCount()

            item = QtGui.QStandardItem(data['Success'])
            self.parent.offers_model.setItem(row, dojima.data.offers.ID, item)

            item = QtGui.QStandardItem()
            item.setData(self.price, QtCore.Qt.UserRole)
            self.parent.offers_model.setItem(row, dojima.data.offers.PRICE, item)
        
            item = QtGui.QStandardItem()
            item.setData(self.quantity, QtCore.Qt.UserRole)
            self.parent.offers_model.setItem(row, dojima.data.offers.OUTSTANDING, item)        

            item = QtGui.QStandardItem(self.type_)
            self.parent.offers_model.setItem(row, dojima.data.offers.TYPE, item)

                
class CampbxCancelOrderRequest(_CampbxPrivateRequest):
    url = QtCore.QUrl(URL_BASE + 'tradecancel.php')
    priority = 0
    
    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw)

        words = data['Success'].split()
        order_id = words[2]
        search = self.parent.offers_model.findItems(order_id)
        for item in search:
            self.parent.offers_model.removeRow(item.row())

class CampbxBitcoinAddressRequest(_CampbxPrivateRequest):
    url = QtCore.QUrl(URL_BASE + 'getbtcaddr.php')
    priority = 2
    
    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw)
        
        logger.debug(data)
        address = data['Success']
        self.parent._bitcoin_deposit_address = address
        self.parent.bitcoin_deposit_address_signal.emit(address)


class CampbxWithdrawBitcoinRequest(_CampbxPrivateRequest):
    priority = 2
    
    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw)

        transaction = data['Success']
        reply = QtCore.QCoreApplication.translate(
            "CampbxWithdrawBitcoinRequest", "transaction id: {}")
        self.parent.withdraw_bitcoin_reply_signal.emit(
            reply.format(transaction))

def parse_markets():
    if 'campbx' in dojima.exchanges.container: return
    exchange_proxy = CampbxExchangeProxy()
    dojima.exchanges.container.addExchange(exchange_proxy)

parse_markets()
