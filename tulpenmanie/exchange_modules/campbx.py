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


class CampbxExchangeItem(tulpenmanie.exchange.ExchangeItem):

    exchange_name = EXCHANGE_NAME

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
            data = json.loads(raw_reply)

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

    ask_signal = QtCore.pyqtSignal(decimal.Decimal)
    last_signal = QtCore.pyqtSignal(decimal.Decimal)
    bid_signal = QtCore.pyqtSignal(decimal.Decimal)

    def __init__(self, remote_market, network_manager=None, parent=None):
        if network_manager is None:
            network_manager = tulpenmanie.network.get_network_manager()
        super(CampbxExchangeMarket, self).__init__(parent)

        self.base_query = QtCore.QUrl()
        self.network_manager = network_manager
        self.host_queue = self.network_manager.get_host_request_queue(
            HOSTNAME, 500)
        self.requests = list()
        self.replies = set()

    def refresh_ticker(self):
        CampbxTickerRequest(self._xticker_url, self)


class CampbxTickerRequest(_CampbxRequest):
    def _handle_reply(self, data):
        logger.debug(data)
        self.parent.ask_signal.emit(decimal.Decimal(data['Best Ask']))
        self.parent.last_signal.emit(decimal.Decimal(data['Last Trade']))
        self.parent.bid_signal.emit(decimal.Decimal(data['Best Bid']))


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
        self.host_queue = self.network_manager.get_host_request_queue(
            HOSTNAME, 500)
        self.requests = list()
        self.replies = set()

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
        self.parent.BTC_balance_signal.emit(decimal.Decimal(data['Liquid BTC']))
        self.parent.USD_balance_signal.emit(decimal.Decimal(data['Liquid USD']))

class CampbxOrdersRequest(_CampbxRequest):
    def _handle_reply(self, data):
        for model, array, in ((self.parent.ask_orders_model, 'Sell'),
                              (self.parent.bid_orders_model, 'Buy') ):
            model.clear_orders()
            for order in data[array]:
                if 'Info' in order:
                    break

                order_id = order['Order ID']
                price = order['Price']
                amount = order['Quantity']

                model.append_order(order_id, price, amount)
            model.sort(1, QtCore.Qt.DescendingOrder)

class CampbxTradeRequest(_CampbxRequest):
    priority = 1
    def _handle_reply(self, data):
        order_id = int(data['Success'])
        data = self.data['query']
        amount = data['Quantity']
        price = data['Price']

        if data['TradeMode'][-4:] == 'Sell':
            if order_id:
                logger.info("ask order %s in place", order_id)
                self.parent.ask_orders_model.append_order(order_id,
                                                          price, amount)
            self.parent.BTC_balance_changed_signal.emit(
                -decimal.Decimal(data['Quantity']))
        elif data['TradeMode'][-3:] == 'Buy':
            if order_id:
                logger.info("bid order %s in place", order_id)
                self.parent.bid_orders_model.append_order(order_id,
                                                          price, amount)
            if price == 'Market':
                price = tulpenmanie.translate.market_order_type
            else:
                self.parent.USD_balance_changed_signal.emit(
                    -(decimal.Decimal(data['Quantity']) *
                      decimal.Decimal(data['Price'])))


class CampbxCancelOrderRequest(_CampbxRequest):
    priority = 0
    def _handle_reply(self, data):

        words = data['Success'].split()
        order_id = words[2]
        order_type = self.data['query']['Type']
        if order_type == 'Sell':
            items = self.parent.ask_orders_model.findItems(
                order_id, QtCore.Qt.MatchExactly, 0)
            if items:
                row = items[0].row()
                self.parent.ask_orders_model.removeRow(row)
                logger.debug("Trimmed ask order %s from a model", order_id)
        elif order_type == 'Buy':
            items = self.parent.bid_orders_model.findItems(
                order_id, QtCore.Qt.MatchExactly, 0)
            if items:
                row = items[0].row()
                self.parent.bid_orders_model.removeRow(row)
                logger.debug("Trimmed bid order %s from a model", order_id)

class CampbxBitcoinAddressRequest(_CampbxRequest):
    priority = 2
    def _handle_reply(self, data):
        address = data['Success']
        self.parent._bitcoin_deposit_address = address
        self.parent.bitcoin_deposit_address_signal.emit(address)

class CampbxWithdrawBitcoinRequest(_CampbxRequest):
    priority = 2
    def _handle_reply(self, data):
        transaction = data['Success']
        reply = str(QtCore.QCoreApplication.translate(
            "CampbxWithdrawBitcoinRequest", "transaction id: {}"))
        self.parent.withdraw_bitcoin_reply_signal.emit(
            reply.format(transaction))


tulpenmanie.exchange.register_exchange(CampbxExchangeMarket)
tulpenmanie.exchange.register_account(CampbxAccount)
tulpenmanie.exchange.register_exchange_model_item(CampbxExchangeItem)
