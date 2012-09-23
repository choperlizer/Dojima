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

import tulpenmanie.exchange
import tulpenmanie.network

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


class MtgoxExchangeItem(tulpenmanie.exchange.ExchangeItem):

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


class MtgoxExchange(QtCore.QObject, _Mtgox):
    # BAD redundant
    exchange_error_signal = QtCore.pyqtSignal(str)

    ask_signal = QtCore.pyqtSignal(decimal.Decimal)
    last_signal = QtCore.pyqtSignal(decimal.Decimal)
    bid_signal = QtCore.pyqtSignal(decimal.Decimal)
    trades_signal = QtCore.pyqtSignal(tuple)

    def __init__(self, remote_market, network_manager=None, parent=None):
        if not network_manager:
            network_manager = tulpenmanie.network.get_network_manager()
        super(MtgoxExchange, self).__init__(parent)
        self.network_manager = network_manager
        self.host_queue = self.network_manager.get_host_request_queue(
            HOSTNAME, 5000)
        self.requests = list()
        self.replies = set()
        self._ticker_url = QtCore.QUrl(_BASE_URL + remote_market + '/ticker')
        self._trades_url = QtCore.QUrl(_BASE_URL + remote_market + '/trades')
        self._depth_url = QtCore.QUrl(_BASE_URL + remote_market + '/depth')

    def refresh_ticker(self):
        MtgoxTickerRequest(self._ticker_url, self)

    def refresh_trade_data(self):
        MtgoxTradesRequest(self._trades_url, self)

    def refresh_depth_data(self):
        MtgoxDepthRequest(self._depth_url, self)


class MtgoxTickerRequest(tulpenmanie.network.ExchangePOSTRequest):

    def _handle_reply(self, raw):
            data = json.loads(raw, object_hook=_object_hook)
            if data['result'] != u'success':
                self._handle_error(data['error'])
            else:
                data = data['return']
                self.parent.ask_signal.emit(data['sell'])
                self.parent.last_signal.emit(data['last_local'])
                self.parent.bid_signal.emit(data['buy'])


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
        if 'return' in dict_:
            return

        self.dates.append(int(dict_[u'date']))
        self.prices.append(float(dict_[u'price']))
        self.amounts.append(float(dict_[u'amount']))


class MtgoxDepthRequest(MtgoxPublicRequest):

    def _handle_reply(self, raw):
        data = json.loads(raw, object_hook=self._object_hook)
        f = file('/tmp/depth_tuples.pickle', 'wb')
        import pickle
        pickle.dump(data, f)
        f.close
        self.parent.depth_signal.emit(data)

    def _object_hook(self, dict_):
        if 'currency' in dict_:
            return None
        if 'asks' in dict_:
            return (dict_['asks'], dict_['bids'])
        if 'return' in dict_:
            return dict_['return']

        else:
            price = float(dict_['price'])
            amount = float(dict_['amount'])
            return (price, amount)



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
    withdraw_bitcoin_reply_signal = QtCore.pyqtSignal(str)

    _currency_url = QtCore.QUrl(_BASE_URL + "generic/currency")
    _info_url = QtCore.QUrl(_BASE_URL + "generic/private/info")
    _orders_url = QtCore.QUrl(_BASE_URL + "generic/private/orders")
    _cancel_order_url = QtCore.QUrl("https://" + HOSTNAME +
                                   "/api/0/cancelOrder.php")
    _bitcoin_address_url = QtCore.QUrl(_BASE_URL + "generic/bitcoin/address")

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
        self.ask_orders = dict()
        self.bid_orders = dict()
        self._bitcoin_deposit_address = None
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
        amount = decimal.Decimal(amount)
        query_data = {'type': order_type,
                      'amount_int': int(amount * self.multipliers['BTC'])}
        if price:
            price = decimal.Decimal(price)
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
            return self._bitcoin_deposit_address
        else:
            MtgoxBitcoinDepositAddressRequest(self._bitcoin_address_url, self)


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
        data = json.loads(raw, object_hook=_object_hook)
        for symbol, dict_ in data['return']['Wallets'].items():
            signal = getattr(self.parent, symbol + '_balance_signal', None)
            if signal:
                balance = dict_['Balance'] -  dict_['Open_Orders']
                signal.emit(balance)
            else:
                logger.warning("unknown commodity %s found in balances", symbol)


class MtgoxOrdersRequest(MtgoxPrivateRequest):
    priority = 1

    def _handle_reply(self, raw):
        data = json.loads(raw, object_hook=_object_hook)
        data = data['return']
        if data:
            for models in self.parent.ask_orders, self.parent.bid_orders:
                for model in models.values():
                    model.clear_orders()
            for order in data:
                pair = order['item'] + order['currency']
                order_id = order['oid']
                price = order['price']
                amount = order['amount']
                order_type = order['type']

                if order_type == u'ask':
                    self.parent.ask_orders[pair].append_order(
                        order_id, price, amount)
                elif order_type == u'bid':
                    self.parent.bid_orders[pair].append_order(
                        order_id, price, amount)
                else:
                    logger.warning("unknown order type: %s", order_type)
                    continue

            for models in self.parent.ask_orders, self.parent.bid_orders:
                for model in models.values():
                    model.sort(1, QtCore.Qt.DescendingOrder)


class MtgoxPlaceOrderRequest(MtgoxPrivateRequest):
    priority = 1

    def _handle_reply(self, raw):
        self.data.update(json.loads(raw, object_hook=_object_hook))
        order_id = self.data['return']
        amount = self.data['amount']
        price = self.data['price']
        pair = self.data['pair']
        order_type = self.data['query']['type']

        base_signal = self.parent.BTC_balance_changed_signal
        counter_signal = getattr(self.parent,
                                 pair[-3:] + '_balance_changed_signal')
        if order_type == 'ask':
            self.parent.ask_orders[pair].append_order(order_id, price, amount)
            base_signal.emit(-amount)
        elif order_type == 'bid':
            if price:
                counter_signal.emit(-decimal.Decimal(amount * price))
            else:
                price = tulpenmanie.translate.market_order_type
            self.parent.bid_orders[pair].append_order(order_id, price, amount)


class MtgoxCancelOrderRequest(MtgoxPrivateRequest):
    priority = 0

    def _handle_reply(self, raw):
        self.data.update(json.loads(raw, object_hook=_object_hook))
        pair = self.data['pair']
        order_id = self.data['query']['oid']
        order_type = self.data['query']['type']

        if order_type == 1:
            self.parent.ask_orders[pair].remove_order(order_id)
        elif order_type == 2:
            self.parent.bid_orders[pair].remove_order(order_id)

class MtgoxBitcoinDepositAddressRequest(MtgoxPrivateRequest):
    priority = 2

    def _handle_reply(self, raw):
        data = json.loads(raw)
        address = data['return']['addr']
        self.parent._bitcoin_deposit_address = address
        self.parent.bitcoin_deposit_address_signal.emit(address)


tulpenmanie.exchange.register_exchange(MtgoxExchange)
tulpenmanie.exchange.register_account(MtgoxAccount)
tulpenmanie.exchange.register_exchange_model_item(MtgoxExchangeItem)
