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


import heapq
import json
import logging
from decimal import Decimal

import numpy as np
from PyQt4 import QtCore, QtGui, QtNetwork

import dojima.exchange
import dojima.exchanges
import dojima.data.account
import dojima.data.market
import dojima.data.offers
import dojima.network
import dojima.ui.wizard

PRETTY_NAME = "Bitstamp"
PLAIN_NAME = "bitstamp"
HOSTNAME = "www.bitstamp.net"
URL_BASE = "https://" + HOSTNAME + "/api/"
MARKET_ID = 'BTCUSD'

logger = logging.getLogger(PLAIN_NAME)

# type - buy or sell (0 - buy; 1 - sell)
BUY = 0
SELL = 1        

def saveAccountSettings(username, password):
    settings = QtCore.QSettings()
    settings.beginGroup(PLAIN_NAME)
    settings.setValue('username', username)
    settings.setValue('password', password)

def loadAccountSettings():
    settings = QtCore.QSettings()
    settings.beginGroup(PLAIN_NAME)
    username = settings.value('username')
    password = settings.value('password')
    return username, password


class BitstampExchangeProxy(dojima.exchange.ExchangeProxySingleMarket):

    id = PLAIN_NAME
    name = PRETTY_NAME
    local_market_map = None
    remote_market_map = None
    base_id = 'bitstamp-BTC'
    counter_id = 'bitstamp-USD'

    def getExchangeObject(self):
        if self.exchange_object is None:
            self.exchange_object = BitstampExchange()
        return self.exchange_object

    def getPrettyMarketName(self, market_id=None):
        return 'BTCUSD'
        
    def getWizardPage(self, wizard):
        return BitstampWizardPage(wizard)

    
class BitstampWizardPage(dojima.ui.wizard.ExchangeWizardPage):
    
    def __init__(self, parent):
        super(BitstampWizardPage, self).__init__(parent)
        self.setTitle(PRETTY_NAME)
        self._is_complete = False

    def checkCompleteState(self):
        if ( len(self.username_edit.text()) < 4 or
             len(self.password_edit.text()) < 4 or
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
        layout.addRow(QtCore.QCoreApplication.translate(PRETTY_NAME, "Customer ID"), self.username_edit)
        layout.addRow(QtCore.QCoreApplication.translate(PRETTY_NAME, "Password"), self.password_edit)
        layout.addRow(QtCore.QCoreApplication.translate(PRETTY_NAME, "Local Bitcoin Commodity"), self.base_combo)
        layout.addRow(QtCore.QCoreApplication.translate(PRETTY_NAME, "Local USD Commodity"), self.counter_combo)
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

    def validatePage(self):
        saveAccountSettings(self.username_edit.text(), self.password_edit.text())

        local_base_id    = self.base_combo.itemData(self.base_combo.currentIndex(), QtCore.Qt.UserRole)
        local_counter_id = self.counter_combo.itemData(self.counter_combo.currentIndex(), QtCore.Qt.UserRole)

        dojima.model.commodities.remote_model.map('bitstamp-BTC', local_base_id)
        dojima.model.commodities.remote_model.map('bitstamp-USD', local_counter_id)
        return dojima.model.commodities.remote_model.submit()


class BitstampExchange(QtCore.QObject, dojima.exchange.ExchangeSingleMarket):
    valueType = Decimal
    
    accountChanged = QtCore.pyqtSignal(str)
    bitcoinDepositAddress = QtCore.pyqtSignal(str)
    bitcoinWithdrawalReply = QtCore.pyqtSignal(str)
    exchange_error_signal = QtCore.pyqtSignal(str)

    def __init__(self, network_manager=None, parent=None):
        if network_manager is None:
            network_manager = dojima.network.get_network_manager()
        super(BitstampExchange, self).__init__(parent)

        self.network_manager = network_manager
        self.host_queue = self.network_manager.get_host_request_queue(HOSTNAME, 500)
        self.requests = list()
        self.replies = set()

        self._username = None
        self._password = None
        self._bitcoin_deposit_address = None
        
        self._ticker_refresh_rate = 16
        self.balance_proxies = dict()
        self.ticker_proxy = dojima.data.market.TickerProxy(self)
        self.depth_proxy = dojima.data.market.DepthProxy('BTCUSD', self)
        self.ticker_clients = 0
        self.ticker_timer = QtCore.QTimer(self)
        self.ticker_timer.timeout.connect(self.refreshTicker)

        self.base_balance_proxy = dojima.data.balance.BalanceProxy(self)
        self.counter_balance_proxy = dojima.data.balance.BalanceProxy(self)

        self.offers_model = dojima.data.offers.Model()
        self.offer_proxy_asks = dojima.data.offers.FilterAsksModel(self.offers_model)
        self.offer_proxy_bids = dojima.data.offers.FilterBidsModel(self.offers_model)
                
        self.loadAccountCredentials()

    def cancelOffer(self, order_id, market=None):
        params = {'id': order_id}
        BitstampCancelOrderRequest(params, self)
        
    cancelAskOffer = cancelOffer
    cancelBidOffer = cancelOffer

    def getBitcoinDepositAddress(self):
        if self._bitcoin_deposit_address:
            self.bitcoinDepositAddress.emit(self._bitcoin_deposit_address)
            return
        
        BitstampBitcoinDepositAddressRequest(None, self)
    
    def hasAccount(self, market=None):
        return bool(self._username and self._password)
        
    def loadAccountCredentials(self, market=None):
        username, password = loadAccountSettings()
        if self._username != username or self._password != password:
            self._username = username
            self._password = password
            self.accountChanged.emit(MARKET_ID)

    def placeAskLimitOffer(self, amount, price, market=None):
        params = {'amount': str(amount), 'price': str(price)}
        request = BitstampSellRequest(params, self)
        request.amount = amount
        request.price = price        

    def placeBidLimitOffer(self, amount, price, market=None):
        params = {'amount': str(amount), 'price': str(price)}
        request = BitstampBuyRequest(params, self)
        request.amount = amount
        request.price = price  

    def populateMenuBar(self, menu_bar, market_id):
        account_menu = menu_bar.getAccountMenu()
        edit_credentials_action = BitstampEditCredentialsAction(account_menu)
        account_menu.addAction(edit_credentials_action)
        edit_credentials_action.accountSettingsChanged.connect(self.loadAccountCredentials)

    def refreshBalance(self, market=None):
        BitstampBalanceRequest(None, self)

    def refreshDepth(self, market=None):
        BitstampOrderBookRequest(self)

    def refreshTicker(self, market=None):
        BitstampTickerRequest(self)

    def refreshOffers(self, market=None):
        BitstampOpenOrdersRequest(None, self)

    def withdrawBitcoin(self, address, amount):
        params = {'address': address,
                  'amount': str(amount)}
        BitstampBitcoinWithdrawalRequest(params, self)        

        
class _BitstampRequest(dojima.network.ExchangeGETRequest):
    priority = 3
    host_priority = None

    
class _BitstampPrivateRequest(dojima.network.ExchangePOSTRequest):

    def _prepare_request(self):
        self.request = QtNetwork.QNetworkRequest(self.url)
        self.request.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader,
                               "application/x-www-form-urlencoded")
        query = QtCore.QUrl()
        query.addQueryItem('user',     self.parent._username)
        query.addQueryItem('password', self.parent._password)
        
        if self.params:
            for key, value in list(self.params.items()):
                query.addQueryItem(key, value)
        self.query = query.encodedQuery()

    
class BitstampOrderBookRequest(_BitstampRequest):
    url = QtCore.QUrl(URL_BASE + 'order_book/')

    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw)

        bids = data['bids']
        bids.reverse()
        bids = np.array(bids, dtype=np.float).transpose()

        asks = data['asks']
        asks = np.array(asks, dtype=np.float).transpose()

        self.parent.depth_proxy.processBidsAsks(bids, asks)


class BitstampTickerRequest(_BitstampRequest):
    url = QtCore.QUrl(URL_BASE + 'ticker/')
    
    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw)
        self.parent.ticker_proxy.last_signal.emit(Decimal(data['last']))
        self.parent.ticker_proxy.bid_signal.emit(Decimal(data['bid']))
        self.parent.ticker_proxy.ask_signal.emit(Decimal(data['ask']))


class BitstampBalanceRequest(_BitstampPrivateRequest):    
    url = QtCore.QUrl(URL_BASE + 'balance/')
    priority = 2

    """
    usd_balance - USD balance
    btc_balance - BTC balance
    usd_reserved - USD reserved in open orders
    btc_reserved - BTC reserved in open orders
    usd_available - USD available for trading
    btc_available - BTC available for trading
    fee - customer trading fee
    """
    
    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw)
        self.parent.base_balance_proxy.balance_total.emit(Decimal(data['btc_balance']))
        self.parent.base_balance_proxy.balance_liquid.emit(Decimal(data['btc_available']))
        self.parent.counter_balance_proxy.balance_total.emit(Decimal(data['usd_balance']))
        self.parent.counter_balance_proxy.balance_liquid.emit(Decimal(data['usd_available']))

                
        fee = data['fee'].rstrip('0')
        self.parent.commission = Decimal(fee) / 100


class BitstampBitcoinDepositAddressRequest(_BitstampPrivateRequest):
    url = QtCore.QUrl(URL_BASE + 'bitcoin_deposit_address/')
    priority = 2

    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw)
        self.parent.bitcoinDepositAddress.emit(data)


class BitstampBitcoinWithdrawalRequest(_BitstampPrivateRequest):
    url = QtCore.QUrl(URL_BASE + 'bitcoin_withdrawal/')
    priority = 2

    def _handle_reply(self, raw):
        logger.debug(raw)
        self.parent.bitcoinWithdrawalReply.emit(raw)
        
        
class BitstampCancelOrderRequest(_BitstampPrivateRequest):
    url = QtCore.QUrl(URL_BASE + 'cancel_order/')
    priority = 0

    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw)

        if data == True:
            search = self.parent.offers_model.findItems(self.params['id'])
            for item in search:
                self.parent.offers_model.removeRow(item.row())

        
class _BitstampOrderRequest(_BitstampPrivateRequest):

    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw)

        if 'error' in data:
            self._handle_error(data['error'])
            return
        
        row = self.parent.offers_model.rowCount()
        
        item = QtGui.QStandardItem(data['id'])
        self.parent.offers_model.setItem(row, dojima.data.offers.ID, item)

        item = QtGui.QStandardItem()
        item.setData(Decimal(data['price']), QtCore.Qt.UserRole)
        self.parent.offers_model.setItem(row, dojima.data.offers.PRICE, item)

        item = QtGui.QStandardItem()
        item.setData(Decimal(data['amount']), QtCore.Qt.UserRole)
        self.parent.offers_model.setItem(row, dojima.data.offers.OUTSTANDING, item)

        item = QtGui.QStandardItem(self.order_type)
        self.parent.offers_model.setItem(row, dojima.data.offers.TYPE, item)

        
class BitstampBuyRequest(_BitstampOrderRequest):
    url = QtCore.QUrl(URL_BASE + 'buy/')
    order_type = dojima.data.offers.BID

    
class BitstampSellRequest(_BitstampOrderRequest):
    url = QtCore.QUrl(URL_BASE + 'sell/')
    order_type = dojima.data.offers.ASK
        
        
class BitstampOpenOrdersRequest(_BitstampPrivateRequest):    
    url = QtCore.QUrl(URL_BASE + 'open_orders/')
    priority = 2

    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw)
        self.parent.offers_model.clear()
        if not data: return

        row = 0

        for order in data:
            self.addOrder(row, order)
            row += 1

    def addOrder(self, row, order):
        item = QtGui.QStandardItem(str(order['id']))
        self.parent.offers_model.setItem(row, dojima.data.offers.ID, item)        

        item = QtGui.QStandardItem()
        item.setData(order['price'], QtCore.Qt.UserRole)
        self.parent.offers_model.setItem(row, dojima.data.offers.PRICE, item)

        item = QtGui.QStandardItem()
        item.setData(order['amount'], QtCore.Qt.UserRole)
        self.parent.offers_model.setItem(row, dojima.data.offers.OUTSTANDING, item)

        if order['type'] == BUY:
            order_type = dojima.data.offers.BID
        else:
            order_type = dojima.data.offers.ASK
        
        item = QtGui.QStandardItem(order_type)           
        self.parent.offers_model.setItem(row, dojima.data.offers.TYPE, item)
        

class BitstampEditCredentialsAction(dojima.exchange.EditCredentialsAction):

    def show_dialog(self):
        dialog = BitstampEditCredentialsDialog(self.parent())
        if dialog.exec_():
            self.accountSettingsChanged.emit()

        
class BitstampEditCredentialsDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        super(BitstampEditCredentialsDialog, self).__init__(parent)
        
        self.username_edit = QtGui.QLineEdit()
        self.password_edit = QtGui.QLineEdit(echoMode=QtGui.QLineEdit.Password)
        button_box = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Save)
        button_box.accepted.connect(self.save)
        button_box.rejected.connect(self.reject)
        
        layout = QtGui.QFormLayout()
        layout.addRow(QtCore.QCoreApplication.translate(PLAIN_NAME, "Username"), self.username_edit)
        layout.addRow(QtCore.QCoreApplication.translate(PLAIN_NAME, "Password"), self.password_edit)
        layout.addRow(button_box)
        self.setLayout(layout)

        username, password = loadAccountSettings()
        if username:
            self.username_edit.setText(username)
        if password:
            self.password_edit.setText(password)

    def save(self):
        saveAccountSettings(self.username_edit.text(), self.password_edit.text())
        self.accept()
        
        
def parse_markets():
    if PLAIN_NAME in dojima.exchanges.container: return
    exchange_proxy = BitstampExchangeProxy()
    dojima.exchanges.container.addExchange(exchange_proxy)

parse_markets()
