import json
import logging
from decimal import Decimal

from PyQt4 import QtCore, QtGui, QtNetwork

from tulpenmanie.model.account import AccountsModel
from tulpenmanie.model.order import OrdersModel
from tulpenmanie.services import BaseExchangeMarket, register_exchange, register_exchange_account, register_account_model


logger = logging.getLogger(__name__)

EXCHANGE_NAME = "CampBX"
HOSTNAME = "campbx.com"
_BASE_URL = "https://" + HOSTNAME + "/api/"


def _object_pairs_hook(pairs):
    dct = dict()
    for key, value in pairs:
        dct[key] = Decimal(value)
    return dct

def _process_reply(reply):
    if logger.isEnabledFor(logging.INFO):
        logger.debug("received reply to %s", reply.url().toString())
    # TODO error handling
    data = json.loads(str(reply.readAll()))#,
        #object_pairs_hook=_object_pairs_hook)
    if 'Error' in data:
        msg = str(reply.url().toString()) + " : " + data['Error']
        raise CampbxError(msg)
    elif 'Info' in data:
        msg = str(reply.url().toString()) + " : " + data['Error']
        logger.info(msg)
        return None
    else:
        return data


class CampbxError(Exception):

    def __init__(self, value):
        self.value = value
    def __str__(self):
        error_msg= repr(self.value)
        logger.error(error_msg)
        return error_msg


class _Campbx(QtCore.QObject):
    name = EXCHANGE_NAME

class CampbxAccount(_Campbx):
    _refresh_url = QtCore.QUrl(_BASE_URL + "myfunds.php")
    _orders_url = QtCore.QUrl(_BASE_URL + "myorders.php")
    _tradeenter_url = QtCore.QUrl(_BASE_URL + "tradeenter.php")
    _tradecancel_url = QtCore.QUrl(_BASE_URL + "tradecancel.php")

    counter_balance_signal = QtCore.pyqtSignal(Decimal)
    base_balance_signal = QtCore.pyqtSignal(Decimal)
    orders_refreshed_signal = QtCore.pyqtSignal()

    ask_enable_signal = QtCore.pyqtSignal(bool)
    bid_enable_signal = QtCore.pyqtSignal(bool)

    # pending requests comes from the request queue
    pending_replies_signal = QtCore.pyqtSignal(int)

    def __init__(self, credentials, remote, parent=None):
        super(CampbxAccount, self).__init__(parent)
        self._base_query = QtCore.QUrl()
        self._base_query.addQueryItem('user', credentials[2])
        self._base_query.addQueryItem('pass', credentials[3])

        self._request_queue = self.manager.network_manager.host_queue(
            HOSTNAME, 500)
        self.pending_requests_signal = self._request_queue.pending_requests_signal
        
        for url, handler in (
                (self._refresh_url, self._funds_handler),
                (self._orders_url, self._orders_handler),
                (self._tradeenter_url, self._tradeenter_handler),
                (self._tradecancel_url, self._tradecancel_handler) ):
            self.manager.network_manager.register_reply_handler(url, handler)

        self.ask_orders_model = OrdersModel()
        self.bid_orders_model = OrdersModel()
        self.pending_replies = 0

    def _request(self, url, query_data=None, priority=1):
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("requesting %s", url.toString())
        request = QtNetwork.QNetworkRequest(url)
        request.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader,
                          "application/x-www-form-urlencoded")
        if query_data is None:
            query_data = self._base_query.encodedQuery()
        else:
            query = self._base_query
            for key, value in query_data.items():
                query.addQueryItem(key, str(value))
            query_data = query.encodedQuery()
        self._request_queue.enqueue(request, query_data, priority)
        self.pending_replies += 1
        self.pending_replies_signal.emit(self.pending_replies)

    def _receive_reply(self):
        # TODO may cause race condition
        self.pending_replies -=1
        self.pending_replies_signal.emit(self.pending_replies)

    def _funds_handler(self, reply):
        self._receive_reply()
        data = _process_reply(reply)
        self.base_balance_signal.emit(Decimal(data['Total BTC']))
        self.counter_balance_signal.emit(Decimal(data['Total USD']))

    def check_order_status(self):
        self.ask_enable_signal.emit(True)
        self.bid_enable_signal.emit(True)

    def refresh(self):
        # TODO make superclass do some logging
        self._request(self._refresh_url)
        self._request(self._orders_url)

    def refresh_orders(self):
        self._request(self._orders_url)

    def _orders_handler(self, reply):
        self._receive_reply()
        data = _process_reply(reply)
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

    def place_ask_order(self, amount, price=0):
        self._place_order(amount, price, "QuickSell")

    def place_bid_order(self, amount, price=0):
        self._place_order(amount, price, "QuickBuy")

    def _place_order(self, amount, price, trade_mode):
        data = {'TradeMode' : trade_mode,
                'Quantity' : amount}
        if price:
            data['Price'] = price
        else:
            data['Price'] = 'Market'
        self._request(self._tradeenter_url, data, 0)

    def _tradeenter_handler(self, reply):
        self._receive_reply()
        data = _process_reply(reply)
        if data['Success'] != '0':
            # Make a low priority request to refresh orders
            self._request(self._orders_url, None, 2)

    def cancel_ask_order(self, order_id):
        self._cancel_order(order_id, 'Sell')

    def cancel_bid_order(self, order_id):
        self._cancel_order(order_id, 'Buy')

    def _cancel_order(self, order_id, order_type):
        data = { 'Type' : order_type,
                 'OrderID' : order_id }
        self._request(self._tradecancel_url, data, 0)

    def _tradecancel_handler(self, reply):
        self._receive_reply()
        data = _process_reply(reply)
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


class CampbxExchangeMarket(BaseExchangeMarket, _Campbx):

    register_url = "https://CampBX.com/register.php?r=P3hAnksjDmY"
    register_url_info = """register at this link and receive a lifetime 10% """ \
                        """discount on exchange commissions"""
    icon_url = "https://campbx.com/images/favicon.ico"
    services_provided = ["market"]
    markets = ['BTC/USD']
    credential_items = ({ 'field' : "username", 'hide' : False,
                          'required': True },
                        { 'field' : "password", 'hide' : True,
                          'required': True },
                        { 'field' : 'instant transfer code', 'hide' : False,
                          'required': False })
    _refresh_url = QtCore.QUrl(_BASE_URL + "xticker.php")

    ask = QtCore.pyqtSignal(Decimal)
    bid = QtCore.pyqtSignal(Decimal)
    last = QtCore.pyqtSignal(Decimal)

    def __init__(self, remote_market, parent=None):
        super(CampbxExchangeMarket, self).__init__(parent)
        # These must be the same length
        remote_stats = ('Best Ask', 'Best Bid', 'Last Trade')
        self.stats = ('ask', 'bid', 'last')
        self.is_counter = (True, True, True)
        self._signals = dict()
        self.signals = dict()
        for i in range(len(remote_stats)):
            signal = getattr(self, self.stats[i])
            self._signals[remote_stats[i]] = signal
            self.signals[self.stats[i]] = signal

        self._request_queue = self.manager.network_manager.host_queue(
            HOSTNAME, 500)

        self.icon = QtGui.QIcon("~/tulpenmanie/tulpenmaine/providers/campbx.ico")

        self.manager.network_manager.register_reply_handler(
            self._refresh_url, self._xticker_handler)

        refresh_timer = QtCore.QTimer(self)
        refresh_timer.timeout.connect(self.refresh)
        refresh_timer.start(16000)


    def _xticker_handler(self, reply):
        if logger.isEnabledFor(logging.INFO):
            logger.debug("received reply to %s", reply.url().toString())
        # TODO error handling
        data = json.loads(str(reply.readAll()))
        for key, value in data.items():
            signal =  self._signals[key]
            signal.emit(Decimal(value))


class CampbxAccountModel(AccountsModel):

    COLUMNS = 5
    NAME, ENABLE, USERNAME, PASSWORD, TRANSFER_CODE = range(COLUMNS)
    MAPPINGS = (('name', NAME),
                ('enable', ENABLE),
                ('username', USERNAME),
                ('password', PASSWORD),
                ('transfer code', TRANSFER_CODE))
    required = (USERNAME, PASSWORD)
    hide = [PASSWORD]

    def __init__(self, parent=None):
        super(CampbxAccountModel, self).__init__(EXCHANGE_NAME, parent)

    def new_account(self):
        item = QtGui.QStandardItem()
        self.appendRow( (item,
                         QtGui.QStandardItem(),
                         QtGui.QStandardItem(),
                         QtGui.QStandardItem(),
                         QtGui.QStandardItem(),
                         QtGui.QStandardItem()) )
        return item.row()

register_exchange(CampbxExchangeMarket)
register_exchange_account(CampbxAccount)
register_account_model(CampbxAccountModel)
