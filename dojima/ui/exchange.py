# Dojima, a markets client.
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

import dojima.ui.widget
#import dojima.model.orders
import dojima.model.commodities

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
        search = dojima.model.commodities.local_model.findItems(self.base_id)
        self.base_row = search[0].row()
        base_name = dojima.model.commodities.local_model.item(self.base_row,
                                           dojima.model.commodities.local_model.NAME).text()

        search = dojima.model.commodities.local_model.findItems(self.counter_id)
        self.counter_row = search[0].row()
        counter_name = dojima.model.commodities.local_model.item(self.counter_row,
                                              dojima.model.commodities.local_model.NAME).text()
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
        self.scale = self.exchange_obj.getScale(self.remote_market)

        self.base_precision, ok = dojima.model.commodities.local_model.item(
            self.base_row, dojima.model.commodities.local_model.PRECISION).text().toInt()
        if not ok: self.base_precision = 0

        self.counter_precision, ok = dojima.model.commodities.local_model.item(
            self.counter_row, dojima.model.commodities.local_model.PRECISION).text().toInt()
        if not ok: self.counter_precision = 0

        #Widgets
        self.widget = QtGui.QWidget(self)
        side_layout = QtGui.QVBoxLayout()
        label_font = QtGui.QFont()
        label_font.setPointSize(7)

        if self.counter_factor > 1:
            AssetLCDWidget = dojima.ui.widget.AssetDecimalLCDWidget
        else:
            AssetLCDWidget = dojima.ui.widget.AssetIntLCDWidget

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

        proxy = self.exchange_obj.getAccountValidityProxy(self.remote_market)
        proxy.accountValidityChanged.connect(self.enableAccount)

    def changeMarket(self, market_id):
        print "market change requested, market id:", market_id
        self.exchange_obj.setTickerStreamState(self.remote_market, False)
        self.remote_market = marked_id
        self.exchange_obj.setTickerStreamState(self.remote_market, True)
        self.exchange_obj.echoTicker(self.remote_market)

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
        self.dock.remote_market = parent.remote_market

        # Create UI
        layout = QtGui.QGridLayout()

        self.base_balance_label = dojima.ui.widget.AssetAmountView(
            factor=parent.base_factor)
        self.counter_balance_label = dojima.ui.widget.AssetAmountView(
            factor=parent.counter_factor)

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

        self.ask_amount_spin = dojima.ui.widget.AssetSpinBox(
            factor=parent.base_factor, scale=parent.scale)
        self.bid_amount_spin = dojima.ui.widget.AssetSpinBox(
            factor=parent.base_factor, scale=parent.scale)

        self.ask_price_spin = dojima.ui.widget.AssetSpinBox(
            factor=parent.counter_factor, scale=parent.scale)

        self.bid_price_spin = dojima.ui.widget.AssetSpinBox(
            factor=parent.counter_factor, scale=parent.scale)

        self.ask_estimate_view = dojima.ui.widget.AssetAmountView(
            factor=parent.counter_factor)
        self.ask_estimate_view.setDisabled(True)

        self.bid_estimate_view = dojima.ui.widget.AssetAmountView(
            factor=parent.counter_factor)
        self.bid_estimate_view.setDisabled(True)

        # Set the prefixi and suffixi
        base_prefix = dojima.model.commodities.local_model.item(
            parent.base_row, dojima.model.commodities.local_model.PREFIX).text()
        counter_prefix = dojima.model.commodities.local_model.item(
            parent.counter_row, dojima.model.commodities.local_model.PREFIX).text()

        base_suffix = dojima.model.commodities.local_model.item(
            parent.base_row, dojima.model.commodities.local_model.SUFFIX).text()
        counter_suffix = dojima.model.commodities.local_model.item(
            parent.counter_row, dojima.model.commodities.local_model.SUFFIX).text()

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
                           self.ask_estimate_view,
                           self.bid_estimate_view):
                widget.setPrefix(counter_prefix)

        if counter_suffix:
            for widget in (self.counter_balance_label,
                           self.ask_price_spin, self.bid_price_spin,
                           self.ask_estimate_view,
                           self.bid_estimate_view):
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

        layout.addWidget(self.base_balance_label, 0,0, 1,3)
        layout.addWidget(self.counter_balance_label, 0,3, 1,3)

        layout.addWidget(self.ask_amount_spin, 1,0)
        layout.addWidget(QtGui.QLabel(at_seperator), 1,1)
        layout.addWidget(self.ask_price_spin, 1,2)

        layout.addWidget(ask_button, 2,0, 1,2)
        layout.addWidget(self.ask_estimate_view, 2,2)

        layout.addWidget(self.bid_amount_spin, 1,3)
        layout.addWidget(QtGui.QLabel(at_seperator), 1,4)
        layout.addWidget(self.bid_price_spin, 1,5)

        layout.addWidget(bid_button, 2,3, 1,2)
        layout.addWidget(self.bid_estimate_view, 2,5)

        for spin in (self.ask_amount_spin, self.bid_amount_spin,
                     self.ask_price_spin,self.bid_price_spin):
            spin.setMaximum(999999)

        self.ask_offers_view = dojima.ui.widget.OffersView()
        layout.addWidget(self.ask_offers_view, 5,0, 1,3)

        self.bid_offers_view = dojima.ui.widget.OffersView()
        layout.addWidget(self.bid_offers_view, 5,3, 1,3)

        for view in self.ask_offers_view, self.bid_offers_view:
            view.setSelectionMode(QtGui.QListView.SingleSelection)
            view.setSelectionBehavior(QtGui.QListView.SelectRows)
            view.setShowGrid(False)
            view.verticalHeader().hide()
            view.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

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
        self.ask_amount_spin.editingFinished.connect(self.ask_offer_changed)
        self.bid_amount_spin.editingFinished.connect(self.bid_offer_changed)

        self.ask_price_spin.editingFinished.connect(self.ask_offer_changed)
        self.bid_price_spin.editingFinished.connect(self.bid_offer_changed)

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

        if not self.account_obj.hasAccount(self.dock.remote_market):
            self.setDisabled(True)
            return

        self.setEnabled(True)

        b_ac_id, c_ac_id = self.account_obj.getAccountPair(self.dock.remote_market)

        self.base_balance_proxy = self.account_obj.getBalanceProxy(
            b_ac_id)
        self.base_balance_proxy.balance.connect(
            self.base_balance_label.setValue)
        #self.base_balance_proxy.balance_changed.connect(
        #    self.base_balance_label.change_value)

        self.counter_balance_proxy = self.account_obj.getBalanceProxy(
            c_ac_id)
        self.counter_balance_proxy.balance.connect(
            self.counter_balance_label.setValue)
        #self.counter_balance_proxy.balance_changed.connect(
        #    self.counter_balance_label.change_value)

        offers_model = self.account_obj.getOffersModel(self.dock.remote_market)
        self.asks_model = dojima.data.offers.AsksFilterModel(offers_model)
        self.bids_model = dojima.data.offers.BidsFilterModel(offers_model)

        self.ask_offers_view.setModel(self.asks_model)
        self.bid_offers_view.setModel(self.bids_model)
        self.ask_offers_view.hideColumns()
        self.bid_offers_view.hideColumns()

        offers_model.dataChanged.connect(self.ask_offers_view.hideColumns)
        offers_model.dataChanged.connect(self.bid_offers_view.hideColumns)

        self.account_obj.refresh(self.dock.remote_market)

    def _ask_limit(self):
        amount = self.ask_amount_spin.value()
        price = self.ask_price_spin.value()
        self.account_obj.placeAskLimitOffer(self.dock.remote_market, amount, price)

    def _bid_limit(self):
        amount = self.bid_amount_spin.value()
        price = self.bid_price_spin.value()
        self.account_obj.placeBidLimitOffer(self.dock.remote_market, amount, price)

    def _ask_market(self):
        amount = self.ask_amount_spin.value()
        self.account_obj.placeAskMarketOffer(self.dock.remote_market, amount)

    def _bid_market(self):
        amount = self.bid_amount_spin.value()
        self.account_obj.placeBidMarketOffer(self.dock.remote_market, amount)

    def _cancel_ask(self):
        row = self.ask_offers_view.currentIndex().row()
        index = self.asks_model.index(row, dojima.data.offers.ID)
        offer_id = self.asks_model.data(index)
        if offer_id:
            self.account_obj.cancelAskOffer(offer_id, self.dock.remote_market)

    def _cancel_bid(self):
        row = self.bid_offers_view.currentIndex().row()
        index = self.bids_model.index(row, dojima.data.offers.ID)
        offer_id = self.bids_model.data(index)
        if offer_id:
            self.account_obj.cancelBidOffer(offer_id, self.dock.remote_market)

    def ask_offer_changed(self):
        amount = self.ask_amount_spin.value()
        if not amount: return
        price = self.ask_price_spin.value()
        if not price: return

        estimate = amount * price
        commission = self.account_obj.getCommission(estimate, self.dock.remote_market)
        if commission: estimate -= commission

        self.ask_estimate_view.setValue(estimate)

    def bid_offer_changed(self):
        amount = self.bid_amount_spin.value()
        if not amount: return
        price = self.bid_price_spin.value()
        if not price: return

        estimate = amount * price
        commission = self.account_obj.getCommission(estimate, self.dock.remote_market)
        if commission: estimate -= commission

        self.bid_estimate_view.setValue(estimate)

    def changeAccount(self, market_id):
        print "market changed for", market_id
        # maybe this slot should receive an account id
        if market_id != self.dock.remote_market:
            print "but it's not ours"
            return

        if not self.account_obj.hasAccount(str(market_id)):
            print "account_obj does not have valid accounts"
            return
        print "account_obj does have valid accounts"

        """
        if hasattr(self, 'base_balance_proxy'):
            self.base_balance_proxy.balance_changed.disconnect(
                self.base_balance_label.change_value)
        if hasattr(self, 'counter_balance_proxy'):
            self.counter_balance_proxy.balance_changed.disconnect(
                self.counter_balance_label.change_value)
        """

        b_ac_id, c_ac_id = self.account_obj.getAccountPair(self.dock.remote_market)

        self.base_balance_proxy = self.account_obj.getBalanceProxy(b_ac_id)
        self.base_balance_proxy.balance.connect(
            self.base_balance_label.setValue)
        #self.base_balance_proxy.balance_changed.connect(
        #    self.base_balance_label.change_value)

        self.counter_balance_proxy = self.account_obj.getBalanceProxy(c_ac_id)
        self.counter_balance_proxy.balance.connect(
            self.counter_balance_label.setValue)
        #self.counter_balance_proxy.balance_changed.connect(
        #    self.counter_balance_label.change_value)

        self.account_obj.refreshBalance(self.dock.remote_market)

    def change_ask_counter(self, base_amount, price):
        counter_amount = base_amount * price
        #self.ask_amount_label.setValue(counter_amount)

        if commission:
            counter_amount -= commission

        self.ask_estimate_view.setValue(counter_amount)

    def change_bid_counter(self, base_amount, price):
        counter_amount = base_amount * price
        commission = self.account_obj.getCommission(counter_amount,
                                                self.dock.remote_market)
        if commission:
            counter_amount -= commission

    def refreshBalance(self):
        self.account_obj.refreshBalance(self.dock.remote_market)
