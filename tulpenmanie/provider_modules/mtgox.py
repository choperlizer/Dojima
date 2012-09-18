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

import base64
import decimal
import heapq
import hashlib
import hmac
import json
import logging
import random
import time


from PyQt4 import QtCore, QtGui, QtNetwork

import tulpenmanie.providers
import tulpenmanie.exchange


logger = logging.getLogger(__name__)


EXCHANGE_NAME = "MtGox"
COMMODITIES = ( 'AUD', 'BTC', 'CAD', 'CHF', 'CNY', 'DKK',
                'EUR', 'GBP', 'HKD', 'JPY', 'NZD', 'PLN',
                'RUB', 'SEK', 'SGD', 'THB', 'USD' )
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

    def _prepare_request(self):
        self.request = tulpenmanie.network.NetworkRequest(self.url)
        self.request.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader,
                               "application/x-www-form-urlencoded")
        query = QtCore.QUrl()
        if self.data:
            for key, value in self.data['query'].items():
                query.addQueryItem(key, str(value))
        self.query = query.encodedQuery()

    def post(self):
        self._prepare_request()
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("POST to %s", self.url.toString())
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
                msg = str(self.reply.url().toString()) + " : " + data['error']
                self.parent.exchange_error_signal.emit(msg)
                logger.warning(msg)
            else:
                if self.data:
                    self.data.update(data)
                    self.handler(self.data)
                else:
                    self.handler(data)
        self.reply.deleteLater()
        self.parent._replies.remove(self)


class MtgoxPrivateRequest(MtgoxRequest):

    def _prepare_request(self):
        self.request = tulpenmanie.network.NetworkRequest(self.url)
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
        self.parent._replies.remove(self)


class _Mtgox(QtCore.QObject):
    provider_name = EXCHANGE_NAME
    exchange_error_signal = QtCore.pyqtSignal(str)

    def pop_request(self):
        request = heapq.heappop(self._requests)[1]
        request.post()
        self._replies.add(request)


class MtgoxExchange(_Mtgox):

    register_url = None

    ask = QtCore.pyqtSignal(decimal.Decimal)
    last = QtCore.pyqtSignal(decimal.Decimal)
    bid = QtCore.pyqtSignal(decimal.Decimal)
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
        remote_stats = ('sell', 'last_local', 'buy')
        self.stats = ('ask', 'last', 'bid')
        self._signals = dict()
        self.signals = dict()
        for i in range(len(remote_stats)):
            signal = getattr(self, self.stats[i])
            self._signals[remote_stats[i]] = signal
            self.signals[self.stats[i]] = signal

        # TODO make this wait time a user option
        self.network_manager = network_manager
        self._host_queue = self.network_manager.get_host_request_queue(
            HOSTNAME, 5000)
        self._requests = list()
        self._replies = set()

    def refresh(self):
        request = MtgoxRequest(self._ticker_url, self._ticker_handler, self)
        self._requests.append((1, request))
        self._host_queue.enqueue(self)

    def _ticker_handler(self, data):
        data = data['return']
        for key, value in data.items():
            if self._signals.has_key(key):
                signal = self._signals[key]
                signal.emit(value)


class MtgoxAccount(_Mtgox, tulpenmanie.exchange.ExchangeAccount):

    # BAD redundant
    markets = ( 'BTCAUD', 'BTCCAD', 'BTCCHF', 'BTCCNY', 'BTCDKK',
                'BTCEUR', 'BTCGBP', 'BTCHKD', 'BTCJPY', 'BTCNZD',
                'BTCPLN', 'BTCRUB', 'BTCSEK', 'BTCSGD', 'BTCTHB',
                'BTCUSD' )

    AUD_balance_signal = QtCore.pyqtSignal(decimal.Decimal)
    BTC_balance_signal = QtCore.pyqtSignal(decimal.Decimal)
    CAD_balance_signal = QtCore.pyqtSignal(decimal.Decimal)
    CHF_balance_signal = QtCore.pyqtSignal(decimal.Decimal)
    CNY_balance_signal = QtCore.pyqtSignal(decimal.Decimal)
    DKK_balance_signal = QtCore.pyqtSignal(decimal.Decimal)
    EUR_balance_signal = QtCore.pyqtSignal(decimal.Decimal)
    GBP_balance_signal = QtCore.pyqtSignal(decimal.Decimal)
    HKD_balance_signal = QtCore.pyqtSignal(decimal.Decimal)
    JPY_balance_signal = QtCore.pyqtSignal(decimal.Decimal)
    NZD_balance_signal = QtCore.pyqtSignal(decimal.Decimal)
    PLN_balance_signal = QtCore.pyqtSignal(decimal.Decimal)
    RUB_balance_signal = QtCore.pyqtSignal(decimal.Decimal)
    SEK_balance_signal = QtCore.pyqtSignal(decimal.Decimal)
    SGD_balance_signal = QtCore.pyqtSignal(decimal.Decimal)
    THB_balance_signal = QtCore.pyqtSignal(decimal.Decimal)
    USD_balance_signal = QtCore.pyqtSignal(decimal.Decimal)

    AUD_balance_changed_signal = QtCore.pyqtSignal(decimal.Decimal)
    BTC_balance_changed_signal = QtCore.pyqtSignal(decimal.Decimal)
    CAD_balance_changed_signal = QtCore.pyqtSignal(decimal.Decimal)
    CHF_balance_changed_signal = QtCore.pyqtSignal(decimal.Decimal)
    CNY_balance_changed_signal = QtCore.pyqtSignal(decimal.Decimal)
    DKK_balance_changed_signal = QtCore.pyqtSignal(decimal.Decimal)
    EUR_balance_changed_signal = QtCore.pyqtSignal(decimal.Decimal)
    GBP_balance_changed_signal = QtCore.pyqtSignal(decimal.Decimal)
    HKD_balance_changed_signal = QtCore.pyqtSignal(decimal.Decimal)
    JPY_balance_changed_signal = QtCore.pyqtSignal(decimal.Decimal)
    NZD_balance_changed_signal = QtCore.pyqtSignal(decimal.Decimal)
    PLN_balance_changed_signal = QtCore.pyqtSignal(decimal.Decimal)
    RUB_balance_changed_signal = QtCore.pyqtSignal(decimal.Decimal)
    SEK_balance_changed_signal = QtCore.pyqtSignal(decimal.Decimal)
    SGD_balance_changed_signal = QtCore.pyqtSignal(decimal.Decimal)
    THB_balance_changed_signal = QtCore.pyqtSignal(decimal.Decimal)
    USD_balance_changed_signal = QtCore.pyqtSignal(decimal.Decimal)

    BTCAUD_limit_ready_signal = QtCore.pyqtSignal(bool)
    BTCCAD_limit_ready_signal = QtCore.pyqtSignal(bool)
    BTCCHF_limit_ready_signal = QtCore.pyqtSignal(bool)
    BTCCNY_limit_ready_signal = QtCore.pyqtSignal(bool)
    BTCDKK_limit_ready_signal = QtCore.pyqtSignal(bool)
    BTCEUR_limit_ready_signal = QtCore.pyqtSignal(bool)
    BTCGBP_limit_ready_signal = QtCore.pyqtSignal(bool)
    BTCHKD_limit_ready_signal = QtCore.pyqtSignal(bool)
    BTCJPY_limit_ready_signal = QtCore.pyqtSignal(bool)
    BTCNZD_limit_ready_signal = QtCore.pyqtSignal(bool)
    BTCPLN_limit_ready_signal = QtCore.pyqtSignal(bool)
    BTCRUB_limit_ready_signal = QtCore.pyqtSignal(bool)
    BTCSEK_limit_ready_signal = QtCore.pyqtSignal(bool)
    BTCSGD_limit_ready_signal = QtCore.pyqtSignal(bool)
    BTCTHB_limit_ready_signal = QtCore.pyqtSignal(bool)
    BTCUSD_limit_ready_signal = QtCore.pyqtSignal(bool)

    BTCAUD_market_ready_signal = QtCore.pyqtSignal(bool)
    BTCCAD_market_ready_signal = QtCore.pyqtSignal(bool)
    BTCCHF_market_ready_signal = QtCore.pyqtSignal(bool)
    BTCCNY_market_ready_signal = QtCore.pyqtSignal(bool)
    BTCDKK_market_ready_signal = QtCore.pyqtSignal(bool)
    BTCEUR_market_ready_signal = QtCore.pyqtSignal(bool)
    BTCGBP_market_ready_signal = QtCore.pyqtSignal(bool)
    BTCHKD_market_ready_signal = QtCore.pyqtSignal(bool)
    BTCJPY_market_ready_signal = QtCore.pyqtSignal(bool)
    BTCNZD_market_ready_signal = QtCore.pyqtSignal(bool)
    BTCPLN_market_ready_signal = QtCore.pyqtSignal(bool)
    BTCRUB_market_ready_signal = QtCore.pyqtSignal(bool)
    BTCSEK_market_ready_signal = QtCore.pyqtSignal(bool)
    BTCSGD_market_ready_signal = QtCore.pyqtSignal(bool)
    BTCTHB_market_ready_signal = QtCore.pyqtSignal(bool)
    BTCUSD_market_ready_signal = QtCore.pyqtSignal(bool)


    _info_url = QtCore.QUrl(_BASE_URL + "generic/private/info")
    _currency_url = QtCore.QUrl(_BASE_URL + "generic/currency")
    _orders_url = QtCore.QUrl(_BASE_URL + "generic/private/orders")
    _cancelorder_url = QtCore.QUrl("https://" + HOSTNAME +
                                   "/api/0/cancelOrder.php")

    multipliers = dict()

    def __init__(self, credentials, network_manager=None, parent=None):
        if network_manager is None:
            network_manager = self.manager.network_manager
        super(MtgoxAccount, self).__init__(parent)
        self.set_credentials(credentials)
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
        self._host_queue = self.network_manager.get_host_request_queue(
            HOSTNAME, 5000)
        self._requests = list()
        self._replies = set()

        self.ask_orders = dict()
        self.bid_orders = dict()

        # TODO maybe divide smaller
        self.nonce = int(time.time() / 2)

    def set_credentials(self, credentials):
        self._key = str(credentials[0])
        self._secret = base64.b64decode(credentials[1])

    def check_order_status(self, remote_pair):
        # This can probaly call for BTC info twice at
        # startup but whatever
        counter = remote_pair[-3:]
        multipliers = self.multipliers.keys()

        if counter not in multipliers:
            request = MtgoxRequest(self._currency_url,
                                   self._currency_handler,
                                   self, {'pair': remote_pair,
                                          'query': {'currency':counter} })
            self._requests.append((1, request))
            self._host_queue.enqueue(self, 0)
            return

        if 'BTC' not in multipliers:
            request = MtgoxRequest(self._currency_url,
                                   self._currency_handler,
                                   self, {'pair': remote_pair,
                                          'query': {'currency':'BTC'} })
            self._requests.append((1, request))
            self._host_queue.enqueue(self, 1)
            return

        signal = getattr(self, remote_pair + "_limit_ready_signal")
        signal.emit(True)
        signal = getattr(self, remote_pair + "_market_ready_signal")
        signal.emit(True)

    def _currency_handler(self, data):
        pair = data['pair']
        data = data['return']
        symbol = data['currency']
        places = int(data['decimals'])
        self.multipliers[symbol] = pow(10, places)
        self.check_order_status(pair)

    def refresh(self):
        request = MtgoxPrivateRequest(self._info_url,
                                      self._info_handler,
                                      self)
        self._requests.append((2, request))
        self._host_queue.enqueue(self, 2)

    def _info_handler(self, data):
        data = data['return']
        for symbol, dct in data['Wallets'].items():
            signal = getattr(self, symbol + '_balance_signal', None)
            if signal:
                balance = dct['Balance'] - dct['Open_Orders']
                signal.emit(balance)
            else:
                logger.warning("unknown commodity %s found in balances", symbol)

    def refresh_orders(self):
        request = MtgoxPrivateRequest(self._orders_url, self._orders_handler,
                                      self)
        self._requests.append((2, request))
        self._host_queue.enqueue(self, 2)

    def _orders_handler(self, data):
        #TODO probably contains multi-market order list
        data = data['return']
        if data:
            for models in self.ask_orders, self.bid_orders:
                for model in models.values():
                    model.clear_orders()
        for order in data:
            pair = order['item'] + order['currency']
            order_id = order['oid']
            price = order['price']
            amount = order['amount']
            order_type = order['type']

            if order_type == u'ask':
                logger.info("ask order %s in place", order_id)
                self.ask_orders[pair].append_order(order_id, price, amount)
            elif order_type == u'bid':
                logger.info("bid order %s in place", order_id)
                self.bid_orders[pair].append_order(order_id, price, amount)
            else:
                logger.error("unknown order type: %s", order_type)
                return

            for models in self.ask_orders, self.bid_orders:
                for model in models.values():
                    model.sort(1, QtCore.Qt.DescendingOrder)

    def place_ask_limit_order(self, remote_pair, amount, price):
        self._place_order(remote_pair, 'ask', amount, price)

    def place_bid_limit_order(self, remote_pair, amount, price):
        self._place_order(remote_pair, 'bid', amount, price)

    def place_ask_market_order(self, remote_pair, amount):
        self._place_order(remote_pair, 'ask', amount)

    def place_bid_market_order(self, remote_pair, amount):
        self._place_order(remote_pair, 'bid', amount)

    def _place_order(self, remote_pair, order_type, amount, price=None):
        counter = remote_pair[-3:]
        amount = decimal.Decimal(amount)
        query_data = {'type': order_type,
                      'amount_int': int(amount * self.multipliers['BTC'])}
        if price:
            price = decimal.Decimal(price)
            query_data['price_int'] = int(price * self.multipliers[counter])

        data = {'pair': remote_pair, 'amount':amount, 'price':price,
                'query': query_data }

        url = QtCore.QUrl(_BASE_URL + remote_pair + "/private/order/add")
        request = MtgoxPrivateRequest(url, self._order_add_handler,
                                      self, data)
        self._requests.append((1, request))
        self._host_queue.enqueue(self, 1)

    def _order_add_handler(self, data):
        order_id = data['return']
        amount = data['amount']
        price = data['price']
        pair = data['pair']
        order_type = data['query']['type']
        base_signal = self.BTC_balance_changed_signal
        counter_signal = getattr(self, pair[-3:] + '_balance_changed_signal')
        if order_type == 'ask':
            self.ask_orders[pair].append_order(order_id, price, amount)
            base_signal.emit(-amount)
        elif order_type == 'bid':
            if price:
                counter_signal.emit(-decimal.Decimal(amount * price))
            else:
                price = tulpenmanie.translate.market_order_type
            self.bid_orders[pair].append_order(order_id, price, amount)

    def cancel_ask_order(self, pair, order_id):
        self._cancel_order(pair, order_id, 1)

    def cancel_bid_order(self, pair, order_id):
        self._cancel_order(pair, order_id, 2)

    def _cancel_order(self, pair, order_id, order_type):
        # MtGox doesn't have a method to cancel orders for API 1.
        # type: 1 for ask order or 2 for bid order
        url = QtCore.QUrl("https://mtgox.com/api/0/cancelOrder.php")
        data = {'pair': pair,
                'query': {'oid': order_id, 'type': order_type} }
        request = MtgoxPrivateRequestAPI0(url, self._cancelorder_handler,
                                          self, data)
        self._requests.append((0, request))
        self._host_queue.enqueue(self, 0)

    def _cancelorder_handler(self, data):
        pair = data['pair']
        order_id = data['query']['oid']
        order_type = data['query']['type']
        if order_type == 1:
            self.ask_orders[pair].remove_order(order_id)
        elif order_type == 2:
            self.bid_orders[pair].remove_order(order_id)


class MtgoxExchangeItem(tulpenmanie.exchange.ExchangeItem):

    provider_name = EXCHANGE_NAME

    COLUMNS = 4
    MARKETS, REFRESH_RATE, ACCOUNT_KEY, ACCOUNT_SECRET = range(COLUMNS)
    mappings = (('refresh rate', REFRESH_RATE),
                ('key', ACCOUNT_KEY),
                ('secret', ACCOUNT_SECRET),)
    markets = ( 'BTCAUD', 'BTCCAD', 'BTCCHF', 'BTCCNY', 'BTCDKK',
                'BTCEUR', 'BTCGBP', 'BTCHKD', 'BTCJPY', 'BTCNZD',
                'BTCPLN', 'BTCRUB', 'BTCSEK', 'BTCSGD', 'BTCTHB',
                'BTCUSD' )

    numeric_settings = (REFRESH_RATE,)
    boolean_settings = ()
    required_account_settings = (ACCOUNT_KEY, ACCOUNT_SECRET)
    hidden_settings = ()


tulpenmanie.providers.register_exchange(MtgoxExchange)
tulpenmanie.providers.register_account(MtgoxAccount)
tulpenmanie.providers.register_exchange_model_item(MtgoxExchangeItem)
