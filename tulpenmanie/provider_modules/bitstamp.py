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
import heapq
import json
import logging
from PyQt4 import QtCore, QtGui, QtNetwork

import tulpenmanie.exchange
import tulpenmanie.providers
import tulpenmanie.translate
import tulpenmanie.orders


logger = logging.getLogger(__name__)

EXCHANGE_NAME = "Bitstamp"
HOSTNAME = "www.bitstamp.net"
_BASE_URL = "https://" + HOSTNAME + "/api/"


class BitstampError(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        error_msg= repr(self.value)
        logger.error(error_msg)
        return error_msg


class BitstampRequest(object):

    def __init__(self, url, handler, parent, data=None):
        self.url = url
        self.handler = handler
        self.parent = parent
        if data:
            self.data = data
        else:
            self.data = dict()
        self.reply = None

        self.request = tulpenmanie.network.NetworkRequest(self.url)
        self.request.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader,
                               "application/x-www-form-urlencoded")
        query = parent.base_query
        if data:
            for key, value in data['query'].items():
                query.addQueryItem(key, str(value))
        self.query = query.encodedQuery()

    def _process_reply(self):
        if self.reply.error():
            logger.error(self.reply.errorString())
        else:
            if logger.isEnabledFor(logging.INFO):
                logger.debug("received reply to %s", self.reply.url().toString())
            data = json.loads(str(self.reply.readAll()))
            if type(data) is dict and 'error' in data:
                msg = str(self.reply.url().toString()) + " : " + str(data['error'])
                self.parent.exchange_error_signal.emit(msg)
                logger.warning(msg)
            else:
                self.data['return'] = data
                self.handler(self.data)
        self.reply.deleteLater()
        self.parent._replies.remove(self)

class BitstampGETRequest(BitstampRequest):

    def send(self):
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("GET to %s", self.url.toString())
        self.reply = self.parent.network_manager.get(self.request)
        self.reply.finished.connect(self._process_reply)
        self.reply.error.connect(self._process_reply)

class BitstampPOSTRequest(BitstampRequest):

    def send(self):
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("POST to %s", self.url.toString())
        self.reply = self.parent.network_manager.post(self.request,
                                                      self.query)
        self.reply.finished.connect(self._process_reply)
        self.reply.error.connect(self._process_reply)


class _Bitstamp(QtCore.QObject):

    provider_name = EXCHANGE_NAME
    exchange_error_signal = QtCore.pyqtSignal(str)

    def pop_request(self):
        request = heapq.heappop(self._requests)
        request.send()
        self._replies.add(request)


class BitstampExchangeMarket(_Bitstamp):

    base_query = QtCore.QUrl()
    _ticker_url = QtCore.QUrl(_BASE_URL + "ticker/")

    ask = QtCore.pyqtSignal(decimal.Decimal)
    last = QtCore.pyqtSignal(decimal.Decimal)
    bid = QtCore.pyqtSignal(decimal.Decimal)
    high = QtCore.pyqtSignal(decimal.Decimal)
    low = QtCore.pyqtSignal(decimal.Decimal)

    def __init__(self, remote_market, network_manager=None, parent=None):
        if network_manager is None:
            network_manager = self.manager.network_manager
        super(BitstampExchangeMarket, self).__init__(parent)
        # These must be the same length
        self.stats = ('ask', 'last', 'bid', 'high', 'low')
        self.is_counter = (True, True, True, True, True)
        self.signals = dict()
        for i in range(len(self.stats)):
            signal = getattr(self, self.stats[i])
            self.signals[self.stats[i]] = signal

        self.network_manager = network_manager
        self._request_queue = self.network_manager.get_host_request_queue(
            HOSTNAME, 500)
        self._requests = list()
        self._replies = set()

    def refresh(self):
        request = BitstampGETRequest(self._ticker_url,
                                     self._ticker_handler, self)
        self._requests.append(request)
        self._request_queue.enqueue(self)

    def _ticker_handler(self, data):
        for key, value in data['return'].items():
            if self.signals.has_key(key):
                signal =  self.signals[key]
                signal.emit(decimal.Decimal(value))


class BitstampAccount(_Bitstamp, tulpenmanie.exchange.ExchangeAccount):
    _balance_url = QtCore.QUrl(_BASE_URL + 'balance/')
    _open_orders_url = QtCore.QUrl(_BASE_URL + 'open_orders/')
    _cancel_order_url = QtCore.QUrl(_BASE_URL + 'cancel_order/')
    _buy_limit_url = QtCore.QUrl(_BASE_URL + 'buy/')
    _sell_limit_url = QtCore.QUrl(_BASE_URL + 'sell/')

    BTC_balance_signal = QtCore.pyqtSignal(decimal.Decimal)
    USD_balance_signal = QtCore.pyqtSignal(decimal.Decimal)

    BTC_balance_changed_signal = QtCore.pyqtSignal(decimal.Decimal)
    USD_balance_changed_signal = QtCore.pyqtSignal(decimal.Decimal)

    BTC_USD_limit_ready_signal = QtCore.pyqtSignal(bool)

    def __init__(self, credentials, network_manager=None, parent=None):
        if network_manager is None:
            network_manager = self.manager.network_manager
        super(BitstampAccount, self).__init__(parent)
        self.base_query = QtCore.QUrl()
        self.set_credentials(credentials)
        self.network_manager = network_manager
        self._request_queue = self.network_manager.get_host_request_queue(
            HOSTNAME, 500)
        self._requests = list()
        self._replies = set()

        self.ask_orders_model = tulpenmanie.orders.OrdersModel()
        self.bid_orders_model = tulpenmanie.orders.OrdersModel()

    def set_credentials(self, credentials):
        self.base_query.addQueryItem('user', credentials[0])
        self.base_query.addQueryItem('password', credentials[1])

    def check_order_status(self, remote_pair):
        self.BTC_USD_limit_ready_signal.emit(True)

    def get_ask_orders_model(self, remote_pair):
        return self.ask_orders_model

    def get_bid_orders_model(self, remote_pair):
        return self.bid_orders_model

    def refresh(self):
        self._refresh_funds()

    def _refresh_funds(self):
        request = BitstampPOSTRequest(self._balance_url,
                                      self._balance_handler, self)
        self._requests.append(request)
        self._request_queue.enqueue(self, 2)

    def _balance_handler(self, data):
        data = data['return']
        #TODO maybe not emit 'Total' but rather available
        self.BTC_balance_signal.emit(decimal.Decimal(data['btc_available']))
        self.USD_balance_signal.emit(decimal.Decimal(data['usd_available']))

    def refresh_orders(self):
        request = BitstampPOSTRequest(self._open_orders_url,
                                      self._open_orders_handler, self)
        self._requests.append(request)
        self._request_queue.enqueue(self, 2)

    def _open_orders_handler(self, data):
        for model in self.ask_orders_model, self.bid_orders_model:
            model.clear_orders()
        if data['return']:
            for order in data['return']:
                order_id = order['id']
                price = order['price']
                amount = order['amount']
                # type - buy or sell (0 - buy; 1 - sell)
                if order['type'] == 0:
                    self.bid_orders_model.append_order(order_id, price, amount)
                elif order['type'] == 1:
                    self.ask_orders_model.append_order(order_id, price, amount)
            for model in self.ask_orders_model, self.bid_orders_model:
                model.sort(1, QtCore.Qt.DescendingOrder)

    def place_ask_limit_order(self, pair, amount, price):
        self._place_limit_order(amount, price, self._sell_limit_url)

    def place_bid_limit_order(self, pair, amount, price):
        self._place_limit_order(amount, price, self._buy_limit_url)

    def place_ask_market_order(self, pair, amount):
        pass

    def place_bid_market_order(self, pair, amount):
        pass

    # TODO these could both be advanced
    def _place_limit_order(self, amount, price, url):
        query = {'amount': amount,
                 'price': price}
        data = {'query': query}
        request = BitstampPOSTRequest(url, self._place_order_handler,
                                      self, data)
        self._requests.append(request)
        self._request_queue.enqueue(self, 1)

    def _place_order_handler(self, data):
        data = data['return']
        order_id = int(data['id'])
        amount = decimal.Decimal(data['amount'])
        price = decimal.Decimal(data['price'])
        # type - buy or sell (0 - buy; 1 - sell)
        if data['type'] == 0:
            logger.info("bid order %s in place", order_id)
            self.bid_orders_model.append_order(order_id, price, amount)
            self.USD_balance_changed_signal.emit( -(amount * price))

        elif data['type'] == 1:
            logger.info("ask order %s in place", order_id)
            self.ask_orders_model.append_order(order_id, price, amount)
            self.BTC_balance_changed_signal.emit( -amount)

    def cancel_ask_order(self, pair, order_id):
        self._cancel_order(order_id)

    def cancel_bid_order(self, pair, order_id):
        self._cancel_order(order_id)

    def _cancel_order(self, order_id):
        data = {'query':{ 'id': order_id }}
        request = BitstampPOSTRequest(self._cancel_order_url,
                                      self._cancel_order_handler,
                                      self, data)
        self._requests.append(request)
        self._request_queue.enqueue(self, 0)

    def _cancel_order_handler(self, data):
        logger.info('%s', data['return'])
        if data['return']:
            order_id = data['query']['id']
            items = self.ask_orders_model.findItems(order_id,
                                                    QtCore.Qt.MatchExactly, 0)
            if items:
                row = items[0].row()
                self.ask_orders_model.removeRow(row)
            else:
                items = self.bid_orders_model.findItems(order_id,
                                                        QtCore.Qt.MatchExactly,
                                                        0)
                row = items[0].row()
                self.bid_orders_model.removeRow(row)
            logger.info("order %s canceled", order_id)


class BitstampExchangeItem(tulpenmanie.exchange.ExchangeItem):

    provider_name = EXCHANGE_NAME

    COLUMNS = 4
    MARKETS, REFRESH_RATE, ACCOUNT_USERNAME, ACCOUNT_PASSWORD = range(COLUMNS)
    mappings = (("refresh rate", REFRESH_RATE),
                ("customer ID", ACCOUNT_USERNAME),
                ("password", ACCOUNT_PASSWORD),)
    markets = ('BTC_USD',)

    numeric_settings = (REFRESH_RATE,)
    boolean_settings = ()
    required_account_settings = (ACCOUNT_USERNAME, ACCOUNT_PASSWORD,)
    hidden_settings = (ACCOUNT_PASSWORD,)


tulpenmanie.providers.register_exchange(BitstampExchangeMarket)
tulpenmanie.providers.register_account(BitstampAccount)
tulpenmanie.providers.register_exchange_model_item(BitstampExchangeItem)
