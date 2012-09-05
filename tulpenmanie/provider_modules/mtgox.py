# Tuplenmanie, a commodities market client.
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
import decimal
import heapq
import hashlib
import hmac
import json
import logging
import time


from PyQt4 import QtCore, QtGui, QtNetwork

import tulpenmanie.providers
from tulpenmanie.model.order import OrdersModel


logger = logging.getLogger(__name__)


EXCHANGE_NAME = "MtGox"
HOSTNAME = "mtgox.com"
_BASE_URL = "https://" + HOSTNAME + "/api/1/"


def _object_hook(dct):
    if 'value' in dct:
        return decimal.Decimal(dct['value'])
    else:
        return dct


class MtgoxError(Exception):

    def __init__(self, value):
        self.value = value
    def __str__(self):
        error_msg= repr(self.value)
        logger.error(error_msg)
        return error_msg

class MtgoxRequest(QtCore.QObject):

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

    def _process_reply(self):
        if self.reply.error():
            logger.error(self.reply.errorString())
        else:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("received reply to %s", self.url.toString())
            raw = str(self.reply.readAll())
            data = json.loads(raw, object_hook=_object_hook)
            if data['result'] != u'success':
                msg = str(reply.url().toString()) + " : " + data['error']
                raise MtgoxError(msg)
            else:
                if self.data:
                    self.data.update(data)
                else:
                    self.data = data
                self.handler(self.data)
        self.reply.deleteLater()


class MtgoxPrivateRequest(MtgoxRequest):

    def _prepare_request(self):
        self.request = QtNetwork.QNetworkRequest(self.url)
        self.request.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader,
                          "application/x-www-form-urlencoded")
        query = QtCore.QUrl()
        query.addQueryItem('nonce', str(int(time.time() * 16)))
        if self.data:
            for key, value in self.data['query'].items():
                query.addQueryItem(key, str(value))
        self.query = query.encodedQuery()

        h = hmac.new(self.parent._secret, self.query, hashlib.sha512)
        signature =  base64.b64encode(h.digest())

        self.request.setRawHeader('Rest-Key', self.parent._key)
        self.request.setRawHeader('Rest-Sign', signature)

class MtgoxPrivateRequestAPI0(MtgoxPrivateRequest):

    def _process_reply(self):
        if self.reply.error():
            logger.error(self.reply.errorString())
        else:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("received reply to %s", self.url.toString())
            raw = str(self.reply.readAll())
            data = json.loads(raw, object_hook=_object_hook)
            if self.data:
                self.data.update(data)
            else:
                self.data = data
            self.handler(self.data)
        self.reply.deleteLater()


class _Mtgox(QtCore.QObject):
    provider_name = EXCHANGE_NAME

    def pop_request(self):
        request = heapq.heappop(self._requests)
        request.post()
        self._replies.append(request)


class MtgoxExchange(_Mtgox):

    register_url = None

    ask = QtCore.pyqtSignal(decimal.Decimal)
    bid = QtCore.pyqtSignal(decimal.Decimal)
    last = QtCore.pyqtSignal(decimal.Decimal)
    volume = QtCore.pyqtSignal(decimal.Decimal)
    high = QtCore.pyqtSignal(decimal.Decimal)
    high = QtCore.pyqtSignal(decimal.Decimal)
    low = QtCore.pyqtSignal(decimal.Decimal)
    average = QtCore.pyqtSignal(decimal.Decimal)
    VWAP = QtCore.pyqtSignal(decimal.Decimal)

    def __init__(self, remote_market, network_manager=None, parent=None):
        if not network_manager:
            network_manager = self.manager.network_manager
        super(MtgoxExchange, self).__init__(parent)
        self._ticker_url = QtCore.QUrl(_BASE_URL +
                                        remote_market + "/ticker")
        # These must be the same length
        remote_stats = ('sell', 'buy', 'last_local', 'vol',
                        'high', 'low', 'avg', 'vwap')
        self.stats = ('ask', 'bid', 'last', 'volume',
                       'high', 'low', 'average', 'VWAP')
        self.is_counter = (True, True, True, False,
                           True, True, True, True)

        self._signals = dict()
        self.signals = dict()
        for i in range(len(remote_stats)):
            signal = getattr(self, self.stats[i])
            self._signals[remote_stats[i]] = signal
            self.signals[self.stats[i]] = signal

        # TODO make this wait time a user option
        self.network_manager = network_manager
        self._request_queue = self.network_manager.get_host_request_queue(
            HOSTNAME, 5000)
        self._requests = list()
        self._replies = list()

    def refresh(self):
        request = MtgoxRequest(self._ticker_url, self._ticker_handler, self)
        self._requests.append(request)
        self._request_queue.enqueue(self)

    def _ticker_handler(self, data):
        data = data['return']
        for key, value in data.items():
            if self._signals.has_key(key):
                signal = self._signals[key]
                signal.emit(value)


class MtgoxAccount(_Mtgox):

    _info_url = QtCore.QUrl(_BASE_URL + "generic/private/info")
    _currency_url = QtCore.QUrl(_BASE_URL + "generic/currency")
    _orders_url = QtCore.QUrl(_BASE_URL + "generic/private/orders")
    _cancelorder_url = QtCore.QUrl("https://mtgox.com/api/0/cancelOrder.php")

    last_login_signal = QtCore.pyqtSignal(decimal.Decimal)
    monthly_volume_signal = QtCore.pyqtSignal(decimal.Decimal)
    fee_signal = QtCore.pyqtSignal(decimal.Decimal)
    counter_balance_signal = QtCore.pyqtSignal(decimal.Decimal)
    base_balance_signal = QtCore.pyqtSignal(decimal.Decimal)

    orders_refresh_signal = QtCore.pyqtSignal()

    ask_enable_signal = QtCore.pyqtSignal(bool)
    bid_enable_signal = QtCore.pyqtSignal(bool)

    # pending requests comes from the request queue
    pending_replies_signal = QtCore.pyqtSignal(int)

    def __init__(self, credentials, remote,
                 network_manager=None, parent=None):
        if network_manager is None:
            network_manager = self.manager.network_manager
        super(MtgoxAccount, self).__init__(parent)
        ##BAD, hardcoding
        self._key = str(credentials[2])
        self._secret = base64.b64decode(credentials[3])

        self.remote_pair = str(remote)
        self.base = self.remote_pair[:3]
        self.counter = self.remote_pair[3:]
        self._order_add_url = QtCore.QUrl(
            _BASE_URL + self.remote_pair + "/private/order/add")

        # These must be the same length
        remote_stats = ()
        local_stats = ()
        self._signals = dict()
        self.signals = dict()
        for i in range(len(remote_stats)):
            signal = getattr(self, local_stats[i])
            self._signals[remote_stats[i]] = signal
            self.signals[local_stats[i]] = signal

        self.network_manager = network_manager
        self._request_queue = self.network_manager.get_host_request_queue(
            HOSTNAME, 5000)
        self._requests = list()
        self._replies = list()

        self.ask_orders_model = OrdersModel()
        self.bid_orders_model = OrdersModel()

        # Set currency information so we don't under-price and under-volume
        self.base_multiplier = None
        self.counter_multiplier = None
        for symbol in self.base, self.counter:
            request = MtgoxRequest(self._currency_url,
                                   self._currency_handler, self,
                                   {'query': {'currency': symbol} })
            self._requests.append(request)
            self._request_queue.enqueue(self)

    def refresh(self):
        request = MtgoxPrivateRequest(self._info_url,
                                      self._info_handler,
                                      self)
        self._requests.append(request)
        self._request_queue.enqueue(self)

    def _info_handler(self, data):
        data = data['return']
        self.base_balance_signal.emit(data['Wallets']
                                      [self.base]['Balance'])
        self.counter_balance_signal.emit(data['Wallets']
                                         [self.counter]['Balance'])

    def _currency_handler(self, data):
        data = data['return']
        places = int(data['decimals'])
        if data['currency'] == self.base:
            self.base_multiplier = pow(10, places)
        elif data['currency'] == self.counter:
            self.counter_multiplier = pow(10, places)
        self.check_order_status()

    def check_order_status(self):
        if self.base_multiplier is None:
            return
        elif self.counter_multiplier is None:
            return
        else:
            self.ask_enable_signal.emit(True)
            self.bid_enable_signal.emit(True)

    def refresh_orders(self):
        request = MtgoxPrivateRequest(self._orders_url, self._orders_handler,
                                      self)
        self._requests.append(request)
        self._request_queue.enqueue(self)

    def _orders_handler(self, data):
        data = data['return']
        if data:
            for model in self.ask_orders_model, self.bid_orders_model:
                model.clear_orders()
        for order in data:
            order_id = order['oid']
            price = order['price']
            amount = order['amount']
            order_type = order['type']

            if order_type == u'ask':
                self.ask_orders_model.append_order(order_id, price, amount)
            elif order_type == u'bid':
                self.bid_orders_model.append_order(order_id, price, amount)
            else:
                logger.error("unknown order type: %s", order_type)
                return

            for model in self.ask_orders_model, self.bid_orders_model:
                model.sort(1, QtCore.Qt.DescendingOrder)

    def place_bid_order(self, amount, price=0):
        self._place_order('bid', amount, price)

    def place_ask_order(self, amount, price=0):
        self._place_order('ask', amount, price)

    def _place_order(self, order_type, amount, price):
        data = {'type': order_type,
                'amount_int': amount * self.base_multiplier}
        if price:
            data['price_int'] = price * self.counter_multiplier
        else:
            logger.info("placing a market order")

        data = {'amount':amount, 'price':price,
                'query': data }
        request = MtgoxPrivateRequest(self._order_add_url,
                                      self._order_add_handler,
                                      self, data)
        self._requests.append(request)
        self._request_queue.enqueue(self)

    def _order_add_handler(self, data):
        order_id = data['return']
        amount = data['amount']
        price = data['price']
        order_type = data['query']['type']
        if order_type == 'ask':
            self.ask_orders_model.append_order(order_id, price, amount)
        elif order_type == 'bid':
            self.bid_orders_model.append_order(order_id, price, amount)

    def cancel_ask_order(self, order_id):
        self._cancel_order(order_id, 1)

    def cancel_bid_order(self, order_id):
        self._cancel_order(order_id, 2)

    def _cancel_order(self, order_id, order_type):
        # MtGox doesn't have a method to cancel orders for API 1.
        # type: 1 for ask order or 2 for bid order
        url = QtCore.QUrl("https://mtgox.com/api/0/cancelOrder.php")
        data = {'query': {'oid': order_id, 'type': order_type} }
        request = MtgoxPrivateRequestAPI0(url, self._cancelorder_handler,
                                          self, data)
        self._requests.append(request)
        self._request_queue.enqueue(self)

    def _cancelorder_handler(self, data):
        order_id = data['query']['oid']
        order_type = data['query']['type']
        if order_type == 1:
            self.ask_orders_model.remove_order(order_id)
        elif order_type == 2:
            self.bid_orders_model.remove_order(order_id)


class MtgoxProviderItem(tulpenmanie.providers.ProviderItem):

    provider_name = EXCHANGE_NAME

    COLUMNS = 3
    MARKETS, ACCOUNTS, REFRESH_RATE = range(COLUMNS)
    mappings = (('refresh rate', REFRESH_RATE),)

    markets = ( 'BTCUSD', 'BTCEUR', 'BTCAUD', 'BTCCAD', 'BTCCHF', 'BTCCNY',
                'BTCDKK', 'BTCGBP', 'BTCHKD', 'BTCJPY', 'BTCNZD', 'BTCPLN',
                'BTCRUB', 'BTCSEK', 'BTCSGD', 'BTCTHB' )

    ACCOUNT_COLUMNS = 4
    ACCOUNT_NAME, ACCOUNT_ENABLE, ACCOUNT_KEY, ACCOUNT_SECRET = range(ACCOUNT_COLUMNS)
    account_mappings = (('enable', ACCOUNT_ENABLE),
                        ('api_key', ACCOUNT_KEY),
                        ('secret', ACCOUNT_SECRET))

    numeric_settings = (REFRESH_RATE,)
    boolean_settings = ()
    required_account_settings = (ACCOUNT_KEY, ACCOUNT_SECRET)
    hidden_account_settings = ()


tulpenmanie.providers.register_exchange(MtgoxExchange)
tulpenmanie.providers.register_account(MtgoxAccount)
tulpenmanie.providers.register_exchange_model_item(MtgoxProviderItem)
