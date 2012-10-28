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

import decimal
import logging

from PyQt4 import QtCore, QtGui

import tulpenmanie.ui.widget
import tulpenmanie.model.orders
from tulpenmanie.model.commodities import commodities_model

logger =  logging.getLogger(__name__)


class ErrorHandling(object):

    # TODO this thing make redundant messages, it sucks.
    # maybe do something with class variables

    def exchange_error_handler(self, message):
        message_box = QtGui.QMessageBox(self)
        message_box.setIcon(QtGui.QMessageBox.Warning)
        message_box.setText(message)
        message_box.exec_()


class ExchangeDockWidget(QtGui.QDockWidget, ErrorHandling):

    def __init__(self, exchangeProxy, marketPair, action, parent=None):
        exchange_name = exchangeProxy.name
        self.base_id, self.counter_id = marketPair.split('_')

        # Building the pretty name again
        # there will probably be problems when commodities are deleted
        search = commodities_model.findItems(self.base_id)
        self.base_row = search[0].row()
        base_name = commodities_model.item(self.base_row,
                                           commodities_model.NAME).text()

        search = commodities_model.findItems(self.counter_id)
        self.counter_row = search[0].row()
        counter_name = commodities_model.item(self.counter_row,
                                              commodities_model.NAME).text()
        title = QtCore.QCoreApplication.translate(
            'ExchangeDockWidget', "%1 - %2 / %3", "exchange name, base, counter"
            ).arg(exchange_name).arg(base_name).arg(counter_name)

        super(ExchangeDockWidget, self).__init__(title, parent)

        self.remote_market = exchangeProxy.getMapping(marketPair)

        self.account = None
        self.exchange = exchangeProxy.getExchangeObject()
        self.enable_exchange_action = action

        #Widgets
        self.widget = QtGui.QWidget(self)
        side_layout = QtGui.QGridLayout()
        side_layout.setColumnStretch(1,1)
        label_font = QtGui.QFont()
        label_font.setPointSize(7)

        row = 0
        for translation, stat in (
            (QtCore.QCoreApplication.translate(
                'ExchangeDockWidget', "ask", "best ask price"), 'ask'),
            (QtCore.QCoreApplication.translate(
                'ExchangeDockWidget', "last", "price of last trade"), 'last'),
            (QtCore.QCoreApplication.translate(
                'ExchangeDockWidget', "bid", "best bid price"), 'bid')):

            label = QtGui.QLabel(translation)
            label.setAlignment(QtCore.Qt.AlignRight)
            label.setFont(label_font)
            widget = tulpenmanie.ui.widget.CommodityLcdWidget(self.counter_row)
            setattr(self, '{}_widget'.format(stat), widget)
            side_layout.addWidget(label, row,0)
            side_layout.addWidget(widget, row,1)
            row += 1

        self.layout = QtGui.QHBoxLayout()
        self.layout.addLayout(side_layout)
        self.widget.setLayout(self.layout)
        self.setWidget(self.widget)

    def set_signal_connection_state(self, state):
        if not state: return

        self.exchange.exchange_error_signal.connect(self.exchange_error_handler)
        ticker_proxy = self.exchange.getTickerProxy(self.remote_market)
        ticker_proxy.ask_signal.connect(self.ask_widget.setValue)
        ticker_proxy.last_signal.connect(self.last_widget.setValue)
        ticker_proxy.bid_signal.connect(self.bid_widget.setValue)

    def closeEvent(self, event):
        self.enableExchange(False)

        self.enable_exchange_action.setChecked(False)
        event.accept()

    def enableExchange(self, enable):
        self.setEnabled(enable)
        self.setVisible(enable)
        self.set_signal_connection_state(enable)
        self.exchange.setTickerStreamState(enable, self.remote_market)
        if self.account:
            self.account_widget.enableAccount(enable)

        if enable and self.account is None:
            self.createAccountWidget()
        # this model is gone for now, rewrite this when there is an active
        # exchange markets model
        """
        market_item = self.exchange_item.child(0, self.exchange_item.MARKETS)
        enable_item = market_item.child(self.market_row,
                                        self.exchange_item.MARKET_ENABLE)
        if enable:
            enable_item.setText("true")
        else:
            enable_item.setText("false")
        """

    def createAccountWidget(self):
        # TODO there should be an option to change account from this dock
        if not self.exchange.hasDefaultAccount(self.remote_market):
            if not self.exchange.showAccountDialog(self.remote_market, self):
                return

        self.account = self.exchange.getAccountObject()

        self.account_widget = AccountWidget(self.account, self)
        self.layout.addWidget(self.account_widget)


class AccountWidget(QtGui.QWidget, ErrorHandling):

    # TODO now I've got to deal with these OT double accounts

    def __init__(self, account_object, parent):
        super(AccountWidget, self).__init__(parent)

        # Data
        self.account = account_object
        self.market_id = parent.remote_market

        # TODO see if the orders model can be optimized
        self.asks_model = tulpenmanie.model.orders.OrdersModel(
            parent.base_row, parent.counter_row, self)
        self.bids_model = tulpenmanie.model.orders.OrdersModel(
            parent.base_row, parent.counter_row, self)
        self.asks_model.setHorizontalHeaderLabels(
            ("id",
             QtCore.QCoreApplication.translate('AccountWidget',
                                               "ask", "ask price"),
             QtCore.QCoreApplication.translate('AccountWidget',
                                               "amount", "ask amount")))
        self.bids_model.setHorizontalHeaderLabels(
            ("id",
             QtCore.QCoreApplication.translate('AccountWidget',
                                               "bid", "bid price"),
             QtCore.QCoreApplication.translate('AccountWidget',
                                               "amount", "bid amount")))
        # Create UI
        layout = QtGui.QGridLayout()

        base_funds_label = tulpenmanie.ui.widget.FundsLabel(
            parent.base_row)
        counter_funds_label = tulpenmanie.ui.widget.FundsLabel(
            parent.counter_row)

        refresh_funds_action = QtGui.QAction(
            QtCore.QCoreApplication.translate('AccountWidget',
                                              "&refresh funds"),
            self, triggered=self.refreshFunds)

        funds_font = QtGui.QFont()
        funds_font.setPointSize(13)
        for label in (base_funds_label,
                      counter_funds_label):
            label.setAlignment(QtCore.Qt.AlignHCenter)
            label.setFont(funds_font)
            label.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
            label.addAction(refresh_funds_action)

        layout.addWidget(base_funds_label, 0,0, 1,3)
        layout.addWidget(counter_funds_label, 0,3, 1,3)

        self.ask_base_amount_spin = tulpenmanie.ui.widget.CommoditySpinBox(
            parent.base_row)
        self.ask_base_amount_spin.valueChanged[float].connect(
            self.ask_base_amount_changed)

        self.bid_base_amount_spin = tulpenmanie.ui.widget.CommoditySpinBox(
            parent.base_row)
        self.bid_base_amount_spin.valueChanged[float].connect(
            self.bid_base_amount_changed)

        self.ask_price_spin = tulpenmanie.ui.widget.CommoditySpinBox(
            parent.counter_row)
        self.ask_price_spin.valueChanged[float].connect(self.ask_price_changed)

        self.bid_price_spin = tulpenmanie.ui.widget.CommoditySpinBox(
            parent.counter_row)
        self.bid_price_spin.valueChanged[float].connect(self.bid_price_changed)

        self.ask_counter_amount_label = tulpenmanie.ui.widget.AmountLabel(
            parent.counter_row)
        self.ask_counter_estimate_label = tulpenmanie.ui.widget.EstimateLabel(
            parent.counter_row)
        self.bid_counter_amount_label = tulpenmanie.ui.widget.AmountLabel(
            parent.counter_row)
        self.bid_counter_estimate_label = tulpenmanie.ui.widget.EstimateLabel(
            parent.counter_row)

        ask_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate('AccountWidget', "&ask",
                                              "as in place ask order"))
        bid_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate('AccountWidget', "&bid",
                                              "as in place bid order"))
        ask_order_menu = QtGui.QMenu()
        ask_limit_action = QtGui.QAction(
            QtCore.QCoreApplication.translate('AccountWidget', "limit order"),
            ask_button)
        ask_limit_action.setEnabled(False)
        ask_market_action = QtGui.QAction(
            QtCore.QCoreApplication.translate('AccountWidget', "market order"),
            ask_button)
        ask_market_action.setEnabled(False)
        ask_order_menu.addAction(ask_limit_action)
        ask_order_menu.addAction(ask_market_action)
        ask_order_menu.setDefaultAction(ask_limit_action)
        ask_button.setMenu(ask_order_menu)

        bid_order_menu = QtGui.QMenu()
        bid_limit_action = QtGui.QAction(
            QtCore.QCoreApplication.translate('AccountWidget', "limit order"),
            bid_button)
        bid_limit_action.setEnabled(False)
        bid_market_action = QtGui.QAction(
            QtCore.QCoreApplication.translate('AccountWidget', "market order"),
            bid_button)
        bid_market_action.setEnabled(False)
        bid_order_menu.addAction(bid_limit_action)
        bid_order_menu.addAction(bid_market_action)
        bid_order_menu.setDefaultAction(bid_limit_action)
        bid_button.setMenu(bid_order_menu)

        at_seperator = QtCore.QCoreApplication.translate('AccountWidget',
                                                         "@", "amount @ price")

        layout.addWidget(self.ask_base_amount_spin, 1,0)
        layout.addWidget(QtGui.QLabel(at_seperator), 1,1)
        layout.addWidget(self.ask_price_spin, 1,2)
        layout.addWidget(ask_button, 2,0, 2,1)
        layout.addWidget(self.ask_counter_amount_label, 2,2,)
        layout.addWidget(self.ask_counter_estimate_label, 3,2,)

        layout.addWidget(self.bid_base_amount_spin, 1,3)
        layout.addWidget(QtGui.QLabel(at_seperator), 1,4)
        layout.addWidget(self.bid_price_spin, 1,5)
        layout.addWidget(bid_button, 2,3, 2,1)
        layout.addWidget(self.bid_counter_amount_label, 2,5)
        layout.addWidget(self.bid_counter_estimate_label, 3,5)

        for spin in (self.ask_base_amount_spin, self.bid_base_amount_spin,
                     self.ask_price_spin,self.bid_price_spin):
            spin.setMaximum(999999)

        self.ask_orders_view = QtGui.QTableView()
        self.ask_orders_view.setModel(self.asks_model)
        layout.addWidget(self.ask_orders_view, 4,0, 1,3)

        self.bid_orders_view = QtGui.QTableView()
        self.bid_orders_view.setModel(self.bids_model)
        layout.addWidget(self.bid_orders_view, 4,3, 1,3)

        for view in self.ask_orders_view, self.bid_orders_view:
            view.setSelectionMode(QtGui.QListView.SingleSelection)
            view.setSelectionBehavior(QtGui.QListView.SelectRows)
            view.setColumnHidden(0, True)
            #view.setShowGrid(False)
            view.verticalHeader().hide()
            view.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

        #Refresh orders action
        refresh_orders_action = QtGui.QAction(
            "&refresh orders", self, triggered=self.account.refresh_orders)
        #Cancel order action
        cancel_ask_action = QtGui.QAction("&cancel ask order", self,
                                   triggered=self._cancel_ask)
        self.ask_orders_view.addAction(cancel_ask_action)
        self.ask_orders_view.addAction(refresh_orders_action)
        cancel_bid_action = QtGui.QAction("&cancel bid order", self,
                                   triggered=self._cancel_bid)
        self.bid_orders_view.addAction(cancel_bid_action)
        self.bid_orders_view.addAction(refresh_orders_action)

        self.setLayout(layout)

        # Connect to account
        # these are remote ids, not local
        b_ac_id, c_ac_id = self.account.getAccountPair(self.market_id)

        base_funds_proxy = self.account.getFundsProxy(b_ac_id)
        base_funds_proxy.balance.connect(base_funds_label.setValue)
        base_funds_proxy.balance_changed.connect(
            base_funds_label.change_value)

        counter_funds_proxy = self.account.getFundsProxy(c_ac_id)
        counter_funds_proxy.balance.connect(counter_funds_label.setValue)
        counter_funds_proxy.balance_changed.connect(
            counter_funds_label.change_value)

        self.account.exchange_error_signal.connect(self.exchange_error_handler)

        orders_proxy = self.account.getOrdersProxy(self.market_id)
        orders_proxy.asks.connect(self.new_asks)
        orders_proxy.bids.connect(self.new_bids)
        orders_proxy.ask.connect(self.new_ask)
        orders_proxy.bid.connect(self.new_bid)
        orders_proxy.ask_cancelled.connect(self.ask_cancelled)
        orders_proxy.bid_cancelled.connect(self.bid_cancelled)

        self.account.refresh(self.market_id)

    def enableAccount(self, enable):
        if enable:
            self.account.refresh(self.market_id)

    def new_asks(self, orders):
        self.asks_model.clear_orders()
        self.asks_model.append_orders(orders)

    def new_ask(self, order):
        self.asks_model.append_orders( (order,) )

    def new_bids(self, orders):
        self.bids_model.clear_orders()
        self.bids_model.append_orders(orders)

    def new_bid(self, order):
        self.bids_model.append_orders( (order,) )

    def _ask_limit(self):
        amount = self.ask_base_amount_spin.decimal_value()
        price = self.ask_price_spin.decimal_value()
        self.account.placeAskLimitOrder(self.market_id, amount, price)

    def _bid_limit(self):
        amount = self.bid_base_amount_spin.decimal_value()
        price = self.bid_price_spin.decimal_value()
        self.account.placeBidLimitOrder(self.market_id, amount, price)

    def _ask_market(self):
        amount = self.ask_base_amount_spin.decimal_value()
        self.account.placeAskMarketOrder(self.market_id, amount)

    def _bid_market(self):
        amount = self.bid_base_amount_spin.decimal_value()
        self.account.placeBidMarketOrder(self.market_id, amount)

    def _cancel_ask(self):
        row = self.ask_orders_view.currentIndex().row()
        item = self.asks_model.item(row, self.asks_model.ORDER_ID)
        if item:
            order_id = item.text()
            self.account.cancelAskOrder(self.market_id, order_id)

    def ask_cancelled(self, order_id):
        items = self.asks_model.findItems(order_id, QtCore.Qt.MatchExactly, 0)
        for item in items:
            self.asks_model.removeRow(item.row())

    def _cancel_bid(self):
        row = self.bid_orders_view.currentIndex().row()
        item = self.bids_model.item(row, self.bids_model.ORDER_ID)
        if item:
            order_id = item.text()
            self.account.cancelBidOrder(self.market_id, order_id)

    def bid_cancelled(self, order_id):
        items = self.bids_model.findItems(order_id, QtCore.Qt.MatchExactly, 0)
        for item in items:
            self.bids_model.removeRow(item.row())

    def ask_base_amount_changed(self, base_amount):
        base_amount = decimal.Decimal(str(base_amount))
        if not base_amount:
            self.ask_counter_amount_label.clear()
            return
        price = self.ask_price_spin.decimal_value()
        if not price:
            self.ask_counter_amount_label.clear()
            return
        self.change_ask_counter(base_amount, price)

    def ask_price_changed(self, price):
        price = decimal.Decimal(str(price))
        if not price:
            self.ask_counter_amount_label.clear()
            return
        base_amount = self.ask_base_amount_spin.decimal_value()
        if not base_amount:
            self.ask_counter_amount_label.clear()
            return
        self.change_ask_counter(base_amount, price)

    def change_ask_counter(self, base_amount, price):
        counter_amount = base_amount * price
        self.ask_counter_amount_label.setValue(counter_amount)
        commission = self.account.getCommission(counter_amount,
                                                self.market_id)
        if commission:
            self.ask_counter_estimate_label.setValue(counter_amount - commission)
            return
        self.ask_counter_estimate_label.clear()

    def bid_base_amount_changed(self, base_amount):
        base_amount = decimal.Decimal(str(base_amount))
        if not base_amount:
            self.bid_counter_amount_label.clear()
            return
        price = self.bid_price_spin.decimal_value()
        if not price:
            self.bid_counter_amount_label.clear()
            return
        self.change_bid_counter(base_amount, price)

    def bid_price_changed(self, price):
        price = decimal.Decimal(str(price))
        if not price:
            self.bid_counter_amount_label.clear()
            return
        base_amount = self.bid_base_amount_spin.decimal_value()
        if not base_amount:
            self.bid_counter_amount_label.clear()
        else:
            self.change_bid_counter(base_amount, price)

    def change_bid_counter(self, base_amount, price):
        counter_amount = base_amount * price
        self.bid_counter_amount_label.setValue(counter_amount)
        commission = self.account.getCommission(counter_amount,
                                                self.market_id)
        if commission:
            self.bid_counter_estimate_label.setValue(counter_amount - commission)
        else:
            self.bid_counter_estimate_label.clear()

    def refreshFunds(self):
        self.account.refreshFunds(self.market_id)
