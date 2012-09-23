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
import tulpenmanie.network
import tulpenmanie.orders
import tulpenmanie.translate


logger = logging.getLogger(__name__)

EXCHANGE_NAME = "Bitstamp"
HOSTNAME = "www.bitstamp.net"
_BASE_URL = "https://" + HOSTNAME + "/api/"


class BitstampExchangeItem(tulpenmanie.exchange.ExchangeItem):

    exchange_name = EXCHANGE_NAME

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


class _Bitstamp(QtCore.QObject):
    exchange_name = EXCHANGE_NAME
    exchange_error_signal = QtCore.pyqtSignal(str)
    
    def pop_request(self):
        request = heapq.heappop(self.requests)[1]
        request.send()


class BitstampExchangeMarket(_Bitstamp):

    base_query = QtCore.QUrl()
    _ticker_url = QtCore.QUrl(_BASE_URL + 'ticker/')
    _transactions_url = QtCore.QUrl(_BASE_URL + 'transactions/')

    ask_signal = QtCore.pyqtSignal(decimal.Decimal)
    last_signal = QtCore.pyqtSignal(decimal.Decimal)
    bid_signal = QtCore.pyqtSignal(decimal.Decimal)
    trades_signal = QtCore.pyqtSignal(tuple)

    def __init__(self, remote_market, network_manager=None, parent=None):
        if network_manager is None:
            network_manager = tulpenmanie.network.get_network_manager()
        super(BitstampExchangeMarket, self).__init__(parent)

        self.network_manager = network_manager
        self.host_queue = self.network_manager.get_host_request_queue(
            HOSTNAME, 500)
        self.requests = list()
        self.replies = set()

    def refresh_ticker(self):
        BitstampTickerRequest(self._ticker_url, self)

    def refresh_trade_data(self):
        BitstampTransactionsRequest(self._transactions_url, self)


class BitstampTickerRequest(tulpenmanie.network.ExchangeGETRequest):

    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw)
        self.parent.ask_signal.emit(decimal.Decimal(data['ask']))
        self.parent.last_signal.emit(decimal.Decimal(data['last']))
        self.parent.bid_signal.emit(decimal.Decimal(data['bid']))


class BitstampTransactionsRequest(tulpenmanie.network.ExchangeGETRequest):

    def _handle_reply(self, raw):
        trade_list = json.loads(raw, object_hook=self._object_hook)
        dates = list()
        prices = list()
        amounts = list()
        for date, price, amount in trade_list:
            dates.append(date)
            prices.append(price)
            amounts.append(amount)

        # The trades are FIFO
        for l in dates, prices, amounts:
            l.reverse()
        self.parent.trades_signal.emit( (dates, prices, amounts) )

    def _object_hook(self, dict_):
        date = int(dict_['date'])
        price = float(dict_['price'])
        amount = float(dict_['amount'])
        return (date, price, amount)


class BitstampAccount(_Bitstamp, tulpenmanie.exchange.ExchangeAccount):
    _balance_url = QtCore.QUrl(_BASE_URL + 'balance/')
    _open_orders_url = QtCore.QUrl(_BASE_URL + 'open_orders/')
    _cancel_order_url = QtCore.QUrl(_BASE_URL + 'cancel_order/')
    _buy_limit_url = QtCore.QUrl(_BASE_URL + 'buy/')
    _sell_limit_url = QtCore.QUrl(_BASE_URL + 'sell/')
    _bitcoin_deposit_address_url = QtCore.QUrl(
        _BASE_URL + "bitcoin_deposit_address/")
    _bitcoin_withdrawal_url = QtCore.QUrl(_BASE_URL + "bitcoin_withdrawal/")

    exchange_error_signal = QtCore.pyqtSignal(str)

    BTC_balance_signal = QtCore.pyqtSignal(decimal.Decimal)
    USD_balance_signal = QtCore.pyqtSignal(decimal.Decimal)

    BTC_balance_changed_signal = QtCore.pyqtSignal(decimal.Decimal)
    USD_balance_changed_signal = QtCore.pyqtSignal(decimal.Decimal)

    BTC_USD_ready_signal = QtCore.pyqtSignal(bool)

    bitcoin_deposit_address_signal = QtCore.pyqtSignal(str)
    withdraw_bitcoin_reply_signal = QtCore.pyqtSignal(str)

    def __init__(self, credentials, network_manager=None, parent=None):
        if network_manager is None:
            network_manager = tulpenmanie.network.get_network_manager()
        super(BitstampAccount, self).__init__(parent)
        self.base_query = QtCore.QUrl()
        self.set_credentials(credentials)
        self.network_manager = network_manager
        self.host_queue = self.network_manager.get_host_request_queue(
            HOSTNAME, 500)
        self.requests = list()
        self.replies = set()

        self.ask_orders_model = tulpenmanie.orders.OrdersModel()
        self.bid_orders_model = tulpenmanie.orders.OrdersModel()
        self._bitcoin_deposit_address = None

    def set_credentials(self, credentials):
        self.base_query.addQueryItem('user', credentials[0])
        self.base_query.addQueryItem('password', credentials[1])

    def check_order_status(self, remote_pair):
        self.BTC_USD_ready_signal.emit(True)

    def get_ask_orders_model(self, remote_pair):
        return self.ask_orders_model

    def get_bid_orders_model(self, remote_pair):
        return self.bid_orders_model

    def refresh_funds(self):
        BitstampBalanceRequest(self._balance_url, self)

    def refresh_orders(self):
        BitstampOpenOrdersRequest(self._open_orders_url, self)

    def process_orders(self, orders):
        for model in self.ask_orders_model, self.bid_orders_model:
            model.clear_orders()

        for order in orders:
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

    # TODO these could both be advanced
    def _place_limit_order(self, amount, price, url):
        query = {'amount': amount,
                 'price': price}
        data = {'query': query}

        BitstampPlaceOrderRequest(url, self, data)

    def cancel_ask_order(self, pair, order_id):
        self._cancel_order(order_id, 0)

    def cancel_bid_order(self, pair, order_id):
        self._cancel_order(order_id, 1)

    def _cancel_order(self, order_id, order_type):
        data = {'type': order_type,
                'query':{ 'id': order_id }}
        BitstampCancelOrderRequest(self._cancel_order_url, self, data)

    def get_bitcoin_deposit_address(self):
        if self._bitcoin_deposit_address:
            self.bitcoin_deposit_address_signal.emit(
                self._bitcoin_deposit_address)
        else:
            BitstampBitcoinDepositAddressRequest(
                self._bitcoin_deposit_address_url, self)

    def withdraw_bitcoin(self, address, amount):
        data = {'query':
                {'address': address,
                 'amount': amount}}

        request = BitstampBitcoinWithdrawalRequest(
            self._bitcoin_withdrawal_url, self, data)


class BitstampPrivateRequest(tulpenmanie.network.ExchangePOSTRequest):

    def _prepare_request(self):
        self.request = tulpenmanie.network.NetworkRequest(self.url)
        self.request.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader,
                               "application/x-www-form-urlencoded")
        query = self.parent.base_query
        if self.data:
            for key, value in self.data['query'].items():
                query.addQueryItem(key, str(value))
        self.query = query.encodedQuery()


class BitstampBalanceRequest(BitstampPrivateRequest):
    prority = 1

    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw)
        self.parent.BTC_balance_signal.emit(
            decimal.Decimal(data['btc_available']))
        self.parent.USD_balance_signal.emit(
            decimal.Decimal(data['usd_available']))


class BitstampOpenOrdersRequest(BitstampPrivateRequest):
    priority = 2

    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw)
        if data:
            self.parent.process_orders(data)


class BitstampPlaceOrderRequest(BitstampPrivateRequest):
    priority = 1

    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw)

        order_id = int(data['id'])
        amount = decimal.Decimal(data['amount'])
        price = decimal.Decimal(data['price'])
        # type - buy or sell (0 - buy; 1 - sell)
        if data['type'] == 0:
            logger.info("bid order %s in place", order_id)
            self.parent.bid_orders_model.append_order(order_id, price, amount)
            self.parent.USD_balance_changed_signal.emit( -(amount * price))

        elif data['type'] == 1:
            logger.info("ask order %s in place", order_id)
            self.parent.ask_orders_model.append_order(order_id, price, amount)
            self.parent.BTC_balance_changed_signal.emit( -amount)


class BitstampCancelOrderRequest(BitstampPrivateRequest):
    prority = 0

    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw)

        if data:
            order_id = self.data['query']['id']
            if not self.data['type']:
                items = self.parent.ask_orders_model.findItems(
                    order_id, QtCore.Qt.MatchExactly, 0)
                if items:
                    row = items[0].row()
                    self.parent.ask_orders_model.removeRow(row)
            else:
                items = self.parent.bid_orders_model.findItems(
                    order_id, QtCore.Qt.MatchExactly, 0)
                if items:
                    row = items[0].row()
                    self.parent.bid_orders_model.removeRow(row)
            logger.info("order %s canceled", order_id)


class BitstampBitcoinDepositAddressRequest(BitstampPrivateRequest):
    priority = 2

    def _handle_reply(self, raw):
        logger.debug(raw)
        address = json.loads(raw)
        self.parent.bitcoin_deposit_address_signal.emit(address)


class BitstampBitcoinWithdrawalRequest(BitstampPrivateRequest):
    priority = 2

    def _handle_reply(self, raw):
        logger.debug(raw)
        result = json.loads(raw)
        reply = str(QtCore.QCoreApplication.translate(
            "BitstampExchangeAccount", """Bitstamp replied "{}" """))
        self.parent.withdraw_bitcoin_reply_signal.emit(reply.format(result))


tulpenmanie.exchange.register_exchange(BitstampExchangeMarket)
tulpenmanie.exchange.register_account(BitstampAccount)
tulpenmanie.exchange.register_exchange_model_item(BitstampExchangeItem)
