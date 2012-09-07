# Tulpenmanie, a commodities market client.
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

import decimal
import hashlib
import heapq
import hmac
import json
import logging
import time

from PyQt4 import QtCore, QtGui, QtNetwork

import tulpenmanie.providers
from tulpenmanie.model.order import OrdersModel


logger = logging.getLogger(__name__)


EXCHANGE_NAME = "BTC-e"
COMMODITIES = ( 'btc', 'ltc', 'nmc', 'rur', 'usd' )
HOSTNAME = "btc-e.com"
_PUBLIC_BASE_URL = "https://" + HOSTNAME + "/api/2/"
_PRIVATE_URL = "https://" + HOSTNAME + "/tapi"



class BtceError(Exception):

    def __init__(self, value):
        self.value = value
    def __str__(self):
        error_msg= repr(self.value)
        logger.error(error_msg)
        return error_msg

class BtceRequest(QtCore.QObject):

    def __init__(self, url, handler, parent, data=None):
        self.url = url
        self.handler = handler
        self.parent = parent
        self.data = data
        self.reply = None
        self._prepare_request()


    def _prepare_request(self):
        self.request = QtNetwork.QNetworkRequest(self.url)
        self.request.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader,
                               "application/x-www-form-urlencoded")
        query = QtCore.QUrl()
        if self.data:
            for key, value in self.data['query'].items():
                query.addQueryItem(key, str(value))
        self.query = query.encodedQuery()

    def post(self):
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("POSTing to %s", self.url.toString())
        self.reply = self.parent.network_manager.post(self.request,
                                                      self.query)
        self.reply.finished.connect(self._process_reply)

    def _object_pairs_hook(self, pairs):
        dct = dict()
        for key, value in pairs:
            if key == 'ticker':
                return value
            dct[key] = decimal.Decimal(value)
        return dct

    def _process_reply(self):
        if self.reply.error():
            logger.error(self.reply.errorString())
        else:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("received reply to %s", self.url.toString())
            raw = str(self.reply.readAll())
            self.data = json.loads(raw,
                                   object_pairs_hook=self._object_pairs_hook)
            self.handler(self.data)
        self.reply.deleteLater()
        self.parent._replies.remove(self)


class BtcePrivateRequest(BtceRequest):
    url = QtCore.QUrl(_PRIVATE_URL)

    def __init__(self, method, handler, parent, data=None):
        self.method = method
        self.handler = handler
        self.parent = parent
        self.data = data
        self.reply = None
        self._prepare_request()

    def _prepare_request(self):
        self.request = QtNetwork.QNetworkRequest(self.url)
        self.request.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader,
                          "application/x-www-form-urlencoded")
        query = QtCore.QUrl()
        query.addQueryItem('method', self.method)
        self.parent.nonce += 1
        query.addQueryItem('nonce', str(self.parent.nonce))
        if self.data:
            for key, value in self.data['query'].items():
                query.addQueryItem(key, str(value))
        self.query = query.encodedQuery()

        h = hmac.new(self.parent._secret, digestmod=hashlib.sha512)
        h.update(self.query)
        sign = h.hexdigest()

        self.request.setRawHeader('Key', self.parent._key)
        self.request.setRawHeader('Sign', sign)

    def _process_reply(self):
        if self.reply.error():
            logger.error(self.reply.errorString())
        else:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("received reply to %s", self.url.toString())
            raw = str(self.reply.readAll())
            data = json.loads(raw)
            if data['success'] != 1:
                msg = str(self.method) + " : " + data['error']
                raise BtceError(msg)
            else:
                if self.data:
                    self.data.update(data)
                else:
                    self.data = data
                self.handler(self.data)
        self.reply.deleteLater()
        self.parent._replies.remove(self)


class _Btce(QtCore.QObject):
    provider_name = EXCHANGE_NAME

    def pop_request(self):
        request = heapq.heappop(self._requests)
        request.post()
        self._replies.add(request)


class BtceExchange(_Btce):

    ask = QtCore.pyqtSignal(decimal.Decimal)
    last = QtCore.pyqtSignal(decimal.Decimal)
    bid = QtCore.pyqtSignal(decimal.Decimal)
    high = QtCore.pyqtSignal(decimal.Decimal)
    low = QtCore.pyqtSignal(decimal.Decimal)
    average = QtCore.pyqtSignal(decimal.Decimal)

    def __init__(self, remote_market, network_manager=None, parent=None):
        if not network_manager:
            network_manager = self.manager.network_manager
        super(BtceExchange, self).__init__(parent)
        remote_market = str(remote_market.replace("/", "_")).lower()
        self._ticker_url = QtCore.QUrl(_PUBLIC_BASE_URL +
                                        remote_market + "/ticker")

        # These must be the same length
        remote_stats = ('buy', 'last', 'sell',
                        'high', 'low', 'avg')
        self.stats = ('ask', 'last', 'bid',
                       'high', 'low', 'average')
        self.is_counter = (True, True, True,
                           True, True, True)

        self._signals = dict()
        self.signals = dict()
        for i in range(len(remote_stats)):
            signal = getattr(self, self.stats[i])
            self._signals[remote_stats[i]] = signal
            self.signals[self.stats[i]] = signal

        # TODO make this wait time a user option
        self.network_manager = network_manager
        self._request_queue = self.network_manager.get_host_request_queue(
            HOSTNAME, 500)
        self._requests = list()
        self._replies = set()

    def refresh(self):
        request = BtceRequest(self._ticker_url, self._ticker_handler, self)
        self._requests.append(request)
        self._request_queue.enqueue(self)

    def _ticker_handler(self, data):
        for key, value in data.items():
            if self._signals.has_key(key):
                signal = self._signals[key]
                signal.emit(value)


class BtceAccount(_Btce, tulpenmanie.providers.ExchangeAccount):

    # BAD rudunant
    markets = ( 'btc_usd', 'btc_rur', 'ltc_btc', 'nmc_btc', 'usd_rur' )

    btc_balance_signal = QtCore.pyqtSignal(decimal.Decimal)
    ltc_balance_signal = QtCore.pyqtSignal(decimal.Decimal)
    nmc_balance_signal = QtCore.pyqtSignal(decimal.Decimal)
    rur_balance_signal = QtCore.pyqtSignal(decimal.Decimal)
    usd_balance_signal = QtCore.pyqtSignal(decimal.Decimal)

    btc_usd_ready_signal = QtCore.pyqtSignal(bool)
    btc_rur_ready_signal = QtCore.pyqtSignal(bool)
    ltc_btc_ready_signal = QtCore.pyqtSignal(bool)
    nmc_btc_ready_signal = QtCore.pyqtSignal(bool)
    usd_rur_ready_signal = QtCore.pyqtSignal(bool)

    def __init__(self, credentials, network_manager=None, parent=None):
        if network_manager is None:
            network_manager = self.manager.network_manager
        super(BtceAccount, self).__init__(parent)
        self._key = str(credentials[2])
        self._secret = str(credentials[3])

        self.network_manager = network_manager
        self._request_queue = self.network_manager.get_host_request_queue(
            HOSTNAME, 5000)
        self._requests = list()
        self._replies = set()

        self.ask_orders = dict()
        self.bid_orders = dict()
        # TODO maybe divide smaller
        self.nonce = int(time.time() / 2)

    def check_order_status(self, remote_pair):
        signal = getattr(self, remote_pair + "_ready_signal")
        signal.emit(True)

    def refresh(self):
        request = BtcePrivateRequest('getInfo', self._getinfo_handler, self)
        self._requests.append(request)
        self._request_queue.enqueue(self)

    def _getinfo_handler(self, data):
        self._emit_funds(data['return']['funds'])

    def refresh_orders(self):
        request = BtcePrivateRequest('OrderList', self._orderlist_handler, self)
        self._requests.append(request)
        self._request_queue.enqueue(self)

    def _orderlist_handler(self, data):
        data = data['return']
        if data:
            for models in self.ask_orders, self.bid_orders:
                for model in models.values():
                    model.clear_orders()
        for order_id, order in data.items():
            price = order['rate']
            amount = order['amount']
            order_type = order['type']
            pair = order['pair']

            if order_type == u'sell':
                self.ask_orders[pair].append_order(order_id, price, amount)
            elif order_type == u'buy':
                self.bid_orders_model[pair].append_order(order_id, price, amount)
            else:
                logger.error("unknown order type: %s", order_type)
                return

            for models in self.ask_orders, self.bid_orders:
                for model in models.values():
                    model.sort(1, QtCore.Qt.DescendingOrder)

    def place_bid_order(self, remote, amount, price):
        self._place_order(remote, 'buy', amount, price)

    def place_ask_order(self, remote, amount, price):
        self._place_order(remote, 'sell', amount, price)

    def _place_order(self, remote_pair, order_type, amount, price):
        data = {'query':{'pair': remote_pair,
                         'type': order_type,
                         'amount': amount,
                         'rate': price} }
        request = BtcePrivateRequest('Trade', self._trade_handler, self, data)
        self._requests.append(request)
        self._request_queue.enqueue(self)

    def _trade_handler(self, data):
        order_id = data['return']['order_id']
        amount = data['return']['remains']
        price = data['query']['rate']
        pair = data['query']['pair']
        order_type = data['query']['type']
        if order_type == 'sell':
            self.ask_orders[pair].append_order(order_id, price, amount)
        elif order_type == 'buy':
            self.bid_orders[pair].append_order(order_id, price, amount)
        self._emit_funds(data['return']['funds'])

    def cancel_ask_order(self, pair, order_id):
        self._cancel_order(pair, order_id, 'ask')

    def cancel_bid_order(self, pair, order_id):
        self._cancel_order(pair, order_id, 'bid')

    def _cancel_order(self, pair, order_id, order_type):
        data = {'pair':pair,
                'type':order_type,
                'query':{'order_id':order_id}}
        request = BtcePrivateRequest('CancelOrder', self._cancelorder_handler,
                                     self, data)
        self._requests.append(request)
        self._request_queue.enqueue(self)

    def _cancelorder_handler(self, data):
        order_id = data['return']['order_id']
        pair = data['pair']
        order_type = data['type']
        if order_type == 'ask':
            self.ask_orders[pair].remove_order(order_id)
        elif order_type == 'bid':
            self.bid_orders[pair].remove_order(order_id)
        self._emit_funds(data['return']['funds'])

    def _emit_funds(self, data):
        for commodity, balance in data.items():
            signal = getattr(self, commodity + '_balance_signal', None)
            if signal:
                signal.emit(decimal.Decimal(balance))
            else:
                logger.warning("unknown commodity %s", commodity)

class BtceProviderItem(tulpenmanie.providers.ProviderItem):

    provider_name = EXCHANGE_NAME

    COLUMNS = 3
    MARKETS, ACCOUNTS, REFRESH_RATE = range(COLUMNS)
    mappings = (('refresh rate', REFRESH_RATE),)

    markets = ( 'btc_usd', 'btc_rur', 'ltc_btc', 'nmc_btc', 'usd_rur' )

    ACCOUNT_COLUMNS = 4
    ACCOUNT_ID, ACCOUNT_ENABLE, ACCOUNT_KEY, ACCOUNT_SECRET = range(ACCOUNT_COLUMNS)
    account_mappings = (('identifier', ACCOUNT_ID),
                        ('enable', ACCOUNT_ENABLE),
                        ('key', ACCOUNT_KEY),
                        ('secret', ACCOUNT_SECRET))

    numeric_settings = (REFRESH_RATE,)
    boolean_settings = ()
    required_account_settings = (ACCOUNT_KEY, ACCOUNT_SECRET)
    hidden_account_settings = ()


tulpenmanie.providers.register_exchange(BtceExchange)
tulpenmanie.providers.register_account(BtceAccount)
tulpenmanie.providers.register_exchange_model_item(BtceProviderItem)
