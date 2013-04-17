# Dojima, a markets client.
# Copyright (C) 2012-2013  Emery Hemingway
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
from decimal import Decimal

from PyQt4 import QtCore, QtGui

import dojima.ui.chart
import dojima.ui.widget
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
        self.base_row, self.counter_row = dojima.model.commodities.local_model.getRows(self.base_id, self.counter_id)

        base_name = dojima.model.commodities.local_model.item(
            self.base_row, 0).text()
        counter_name = dojima.model.commodities.local_model.item(
            self.counter_row, 0).text()

        title = QtCore.QCoreApplication.translate(
            'ExchangeDockWidget', "{0} - {1} / {2}", "exchange name, base, counter"
            ).format(exchange_name, base_name, counter_name)

        super(ExchangeDockWidget, self).__init__(title, parent)

        self.remote_market = marketID

        self.exchange = exchangeProxy.getExchangeObject()
        self.enable_exchange_action = action

        # get our display parameters
        if self.exchange.valueType is int:
            self.base_factor, self.counter_factor = self.exchange.getFactors(self.remote_market)
            self.base_power, self.counter_power = self.exchange.getPowers(self.remote_market)
            self.scale = self.exchange.getScale(self.remote_market)

        self.base_precision = dojima.model.commodities.local_model.item(
            self.base_row, dojima.model.commodities.local_model.PRECISION).text()
        if not len(self.base_precision):
            self.base_precision = 0
        else:
            self.base_precision = int(self.base_precision)

        self.counter_precision = dojima.model.commodities.local_model.item(
            self.counter_row, dojima.model.commodities.local_model.PRECISION).text()
        if not len(self.counter_precision):
            self.counter_precision = 0
        else:
            self.counter_precision = int(self.counter_precision)

        side_layout = QtGui.QGridLayout()
        label_font = QtGui.QFont()
        label_font.setPointSize(7)

        row = 0
        for translation, stat in (
            (QtCore.QCoreApplication.translate('ExchangeDockWidget', "ask", "best ask price"), 'ask'),
            (QtCore.QCoreApplication.translate('ExchangeDockWidget', "last", "price of last trade"), 'last'),
            (QtCore.QCoreApplication.translate('ExchangeDockWidget', "bid", "best bid price"), 'bid')):

            label = QtGui.QLabel(translation)
            label.setAlignment(QtCore.Qt.AlignRight)
            label.setFont(label_font)
            
            if self.exchange.valueType is int:
                widget = dojima.ui.widget.LCDIntWidget(factor=self.counter_factor, power=self.counter_power)
            elif self.exchange.valueType is Decimal:
                widget = dojima.ui.widget.LCDDecimalWidget()
            else:
                raise NotImplementedError("{} is not a supported exchange.valueType".format(exchange.valueType))
                    
            setattr(self, '{}_widget'.format(stat), widget)
            side_layout.addWidget(label,  row, 0, 1, 2)
            row += 1
            side_layout.addWidget(widget, row, 0, 1, 2)
            side_layout.setRowStretch(row, 1)
            row += 1

        refresh_label = QtGui.QLabel(QtCore.QCoreApplication.translate('ExchangeDockWidget', "refresh rate:", 
                                                                        "ticker refresh rate"))
        refresh_label.setAlignment(QtCore.Qt.AlignRight)
        refresh_spin = QtGui.QSpinBox(maximum=3600, minimum=4,
            prefix=QtCore.QCoreApplication.translate('ExchangeDockWidget', "", "The prefix before the number in the "
                                                                                "refresh rate spin box"),
            suffix=QtCore.QCoreApplication.translate('ExchangeDockWidget', "s", "The suffix after the number in the "
                                                                                "refresh rate spin box") )
        refresh_spin.valueChanged[int].connect(self.exchange.setTickerRefreshRate)
        refresh_spin.setValue(self.exchange.getTickerRefreshRate())
        side_layout.addWidget(refresh_label, row, 0)
        side_layout.addWidget(refresh_spin,  row, 1)

        self.menu_bar = ExchangeDockWidgetMenuBar(self)
        if hasattr(self.exchange, 'getDepthProxy'):
            self.menu_bar.addDepthChartAction()
        if hasattr(self.exchange, 'getTradesProxy'):
            self.menu_bar.addTradesChartAction()

        # account UI
        account_layout = QtGui.QGridLayout()

        # get the prefixi and suffixi
        base_prefix = dojima.model.commodities.local_model.item(
            self.base_row, dojima.model.commodities.local_model.PREFIX).text()
        counter_prefix = dojima.model.commodities.local_model.item(
            self.counter_row, dojima.model.commodities.local_model.PREFIX).text()

        base_suffix = dojima.model.commodities.local_model.item(
            self.base_row, dojima.model.commodities.local_model.SUFFIX).text()
        counter_suffix = dojima.model.commodities.local_model.item(
            self.counter_row, dojima.model.commodities.local_model.SUFFIX).text()

        if self.exchange.valueType is int:
            self.base_balance_total_label    = dojima.ui.widget.AssetAmountIntView(factor=self.base_factor)
            self.counter_balance_total_label = dojima.ui.widget.AssetAmountIntView(factor=self.counter_factor)
            
            self.base_balance_liquid_label    = dojima.ui.widget.AssetAmountIntView(factor=self.base_factor)
            self.counter_balance_liquid_label = dojima.ui.widget.AssetAmountIntView(factor=self.counter_factor)

            self.amount_spin   = dojima.ui.widget.AssetIntSpinBox(factor=self.base_factor, power=self.base_power, 
                                                                  scale=self.scale)
            self.price_spin    = dojima.ui.widget.AssetIntSpinBox(factor=self.counter_factor, power=self.counter_power)
            self.estimate_view = dojima.ui.widget.AssetAmountIntView(factor=self.counter_factor)

            self.ask_price_delegate = dojima.ui.widget.OfferItemIntDelegate(prefix=counter_prefix, suffix=counter_suffix,
                                                                            factor=self.counter_factor)
            self.bid_price_delegate = dojima.ui.widget.OfferItemIntDelegate(prefix=counter_prefix, suffix=counter_suffix,
                                                                            factor=self.counter_factor)

            self.ask_outstanding_delegate = dojima.ui.widget.OfferItemIntDelegate(prefix=base_prefix, suffix=base_suffix,
                                                                                  factor=self.base_factor)
            self.bid_outstanding_delegate = dojima.ui.widget.OfferItemIntDelegate(prefix=base_prefix, suffix=base_suffix,
                                                                                  factor=self.base_factor)

        elif self.exchange.valueType is Decimal:
            self.base_balance_total_label    = dojima.ui.widget.AssetAmountDecimalView()
            self.counter_balance_total_label = dojima.ui.widget.AssetAmountDecimalView()

            self.base_balance_liquid_label    = dojima.ui.widget.AssetAmountDecimalView()
            self.counter_balance_liquid_label = dojima.ui.widget.AssetAmountDecimalView()

            self.amount_spin = dojima.ui.widget.AssetDecimalSpinBox()
            self.price_spin = dojima.ui.widget.AssetDecimalSpinBox()
            self.estimate_view = dojima.ui.widget.AssetAmountDecimalView()

            self.ask_price_delegate = dojima.ui.widget.OfferItemDecimalDelegate(prefix=counter_prefix, suffix=counter_suffix)
            self.bid_price_delegate = dojima.ui.widget.OfferItemDecimalDelegate(prefix=counter_prefix, suffix=counter_suffix)

            self.ask_outstanding_delegate = dojima.ui.widget.OfferItemDecimalDelegate(prefix=base_prefix, suffix=base_suffix)
            self.bid_outstanding_delegate = dojima.ui.widget.OfferItemDecimalDelegate(prefix=base_prefix, suffix=base_suffix)
            
        else:
            raise NotImplementedError("{} is not a supported exchange.valueType".format(exchange.valueType))

        tool_tip_total_text = QtCore.QCoreApplication.translate('ExchangeDockWidget', "Total balance.")
        tool_tip_liquid_text = QtCore.QCoreApplication.translate('ExchangeDockWidget', "Balance available for trade.")
        
        self.base_balance_total_label.setToolTip(tool_tip_total_text)
        self.counter_balance_total_label.setToolTip(tool_tip_total_text)
        self.base_balance_liquid_label.setToolTip(tool_tip_liquid_text)
        self.counter_balance_liquid_label.setToolTip(tool_tip_liquid_text)
        
        self.estimate_view.setDisabled(True)
                
        refresh_balance_action = QtGui.QAction(
            QtCore.QCoreApplication.translate('ExchangeDockWidget',
                                              "&refresh balance"),
            self, triggered=self.refreshBalance)

        balance_font = QtGui.QFont()
        balance_font.setPointSize(13)
        for label in (self.base_balance_total_label, self.counter_balance_total_label,
                      self.base_balance_liquid_label, self.counter_balance_liquid_label):
            label.setAlignment(QtCore.Qt.AlignHCenter)
            label.setFont(balance_font)
            label.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
            label.addAction(refresh_balance_action)

        if base_prefix:
            for widget in (self.base_balance_total_label, self.base_balance_liquid_label, self.amount_spin):
                widget.setPrefix(base_prefix)

        if base_suffix:
            for widget in (self.base_balance_total_label, self.base_balance_liquid_label, self.amount_spin):
                widget.setSuffix(base_suffix)

        if counter_prefix:
            for widget in (self.counter_balance_total_label,
                           self.counter_balance_liquid_label,
                           self.price_spin,
                           self.estimate_view):
                widget.setPrefix(counter_prefix)

        if counter_suffix:
            for widget in (self.counter_balance_total_label,
                           self.counter_balance_liquid_label,
                           self.price_spin,
                           self.estimate_view):
                widget.setSuffix(counter_suffix)

        offer_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate('ExchangeDockWidget', "offer",
                                              "as in place offer"))
        offer_button_menu = QtGui.QMenu()
        offer_ask_action = QtGui.QAction(
            QtCore.QCoreApplication.translate('ExchangeDockWidget', "Ask"),
            offer_button)
        offer_bid_action = QtGui.QAction(
            QtCore.QCoreApplication.translate('ExchangeDockWidget', "Bid"),
            offer_button)

        offer_button_menu.addAction(offer_ask_action)
        offer_button_menu.addAction(offer_bid_action)
        offer_button.setMenu(offer_button_menu)

        at_seperator = QtCore.QCoreApplication.translate('ExchangeDockWidget',
                                                         "@", "amount @ price")

        account_layout.addWidget(self.base_balance_total_label, 0,0)
        account_layout.addWidget(self.counter_balance_total_label, 0,1)
        account_layout.addWidget(self.base_balance_liquid_label, 1,0)
        account_layout.addWidget(self.counter_balance_liquid_label, 1,1)
        

        sublayout = QtGui.QFormLayout()

        sublayout.addRow(
            QtCore.QCoreApplication.translate('ExchangeDockWidget',
                                              "Amount:",
                                              "The offer amount label."),
            self.amount_spin)

        sublayout.addRow(
            QtCore.QCoreApplication.translate('ExchangeDockWidget',
                                              "Price:",
                                              "The offer price label."),
            self.price_spin)

        #TODO disable the offer menu actions when bid is higher than ask and so on
        # also disable the actions when either price or amount is 0

        account_layout.addLayout(sublayout, 2,0, 2,2)

        account_layout.addWidget(offer_button, 4,0)
        account_layout.addWidget(self.estimate_view, 4,1)

        for spin in (self.amount_spin, self.price_spin):
            spin.setMaximum(999999)

        self.ask_offers_view = dojima.ui.widget.OffersView()
        account_layout.addWidget(self.ask_offers_view, 5,0, 1,2)

        self.bid_offers_view = dojima.ui.widget.OffersView()
        account_layout.addWidget(self.bid_offers_view, 6,0, 1,2)


        self.ask_offers_view.setItemDelegateForColumn(dojima.data.offers.PRICE, self.ask_price_delegate)
        self.bid_offers_view.setItemDelegateForColumn(dojima.data.offers.PRICE, self.bid_price_delegate)
        self.ask_offers_view.setItemDelegateForColumn(dojima.data.offers.OUTSTANDING, self.ask_outstanding_delegate)
        self.bid_offers_view.setItemDelegateForColumn(dojima.data.offers.OUTSTANDING, self.bid_outstanding_delegate)

        for view in self.ask_offers_view, self.bid_offers_view:
            view.setSelectionMode(QtGui.QListView.SingleSelection)
            view.setSelectionBehavior(QtGui.QListView.SelectRows)
            view.setShowGrid(False)
            view.verticalHeader().hide()
            view.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)


            #base_offer_delegate = dojima.ui.widget.OfferItemDelegate(
            #    factor=self.base_factor,
            #    prefix=base_prefix, suffix=base_suffix)
            #view.setItemDelegateForColumn(dojima.data.offers.OUTSTANDING,
            #                              base_offer_delegate)

        #Refresh offers action
        refresh_offers_action = QtGui.QAction(QtCore.QCoreApplication.translate('ExchangeDockWidget', "&refresh offers")
                                              , self, triggered=self.refreshOffers)
        #Cancel offer action
        cancel_ask_action = QtGui.QAction(QtCore.QCoreApplication.translate('ExchangeDockWidget', "&cancel ask offer"),
                                          self, triggered=self.cancelAsk)

        self.ask_offers_view.addAction(cancel_ask_action)
        self.ask_offers_view.addAction(refresh_offers_action)
        cancel_bid_action = QtGui.QAction(QtCore.QCoreApplication.translate('ExchangeDockWidget', "&cancel bid offer"),
                                          self, triggered=self.cancelBid)

        self.bid_offers_view.addAction(cancel_bid_action)
        self.bid_offers_view.addAction(refresh_offers_action)

        # inter-widget connections
        self.amount_spin.editingFinished.connect(self.offerChanged)
        self.price_spin.editingFinished.connect(self.offerChanged)

        # Connect to account
        # these are remote ids, not local
        self.exchange.accountChanged.connect(self.setAccounts)

        self.exchange.exchange_error_signal.connect(
            self.exchange_error_handler)

        offer_ask_action.triggered.connect(self.placeAskLimit)
        offer_bid_action.triggered.connect(self.placeBidLimit)

        self.layout = QtGui.QHBoxLayout()
        self.layout.setMenuBar(self.menu_bar)
        self.layout.addLayout(side_layout)
        self.layout.addLayout(account_layout)
        self.layout.setStretchFactor(side_layout, 1)
        self.layout.setStretchFactor(account_layout, 4)
        widget = QtGui.QWidget(self)
        widget.setLayout(self.layout)
        self.setWidget(widget)

        # Exchanges may store a reference to this menu and update it
        self.exchange.populateMenuBar(self.menu_bar, self.remote_market)

        #proxy = self.exchange.getAccountValidityProxy(self.remote_market)
        #proxy.accountValidityChanged.connect(self.setEnabled)

        self.account_widgets = ( self.base_balance_total_label,     
                                 self.base_balance_liquid_label, 
                                 self.counter_balance_total_label, 
                                 self.counter_balance_liquid_label,
                                 self.amount_spin,
                                 self.price_spin,
                                 self.ask_offers_view,
                                 self.bid_offers_view )
        
        self.setAccounts(self.remote_market)               
        
    def cancelAsk(self):
        row = self.ask_offers_view.currentIndex().row()
        index = self.asks_model.index(row, dojima.data.offers.ID)
        offer_id = self.asks_model.data(index)
        if offer_id:
            self.exchange.cancelAskOffer(offer_id, self.remote_market)

    def cancelBid(self):
        row = self.bid_offers_view.currentIndex().row()
        index = self.bids_model.index(row, dojima.data.offers.ID)
        offer_id = self.bids_model.data(index)
        if offer_id:
            self.exchange.cancelBidOffer(offer_id, self.remote_market)

    def changeMarket(self, market_id):
        self.exchange.setTickerStreamState(self.remote_market, False)
        self.remote_market = marked_id
        self.exchange.setTickerStreamState(self.remote_market, True)
        self.exchange.echoTicker(self.remote_market)

    def closeEvent(self, event):
        self.enableExchange(False)

        self.enable_exchange_action.setChecked(False)
        event.accept()

    def enableExchange(self, enable):
        self.setEnabled(enable)
        self.setVisible(enable)
        self.set_signal_connection_state(enable)
        self.exchange.setTickerStreamState(enable, self.remote_market)

        if enable:
            self.exchange.echoTicker(self.remote_market)

    def placeAskLimit(self):
        amount = self.amount_spin.value()
        price = self.price_spin.value()

        dialog = AskOfferConfirmationDialog(self.amount_spin.text(),
                                            self.price_spin.text(),
                                            self)
        if dialog.exec_():
            self.exchange.placeAskLimitOffer(amount, price, self.remote_market)


    def placeBidLimit(self):
        amount = self.amount_spin.value()
        price = self.price_spin.value()

        dialog = BidOfferConfirmationDialog(self.amount_spin.text(),
                                            self.price_spin.text(),
                                            self)
        if dialog.exec_():
            self.exchange.placeBidLimitOffer(amount, price, self.remote_market)

    def refreshOffers(self):
        self.exchange.refreshOffers(self.remote_market)
                
    def setAccounts(self, market_id):
        has_account = self.exchange.hasAccount(market_id)

        for widget in self.account_widgets:
            widget.setEnabled(has_account)

        if has_account is False:
            return
        
        if hasattr(self, 'base_balance_proxy'):
            self.base_balance_proxy.balance_total_changed.disconnect(self.base_balance_total_label.changeValue)
            self.base_balance_proxy.balance_liquid_changed.disconnect(self.base_balance_liquid_label.changeValue)
            
        if hasattr(self, 'counter_balance_proxy'):
            self.counter_balance_proxy.balance_total_changed.disconnect(self.counter_balance_total_label.changeValue)
            self.counter_balance_proxy.balance_liquid_changed.disconnect(self.counter_balance_liquid_label.changeValue)

        self.base_balance_proxy = self.exchange.getBalanceBaseProxy(self.remote_market)
        self.base_balance_proxy.balance_total.connect(self.base_balance_total_label.setValue)
        self.base_balance_proxy.balance_liquid.connect(self.base_balance_liquid_label.setValue)
        self.base_balance_proxy.balance_total_changed.connect(self.base_balance_total_label.changeValue)
        self.base_balance_proxy.balance_liquid_changed.connect(self.base_balance_liquid_label.changeValue)

        self.counter_balance_proxy = self.exchange.getBalanceCounterProxy(self.remote_market)
        self.counter_balance_proxy.balance_total.connect(self.counter_balance_total_label.setValue)
        self.counter_balance_proxy.balance_liquid.connect(self.counter_balance_liquid_label.setValue)
        self.counter_balance_proxy.balance_total_changed.connect(self.counter_balance_total_label.changeValue)
        self.counter_balance_proxy.balance_liquid_changed.connect(self.counter_balance_liquid_label.changeValue)

        self.asks_model = self.exchange.getOffersModelAsks(self.remote_market)
        self.bids_model = self.exchange.getOffersModelBids(self.remote_market)

        self.ask_offers_view.setModel(self.asks_model)
        self.bid_offers_view.setModel(self.bids_model)
        self.ask_offers_view.hideColumns()
        self.bid_offers_view.hideColumns()

        self.asks_model.dataChanged.connect(self.ask_offers_view.hideColumns)
        self.bids_model.dataChanged.connect(self.bid_offers_view.hideColumns)
 
        self.exchange.refresh(self.remote_market)       

    def offerChanged(self):
        amount = self.amount_spin.value()
        if not amount: return
        price = self.price_spin.value()
        if not price: return

        estimate = amount * price
        if hasattr(self.exchange, 'getCommission'):
            estimate -= self.exchange.getCommission(estimate, self.remote_market)
        self.estimate_view.setValue(estimate)

    def refreshBalance(self):
        self.exchange.refreshBalance(self.remote_market)

    def setPrice(self, price):
        self.price_spin.setValue(price)

    def set_signal_connection_state(self, state):
        if not state: return

        self.exchange.exchange_error_signal.connect(
            self.exchange_error_handler)
        ticker_proxy = self.exchange.getTickerProxy(self.remote_market)
        ticker_proxy.ask_signal.connect(self.ask_widget.setValue)
        ticker_proxy.last_signal.connect(self.last_widget.setValue)
        ticker_proxy.bid_signal.connect(self.bid_widget.setValue)


class ExchangeDockWidgetMenuBar(QtGui.QMenuBar):

    def __init__(self, parent):
        super(ExchangeDockWidgetMenuBar, self).__init__(parent)
        self.dock = parent
        self.market_menu = self.addMenu(
            QtCore.QCoreApplication.translate('ExchangeDockWidgetMenuBar',
                                              "Market",
                                              "The title of a drop down menu "
                                              "to edit market settings."))

        """
        self.exchange_menu = self.addMenu(
            QtCore.QCoreApplication.translate('ExchangeDockWidget',
                                              "Exchange",
                                              "The title of a drop down menu "
                                              "to edit exchange settings."))
        """

        self.account_menu = self.addMenu(
            QtCore.QCoreApplication.translate('ExchangeDockWidget',
                                              "Account",
                                              "The title of a drop down menu "
                                              "to edit account settings."))

    def addDepthChartAction(self):
        action = self.market_menu.addAction(
            QtCore.QCoreApplication.translate('ExchangeDockWidget',
                                              "Depth Chart",
                                              "A menu action to show the current "
                                              "offers depth cart."))
        action.triggered.connect(self.showDepthChart)

    def addTradesChartAction(self):
        action = self.market_menu.addAction(
            QtCore.QCoreApplication.translate('ExchangeDockWidget',
                                              "Trades Chart",
                                              "A menu action to show the current "
                                              "the recent trades chart."))
        action.triggered.connect(self.showTradesChart)

    def getMarketMenu(self):
        return self.market_menu

    def getExchangeMenu(self):
        return self.exchange_menu

    def getAccountMenu(self):
        return self.account_menu

    def showDepthChart(self):
        proxy = self.dock.exchange.getDepthProxy(self.dock.remote_market)
        dialog = dojima.ui.chart.DepthDialog(proxy, self)
        dialog.show()

    def showTradesChart(self):
        proxy = self.dock.exchange.getTradesProxy(self.dock.remote_market)
        dialog = dojima.ui.chart.TradesDialog(proxy, self)
        dialog.show()


class _OfferConfirmationDialog(QtGui.QDialog):

    def __init__(self, amount, price, parent=None):
        super(_OfferConfirmationDialog, self).__init__(parent)

        dialog_text_label = QtGui.QLabel(self.dialog_text.format(amount, price))

        place_offer_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate('ExchangeDockWidget',
                                              "Place Offer",
                                              "The label on the button to "
                                              "confirm an offer"))

        button_box = QtGui.QDialogButtonBox()
        button_box.addButton(place_offer_button, button_box.AcceptRole)
        button_box.addButton(button_box.Abort)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(dialog_text_label)
        layout.addWidget(button_box)

        self.setLayout(layout)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)


class AskOfferConfirmationDialog(_OfferConfirmationDialog):

    dialog_text = QtCore.QCoreApplication.translate('ExchangeDockWidget',
                                                    "Sell {0} at {1}?",
                                                    "Text on the "
                                                    "AskConfirmationDialog. "
                                                    "{0} will be the amount, and "
                                                    "{1} will be the price.")


class BidOfferConfirmationDialog(_OfferConfirmationDialog):

    dialog_text = QtCore.QCoreApplication.translate('ExchangeDockWidget',
                                                    "Buy {0} at {1}?",
                                                    "Text on the "
                                                    "BidConfirmationDialog. "
                                                    "{0} will be the amount, and "
                                                    "{1} will be the price.")
