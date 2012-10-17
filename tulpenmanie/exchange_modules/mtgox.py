# Tulpenmanie, a markets client.
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
import heapq
import hashlib
import hmac
import json
import logging
import random
import time
from decimal import Decimal

from PyQt4 import QtCore, QtGui, QtNetwork

import tulpenmanie.exchange
import tulpenmanie.data.orders
import tulpenmanie.data.ticker
import tulpenmanie.network
from tulpenmanie.model.exchanges import exchanges_model

logger = logging.getLogger(__name__)

EXCHANGE_NAME = "MtGox"
COMMODITIES = ( 'AUD', 'BTC', 'CAD', 'CHF', 'CNY', 'DKK',
                'EUR', 'GBP', 'HKD', 'JPY', 'NZD', 'PLN',
                'RUB', 'SEK', 'SGD', 'THB', 'USD' )
HOSTNAME = "mtgox.com"
_BASE_URL = "https://" + HOSTNAME + "/api/1/"


def _object_hook(dct):
    if 'value' in dct:
        return Decimal(dct['value'])
    else:
        return dct


class MtgoxExchangeItem(tulpenmanie.model.exchanges.ExchangeItem):

    exchange_name = EXCHANGE_NAME

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

    # TODO could be abstract, no object
class _Mtgox():
    exchange_name = EXCHANGE_NAME

    def pop_request(self):
        request = heapq.heappop(self.requests)[1]
        request.send()


class _MtgoxRequest(tulpenmanie.network.ExchangePOSTRequest):
    pass


class MtgoxPublicRequest(tulpenmanie.network.ExchangePOSTRequest):
    pass


class MtgoxExchangeMarket(QtCore.QObject, _Mtgox):
    # BAD redundant
    exchange_error_signal = QtCore.pyqtSignal(str)

    trades_signal = QtCore.pyqtSignal(tuple)
    depth_signal = QtCore.pyqtSignal(tuple)

    def __init__(self, network_manager=None, parent=None):
        if not network_manager:
            network_manager = tulpenmanie.network.get_network_manager()
        super(MtgoxExchangeMarket, self).__init__(parent)
        self.network_manager = network_manager
        self.host_queue = self.network_manager.get_host_request_queue(
            HOSTNAME, 5000)
        self.requests = list()
        self.replies = set()
        self._ticker_proxies = dict()
        self._ticker_clients = dict()
        self._ticker_timer = QtCore.QTimer(self)
        self._ticker_timer.timeout.connect(self._refresh_tickers)
        search = exchanges_model.findItems(self.exchange_name,
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
                'MtgoxExchangeMarketMarket', "starting ticker stream"))
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
                    'MtgoxExchangeMarketMarket', "stopping ticker stream"))
                self._ticker_timer.stop()

    def refresh_ticker(self, remote_market):
        ticker_url = QtCore.QUrl(_BASE_URL + remote_market + '/ticker')
        MtgoxTickerRequest(ticker_url, self)

    def _refresh_tickers(self):
        for remote_market in self._ticker_clients.keys():
            ticker_url = QtCore.QUrl(_BASE_URL + remote_market + "/ticker")
            MtgoxTickerRequest(ticker_url, self)

    def refresh_trade_data(self, remote_market):
        trades_url = QtCore.QUrl(_BASE_URL + remote_market + '/trades')
        MtgoxTradesRequest(trades_url, self)

    def refresh_depth_data(self, remote_market):
        depth_url = QtCore.QUrl(_BASE_URL + remote_market + '/depth')
        MtgoxDepthRequest(depth_url, self)


class MtgoxTickerRequest(tulpenmanie.network.ExchangePOSTRequest):

    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw, object_hook=_object_hook)
        if data['result'] != u'success':
            self._handle_error(data['error'])
            return
        data = data['return']
        path = self.url.path().split('/')
        remote_market = str(path[3])
        proxy = self.parent._ticker_proxies[remote_market]
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
        data = (data['asks'], data['bids'])
        self.parent.depth_signal.emit(data)

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


class MtgoxAccount(QtCore.QObject, _Mtgox, tulpenmanie.exchange.ExchangeAccount):
    # BAD redundant
    exchange_error_signal = QtCore.pyqtSignal(str)
    markets = ( 'BTCAUD', 'BTCCAD', 'BTCCHF', 'BTCCNY', 'BTCDKK',
                'BTCEUR', 'BTCGBP', 'BTCHKD', 'BTCJPY', 'BTCNZD',
                'BTCPLN', 'BTCRUB', 'BTCSEK', 'BTCSGD', 'BTCTHB',
                'BTCUSD' )

    BTCAUD_ready_signal = QtCore.pyqtSignal(bool)
    BTCCAD_ready_signal = QtCore.pyqtSignal(bool)
    BTCCHF_ready_signal = QtCore.pyqtSignal(bool)
    BTCCNY_ready_signal = QtCore.pyqtSignal(bool)
    BTCDKK_ready_signal = QtCore.pyqtSignal(bool)
    BTCEUR_ready_signal = QtCore.pyqtSignal(bool)
    BTCGBP_ready_signal = QtCore.pyqtSignal(bool)
    BTCHKD_ready_signal = QtCore.pyqtSignal(bool)
    BTCJPY_ready_signal = QtCore.pyqtSignal(bool)
    BTCNZD_ready_signal = QtCore.pyqtSignal(bool)
    BTCPLN_ready_signal = QtCore.pyqtSignal(bool)
    BTCRUB_ready_signal = QtCore.pyqtSignal(bool)
    BTCSEK_ready_signal = QtCore.pyqtSignal(bool)
    BTCSGD_ready_signal = QtCore.pyqtSignal(bool)
    BTCTHB_ready_signal = QtCore.pyqtSignal(bool)
    BTCUSD_ready_signal = QtCore.pyqtSignal(bool)

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
    multipliers = dict()

    def __init__(self, credentials, network_manager=None, parent=None):
        if network_manager is None:
            network_manager = tulpenmanie.network.get_network_manager()

        super(MtgoxAccount, self).__init__(parent)
        self.network_manager = network_manager
        self.host_queue = self.network_manager.get_host_request_queue(
            HOSTNAME, 5000)
        self.requests = list()
        self.replies = set()
        self.set_credentials(credentials)
        self.funds_proxies = dict()
        self.orders_proxies = dict()
        self._bitcoin_deposit_address = None
        self.commission = None
        self.nonce = int(time.time() / 2)

    def set_credentials(self, credentials):
        self._key = str(credentials[0])
        self._secret = base64.b64decode(credentials[1])

    def get_orders_proxy(self, remote_market):
        if remote_market not in self.orders_proxies:
            orders_proxy = tulpenmanie.data.orders.OrdersProxy(self)
            self.orders_proxies[remote_market] = orders_proxy
            return orders_proxy
        return self.orders_proxies[remote_market]

    def check_order_status(self, remote_pair):
        # This can probaly call for BTC info twice at
        # startup but whatever
        counter = remote_pair[-3:]
        multipliers = self.multipliers.keys()

        if counter not in multipliers:
            MtgoxCurrencyRequest(self._currency_url, self,
                                 {'pair': remote_pair,
                                  'query': {'currency':counter} })
            return

        if 'BTC' not in multipliers:
            MtgoxCurrencyRequest(self._currency_url, self,
                                 {'pair': remote_pair,
                                  'query': {'currency':'BTC'} })
            return

        signal = getattr(self, remote_pair + "_ready_signal")
        signal.emit(True)


    def refresh_funds(self):
        MtgoxInfoRequest(self._info_url, self)

    def refresh_orders(self):
        MtgoxOrdersRequest(self._orders_url, self)

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
        query_data = {'type': order_type,
                      'amount_int': int(amount * self.multipliers['BTC'])}
        if price:
            query_data['price_int'] = int(price * self.multipliers[counter])

        data = {'pair': remote_pair, 'amount':amount, 'price':price,
                'query': query_data }

        MtgoxPlaceOrderRequest(QtCore.QUrl(_BASE_URL + remote_pair +
                                           "/private/order/add"),
                                self, data)

    def cancel_ask_order(self, pair, order_id):
        self._cancel_order(pair, order_id, 1)
    def cancel_bid_order(self, pair, order_id):
        self._cancel_order(pair, order_id, 2)

    def _cancel_order(self, pair, order_id, order_type):
        # Mtgox doesn't have a method to cancel orders for API 1.
        # type: 1 for ask order or 2 for bid order
        data = {'pair': pair,
                'query': {'oid': order_id, 'type': order_type} }
        request = MtgoxCancelOrderRequest(self._cancel_order_url,
                                          self, data)

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


class MtgoxInfoRequest(MtgoxPrivateRequest):
    priority = 2

    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw, object_hook=_object_hook)
        for symbol, dict_ in data['return']['Wallets'].items():
            if symbol in self.parent.funds_proxies:
                signal = self.parent.funds_proxies[symbol].balance
                balance = dict_['Balance'] -  dict_['Open_Orders']
                signal.emit(balance)
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
        asks = dict()
        bids = dict()
        for order in data:
            pair = order['item'] + order['currency']
            order_id = order['oid']
            price = order['price']
            amount = order['amount']
            order_type = order['type']

            if order_type == u'ask':
                if pair not in asks:
                    asks[pair] = list()
                ask[pair].append((order_id, price, amount,))
            elif order_type == u'bid':
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


class MtgoxPlaceOrderRequest(MtgoxPrivateRequest):
    priority = 1

    def _handle_reply(self, raw):
        logger.debug(raw)
        self.data.update(json.loads(raw, object_hook=_object_hook))
        order_id = self.data['return']
        amount = self.data['amount']
        price = self.data['price']
        pair = self.data['pair']
        order_type = self.data['query']['type']

        base_signal = self.parent.funds_proxies['BTC'].balance_changed
        counter_signal = self.parent.funds_proxies[pair[-3:]].balance_changed
        if order_type == 'ask':
            self.parent.orders_proxies[pair].ask.emit(
                (order_id, price, amount,))
            base_signal.emit(-amount)
        elif order_type == 'bid':
            if price:
                counter_signal.emit(-Decimal(amount * price))
            else:
                price = QtCore.QCoreApplication.translate(
                    'MtgoxPlaceOrderRequest', "market", "at market price")
            self.parent.orders_proxies[pair].bid.emit(
                (order_id, price, amount,))



class MtgoxCancelOrderRequest(MtgoxPrivateRequest):
    priority = 0

    def _handle_reply(self, raw):
        logger.debug(raw)
        self.data.update(json.loads(raw, object_hook=_object_hook))
        pair = self.data['pair']
        order_id = str(self.data['query']['oid'])
        order_type = self.data['query']['type']

        if order_type == 1:
            self.parent.orders_proxies[pair].ask_cancelled.emit(order_id)
        elif order_type == 2:
            self.parent.orders_proxies[pair].bid_cancelled.emit(order_id)

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

tulpenmanie.exchange.register_exchange(MtgoxExchangeMarket)
tulpenmanie.exchange.register_account(MtgoxAccount)
tulpenmanie.exchange.register_exchange_model_item(MtgoxExchangeItem)
