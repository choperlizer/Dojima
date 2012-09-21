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

import numpy as np

import tulpenmanie.exchange
import tulpenmanie.translate
import tulpenmanie.orders


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
        dct[key] = decimal.Decimal(value)
    return dct


class CampbxError(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        error_msg= repr(self.value)
        logger.error(error_msg)
        return error_msg


class CampbxRequest(object):

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

    def post(self):
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("POST to %s", self.url.toString())
        self.reply = self.parent.network_manager.post(self.request,
                                                      self.query)
        self.reply.finished.connect(self._process_reply)
        self.reply.error.connect(self._process_reply)

    def _process_reply(self):
        if self.reply.error():
            logger.error(self.reply.errorString())
        else:
            if logger.isEnabledFor(logging.INFO):
                logger.debug("received reply to %s", self.reply.url().toString())
            data = json.loads(str(self.reply.readAll()))#,
                #object_pairs_hook=_object_pairs_hook)
            if 'Error' in data:
                msg = str(self.reply.url().toString()) + " : " + data['Error']
                self.parent.exchange_error_signal.emit(msg)
                logger.warning(msg)
            elif 'Info' in data:
                msg = str(self.reply.url().toString()) + " : " + data['Error']
                logger.warning(msg)
            else:
                if self.data:
                    self.data.update(data)
                    self.handler(self.data)
                else:
                    self.handler(data)
        self.reply.deleteLater()
        self.parent._replies.remove(self)


class _Campbx(QtCore.QObject):

    provider_name = EXCHANGE_NAME
    exchange_error_signal = QtCore.pyqtSignal(str)

    def pop_request(self):
        request = heapq.heappop(self._requests)
        request.post()
        self._replies.add(request)


class CampbxExchangeMarket(_Campbx, tulpenmanie.exchange.Exchange):


    _xticker_url = QtCore.QUrl(_BASE_URL + "xticker.php")

    ask_signal = QtCore.pyqtSignal(decimal.Decimal)
    last_signal = QtCore.pyqtSignal(decimal.Decimal)
    bid_signal = QtCore.pyqtSignal(decimal.Decimal)

    trades_signal = QtCore.pyqtSignal(np.ndarray)
    depth_signal = QtCore.pyqtSignal(np.ndarray)

    def __init__(self, remote_market, network_manager=None, parent=None):
        if network_manager is None:
            network_manager = tulpenmanie.network.get_network_manager()
        super(CampbxExchangeMarket, self).__init__(parent)

        self.base_query = QtCore.QUrl()
        self.network_manager = network_manager
        self._request_queue = self.network_manager.get_host_request_queue(
            HOSTNAME, 500)
        self._requests = list()
        self._replies = set()

    def refresh_ticker(self):
        request = CampbxRequest(self._xticker_url, self._xticker_handler, self)
        self._requests.append(request)
        self._request_queue.enqueue(self)

    def _xticker_handler(self, data):
        self.ask_signal.emit(decimal.Decimal(data['Best Ask']))
        self.last_signal.emit(decimal.Decimal(data['Last Trade']))
        self.bid_signal.emit(decimal.Decimal(data['Best Bid']))


class CampbxAccount(_Campbx, tulpenmanie.exchange.ExchangeAccount):
    _myfunds_url = QtCore.QUrl(_BASE_URL + "myfunds.php")
    _myorders_url = QtCore.QUrl(_BASE_URL + "myorders.php")
    _tradeenter_url = QtCore.QUrl(_BASE_URL + "tradeenter.php")
    _tradeadv_url = QtCore.QUrl(_BASE_URL + "tradeadv.php")
    _tradecancel_url = QtCore.QUrl(_BASE_URL + "tradecancel.php")
    _getbtcaddr_url = QtCore.QUrl(_BASE_URL + "getbtcaddr.php")
    _sendbtc_url = QtCore.QUrl(_BASE_URL + "sendbtc.php")

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
        super(CampbxAccount, self).__init__(parent)
        self.base_query = QtCore.QUrl()
        self.set_credentials(credentials)
        self.network_manager = network_manager
        self._request_queue = self.network_manager.get_host_request_queue(
            HOSTNAME, 500)
        self._requests = list()
        self._replies = set()

        self.ask_orders_model = tulpenmanie.orders.OrdersModel()
        self.bid_orders_model = tulpenmanie.orders.OrdersModel()

        self._bitcoin_deposit_address = None

    def set_credentials(self, credentials):
        self.base_query.addQueryItem('user', credentials[0])
        self.base_query.addQueryItem('pass', credentials[1])

    def check_order_status(self, remote_pair):
        self.BTC_USD_ready_signal.emit(True)

    def get_ask_orders_model(self, remote_pair):
        return self.ask_orders_model

    def get_bid_orders_model(self, remote_pair):
        return self.bid_orders_model

    def refresh_ticker(self):
        self._refresh_funds()

    def refresh_funds(self):
        request = CampbxRequest(self._myfunds_url, self._myfunds_handler, self)
        self._requests.append(request)
        self._request_queue.enqueue(self, 2)

    def _myfunds_handler(self, data):
        #TODO maybe not emit 'Total' but rather available
        self.BTC_balance_signal.emit(decimal.Decimal(data['Liquid BTC']))
        self.USD_balance_signal.emit(decimal.Decimal(data['Liquid USD']))

    def refresh_orders(self):
        request = CampbxRequest(self._myorders_url, self._myorders_handler, self)
        self._requests.append(request)
        self._request_queue.enqueue(self, 2)

    def _myorders_handler(self, data):
        for model, array, in ((self.ask_orders_model, 'Sell'),
                              (self.bid_orders_model, 'Buy') ):
            model.clear_orders()
            for order in data[array]:
                if 'Info' in order:
                    break

                order_id = order['Order ID']
                price = order['Price']
                amount = order['Quantity']

                model.append_order(order_id, price, amount)
            model.sort(1, QtCore.Qt.DescendingOrder)

    def place_ask_limit_order(self, pair, amount, price):
        self._place_limit_order(amount, price, "QuickSell")

    def place_bid_limit_order(self, pair, amount, price):
        self._place_limit_order(amount, price, "QuickBuy")

    def place_ask_market_order(self, pair, amount):
        self._place_market_order(amount, "AdvancedSell")

    def place_bid_market_order(self, pair, amount):
        self._place_market_order(amount, "AdvancedBuy")

    # TODO these could both be advanced
    def _place_limit_order(self, amount, price, trade_type):
        query = {'TradeMode': trade_type,
                 'Quantity': amount,
                 'Price': price}
        data = {'query': query}
        request = CampbxRequest(self._tradeenter_url, self._tradeenter_handler,
                                self, data)
        self._requests.append(request)
        self._request_queue.enqueue(self, 1)

    def _place_market_order(self, amount, trade_type):
        query = {'TradeMode': trade_type,
                 'Quantity': amount,
                 'Price': 'Market'}
        data = {'query': query}
        request = CampbxRequest(self._tradeadv_url, self._tradeenter_handler,
                                self, data)
        self._requests.append(request)
        self._request_queue.enqueue(self, 1)

    def _tradeenter_handler(self, data):
        order_id = int(data['Success'])
        data = data['query']
        amount = data['Quantity']
        price = data['Price']

        if data['TradeMode'][-4:] == 'Sell':
            if order_id:
                logger.info("ask order %s in place", order_id)
                self.ask_orders_model.append_order(order_id, price, amount)
            self.BTC_balance_changed_signal.emit(
                -decimal.Decimal(data['Quantity']))
        elif data['TradeMode'][-3:] == 'Buy':
            if order_id:
                logger.info("bid order %s in place", order_id)
                self.bid_orders_model.append_order(order_id, price, amount)
            if price == 'Market':
                price = tulpenmanie.translate.market_order_type
            else:
                self.USD_balance_changed_signal.emit(
                    -(decimal.Decimal(data['Quantity']) *
                      decimal.Decimal(data['Price'])))

    def cancel_ask_order(self, pair, order_id):
        self._cancel_order(order_id, 'Sell')

    def cancel_bid_order(self, pair, order_id):
        self._cancel_order(order_id, 'Buy')

    def _cancel_order(self, order_id, order_type):
        data = {'query':{ 'Type' : order_type,
                          'OrderID' : order_id }}
        request = CampbxRequest(self._tradecancel_url,
                                self._tradecancel_handler,
                                self, data)
        self._requests.append(request)
        self._request_queue.enqueue(self, 0)

    def _tradecancel_handler(self, data):
        words = data['Success'].split()
        order_id = words[2]
        items = self.ask_orders_model.findItems(order_id,
                                                QtCore.Qt.MatchExactly, 0)
        if len(items):
            row = items[0].row()
            self.ask_orders_model.removeRow(row)
        if not len(items):
            items = self.bid_orders_model.findItems(order_id,
                                              QtCore.Qt.MatchExactly, 0)
            row = items[0].row()
            self.bid_orders_model.removeRow(row)
        logger.debug("Trimmed order %s from a model", order_id)

    def get_bitcoin_deposit_address(self):
        if self._bitcoin_deposit_address:
            self.bitcoin_deposit_address_signal.emit(
                self._bitcoin_deposit_address)
        else:
            request = CampbxRequest(
                self._getbtcaddr_url,
                self._getbtcaddr_handler, self)
            self._requests.append(request)
            self._request_queue.enqueue(self, 2)

    def _getbtcaddr_handler(self, data):
        address = data['Success']
        self._bitcoin_deposit_address = address
        self.bitcoin_deposit_address_signal.emit(address)

    def withdraw_bitcoin(self, address, amount):
        data = {'query':
                {'BTCTo': address,
                 'BTCAmt': amount}}
        request = CampbxRequest(self._sendbtc_url,
                                self._sendbtc_handler,
                                self, data)
        self._requests.append(request)
        self._request_queue.enqueue(self, 2)

    def _sendbtc_handler(self, data):
        # TODO check this return code,
        # documentation just says returns 'true'
        transaction = data['Success']
        self.withdraw_bitcoin_reply_signal.emit(transaction)


class CampbxExchangeItem(tulpenmanie.exchange.ExchangeItem):

    provider_name = EXCHANGE_NAME

    COLUMNS = 4
    MARKETS, REFRESH_RATE, ACCOUNT_USERNAME, ACCOUNT_PASSWORD = range(COLUMNS)
    mappings = (("refresh rate", REFRESH_RATE),
                ("username", ACCOUNT_USERNAME),
                ("password", ACCOUNT_PASSWORD),)
    markets = ('BTC_USD',)

    numeric_settings = (REFRESH_RATE,)
    boolean_settings = ()
    required_account_settings = (ACCOUNT_USERNAME, ACCOUNT_PASSWORD,)
    hidden_settings = (ACCOUNT_PASSWORD,)


tulpenmanie.exchange.register_exchange(CampbxExchangeMarket)
tulpenmanie.exchange.register_account(CampbxAccount)
tulpenmanie.exchange.register_exchange_model_item(CampbxExchangeItem)
