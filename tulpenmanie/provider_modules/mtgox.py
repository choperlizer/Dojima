import base64
import hashlib
import hmac
import logging
import time
import json
from decimal import Decimal
from PyQt4 import QtCore, QtGui, QtNetwork

import tulpenmanie.providers
from tulpenmanie.model.order import OrdersModel


logger = logging.getLogger(__name__)


EXCHANGE_NAME = "MtGox"
HOSTNAME = "mtgox.com"
_BASE_URL = "https://" + HOSTNAME + "/api/1/"


def _object_hook(dct):
    if 'value' in dct:
        return Decimal(dct['value'])
    else:
        return dct

def _generic_handler(reply):
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("received reply to %s", reply.url().toString())
    raw = str(reply.readAll())
    data = json.loads(raw, object_hook=_object_hook)
    if data['result'] != u'success':
        msg = str(reply.url().toString()) + " : " + data['error']
        raise MtgoxError(msg)
    return data['return']


class MtgoxError(Exception):

    def __init__(self, value):
        self.value = value
    def __str__(self):
        error_msg= repr(self.value)
        logger.error(error_msg)
        return error_msg


class _Mtgox(QtCore.QObject):
    provider_name = EXCHANGE_NAME

    def _public_request(self, url, query_data=None):
        request = QtNetwork.QNetworkRequest(url)
        request.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader,
                          "application/x-www-form-urlencoded")
        if query_data is not None:
            data = QtCore.QUrl()
            for key, value in query_data.items():
                data.addQueryItem(key, str(value))
            query_data = data.encodedQuery()
        self._request_queue.enqueue(request, query_data)

class MtgoxExchange(_Mtgox):

    register_url = None

    ask = QtCore.pyqtSignal(Decimal)
    bid = QtCore.pyqtSignal(Decimal)
    last = QtCore.pyqtSignal(Decimal)
    volume = QtCore.pyqtSignal(Decimal)
    high = QtCore.pyqtSignal(Decimal)
    high = QtCore.pyqtSignal(Decimal)
    low = QtCore.pyqtSignal(Decimal)
    average = QtCore.pyqtSignal(Decimal)
    VWAP = QtCore.pyqtSignal(Decimal)

    def __init__(self, remote_market, parent=None):
        super(MtgoxExchange, self).__init__(parent)
        #TODO automatic _url to _handler connection with getattr
        self._ticker_url = QtCore.QUrl(_BASE_URL +
                                        remote_market + "/ticker")
        # These must be the same length
        remote_stats = ('sell', 'buy', 'last_local', 'vol',
                        'high', 'low', 'avg', 'vwap')
        self.stats = ('ask', 'bid', 'last', 'volume',
                       'high', 'low', 'average', 'VWAP')
        self.is_counter = (True, True, True, False,
                           True, True, True, True)

        self._signals = dict()
        self.signals = dict()
        for i in range(len(remote_stats)):
            signal = getattr(self, self.stats[i])
            self._signals[remote_stats[i]] = signal
            self.signals[self.stats[i]] = signal

        # TODO make this wait time a user option
        self._request_queue = self.manager.network_manager.host_queue(
            HOSTNAME, 5000, False)
        #for url, handler in self._refresh_url, self._ticker_handler:
        self.manager.network_manager.register_reply_handler(
            self._ticker_url, self._ticker_handler)

        refresh_timer = QtCore.QTimer(self)
        refresh_timer.timeout.connect(self.refresh)
        refresh_timer.start(15000)

    def refresh(self):
        self._public_request(self._ticker_url)

    def _ticker_handler(self, reply):
        data = _generic_handler(reply)
        for key, value in data.items():
            if self._signals.has_key(key):
                signal = self._signals[key]
                signal.emit(value)


class MtgoxAccount(_Mtgox):

    _info_url = QtCore.QUrl(_BASE_URL + "generic/private/info")
    _currency_url = QtCore.QUrl(_BASE_URL + "generic/currency")
    _orders_url = QtCore.QUrl(_BASE_URL + "generic/private/orders")
    _cancelorder_url = QtCore.QUrl("https://mtgox.com/api/0/cancelOrder.php")

    last_login_signal = QtCore.pyqtSignal(Decimal)
    monthly_volume_signal = QtCore.pyqtSignal(Decimal)
    fee_signal = QtCore.pyqtSignal(Decimal)
    counter_balance_signal = QtCore.pyqtSignal(Decimal)
    base_balance_signal = QtCore.pyqtSignal(Decimal)

    orders_refresh_signal = QtCore.pyqtSignal()

    ask_enable_signal = QtCore.pyqtSignal(bool)
    bid_enable_signal = QtCore.pyqtSignal(bool)

    # pending requests comes from the request queue
    pending_replies_signal = QtCore.pyqtSignal(int)

    def __init__(self, credentials, remote, parent=None):
        super(MtgoxAccount, self).__init__(parent)
        ##BAD, hardcoding
        self._key = str(credentials[2])
        self._secret = base64.b64decode(credentials[3])

        self.remote_pair = str(remote)
        self.base = self.remote_pair[:3]
        self.counter = self.remote_pair[3:]
        self._place_order_url = QtCore.QUrl(
            _BASE_URL + self.remote_pair + "/private/order/add")

        # These must be the same length
        remote_stats = ()
        local_stats = ()
        self._signals = dict()
        self.signals = dict()
        for i in range(len(remote_stats)):
            signal = getattr(self, local_stats[i])
            self._signals[remote_stats[i]] = signal
            self.signals[local_stats[i]] = signal

        self._request_queue = self.manager.network_manager.host_queue(
            HOSTNAME, 5000, False)
        self.pending_requests_signal = self._request_queue.pending_requests_signal

        for url, handler in (
                (self._info_url, self._info_handler),
                (self._currency_url, self._currency_handler),
                (self._orders_url, self._orders_handler),
                (self._place_order_url, self._debug_handler),
                (self._cancelorder_url, self._cancelorder_handler) ):
            self.manager.network_manager.register_reply_handler(url, handler)

        self.ask_orders_model = OrdersModel()
        self.bid_orders_model = OrdersModel()

        # Set currency information so we don't under-price and under-volume
        self.base_multiplier = None
        self.counter_multiplier = None
        for symbol in self.base, self.counter:
            self._public_request(self._currency_url, {'currency': symbol})
        self.pending_replies = 2

    def _request(self, url, query_data=None, priority=0):
        request = QtNetwork.QNetworkRequest(url)
        request.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader,
                          "application/x-www-form-urlencoded")
        data = QtCore.QUrl()
        data.addQueryItem('nonce', str(time.time() * 1000000))
        if query_data is not None:
            for key, value in query_data.items():
                data.addQueryItem(key, str(value))
        data = data.encodedQuery()

        h = hmac.new(self._secret, data, hashlib.sha512)
        signature =  base64.b64encode(h.digest())

        request.setRawHeader('Rest-Key', self._key)
        request.setRawHeader('Rest-Sign', signature)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("queuing %s request", url.toString())
        #Priority is overidden otherwise nonces will get mixed up
        self._request_queue.enqueue(request, data)
        self.pending_replies += 1
        self.pending_replies_signal.emit(self.pending_replies)

    def _receive_reply(self):
        # TODO may cause race condition
        self.pending_replies -=1
        self.pending_replies_signal.emit(self.pending_replies)

    def refresh(self):
        """Refresh orders, then balances."""
        self._request(self._orders_url)
        self._request(self._info_url)

    def _info_handler(self, reply):
        self._receive_reply()
        data =_generic_handler(reply)
        self.base_balance_signal.emit(data['Wallets']
                                      [self.base]['Balance'])
        self.counter_balance_signal.emit(data['Wallets']
                                         [self.counter]['Balance'])

    def _currency_handler(self, reply):
        self._receive_reply()
        data = _generic_handler(reply)
        places = int(data['decimals'])
        if data['currency'] == self.base:
            self.base_multiplier = pow(10, places)
        elif data['currency'] == self.counter:
            self.counter_multiplier = pow(10, places)
        self.check_order_status()

    def check_order_status(self):
        if self.base_multiplier is None:
            return
        elif self.counter_multiplier is None:
            return
        else:
            self.ask_enable_signal.emit(True)
            self.bid_enable_signal.emit(True)

    def refresh_orders(self):
        self._request(self._orders_url)

    def _orders_handler(self, reply):
        self._receive_reply()
        data = _generic_handler(reply)
        if data:
            for model in self.ask_orders_model, self.bid_orders_model:
                model.clear_orders()
        for order in data:
            order_id = order['oid']
            price = str(order['price'])
            amount = str(order['amount'])
            order_type = order['type']

            if order_type == u'ask':
                self.ask_orders_model.append_order(order_id, price, amount)
            elif order_type == u'bid':
                self.bid_orders_model.append_order(order_id, price, amount)
            else:
                logger.error("unknown order type: %s", order_type)
                return

            for model in self.ask_orders_model, self.bid_orders_model:
                model.sort(1, QtCore.Qt.DescendingOrder)

    def place_bid_order(self, amount, price=0):
        self._place_order('bid', amount, price)

    def place_ask_order(self, amount, price=0):
        self._place_order('ask', amount, price)

    def _place_order(self, order_type, amount, price):
        data = {'type': order_type,
                'amount_int': amount * self.base_multiplier}
        if price:
            data['price_int'] = price * self.counter_multiplier
        else:
            logger.info("placing a market order")
        self._request(self._place_order_url, data)

    def cancel_ask_order(self, order_id):
        self._cancel_order(order_id, 1)

    def cancel_bid_order(self, order_id):
        self._cancel_order(order_id, 2)

    def _cancel_order(self, order_id, order_type):
        # MtGox doesn't have a method to cancel orders for API 1.
        # type: 1 for sell order or 2 for buy order
        url = QtCore.QUrl("https://mtgox.com/api/0/cancelOrder.php")
        data = {'oid': order_id, 'type': order_type}
        req = self._request(url, data)

    def _cancelorder_handler(self, reply):
        self._receive_reply()
        # Since the reply is to an API 0 request, just refresh the orders.
        self.refresh_orders()

    def _debug_handler(self, reply):
        self._receive_reply()
        if logger.isEnabledFor(logging.DEBUG):
            data =_generic_handler(reply)
            logger.debug(data)



class MtgoxProviderItem(tulpenmanie.providers.ProviderItem):

    provider_name = EXCHANGE_NAME
    COLUMNS = 2
    MARKETS, ACCOUNTS = range(COLUMNS)
    markets = ( 'BTCUSD', 'BTCEUR', 'BTCAUD', 'BTCCAD', 'BTCCHF', 'BTCCNY',
                'BTCDKK', 'BTCGBP', 'BTCHKD', 'BTCJPY', 'BTCNZD', 'BTCPLN',
                'BTCRUB', 'BTCSEK', 'BTCSGD', 'BTCTHB' )

    ACCOUNT_COLUMNS = 4
    ACCOUNT_NAME, ACCOUNT_ENABLE, ACCOUNT_KEY, ACCOUNT_SECRET = range(ACCOUNT_COLUMNS)
    account_mappings = (('enable', ACCOUNT_ENABLE),
                        ('api_key', ACCOUNT_KEY),
                        ('secret', ACCOUNT_SECRET))
    account_required = (ACCOUNT_KEY, ACCOUNT_SECRET)
    account_hide = []
    

tulpenmanie.providers.register_exchange(MtgoxExchange)
tulpenmanie.providers.register_account(MtgoxAccount)
tulpenmanie.providers.register_exchange_model_item(MtgoxProviderItem)
