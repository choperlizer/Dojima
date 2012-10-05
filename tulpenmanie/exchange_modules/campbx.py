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

import heapq
import json
import logging
from decimal import Decimal

from PyQt4 import QtCore, QtGui, QtNetwork

import tulpenmanie.exchange
import tulpenmanie.data.funds
import tulpenmanie.data.orders
import tulpenmanie.data.ticker
import tulpenmanie.network

logger = logging.getLogger(__name__)

EXCHANGE_NAME = "CampBX"
HOSTNAME = "campbx.com"
_BASE_URL = "https://" + HOSTNAME + "/api/"


def _reply_has_errors(reply):
    if reply.error():
        logger.error(reply.errorString())

def _object_pairs_hook(pairs):
    dct = dict()
    for key, value in pairs:
        dct[key] = Decimal(value)
    return dct


class CampbxExchangeItem(tulpenmanie.exchange.ExchangeItem):

    exchange_name = EXCHANGE_NAME

    COLUMNS = 4
    MARKETS, REFRESH_RATE, ACCOUNT_USERNAME, ACCOUNT_PASSWORD = range(COLUMNS)
    mappings = (("refresh rate (seconds)", REFRESH_RATE),
                ("username", ACCOUNT_USERNAME),
                ("password", ACCOUNT_PASSWORD),)
    markets = ('BTC_USD',)

    numeric_settings = (REFRESH_RATE,)
    boolean_settings = ()
    required_account_settings = (ACCOUNT_USERNAME, ACCOUNT_PASSWORD,)
    hidden_settings = (ACCOUNT_PASSWORD,)


class _Campbx(QtCore.QObject):
    exchange_name = EXCHANGE_NAME
    exchange_error_signal = QtCore.pyqtSignal(str)

    def pop_request(self):
        request = heapq.heappop(self.requests)[1]
        request.send()

class _CampbxRequest(tulpenmanie.network.ExchangePOSTRequest):

    def _prepare_request(self):
        self.request = tulpenmanie.network.NetworkRequest(self.url)
        self.request.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader,
                               "application/x-www-form-urlencoded")
        query = self.parent.base_query
        if self.data:
            for key, value in self.data['query'].items():
                query.addQueryItem(key, str(value))
        self.query = query.encodedQuery()

    def _extract_reply(self):
        self.parent.replies.remove(self)
        if self.reply.error():
            logger.error(self.reply.errorString())
        else:
            if logger.isEnabledFor(logging.INFO):
                logger.info("received reply to %s", self.url.toString())
            raw_reply = str(self.reply.readAll())
            data = json.loads(raw_reply, parse_float=Decimal, parse_int=Decimal)

            if 'Error' in data:
                self._handle_error(data['Error'])
            else:
                self._handle_reply(data)

"""
-            elif 'Info' in data:
-                msg = str(self.reply.url().toString()) + " : " + data['Error']
-                logger.warning(msg)
-            else:
-                if self.data:
-                    self.data.update(data)
-                    self.handler(self.data)
-                else:
-                    self.handler(data)
"""

class CampbxExchangeMarket(_Campbx, tulpenmanie.exchange.Exchange):

    _xticker_url = QtCore.QUrl(_BASE_URL + "xticker.php")

    def __init__(self, network_manager=None, parent=None):
        if network_manager is None:
            network_manager = tulpenmanie.network.get_network_manager()
        super(CampbxExchangeMarket, self).__init__(parent)

        self.base_query = QtCore.QUrl()
        self.network_manager = network_manager
        self.host_queue = self.network_manager.get_host_request_queue(
            HOSTNAME, 500)
        self.requests = list()
        self.replies = set()
        self._ticker_proxy = tulpenmanie.data.ticker.TickerProxy(self)
        self._ticker_clients = 0
        self._ticker_timer = QtCore.QTimer(self)
        self._ticker_timer.timeout.connect(self.refresh_ticker)
        search = tulpenmanie.exchange.model.findItems(self.exchange_name,
                                                      QtCore.Qt.MatchExactly)
        self._model_item = search[0]

    def get_ticker_proxy(self, remote_market):
        return self._ticker_proxy

    def refresh_ticker(self, remote_market=None):
        CampbxTickerRequest(self._xticker_url, self)

    def set_ticker_stream_state(self, state, remote_market=None):
        if state is True:
            self._ticker_clients += 1
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
                'CampbxExchangeMarket', "starting ticker stream"))
            self._ticker_timer.start(refresh_rate)
        else:
            if self._ticker_clients >1:
                self._ticker_clients -= 1
                return
            if self._ticker_clients == 0:
                return
            self._ticker_clients = 0
            logger.info(QtCore.QCoreApplication.translate(
                'CampbxExchangeMarket', "stopping ticker stream"))
            self._ticker_timer.stop()


class CampbxTickerRequest(_CampbxRequest):
    def _handle_reply(self, data):
        logger.debug(data)
        self.parent._ticker_proxy.ask_signal.emit(Decimal(data['Best Ask']))
        self.parent._ticker_proxy.last_signal.emit(Decimal(data['Last Trade']))
        self.parent._ticker_proxy.bid_signal.emit(Decimal(data['Best Bid']))


class CampbxAccount(_Campbx, tulpenmanie.exchange.ExchangeAccount):
    _myfunds_url = QtCore.QUrl(_BASE_URL + "myfunds.php")
    _myorders_url = QtCore.QUrl(_BASE_URL + "myorders.php")
    _tradeenter_url = QtCore.QUrl(_BASE_URL + "tradeenter.php")
    _tradeadv_url = QtCore.QUrl(_BASE_URL + "tradeadv.php")
    _tradecancel_url = QtCore.QUrl(_BASE_URL + "tradecancel.php")
    _getbtcaddr_url = QtCore.QUrl(_BASE_URL + "getbtcaddr.php")
    _sendbtc_url = QtCore.QUrl(_BASE_URL + "sendbtc.php")

    trade_commission_signal = QtCore.pyqtSignal(Decimal)

    BTC_USD_ready_signal = QtCore.pyqtSignal(bool)

    bitcoin_deposit_address_signal = QtCore.pyqtSignal(str)
    withdraw_bitcoin_reply_signal = QtCore.pyqtSignal(str)

    def __init__(self, credentials, network_manager=None, parent=None):
        if network_manager is None:
            network_manager = tulpenmanie.network.get_network_manager()
        super(CampbxAccount, self).__init__(parent)
        self.base_query = QtCore.QUrl()
        self.set_credentials(credentials)
        self.network_manager = network_manager
        self.host_queue = self.network_manager.get_host_request_queue(
            HOSTNAME, 500)
        self.requests = list()
        self.replies = set()
        self._funds_proxies = dict()
        self._orders_proxy = tulpenmanie.data.orders.OrdersProxy(self)

        self._bitcoin_deposit_address = None

    def set_credentials(self, credentials):
        self.base_query.addQueryItem('user', credentials[0])
        self.base_query.addQueryItem('pass', credentials[1])

    def get_orders_proxy(self, remote_market=None):
        return self._orders_proxy

    def check_order_status(self, remote_pair):
        self.BTC_USD_ready_signal.emit(True)

    def refresh_ticker(self):
        self._refresh_funds()

    def refresh_funds(self):
        CampbxFundsRequest(self._myfunds_url, self)

    def refresh_orders(self):
        CampbxOrdersRequest(self._myorders_url, self)

    def place_ask_limit_order(self, pair, amount, price):
        self._place_order("AdvancedSell", amount, price)
    def place_bid_limit_order(self, pair, amount, price):
        self._place_order("AdvancedBuy", amount, price)

    def place_ask_market_order(self, pair, amount):
        self._place_order("AdvancedSell", amount)
    def place_bid_market_order(self, pair, amount):
        self._place_order("AdvancedBuy", amount)

    def _place_order(self, trade_type, amount, price=None):
        if price is None:
            price = 'Market'
        query = {'TradeMode': trade_type,
                 'Quantity': amount,
                 'Price': price}
        data = {'query': query}
        request = CampbxTradeRequest(self._tradeadv_url, self, data)

    def cancel_ask_order(self, pair, order_id):
        self._cancel_order(order_id, 'Sell')
    def cancel_bid_order(self, pair, order_id):
        self._cancel_order(order_id, 'Buy')

    def _cancel_order(self, order_id, order_type):
        data = {'query':{ 'Type' : order_type,
                          'OrderID' : order_id }}
        CampbxCancelOrderRequest(self._tradecancel_url, self, data)

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


class CampbxFundsRequest(_CampbxRequest):
    def _handle_reply(self, data):
        logger.debug(data)
        self.parent._funds_proxies['BTC'].balance.emit(
            Decimal(data['Liquid BTC']))
        self.parent._funds_proxies['USD'].balance.emit(
            Decimal(data['Liquid USD']))
        self.parent.trade_commission_signal.emit(Decimal('0.55'))

class CampbxOrdersRequest(_CampbxRequest):
    def _handle_reply(self, data):
        logger.debug(data)
        asks = list()
        bids = list()
        for raw_orders, processed_orders in ((data['Sell'], asks),
                                             (data['Buy'], bids)):
            if 'Info' in raw_orders[0]:
                continue
            for order in raw_orders:
                processed_orders.append((order['Order ID'],
                                         order['Price'],
                                         order['Quantity']))
        if asks:
            self.parent._orders_proxy.asks.emit(asks)
        if bids:
            self.parent._orders_proxy.bids.emit(bids)


class CampbxTradeRequest(_CampbxRequest):
    priority = 1
    def _handle_reply(self, data):
        logger.debug(data)
        order_id = str(data['Success'])
        data = self.data['query']
        amount = data['Quantity']
        price = data['Price']

        if data['TradeMode'][-4:] == 'Sell':
            self.parent._funds_proxies['BTC'].balance_changed.emit(
                -Decimal(data['Quantity']))
            if order_id:
                logger.info("ask order %s in place", order_id)
                self.parent._orders_proxy.ask.emit((order_id, price, amount))
        elif data['TradeMode'][-3:] == 'Buy':
            if order_id:
                logger.info("bid order %s in place", order_id)
                self.parent._orders_proxy.bid.emit((order_id, price, amount,))
            if price == 'Market':
                price = QtCore.QCoreApplication.translate(
                    'CampbxTradeRequest', "market", "at market price")
            else:
                self.parent._funds_proxies['USD'].balance_changed.emit(
                    -(Decimal(data['Quantity']) *
                      Decimal(data['Price'])))


class CampbxCancelOrderRequest(_CampbxRequest):
    priority = 0
    def _handle_reply(self, data):
        logger.debug(data)
        words = data['Success'].split()
        order_id = words[2]
        order_type = self.data['query']['Type']
        if order_type == 'Sell':
            self.parent._orders_proxy.ask_cancelled.emit(order_id)
            logger.info("ask order %s cancelled", order_id)
        elif order_type == 'Buy':
            self.parent._orders_proxy.bid_cancelled.emit(order_id)
            logger.debug("bid order %s cancelled", order_id)


class CampbxBitcoinAddressRequest(_CampbxRequest):
    priority = 2
    def _handle_reply(self, data):
        logger.debug(data)
        address = data['Success']
        self.parent._bitcoin_deposit_address = address
        self.parent.bitcoin_deposit_address_signal.emit(address)


class CampbxWithdrawBitcoinRequest(_CampbxRequest):
    priority = 2
    def _handle_reply(self, data):
        logger.debug(data)
        transaction = data['Success']
        reply = str(QtCore.QCoreApplication.translate(
            "CampbxWithdrawBitcoinRequest", "transaction id: {}"))
        self.parent.withdraw_bitcoin_reply_signal.emit(
            reply.format(transaction))


tulpenmanie.exchange.register_exchange(CampbxExchangeMarket)
tulpenmanie.exchange.register_account(CampbxAccount)
tulpenmanie.exchange.register_exchange_model_item(CampbxExchangeItem)
