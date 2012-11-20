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

import logging

from PyQt4 import QtCore, QtGui

import tulpenmanie.ui.widget
#import tulpenmanie.model.orders
from tulpenmanie.model.commodities import commodities_model

logger =  logging.getLogger(__name__)


class ErrorHandling(object):

    # TODO this thing make redundant messages, it sucks.

    def exchange_error_handler(self, message):
        message_box = QtGui.QMessageBox(self)
        message_box.setIcon(QtGui.QMessageBox.Warning)
        message_box.setText(message)
        message_box.exec_()


class ExchangeDockWidget(QtGui.QDockWidget, ErrorHandling):

    def __init__(self, exchangeProxy, marketPair, marketID, action, parent=None):
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

        self.remote_market = marketID

        self.account_obj = None
        self.exchange_obj = exchangeProxy.getExchangeObject()
        self.enable_exchange_action = action

        # get our display parameters
        self.base_factor, self.counter_factor = self.exchange_obj.getFactors(
            self.remote_market)

        self.base_precision, ok = commodities_model.item(
            self.base_row, commodities_model.PRECISION).text().toInt()
        if not ok: self.base_precision = 0

        self.counter_precision, ok = commodities_model.item(
            self.counter_row, commodities_model.PRECISION).text().toInt()
        if not ok: self.counter_precision = 0

        #Widgets
        self.widget = QtGui.QWidget(self)
        side_layout = QtGui.QVBoxLayout()
        label_font = QtGui.QFont()
        label_font.setPointSize(7)

        if self.counter_factor > 1:
            AssetLCDWidget = tulpenmanie.ui.widget.AssetDecimalLCDWidget
        else:
            AssetLCDWidget = tulpenmanie.ui.widget.AssetIntLCDWidget

        row = 1
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
            widget = AssetLCDWidget(self.counter_factor, self.counter_precision)
            setattr(self, '{}_widget'.format(stat), widget)
            side_layout.addWidget(label)
            side_layout.addWidget(widget)
            side_layout.setStretch(row, 1)
            row += 2

        self.menu_bar = ExchangeDockWidgetMenuBar(self)

        self.layout = QtGui.QHBoxLayout()
        self.layout.setMenuBar(self.menu_bar)
        self.layout.addLayout(side_layout)
        self.widget.setLayout(self.layout)
        self.setWidget(self.widget)

        # Exchanges may store a reference to this menu and update it
        self.exchange_obj.populateMenuBar(self.menu_bar, self.remote_market)
        if not hasattr(self.exchange_obj, 'getScale'):
            return

        proxy = self.exchange_obj.getAccountValidityProxy(self.remote_market)
        proxy.accountValidityChanged.connect(self.enableAccount)

        action = self.menu_bar.getMarketMenu().addAction(
            QtCore.QCoreApplication.translate('ScaleSelectDialog',
                                              "Select market scale",
                                              "Title of a menu action to show "
                                              "the ScaleSelectDialog"))

        action.triggered.connect(self.showScaleSelectDialog)
        
        #self.exchange_obj.checkAccountValidity(self.remote_market)

    def enableAccount(self, enable):
        if enable and (self.account_obj is None):
            self.createAccountWidget()
            return

        if self.account_widget:
            self.account_widget.enableAccount(enable)

    def enableExchange(self, enable):
        self.setEnabled(enable)
        self.setVisible(enable)
        self.set_signal_connection_state(enable)
        self.exchange_obj.setTickerStreamState(enable, self.remote_market)
        if self.account_obj:
            self.account_widget.enableAccount(enable)

        if enable:
            self.exchange_obj.echoTicker(self.remote_market)

            if self.account_obj is None:
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

    def closeEvent(self, event):
        self.enableExchange(False)

        self.enable_exchange_action.setChecked(False)
        event.accept()

    def createAccountWidget(self):
        # try and make the menus pop up when they are needed
        #if not self.exchange_obj.hasAccount(self.remote_market):
        #    return
        self.account_obj = self.exchange_obj.getAccountObject()
        self.account_widget = AccountWidget(self.account_obj, self)
        self.layout.addWidget(self.account_widget)

    def setScale(self, scale):
        print "beep beep boop boop, set scale to", scale

    def set_signal_connection_state(self, state):
        if not state: return

        self.exchange_obj.exchange_error_signal.connect(
            self.exchange_error_handler)
        ticker_proxy = self.exchange_obj.getTickerProxy(self.remote_market)
        ticker_proxy.ask_signal.connect(self.ask_widget.setValue)
        ticker_proxy.last_signal.connect(self.last_widget.setValue)
        ticker_proxy.bid_signal.connect(self.bid_widget.setValue)

    def showScaleSelectDialog(self):
        dialog = ScaleSelectDialog(
            self.base_factor, self.base_precision,
            self.exchange_obj.getScale(self.remote_market))
        if dialog.exec_():
            self.setScale(dialog.getScale())


class ExchangeDockWidgetMenuBar(QtGui.QMenuBar):

    def __init__(self, parent=None):
        super(ExchangeDockWidgetMenuBar, self).__init__(parent)
        self.exchange = parent
        self.market_menu = self.addMenu(
            QtCore.QCoreApplication.translate('ExchangeDockWidgetMenuBar',
                                              "Market",
                                              "The title of a drop down menu "
                                              "to edit market settings."))

        self.exchange_menu = self.addMenu(
            QtCore.QCoreApplication.translate('ExchangeDockWidgetMenuBar',
                                              "Exchange",
                                              "The title of a drop down menu "
                                              "to edit exchange settings."))

        self.account_menu = self.addMenu(
            QtCore.QCoreApplication.translate('ExchangeDockWidget',
                                              "Account",
                                              "The title of a drop down menu "
                                              "to edit account settings."))

    def getMarketMenu(self):
        return self.market_menu
    def getExchangeMenu(self):
        return self.exchange_menu
    def getAccountMenu(self):
        return self.account_menu


class AccountWidget(QtGui.QWidget, ErrorHandling):

    def __init__(self, account_object, parent):
        super(AccountWidget, self).__init__(parent)
        self.dock = parent

        # Data
        self.account_obj = account_object
        self.market_id = parent.remote_market

        if parent.base_factor > 1:
            BaseSpinBox = tulpenmanie.ui.widget.AssetDecimalSpinBox
            BaseAmountLabel = tulpenmanie.ui.widget.AssetDecimalAmountLabel
            BaseBalanceLabel = tulpenmanie.ui.widget.BalanceDecimalLabel
        else:
            BaseSpinBox = tulpenmanie.ui.widget.AssetIntSpinBox
            BaseAmountLabel = tulpenmanie.ui.widget.AssetIntAmountLabel
            BaseBalanceLabel = tulpenmanie.ui.widget.BalanceIntLabel

        if parent.counter_factor > 1:
            CounterSpinBox = tulpenmanie.ui.widget.AssetDecimalSpinBox
            CounterAmountLabel = tulpenmanie.ui.widget.AssetDecimalAmountLabel
            CounterBalanceLabel = tulpenmanie.ui.widget.BalanceDecimalLabel
        else:
            CounterSpinBox = tulpenmanie.ui.widget.AssetIntSpinBox
            CounterAmountLabel = tulpenmanie.ui.widget.AssetIntAmountLabel
            CounterBalanceLabel = tulpenmanie.ui.widget.BalanceIntLabel
        # Now use the widget class references below

        # Create UI
        layout = QtGui.QGridLayout()

        self.base_balance_label = BaseBalanceLabel(
            parent.base_factor, parent.base_precision)
        self.counter_balance_label = CounterBalanceLabel(
                parent.counter_factor, parent.counter_precision)

        refresh_balance_action = QtGui.QAction(
            QtCore.QCoreApplication.translate('AccountWidget',
                                              "&refresh balance"),
            self, triggered=self.refreshBalance)

        balance_font = QtGui.QFont()
        balance_font.setPointSize(13)
        for label in (self.base_balance_label, self.counter_balance_label):
            label.setAlignment(QtCore.Qt.AlignHCenter)
            label.setFont(balance_font)
            label.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
            label.addAction(refresh_balance_action)

        layout.addWidget(self.base_balance_label, 0,0, 1,3)
        layout.addWidget(self.counter_balance_label, 0,3, 1,3)

        self.ask_amount_spin = BaseSpinBox(parent.base_factor,
                                           parent.base_precision)

        self.bid_amount_spin = BaseSpinBox(parent.base_factor,
                                           parent.base_precision)

        self.ask_price_spin = CounterSpinBox(parent.counter_factor,
                                             parent.counter_precision)

        self.bid_price_spin = CounterSpinBox(parent.counter_factor,
                                             parent.counter_precision)

        self.ask_amount_label = CounterAmountLabel(
            parent.counter_factor, parent.counter_precision)
        self.ask_counter_estimate_label = CounterAmountLabel(
            parent.counter_factor, parent.counter_precision)

        self.bid_amount_label = CounterAmountLabel(
            parent.counter_factor, parent.counter_precision)
        self.bid_counter_estimate_label = CounterAmountLabel(
            parent.counter_factor, parent.counter_precision)

        # Set the prefixi and suffixi
        base_prefix = commodities_model.item(
            parent.base_row, commodities_model.PREFIX).text()
        counter_prefix = commodities_model.item(
            parent.counter_row, commodities_model.PREFIX).text()

        base_suffix = commodities_model.item(
            parent.base_row, commodities_model.SUFFIX).text()
        counter_suffix = commodities_model.item(
            parent.counter_row, commodities_model.SUFFIX).text()

        if base_prefix:
            for widget in (self.base_balance_label,
                           self.ask_amount_spin,
                           self.bid_amount_spin):
                widget.setPrefix(base_prefix)

        if base_suffix:
            for widget in (self.base_balance_label,
                           self.ask_amount_spin,
                           self.bid_amount_spin):
                widget.setSuffix(base_suffix)

        if counter_prefix:
            for widget in (self.counter_balance_label,
                           self.ask_price_spin, self.bid_price_spin,
                           self.ask_amount_label,
                           self.bid_amount_label):
                widget.setPrefix(counter_prefix)

        if counter_suffix:
            for widget in (self.counter_balance_label,
                           self.ask_price_spin, self.bid_price_spin,
                           self.ask_amount_label,
                           self.bid_amount_label):
                widget.setSuffix(counter_suffix)

        ask_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate('AccountWidget', "&ask",
                                              "as in place ask offer"))
        bid_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate('AccountWidget', "&bid",
                                              "as in place bid offer"))
        ask_offer_menu = QtGui.QMenu()
        ask_limit_action = QtGui.QAction(
            QtCore.QCoreApplication.translate('AccountWidget', "limit offer"),
            ask_button
            )
        ask_market_action = QtGui.QAction(
            QtCore.QCoreApplication.translate('AccountWidget', "market offer"),
            ask_button)
        ask_market_action.setEnabled(False)
        ask_offer_menu.addAction(ask_limit_action)
        ask_offer_menu.addAction(ask_market_action)
        ask_offer_menu.setDefaultAction(ask_limit_action)
        ask_button.setMenu(ask_offer_menu)

        bid_offer_menu = QtGui.QMenu()
        bid_limit_action = QtGui.QAction(
            QtCore.QCoreApplication.translate('AccountWidget', "limit offer"),
            bid_button)
        bid_market_action = QtGui.QAction(
            QtCore.QCoreApplication.translate('AccountWidget', "market offer"),
            bid_button)
        bid_market_action.setEnabled(False)
        bid_offer_menu.addAction(bid_limit_action)
        bid_offer_menu.addAction(bid_market_action)
        bid_offer_menu.setDefaultAction(bid_limit_action)
        bid_button.setMenu(bid_offer_menu)

        at_seperator = QtCore.QCoreApplication.translate('AccountWidget',
                                                         "@", "amount @ price")

        layout.addWidget(self.ask_amount_spin, 2,0)
        layout.addWidget(QtGui.QLabel(at_seperator), 2,1)
        layout.addWidget(self.ask_price_spin, 2,2)
        layout.addWidget(ask_button, 3,0, 2,1)
        layout.addWidget(self.ask_amount_label, 4,2,)
        layout.addWidget(self.ask_counter_estimate_label, 4,2,)

        layout.addWidget(self.bid_amount_spin, 2,3)
        layout.addWidget(QtGui.QLabel(at_seperator), 2,4)
        layout.addWidget(self.bid_price_spin, 2,5)
        layout.addWidget(bid_button, 3,3, 2,1)
        layout.addWidget(self.bid_amount_label, 3,5)
        layout.addWidget(self.bid_counter_estimate_label, 4,5)

        for spin in (self.ask_amount_spin, self.bid_amount_spin,
                     self.ask_price_spin,self.bid_price_spin):
            spin.setMaximum(999999)

        self.ask_offers_view = QtGui.QTableView()
        layout.addWidget(self.ask_offers_view, 5,0, 1,3)

        self.bid_offers_view = QtGui.QTableView()
        layout.addWidget(self.bid_offers_view, 5,3, 1,3)

        for view in self.ask_offers_view, self.bid_offers_view:
            view.setSelectionMode(QtGui.QListView.SingleSelection)
            view.setSelectionBehavior(QtGui.QListView.SelectRows)
            view.setShowGrid(False)
            view.verticalHeader().hide()
            view.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
            view.setColumnHidden(0, True)
            #count = offers_model.columnCount()
            #while count > 4:
            #    count -= 1
            #    view.setColumnHiddden(count, True)

        #Refresh offers action
        refresh_offers_action = QtGui.QAction(
            "&refresh offers", self, triggered=self.account_obj.refreshOffers)
        #Cancel offer action
        cancel_ask_action = QtGui.QAction("&cancel ask offer", self,
                                          triggered=self._cancel_ask)
        self.ask_offers_view.addAction(cancel_ask_action)
        self.ask_offers_view.addAction(refresh_offers_action)
        cancel_bid_action = QtGui.QAction("&cancel bid offer", self,
                                          triggered=self._cancel_bid)
        self.bid_offers_view.addAction(cancel_bid_action)
        self.bid_offers_view.addAction(refresh_offers_action)

        self.setLayout(layout)

        # inter-widget connections
        self.ask_amount_spin.valueChanged[int].connect(
            self.ask_amount_changed)
        self.bid_amount_spin.valueChanged[int].connect(
            self.bid_amount_changed)

        self.ask_price_spin.valueChanged[int].connect(self.ask_price_changed)
        self.bid_price_spin.valueChanged[int].connect(self.bid_price_changed)


        # Connect to account
        # these are remote ids, not local
        self.account_obj.accountChanged.connect(self.changeAccount)

        self.account_obj.exchange_error_signal.connect(
            self.exchange_error_handler)

        ask_limit_action.triggered.connect(self._ask_limit)
        bid_limit_action.triggered.connect(self._bid_limit)

        self.enableAccount(True)

    def enableAccount(self, enable):
        if not enable:
            self.setDisabled(True)
            return

        if not self.account_obj.hasAccount(self.market_id):
            self.setDisabled(True)
            return

        self.setEnabled(True)

        b_ac_id, c_ac_id = self.account_obj.getAccountPair(self.market_id)

        self.base_balance_proxy = self.account_obj.getBalanceProxy(
            b_ac_id)
        self.base_balance_proxy.balance.connect(
            self.base_balance_label.setValue)
        self.base_balance_proxy.balance_changed.connect(
            self.base_balance_label.change_value)

        self.counter_balance_proxy = self.account_obj.getBalanceProxy(
            c_ac_id)
        self.counter_balance_proxy.balance.connect(
            self.counter_balance_label.setValue)
        self.counter_balance_proxy.balance_changed.connect(
            self.counter_balance_label.change_value)

        offers_model = self.account_obj.getOffersModel(self.market_id)
        # SELLING == OT_TRUE, BUYING == OT_FALSE
        self.asks_model = QtGui.QSortFilterProxyModel()
        self.asks_model.setSourceModel(offers_model)
        self.asks_model.setFilterKeyColumn(3)
        self.asks_model.setFilterFixedString('a')
        self.asks_model.setDynamicSortFilter(True)
        self.ask_offers_view.setModel(self.asks_model)

        self.bids_model = QtGui.QSortFilterProxyModel()
        self.bids_model.setSourceModel(offers_model)
        self.bids_model.setFilterKeyColumn(3)
        self.bids_model.setFilterFixedString('b')
        self.bids_model.setDynamicSortFilter(True)
        self.bid_offers_view.setModel(self.bids_model)

        self.account_obj.refresh(self.market_id)

    def _ask_limit(self):
        amount = self.ask_amount_spin.value()
        price = self.ask_price_spin.value()
        self.account_obj.placeAskLimitOffer(self.market_id, amount, price)

    def _bid_limit(self):
        amount = self.bid_amount_spin.value()
        price = self.bid_price_spin.value()
        self.account_obj.placeBidLimitOffer(self.market_id, amount, price)

    def _ask_market(self):
        amount = self.ask_amount_spin.value()
        self.account_obj.placeAskMarketOffer(self.market_id, amount)

    def _bid_market(self):
        amount = self.bid_amount_spin.value()
        self.account_obj.placeBidMarketOffer(self.market_id, amount)

    def _cancel_ask(self):
        row = self.ask_offers_view.currentIndex().row()
        item = self.asks_model.item(row, 0)
        if item:
            offer_id = item.text()
            self.account_obj.cancelAskOffer(self.market_id, offer_id)

    def _cancel_bid(self):
        row = self.bid_offers_view.currentIndex().row()
        item = self.bids_model.item(row, 0)
        if item:
            offer_id = item.text()
            self.account_obj.cancelBidOffer(self.market_id, offer_id)

    def ask_amount_changed(self, base_amount):
        if not base_amount:
            self.ask_amount_label.clear()
            return
        price = self.ask_price_spin.value()
        if not price:
            self.ask_amount_label.clear()
            return
        self.change_ask_counter(base_amount, price)

    def ask_price_changed(self, price):
        if not price:
            self.ask_amount_label.clear()
            return
        base_amount = self.ask_amount_spin.value()
        if not base_amount:
            self.ask_amount_label.clear()
            return
        self.change_ask_counter(base_amount, price)

    def changeAccount(self, market_id):
        print "market changed for", market_id
        # maybe this slot should receive an account id
        if market_id != self.market_id:
            print "but it's not ours"
            return

        if not self.account_obj.hasAccount(str(market_id)):
            print "account_obj does not have valid accounts"
            return
        print "account_obj does have valid accounts"

        if hasattr(self, 'base_balance_proxy'):
            self.base_balance_proxy.balance_changed.disconnect(
                self.base_balance_label.change_value)
        if hasattr(self, 'counter_balance_proxy'):
            self.counter_balance_proxy.balance_changed.disconnect(
                self.counter_balance_label.change_value)

        b_ac_id, c_ac_id = self.account_obj.getAccountPair(self.market_id)

        self.base_balance_proxy = self.account_obj.getBalanceProxy(b_ac_id)
        self.base_balance_proxy.balance.connect(
            self.base_balance_label.setValue)
        self.base_balance_proxy.balance_changed.connect(
            self.base_balance_label.change_value)

        self.counter_balance_proxy = self.account_obj.getBalanceProxy(c_ac_id)
        self.counter_balance_proxy.balance.connect(
            self.counter_balance_label.setValue)
        self.counter_balance_proxy.balance_changed.connect(
            self.counter_balance_label.change_value)

        self.account_obj.refreshBalance(self.market_id)

    def change_ask_counter(self, base_amount, price):
        counter_amount = base_amount * price
        self.ask_amount_label.setValue(counter_amount)
        commission = self.account_obj.getCommission(counter_amount,
                                                self.market_id)
        if commission:
            self.ask_counter_estimate_label.setValue(counter_amount - commission)
            return
        self.ask_counter_estimate_label.clear()

    def change_bid_counter(self, base_amount, price):
        counter_amount = base_amount * price
        self.bid_amount_label.setValue(counter_amount)
        commission = self.account_obj.getCommission(counter_amount,
                                                self.market_id)
        if commission:
            self.bid_counter_estimate_label.setValue(counter_amount - commission)
        else:
            self.bid_counter_estimate_label.clear()

    def bid_amount_changed(self, base_amount):
        if not base_amount:
            self.bid_amount_label.clear()
            return
        price = self.bid_price_spin.value()
        if not price:
            self.bid_amount_label.clear()
            return
        self.change_bid_counter(base_amount, price)

    def bid_price_changed(self, price):
        if not price:
            self.bid_amount_label.clear()
            return
        base_amount = self.bid_amount_spin.value()
        if not base_amount:
            self.bid_amount_label.clear()
        else:
            self.change_bid_counter(base_amount, price)

    def refreshBalance(self):
        self.account_obj.refreshBalance(self.market_id)


class ScaleSelectDialog(QtGui.QDialog):

    def __init__(self, factor, precision, current_scale, parent=None):
        super(ScaleSelectDialog, self).__init__(parent)
        if factor > 1:
            AmountView = tulpenmanie.ui.widget.AssetDecimalAmountLabel
        else:
            AmountView = tulpenmanie.ui.widget.AssetIntAmountLabel

        self.power_spin = QtGui.QSpinBox()
        self.power_spin.setValue(current_scale / 10)
        self.power_spin.valueChanged[int].connect(self.changePower)

        self.scale_view = AmountView(factor, precision)

        self.scale_view.setReadOnly(True)

        button_box = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok |
                                            QtGui.QDialogButtonBox.Cancel)

        layout = QtGui.QFormLayout()
        layout.addRow(
            QtCore.QCoreApplication.translate('ScaleSelectDialog',
                                              "Scale base power:",
                                              "The market base (2, 10, 16) "
                                              "shall be risen to the the power "
                                              "of scale base power to derive "
                                              "the market scale."),
            self.power_spin)

        layout.addRow(
            QtCore.QCoreApplication.translate('ScaleSelectDialog',
                                              "Market scale:",
                                              "Market scale or granularity  "
                                              "is a multiplier that affects "
                                              "the size of orders, a scale of "
                                              "ten means all orders must be a "
                                              "multiple of ten."),
            self.scale_view)
        layout.addRow(button_box)
        self.setLayout(layout)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def changePower(self, power):
        value = pow(10, power)
        self.scale_view.setValue(value)

    def getScale(self):
        return self.scale_spin.value()
