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
import tulpenmanie.data.funds
import tulpenmanie.data.orders
import tulpenmanie.data.ticker
import tulpenmanie.network


logger = logging.getLogger(__name__)

EXCHANGE_NAME = "VirWoX"
HOSTNAME = "api.virwox.com"
PUBLIC_URL = 'http://' + HOSTNAME + '/api/json.php'
public_request = QtNetwork.QNetworkRequest(QtCore.QUrl(PUBLIC_URL))
public_request.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader,
                         'application/json')
PRIVATE_URL = 'https://' + HOSTNAME + '/api/trading.php'
private_request = QtNetwork.QNetworkRequest(QtCore.QUrl(PRIVATE_URL))
private_request.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader,
                         'application/json')

def escape_market(remote_market):
    #return str(remote_market).replace('/',"""\/""")
    return str(remote_market)

class _VirwoxRequest(QtCore.QObject):

    def parse_reply(self):
        if self.reply.error():
            logger.error(self.reply.errorString())
        else:
            raw = str(self.reply.readAll())
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("received reply: %s", raw)
            response = json.loads(raw, parse_float=Decimal)
            if response['error']:
                logger.error(response['error'])
                self.parent.exchange_error_signal.emit(
                    "VirWox " + response['error'])
            else:
                self.handle_result(response['result'])
        self.reply.deleteLater()
        #self.parent.replies.remove(self)


class VirwoxPublicRequest(_VirwoxRequest):

    def __init__(self, data, parent):
        super(VirwoxPublicRequest, self).__init__(parent)
        self.parent = parent
        self.data = data
        self.reply = None
        self.parent.requests.append(self)
        self.parent.host_queue.enqueue(self.parent, None)

    def post(self):
        payload = json.dumps({'method': self.method, 'params': self.data,
                              'id': str(QtCore.QUuid.createUuid().toString())})
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("POSTing %s to %s", self.data, PUBLIC_URL)
        self.reply = self.parent.network_manager.post(public_request, payload)
        self.reply.finished.connect(self.parse_reply)


class VirwoxInstrumentsRequest(QtCore.QObject):
    method = 'getInstruments'

    def __init__(self, item, parent=None):
        super(VirwoxInstrumentsRequest, self).__init__(parent)
        self.item = item
        data = {'method': self.method,
                'id': str(QtCore.QUuid.createUuid().toString())}
        network_manager = tulpenmanie.network.get_network_manager()
        self.reply = network_manager.post(public_request, json.dumps(data))
        self.reply.finished.connect(self.receive_markets)

    def receive_markets(self):
        if self.reply.error():
            logger.error(self.reply.errorString())
            self.reply.deleteLater()
            return
        raw = str(self.reply.readAll())
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("received reply to %s : %s", PUBLIC_URL, raw)
        data = json.loads(raw, parse_float=Decimal)
        if data['error']:
            logger.warning(data['error'])
        for instrument in data['result'].values():
            self.item.markets.add(instrument['symbol'])
        self.item.reload()
        self.reply.deleteLater()
        self.deleteLater()


class VirwoxProviderItem(tulpenmanie.exchange.DynamicExchangeItem):

    exchange_name = EXCHANGE_NAME

    COLUMNS = 4
    MARKETS, REFRESH_RATE, ACCOUNT_USERNAME, ACCOUNT_PASSWORD, = range(COLUMNS)
    mappings = (("refresh rate (seconds)", REFRESH_RATE),
                ("username", ACCOUNT_USERNAME),
                ("password", ACCOUNT_PASSWORD),)
    numeric_settings = (REFRESH_RATE,)
    boolean_settings = ()
    required_account_settings = (ACCOUNT_USERNAME, ACCOUNT_PASSWORD)
    hidden_settings = (ACCOUNT_PASSWORD,)
    markets = set()

    def new_markets_request(self):
        self.markets_request = VirwoxInstrumentsRequest(self)

class _Virwox(QtCore.QObject):

    exchange_name = EXCHANGE_NAME
    exchange_error_signal = QtCore.pyqtSignal(str)

class VirwoxExchangeMarket(_Virwox):

    def __init__(self, network_manager=None, parent=None):
        if not network_manager:
            network_manager = tulpenmanie.network.get_network_manager()
        super(VirwoxExchangeMarket, self).__init__(parent)
        self.network_manager = network_manager
        self.host_queue = self.network_manager.get_host_request_queue(
            HOSTNAME, 1000)
        self.requests = list()
        self.ticker_proxies = dict()
        self.ticker_clients = dict()
        self.ticker_timer = QtCore.QTimer(self)
        self.ticker_timer.timeout.connect(self._refresh_tickers)
        search = tulpenmanie.exchange.model.findItems(self.exchange_name,
                                                      QtCore.Qt.MatchExactly)
        self._model_item = search[0]

    def get_ticker_proxy(self, remote_market):
        remote_market = escape_market(remote_market)
        if remote_market not in self.ticker_proxies:
            ticker_proxy = tulpenmanie.data.ticker.TickerProxy(self)
            self.ticker_proxies[remote_market] = ticker_proxy
            return ticker_proxy
        return self.ticker_proxies[remote_market]

    def set_ticker_stream_state(self, state, remote_market):
        remote_market = escape_market(remote_market)
        if state is True:
            if not remote_market in self.ticker_clients:
                self.ticker_clients[remote_market] = 1
            else:
                self.ticker_clients[remote_market] += 1
            refresh_rate = self._model_item.child(
                0, self._model_item.REFRESH_RATE).text()
            if not refresh_rate:
                refresh_rate = 10000
            else:
                refresh_rate = float(refresh_rate) * 1000
            if self.ticker_timer.isActive():
                self.ticker_timer.setInterval(refresh_rate)
                return
            logger.info(QtCore.QCoreApplication.translate(
                'BteExchange', "starting ticker stream"))
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
                    'VirwoxExchange', "stopping ticker stream"))
                self.ticker_timer.stop()

    def refresh_ticker(self, remote_market):
        remote_market = escape_market(remote_market)
        symbols = set(self.ticker_clients.keys())
        symbols.add(remote_market)
        VirwoxTickerRequest({'symbols': symbols}, self)

    def _refresh_tickers(self):
        symbols = self.ticker_clients.keys()
        VirwoxTickerRequest({'symbols': symbols}, self)

    def pop_request(self):
        request = heapq.heappop(self.requests)
        request.post()


class VirwoxTickerRequest(VirwoxPublicRequest):
    method = 'getBestPrices'

    def handle_result(self, result):
        for instrument in result:
            proxy = self.parent.ticker_proxies[instrument['symbol']]
            proxy.ask_signal.emit(Decimal(instrument['bestSellPrice']))
            proxy.bid_signal.emit(Decimal(instrument['bestBuyPrice']))


class VirwoxAccount(_Virwox, tulpenmanie.exchange.ExchangeAccount):

    # TODO get rid of this crap
    EUR_OMC_ready_signal = QtCore.pyqtSignal(bool)
    BTC_SLL_ready_signal = QtCore.pyqtSignal(bool)
    USD_OMC_ready_signal = QtCore.pyqtSignal(bool)
    USD_SLL_ready_signal = QtCore.pyqtSignal(bool)
    SLL_ACD_ready_signal = QtCore.pyqtSignal(bool)
    CHF_SLL_ready_signal = QtCore.pyqtSignal(bool)
    EUR_SLL_ready_signal = QtCore.pyqtSignal(bool)
    USD_ACD_ready_signal = QtCore.pyqtSignal(bool)
    GBP_SLL_ready_signal = QtCore.pyqtSignal(bool)
    SLL_OMC_ready_signal = QtCore.pyqtSignal(bool)
    EUR_ACD_ready_signal = QtCore.pyqtSignal(bool)

    commissions = {'EUR/SLL': {'fixed':50, 'variable': Decimal('0.029')},
                   'USD/SLL': {'fixed':50, 'variable': Decimal('0.029')},
                   'GBP/SLL': {'fixed':50, 'variable': Decimal('0.029')},
                   'CHF/SLL': {'fixed':50, 'variable': Decimal('0.029')},
                   'EUR/ACD': {'fixed':50, 'variable': Decimal('0.039')},
                   'USD/ACD': {'fixed':50, 'variable': Decimal('0.039')},
                   'SLL/ACD': {'fixed':25, 'variable': Decimal('0.039')},
                   'SLL/OMC': {'fixed':25, 'variable': Decimal('0.019')},
                   'EUR/OMC': {'fixed':50, 'variable': Decimal('0.029')},
                   'USD/OMC': {'fixed':50, 'variable': Decimal('0.019')},
                   'BTC/SLL': {'fixed':50, 'variable': Decimal('0.029')}}


    def __init__(self, credentials, network_manager=None, parent=None):
        if network_manager is None:
            network_manager = tulpenmanie.network.get_network_manager()
        super(VirwoxAccount, self).__init__(parent)
        self._credentials = {'key':'0c7d341e237ae4aec4b1b7376ff702fe'}
        self.set_credentials(credentials)
        self.network_manager = network_manager
        self.host_queue = self.network_manager.get_host_request_queue(
            HOSTNAME, 1000)
        self.requests = list()
        self.replies = set()
        self.funds_proxies = dict()
        self.orders_proxies = dict()


    def pop_request(self):
        request = heapq.heappop(self.requests)[1]
        request.post()
        self.replies.add(request)

    def set_credentials(self, credentials):
        self._credentials['user'] = str(credentials[0])
        self._credentials['pass'] = str(credentials[1])

    def check_order_status(self, remote_pair):
        signal = getattr(self, remote_pair + "_ready_signal")
        signal.emit(True)

    def refresh(self):
        self.refresh_funds()
        self.refresh_orders()

    def refresh_funds(self):
        VirwoxGetBalancesRequest(self)

    def refresh_orders(self):
        params = {'query': {'selection':'OPEN'}}
        VirwoxGetOrdersRequest(self, params)

    def place_ask_limit_order(self, remote, amount, price):
        self._place_order(remote, 'SELL', amount, price)

    def place_bid_limit_order(self, remote, amount, price):
        self._place_order(remote, 'BUY', amount, price)

    def place_ask_market_order(self, remote, amount):
        self._place_order(remote, 'SELL', amount, 0)

    def place_bid_market_order(self, remote, amount):
        self._place_order(remote, 'BUY', amount, 0)

    def _place_order(self, remote_market, order_type, amount, price):
        params = {'query': {'instrument': remote_market, 'orderType': order_type,
                            'price': str(price), 'amount': str(amount)}}
        VirwoxPlaceOrderRequest(self, params)

    def cancel_ask_order(self, pair, order_id):
        self._cancel_order(pair, order_id, 0)

    def cancel_bid_order(self, pair, order_id):
        self._cancel_order(pair, order_id, 1)

    def _cancel_order(self, pair, order_id, order_type):
        params = {'pair':pair, 'type': order_type,
                  'query': {'orderID' : str(order_id)}}
        VirwoxCancelOrderRequest(self, params)

    def get_commission(self, amount, remote_market):
        rates = self.commissions[remote_market]
        return (amount * rates['variable']) + rates['fixed']

        # TODO find the discounted commission rate
        #VirwoxGetCommissionDiscountRequest(self)


class VirwoxPrivateRequest(_VirwoxRequest):
    priority = 2

    def __init__(self, parent, params=None):
        super(VirwoxPrivateRequest, self).__init__(parent)
        self.parent = parent
        if params:
            self.params = params
            self.params['query'].update(self.parent._credentials)
        else:
            self.params = {'query':self.parent._credentials}
        self.parent.requests.append( (self.priority, self,) )
        self.parent.host_queue.enqueue(self.parent, self.priority,)

    def post(self):
        payload = json.dumps({'method': self.method,
                              'params': self.params['query'],
                              'id': str(QtCore.QUuid.createUuid().toString())})
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("POSTing %s to %s", self.params, PRIVATE_URL)
        self.reply = self.parent.network_manager.post(private_request, payload)
        self.parent.network_manager.sslErrors.connect(self.reply.ignoreSslErrors)
        self.reply.finished.connect(self.parse_reply)


class VirwoxGetBalancesRequest(VirwoxPrivateRequest):
    method = 'getBalances'

    def handle_result(self, result):
        if result['errorCode'] != 'OK':
            self.parent.exchange_error_signal.emit(
                "VirWox " + result['errorCode'])
            return
        if not result['accountList']:
            return
        for account in result['accountList']:
            symbol = account['currency']
            if symbol in self.parent.funds_proxies:
                self.parent.funds_proxies[symbol].balance.emit(
                    Decimal(account['balance']))


class VirwoxGetCommissionDiscountRequest(VirwoxPrivateRequest):
    method = u'getCommissionDiscount'

    def handle_result(self, result):
        if result['errorCode'] != 'OK':
            self.parent.exchange_error_signal.emit(
                "VirWox " + result['errorCode'])
            return
        fee = result['commission']['total']
        self.parent.trade_commission_signal.emit(Decimal(fee))


class VirwoxGetOrdersRequest(VirwoxPrivateRequest):
    method = u'getOrders'

    def handle_result(self, result):
        if result['errorCode'] != 'OK':
            self.parent.exchange_error_signal.emit(
                "VirWox " + result['errorCode'])
            return
        if not result['orders']:
            return
        asks = dict()
        bids = dict()
        for order in result['orders']:
            order_id = order['orderID']
            pair = order['instrument']
            order_type = order['orderType']
            price = order['price']
            amount = order['amountOpen']

            if order_type == u'SELL':
                if pair not in asks:
                    asks[pair] = list()
                asks[pair].append((order_id, price, amount,))
            elif order_type == u'BUY':
                if pair not in bids:
                    bids[pair] = list()
                bids[pair].append((order_id, price, amount,))
            else:
                logger.warning("unknown order type: %s", order_type)

        for pair, orders in asks.items():
            if pair in self.parent.orders_proxies:
                self.parent.orders_proxies[pair].asks.emit(orders)
        for pair, orders in bids.items():
            if pair in self.parent.orders_proxies:
                self.parent.orders_proxies[pair].bids.emit(orders)


class VirwoxPlaceOrderRequest(VirwoxPrivateRequest):
    method = 'placeOrder'
    priority = 1

    def handle_result(self, result):
        if result['errorCode'] != 'OK':
            self.parent.exchange_error_signal.emit(
                "VirWox " + result['errorCode'])
            return
        query = self.params['query']
        order_id = result['orderID']
        price = query['price']
        amount = query['amount']
        proxy = self.parent.orders_proxies[query['instrument']]
        if query['orderType'] == 'SELL':
            proxy.ask.emit((order_id, price, amount,))
        else:
            proxy.bid.emit((order_id, price, amount,))


class VirwoxCancelOrderRequest(VirwoxPrivateRequest):
    method = 'cancelOrder'
    priority = 0

    def handle_result(self, result):
        if result['errorCode'] != 'OK':
            self.parent.exchange_error_signal.emit(
                "VirWox " + result['errorCode'])
            return
        order_id = self.params['query']['orderID']
        pair = self.params['pair']
        order_type = self.params['type']
        if order_type == 0:
            if pair in self.parent.orders_proxies:
                self.parent.orders_proxies[pair].ask_cancelled.emit(order_id)
        elif order_type == 'bid':
            if pair in self.parent.orders_proxies:
                self.parent.orders_proxies[pair].bid_cancelled.emit(order_id)



tulpenmanie.exchange.register_exchange(VirwoxExchangeMarket)
tulpenmanie.exchange.register_account(VirwoxAccount)
tulpenmanie.exchange.register_exchange_model_item(VirwoxProviderItem)
