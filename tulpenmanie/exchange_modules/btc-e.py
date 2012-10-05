# Tulpenmanie, a graphical speculation platform.
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

import hashlib
import heapq
import hmac
import json
import logging
import time
from decimal import Decimal

from PyQt4 import QtCore, QtGui, QtNetwork

import tulpenmanie.exchange
import tulpenmanie.data.orders
import tulpenmanie.data.ticker
import tulpenmanie.network


logger = logging.getLogger(__name__)

EXCHANGE_NAME = "BTC-e"
COMMODITIES = ( 'btc', 'ltc', 'nmc', 'rur', 'usd' )
HOSTNAME = "btc-e.com"
_PUBLIC_BASE_URL = "https://" + HOSTNAME + "/api/2/"
_PRIVATE_URL = "https://" + HOSTNAME + "/tapi"


class BtceProviderItem(tulpenmanie.exchange.ExchangeItem):

    exchange_name = EXCHANGE_NAME

    COLUMNS = 4
    MARKETS, REFRESH_RATE, ACCOUNT_KEY, ACCOUNT_SECRET = range(COLUMNS)
    mappings = (("refresh rate (seconds)", REFRESH_RATE),
                ("key", ACCOUNT_KEY),
                ("secret", ACCOUNT_SECRET),)
    markets = ( 'btc_usd', 'btc_rur', 'ltc_btc', 'nmc_btc', 'usd_rur' )

    numeric_settings = (REFRESH_RATE,)
    boolean_settings = ()
    required_account_settings = (ACCOUNT_KEY, ACCOUNT_SECRET)
    hidden_settings = ()


class BtceRequest(QtCore.QObject):

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

    def _object_pairs_hook(self, pairs):
        dct = dict()
        for key, value in pairs:
            if key == 'ticker':
                return value
            dct[key] = Decimal(value)
        return dct

    def _process_reply(self):
        if self.reply.error():
            logger.error(self.reply.errorString())
        else:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("received reply to %s", self.url.toString())
            raw = str(self.reply.readAll())
            logger.debug(raw)
            self.data = json.loads(raw,
                                   parse_float=Decimal,
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

    def _prepare_request(self):
        self.request = tulpenmanie.network.NetworkRequest(self.url)
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
            logger.debug(raw)
            data = json.loads(raw, parse_float=Decimal)
            if data['success'] != 1:
                if data['error'] != 'no orders':
                    msg = HOSTNAME + " " + str(self.method) + " : " + data['error']
                    self.parent.exchange_error_signal.emit(msg)
                    logger.warning(msg)
            else:
                if self.data:
                    self.data.update(data)
                else:
                    self.data = data
                self.handler(self.data)
        self.reply.deleteLater()
        self.parent.replies.remove(self)


class _Btce(QtCore.QObject):

    exchange_name = EXCHANGE_NAME
    exchange_error_signal = QtCore.pyqtSignal(str)

    def pop_request(self):
        request = heapq.heappop(self.requests)[1]
        request.send()


class BtceExchange(_Btce):

    def __init__(self, network_manager=None, parent=None):
        if not network_manager:
            network_manager = tulpenmanie.network.get_network_manager()
        super(BtceExchange, self).__init__(parent)

        # TODO make this wait time a user option
        self.network_manager = network_manager
        self.host_queue = self.network_manager.get_host_request_queue(
            HOSTNAME, 500)
        self.requests = list()
        self.replies = set()
        self._ticker_proxies = dict()
        self._ticker_clients = dict()
        self._ticker_timer = QtCore.QTimer(self)
        self._ticker_timer.timeout.connect(self._refresh_tickers)
        search = tulpenmanie.exchange.model.findItems(self.exchange_name,
                                                      QtCore.Qt.MatchExactly)
        self._model_item = search[0]

    def get_ticker_proxy(self, remote_market):
        if remote_market not in self._ticker_proxies:
            ticker_proxy = tulpenmanie.data.ticker.TickerProxy(self)
            self._ticker_proxies[remote_market] = ticker_proxy
            return ticker_proxy
        return self._ticker_proxies[remote_market]

    def set_ticker_stream_state(self, state, remote_market):
        if state is True:
            if not remote_market in self._ticker_clients:
                self._ticker_clients[remote_market] = 1
            else:
                self._ticker_clients[remote_market] += 1
            refresh_rate = self._model_item.child(
                0, self._model_item.REFRESH_RATE).text()
            if not refresh_rate:
                refresh_rate = 10000
            else:
                refresh_rate = float(refresh_rate) * 1000
            if self._ticker_timer.isActive():
                self._ticker_timer.setInterval(refresh_rate)
                return
            logger.info(QtCore.QCoreApplication.translate(
                'BteExchange', "starting ticker stream"))
            self._ticker_timer.start(refresh_rate)
        else:
            if remote_market in self._ticker_clients:
                market_clients = self._ticker_clients[remote_market]
                if market_clients > 1:
                    self._ticker_clients[remote_market] -= 1
                    return
                if market_clients == 1:
                    self._ticker_clients.pop(remote_market)

            if sum(self._ticker_clients.values()) == 0:
                logger.info(QtCore.QCoreApplication.translate(
                    'BtceExchange', "stopping ticker stream"))
                self._ticker_timer.stop()

    def refresh_ticker(self, remote_market):
        ticker_url = QtCore.QUrl(_PUBLIC_BASE_URL + remote_market + "/ticker")
        BtceTickerRequest(ticker_url, self)

    def _refresh_tickers(self):
        for remote_market in self._ticker_clients.keys():
            ticker_url = QtCore.QUrl(
                _PUBLIC_BASE_URL + remote_market + "/ticker")
            BtceTickerRequest(ticker_url, self)

class BtceTickerRequest(tulpenmanie.network.ExchangeGETRequest):

    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw, parse_float=Decimal, parse_int=Decimal)
        data = data['ticker']
        path = self.url.path().split('/')
        remote_market = path[3]
        proxy = self.parent._ticker_proxies[remote_market]
        proxy.ask_signal.emit(data['buy'])
        proxy.last_signal.emit(data['last'])
        proxy.bid_signal.emit(data['sell'])


class BtceAccount(_Btce, tulpenmanie.exchange.ExchangeAccount):

    # BAD rudunant
    markets = ( 'btc_usd', 'btc_rur', 'ltc_btc', 'nmc_btc', 'usd_rur' )

    trade_commission_signal = QtCore.pyqtSignal(Decimal)

    btc_funds_signal = QtCore.pyqtSignal(Decimal)
    ltc_funds_signal = QtCore.pyqtSignal(Decimal)
    nmc_funds_signal = QtCore.pyqtSignal(Decimal)
    rur_funds_signal = QtCore.pyqtSignal(Decimal)
    usd_funds_signal = QtCore.pyqtSignal(Decimal)

    btc_usd_ready_signal = QtCore.pyqtSignal(bool)
    btc_rur_ready_signal = QtCore.pyqtSignal(bool)
    ltc_btc_ready_signal = QtCore.pyqtSignal(bool)
    nmc_btc_ready_signal = QtCore.pyqtSignal(bool)
    usd_rur_ready_signal = QtCore.pyqtSignal(bool)

    def __init__(self, credentials, network_manager=None, parent=None):
        if network_manager is None:
            network_manager = tulpenmanie.network.get_network_manager()
        super(BtceAccount, self).__init__(parent)
        self.set_credentials(credentials)

        self.network_manager = network_manager
        self.host_queue = self.network_manager.get_host_request_queue(
            HOSTNAME, 5000)
        self.requests = list()
        self.replies = set()
        self._orders_proxies = dict()

        # TODO maybe divide smaller
        self.nonce = int(time.time() / 2)

    def get_orders_proxy(self, remote_market):
        if remote_market not in self._orders_proxies:
            orders_proxy = tulpenmanie.data.orders.OrdersProxy(self)
            self._orders_proxies[remote_market] = orders_proxy
            return orders_proxy
        return self._orders_proxies[remote_market]

    def pop_request(self):
        request = heapq.heappop(self.requests)[1]
        request.post()
        self.replies.add(request)

    def set_credentials(self, credentials):
        self._key = str(credentials[0])
        self._secret = str(credentials[1])

    def check_order_status(self, remote_pair):
        signal = getattr(self, remote_pair + "_ready_signal")
        signal.emit(True)

    def refresh_funds(self):
        request = BtcePrivateRequest('getInfo', self._getinfo_handler, self)
        self.requests.append((2, request))
        self.host_queue.enqueue(self, 2)

    def _getinfo_handler(self, data):
        self._emit_funds(data['return']['funds'])

    def refresh_orders(self):
        request = BtcePrivateRequest('OrderList', self._orderlist_handler, self)
        self.requests.append((2, request))
        self.host_queue.enqueue(self, 2)

    def _orderlist_handler(self, data):
        data = data['return']
        if not data:
            return
        asks = dict()
        bids = dict()
        for order_id, order in data.items():
            price = order['rate']
            amount = order['amount']
            order_type = order['type']
            pair = order['pair']

            if order_type == u'sell':
                if pair not in asks:
                    asks[pair] = list()
                asks[pair].append((order_id, price, amount,))
            elif order_type == u'buy':
                if pair not in bids:
                    bids[pair] = list()
                bids[pair].append((order_id, price, amount,))
            else:
                logger.warning("unknown order type: %s", order_type)

        for pair, orders in asks.items():
            if pair in self._orders_proxies:
                self._orders_proxies[pair].asks.emit(orders)
        for pair, orders in bids.items():
            if pair in self._orders_proxies:
                self._orders_proxies[pair].bids.emit(orders)

    def place_ask_limit_order(self, remote, amount, price):
        self._place_order(remote, 'sell', amount, price)

    def place_bid_limit_order(self, remote, amount, price):
        self._place_order(remote, 'buy', amount, price)

    def _place_order(self, remote_pair, order_type, amount, price):
        data = {'query':{'pair': remote_pair,
                         'type': order_type,
                         'amount': amount,
                         'rate': price} }
        request = BtcePrivateRequest('Trade', self._trade_handler, self, data)
        self.requests.append((1, request))
        self.host_queue.enqueue(self, 1)

    def _trade_handler(self, data):
        order_id = data['return']['order_id']
        amount = data['return']['remains']
        price = data['query']['rate']
        pair = data['query']['pair']
        order_type = data['query']['type']
        if order_type == 'sell':
            logger.info("ask order %s in place", order_id)
            if pair in self._orders_proxies:
                self.orders_proxies[pair].ask.emit((order_id, price, amount,))
        elif order_type == 'buy':
            logger.info("bid order %s in place", order_id)
            if pair in self._orders_proxies:
                self.orders_proxies[pair].bid.emit((order_id, price, amount,))
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
        self.requests.append((0, request))
        self.host_queue.enqueue(self, 0)

    def _cancelorder_handler(self, data):
        order_id = data['return']['order_id']
        pair = data['pair']
        order_type = data['type']
        if order_type == 'ask':
            if pair in self._orders_proxies:
                self.orders_proxies[pair].ask_cancelled(order_id)
        elif order_type == 'bid':
            if pair in self._orders_proxies:
                self.orders_proxies[pair].bid_cancelled(order_id)
        self._emit_funds(data['return']['funds'])

    def _emit_funds(self, data):
        self.trade_commission_signal.emit(Decimal('0.2'))
        for commodity, balance in data.items():
            signal = getattr(self, commodity + '_funds_signal', None)
            if signal:
                signal.emit(Decimal(balance))
            else:
                logger.warning("unknown commodity %s", commodity)

tulpenmanie.exchange.register_exchange(BtceExchange)
tulpenmanie.exchange.register_account(BtceAccount)
tulpenmanie.exchange.register_exchange_model_item(BtceProviderItem)
