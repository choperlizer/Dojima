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

import base64
from decimal import Decimal
import heapq
import hashlib
import hmac
import json
import logging
import random
import time

from PyQt4 import QtCore, QtGui, QtNetwork

import dojima.exchanges
import dojima.exchange
import dojima.data.offers
import dojima.data.market
import dojima.network


logger = logging.getLogger(__name__)

HOSTNAME = "mtgox.com"
_BASE_URL = "https://" + HOSTNAME + "/api/1/"

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


class MtgoxExchangeProxy(object, dojima.exchange.ExchangeProxy):

    id = 'mtgox'
    name = "MtGox"
    local_market_map = dict()
    remote_market_map = dict()

    def __init__(self):
        self.exchange_object = None

    def getExchangeObject(self):
        if self.exchange_object is None:
            self.exchange_object = MtgoxExchange()

        return self.exchange_object

    def getPrettyMarketName(self, remote_market_id):
        return remote_market_id

    def nextPage(self, wizard):
        return MtgoxWizardPage(wizard)

    def refreshMarkets(self):
        local_base_id = dojima.model.commodities.remote_model.getRemoteToLocalMap('mtgox-BTC')
        for market_symbol in market_list:
            local_counter_id = dojima.model.commodities.remote_model.getRemoteToLocalMap('mtgox-' + market_symbol[3:])
            if ((local_base_id is None) or
                (local_counter_id is None)) : continue

            local_pair = str(local_base_id + '_' + local_counter_id)

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


class MtgoxWizardPage(QtGui.QWizardPage):

    def __init__(self, parent):
        super(MtgoxWizardPage, self).__init__(parent)
        self.setTitle("MtGox")
        self.setSubTitle(QtCore.QCoreApplication.translate("MtGox",
            "Only one API key/secret pair may be used at a time, thus changing "
            "the key here shall change the key for all MtGox markets."))
        self._is_complete = True

    def checkCompleteState(self):
        if ((self.key_edit.text().length() != 36) or
            (self.secret_edit.text().length() != 88)):
            self._is_complete = False
        else:
            self._is_complete = True

        self.completeChanged.emit()

    def initializePage(self):
        self.key_edit = QtGui.QLineEdit()
        self.secret_edit = QtGui.QLineEdit() #echoMode=QtGui.QLineEdit.Password)
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
        layout.addRow(
            QtCore.QCoreApplication.translate("MtGox", "API Key"),
            self.key_edit)
        layout.addRow(
            QtCore.QCoreApplication.translate("MtGox", "API Secret"),
            self.secret_edit)
        layout.addRow(
            QtCore.QCoreApplication.translate("MtGox", "Market"),
            self.market_combo)
        layout.addRow(
            QtCore.QCoreApplication.translate("MtGox",
                                              "Local Bitcoin Commodity"),
            self.base_combo)
        layout.addRow(
            QtCore.QCoreApplication.translate("MtGox",
                                              "Local Counter Commodity"),
            self.counter_combo)

        layout.addRow(button_box)

        self.setLayout(layout)

        self.market_combo.addItems(market_list)
        self.base_combo.setModel(dojima.model.commodities.local_model)
        self.counter_combo.setModel(dojima.model.commodities.local_model)

        settings = QtCore.QSettings()
        settings.beginGroup('MtGox')
        self.key_edit.setText(settings.value('API_key'))
        self.secret_edit.setText(settings.value('API_secret'))

        new_local_button.clicked.connect(self.showNewCommodityDialog)

    def isComplete(self):
        return self._is_complete

    def nextId(self):
        return -1

    def saveAccountSettings(self, key, secret):
        settings = QtCore.QSettings()
        settings.beginGroup('MtGox')
        settings.setValue('API_key', key)
        settings.setValue('API_secret', secret)

    def showNewCommodityDialog(self):
        dialog = dojima.ui.edit.commodity.NewCommodityDialog(self)
        dialog.exec_()

    def validatePage(self):
        self.saveAccountSettings(self.key_edit.text(), self.secret_edit.text())

        counter_tla = self.market_combo.currentText()[3:]
        counter_tla.prepend('mtgox-')

        local_base_id = self.base_combo.itemData(
            self.base_combo.currentIndex(), QtCore.Qt.UserRole)
        local_counter_id = self.counter_combo.itemData(
            self.counter_combo.currentIndex(), QtCore.Qt.UserRole)

        dojima.model.commodities.remote_model.map('mtgox-BTC',
                                                  local_base_id)
        dojima.model.commodities.remote_model.map(counter_tla,
                                                  local_counter_id)
        return dojima.model.commodities.remote_model.submit()

class _Mtgox():

    def pop_request(self):
        request = heapq.heappop(self.requests)[1]
        request.send()


class _MtgoxRequest(dojima.network.ExchangePOSTRequest):
    pass


class MtgoxPublicRequest(dojima.network.ExchangePOSTRequest):
    pass


class MtgoxExchange(QtCore.QObject, _Mtgox, dojima.exchange.Exchange):

    exchange_error_signal = QtCore.pyqtSignal(str)

    def __init__(self, network_manager=None, parent=None):
        if not network_manager:
            network_manager = dojima.network.get_network_manager()
        super(MtgoxExchange, self).__init__(parent)
        self.network_manager = network_manager
        self.host_queue = self.network_manager.get_host_request_queue(
            HOSTNAME, 5000)
        self.account_object = None
        self.requests = list()
        self.replies = set()
        self.factors = dict()

        self.account_validity_proxies = dict()

        self.ticker_proxies = dict()
        self.ticker_clients = dict()
        self.ticker_timer = QtCore.QTimer(self)
        self.ticker_timer.timeout.connect(self._refresh_tickers)

        self.depth_proxies =  dict()
        self.trades_proxies = dict()

        self.balance_proxies = dict()

    def getAccountObject(self):
        if self.account_object is None:
            self.account_object = MtgoxExchangeAccount(self)

        return self.account_object

    def getBaseBalanceProxy(self, market):
        if 'BTC' not in self.balance_proxies:
            proxy = dojima.data.balance.BalanceProxy(self)
            self.balance_proxies['BTC'] = proxy
            return proxy

        return self.balance_proxies['BTC']

    def getCounterBalanceProxy(self, market):
        counter_id = market[3:]
        if counter_id not in self.balance_proxies:
            proxy = dojima.data.balance.BalanceProxy(self)
            self.balance_proxies[counter_id] = proxy
            return proxy

        return self.balance_proxies[counter_id]

    def getDepthProxy(self, market_id):
        if market_id not in self.depth_proxies:
            depth_proxy = dojima.data.market.DepthProxy(self, market_id)
            self.depth_proxies[market_id] = depth_proxy
            return depth_proxy
        return self.depth_proxies[market_id]
    
    def getFactors(self, market):
        #base = market[:3]
        counter = market[3:]
        return 100000000, factors[counter]

    def getPowers(self, market):
        counter = market[3:]
        return 8, powers[counter]

    def setTickerStreamState(self, state, remote_market):
        if state is True:
            if not remote_market in self.ticker_clients:
                self.ticker_clients[remote_market] = 1
            else:
                self.ticker_clients[remote_market] += 1

            # BAD Hardcoding
            refresh_rate = 10000

            if self.ticker_timer.isActive():
                self.ticker_timer.setInterval(refresh_rate)
                return
            logger.info(QtCore.QCoreApplication.translate(
                'MtgoxExchangeMarketMarket', "starting ticker stream"))
            self.ticker_timer.start(refresh_rate)
        else:
            if remote_market in self.ticker_clients:
                market_clients = self.ticker_clients[remote_market]
                if market_clients > 1:
                    self.ticker_clients[remote_market] -= 1
                    return
                if market_clients == 1:
                    self.ticker_clients.pop(remote_market)

            if sum(self.ticker_clients.values()) == 0:
                logger.info(QtCore.QCoreApplication.translate(
                    'MtgoxExchangeMarketMarket', "stopping ticker stream"))
                self.ticker_timer.stop()

    def refreshTrades(self, remote_market):
        trades_url = QtCore.QUrl(_BASE_URL + remote_market + '/trades')
        MtgoxTradesRequest(trades_url, self)

    def refreshDepth(self, remote_market):
        depth_url = QtCore.QUrl(_BASE_URL + remote_market + '/depth')
        MtgoxDepthRequest(depth_url, self, {'market_id':remote_market})

                
    def refresh_ticker(self, remote_market):
        ticker_url = QtCore.QUrl(_BASE_URL + remote_market + '/ticker')
        MtgoxTickerRequest(ticker_url, self)

    def _refresh_tickers(self):
        for remote_market in self.ticker_clients.keys():
            ticker_url = QtCore.QUrl(_BASE_URL + remote_market + "/ticker")
            MtgoxTickerRequest(ticker_url, self)


class MtgoxTickerRequest(dojima.network.ExchangePOSTRequest):

    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw, object_hook=_object_hook)
        if data['result'] != u'success':
            self._handle_error(data['error'])
            return
        data = data['return']
        path = self.url.path().split('/')
        remote_market = str(path[3])
        proxy = self.parent.ticker_proxies[remote_market]
        proxy.ask_signal.emit(data['buy'])
        proxy.last_signal.emit(data['last'])
        proxy.bid_signal.emit(data['sell'])


class MtgoxTradesRequest(MtgoxPublicRequest):

    # TODO it may be faster to return (order, order, ...)
    # and transpose rather than (date, price, amount)

    def _handle_reply(self, raw):
        self.dates = list()
        self.prices = list()
        self.amounts = list()

        json.loads(raw, object_hook=self._object_hook)
        self.parent.trades_signal.emit( (self.dates, self.prices, self.amounts) )

    def _object_hook(self, dict_):
        try:
            self.dates.append(int(dict_[u'date']))
            self.prices.append(float(dict_[u'price']))
            self.amounts.append(float(dict_[u'amount']))
        except KeyError:
            return


class MtgoxDepthRequest(MtgoxPublicRequest):

    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw, object_hook=self._object_hook)
        data = data['return']

        proxy = self.parent.getDepthProxy(self.data['market_id'])
        proxy.processDepth(data['asks'], data['bids'])

    def _object_hook(self, dict_):
        try:
            return ( float(dict_['price']), float(dict_['amount']))
        except KeyError:
            return dict_


class MtgoxCurrencyRequest(MtgoxPublicRequest):
    priority = 1
    host_priority = 1

    def _handle_reply(self, raw):
        self.data.update(json.loads(raw))
        pair = self.data['pair']
        data = self.data['return']
        symbol = data['currency']
        places = int(data['decimals'])
        self.parent.multipliers[symbol] = pow(10, places)
        self.parent.check_order_status(pair)


class MtgoxExchangeAccount(QtCore.QObject, _Mtgox, dojima.exchange.ExchangeAccount):
    exchange_error_signal = QtCore.pyqtSignal(str)
    accountChanged = QtCore.pyqtSignal(str)

    bitcoin_deposit_address_signal = QtCore.pyqtSignal(str)
    #withdraw_bitcoin_reply_signal = QtCore.pyqtSignal(str)

    _currency_url = QtCore.QUrl(_BASE_URL + "generic/currency")
    _info_url = QtCore.QUrl(_BASE_URL + "generic/private/info")
    _orders_url = QtCore.QUrl(_BASE_URL + "generic/private/orders")
    _cancel_order_url = QtCore.QUrl("https://" + HOSTNAME +
                                   "/api/0/cancelOrder.php")
    _bitcoin_address_url = QtCore.QUrl(_BASE_URL + "generic/bitcoin/address")
    #_withdraw_bitcoin_url = QtCore.QUrl('https://' + HOSTNAME +
    #                                   '/api/0/withdraw.php')

    def __init__(self, exchangeObj, network_manager=None):
        if network_manager is None:
            network_manager = dojima.network.get_network_manager()

        super(MtgoxExchangeAccount, self).__init__(exchangeObj)
        self.exchange_obj = exchangeObj
        self.ask_offers_proxies = dict()
        self.bid_offers_proxies = dict()
        self.offers_proxies = dict()

        self.network_manager = network_manager
        self.host_queue = self.network_manager.get_host_request_queue(
            HOSTNAME, 5000)
        self.requests = list()
        self.replies = set()
        self._bitcoin_deposit_address = None
        self.commission = None
        self.nonce = int(time.time() / 2)

        self.offers_proxies = dict()
        self.offers_model = dojima.data.offers.Model()

        settings = QtCore.QSettings()
        settings.beginGroup('MtGox')
        self._key = str(settings.value('API_key'))
        self._secret = base64.b64decode(settings.value('API_secret'))

    def cancelAskOffer(self, order_id, pair):
        self._cancel_order(pair, order_id, 1)
    def cancelBidOffer(self, order_id, pair):
        self._cancel_order(pair, order_id, 2)

    def _cancel_order(self, pair, order_id, order_type):
        # Mtgox doesn't have a method to cancel orders for API 1.
        # type: 1 for ask order or 2 for bid order
        data = {'pair': pair,
                'query': {'oid': order_id, 'type': order_type} }
        request = MtgoxCancelOrderRequest(self._cancel_order_url,
                                          self, data)

    def hasAccount(self, market_id):
        return (self._key and self._secret)

    def getOffersModel(self, market):

        currency = market[3:]

        if currency in self.offers_proxies:
            return self.offers_proxies[currency]

        proxy = QtGui.QSortFilterProxyModel()
        proxy.setSourceModel(self.offers_model)
        proxy.setFilterKeyColumn(dojima.data.offers.COUNTER)
        proxy.setFilterFixedString(currency)
        proxy.setDynamicSortFilter(True)
        self.offers_proxies[currency] = proxy
        return proxy

    def placeAskLimitOffer(self, remote_pair, amount, price):
        self._place_order(remote_pair, 'ask', amount, price)

    def placeBidLimitOffer(self, remote_pair, amount, price):
        self._place_order(remote_pair, 'bid', amount, price)

    def _place_order(self, remote_pair, order_type, amount, price=None):
        counter = remote_pair[3:]
        query_data = {'type': order_type,
                      'amount_int': amount,
                      'price_int': price}

        data = {'pair': remote_pair,
                'query': query_data }

        MtgoxPlaceOrderRequest(QtCore.QUrl(_BASE_URL + remote_pair +
                                           "/private/order/add"),
                               self, data)

    def refreshBalance(self):
        MtgoxInfoRequest(self._info_url, self)

    def refreshOffers(self):
        MtgoxOrdersRequest(self._orders_url, self)

    def get_bitcoin_deposit_address(self):
        if self._bitcoin_deposit_address:
            self.bitcoin_deposit_address_signal.emit(
                self._bitcoin_deposit_address)
            return self._bitcoin_deposit_address
        else:
            MtgoxBitcoinDepositAddressRequest(self._bitcoin_address_url, self)
    """
    def withdraw_bitcoin(self, address, amount):
        data = {'query':
                {'btca': address,
                 'amount': amount}}
        MtgoxWithdrawBitcoinRequest(self._withdraw_bitcoin_url, self, data)
    """

    def get_commission(self, amount, remote_market=None):
        if self.commission is None:
            return None
        return amount * self.commission

class MtgoxPrivateRequest(_MtgoxRequest):
    priority = 1
    host_priority = 0

    def _prepare_request(self):
        self.request = dojima.network.NetworkRequest(self.url)
        self.request.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader,
                          "application/x-www-form-urlencoded")
        query = QtCore.QUrl()
        self.parent.nonce += 1
        query.addQueryItem('nonce', str(self.parent.nonce))
        if self.data:
            for key, value in self.data['query'].items():
                query.addQueryItem(key, str(value))
        self.query = query.encodedQuery()

        h = hmac.new(self.parent._secret, self.query, hashlib.sha512)
        signature =  base64.b64encode(h.digest())

        self.request.setRawHeader('Rest-Key', self.parent._key)
        self.request.setRawHeader('Rest-Sign', signature)


class MtgoxInfoRequest(MtgoxPrivateRequest):
    priority = 2

    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw, object_hook=_object_hook)
        for symbol, dict_ in data['return']['Wallets'].items():
            if symbol in self.parent.exchange_obj.balance_proxies:
                proxy = self.parent.exchange_obj.balance_proxies[symbol]
                balance = dict_['Balance'] -  dict_['Open_Orders']
                proxy.balance.emit(balance)
            else:
                logger.info("ignoring %s balance", symbol)
        self.parent.commission = Decimal(str(data['return']['Trade_Fee'])) / 100


class MtgoxOrdersRequest(MtgoxPrivateRequest):
    priority = 1

    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw, object_hook=_object_hook)
        data = data['return']
        if not data:
            return

        self.parent.offers_model.clear()
        for row, offer in enumerate(data):

            # TODO deduplicate with PlaceOrderRequest

            # offer ID
            item = QtGui.QStandardItem(offer['oid'])
            self.parent.offers_model.setItem(row, dojima.data.offers.ID, item)

            # offer price
            item = QtGui.QStandardItem()
            item.setData(offer['price'], QtCore.Qt.UserRole)
            self.parent.offers_model.setItem(row, dojima.data.offers.PRICE, item)

            # offer outstanding
            item = QtGui.QStandardItem()
            item.setData(offer['amount'], QtCore.Qt.UserRole)
            self.parent.offers_model.setItem(row, dojima.data.offers.OUTSTANDING, item)

            # offer type
            offer_type = offer['type']
            if offer_type == u'ask':
                item = QtGui.QStandardItem(dojima.data.offers.ASK)
            elif offer_type == u'bid':
                item = QtGui.QStandardItem(dojima.data.offers.BID)
            else:
                logger.error("Unrecognized order type: %s", offer_type)
                continue
            self.parent.offers_model.setItem(row, dojima.data.offers.TYPE, item)


class MtgoxPlaceOrderRequest(MtgoxPrivateRequest):
    priority = 1

    def _handle_reply(self, raw):
        logger.debug(raw)
        self.data.update(json.loads(raw, object_hook=_object_hook))
        order_id = self.data['return']
        pair = self.data['pair']

        self.data = data['query']
        amount = self.data['amount']
        price = self.data['price']

        # TODO deduplicate with OrdersRequest

        row = self.parent.offers_model.rowCount()

        item = QtGui.QStandardItem(order_id)
        self.parent.offers_model.setItem(row, dojima.data.offers.ID, item)

        item = QtGui.QStandardItem()
        item.setData(self.data['price'], QtCore.Qt.UserRole)
        self.parent.offers_model.setItem(row, dojima.data.offers.PRICE, item)

        item = QtGui.QStandardItem()
        item.setData(self.data['amount'], QtCore.Qt.UserRole)
        self.parent.offers_model.setItem(row,
                                         dojima.data.offers.OUTSTANDING,
                                         item)

        offer_type = self.data['type']
        if offer_type == u'ask':
            item = QtGui.QStandardItem(dojima.data.offers.ASK)
        elif offer_type == u'bid':
            item = QtGui.QStandardItem(dojima.data.offers.BID)
        else:
            logger.error("Unrecognized order type: %s", offer_type)
            return
        
        self.parent.offers_model.setItem(row, dojima.data.offers.TYPE, item)


class MtgoxCancelOrderRequest(MtgoxPrivateRequest):
    priority = 0

    def _handle_reply(self, raw):
        logger.debug(raw)
        self.data.update(json.loads(raw, object_hook=_object_hook))
        pair = self.data['pair']
        order_id = str(self.data['query']['oid'])

        search = self.parent.offers_model.findItems(order_id)

        for item in search:
            self.parent.offers_model.removeRows(item.row(), 1)


class MtgoxBitcoinDepositAddressRequest(MtgoxPrivateRequest):
    priority = 2

    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw)
        address = data['return']['addr']
        self.parent._bitcoin_deposit_address = address
        self.parent.bitcoin_deposit_address_signal.emit(address)
"""
class MtgoxWithdrawBitcoinRequest(MtgoxPrivateRequest):
    priority = 2

    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw)

        self.parent.withdraw_bitcoin_reply_signal.emit(str(data))
"""

def parse_markets():
    if 'mtgox' in dojima.exchanges.container: return
    exchange_proxy = MtgoxExchangeProxy()
    dojima.exchanges.container.addExchange(exchange_proxy)

parse_markets()
