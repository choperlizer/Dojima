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

import otapi
from PyQt4 import QtCore, QtGui

import tulpenmanie.markets
from tulpenmanie.model.commodities import commodities_model
#This next import registers the exchanges into tulpenmanie.markets
from tulpenmanie.exchange_modules import *
import tulpenmanie.ui.exchange
import tulpenmanie.ui.edit
import tulpenmanie.ui.ot
import tulpenmanie.ui.transfer.bitcoin

logger = logging.getLogger(__name__)

class MainWindow(QtGui.QMainWindow):

    def __init__(self, parent=None):
        super (MainWindow, self).__init__(parent)

        edit_definitions_action = QtGui.QAction(
            QtCore.QCoreApplication.translate("MainWindow",
                                              "&markets and exchanges"),
            self, triggered=self._edit_definitions)

        self.markets_menu = MarketsMenu(self)
        self.menuBar().addMenu(self.markets_menu)

        transfer_menu = QtGui.QMenu(
            QtCore.QCoreApplication.translate("MainWindow", "&transfer"), self)
        bitcoin_menu = QtGui.QMenu(
            QtCore.QCoreApplication.translate("MaineWindow", "&bitcoin"), self)
        for Action in tulpenmanie.ui.transfer.bitcoin.actions:
            action = Action(self)
            bitcoin_menu.addAction(action)
        transfer_menu.addMenu(bitcoin_menu)
        self.menuBar().addMenu(transfer_menu)

        ot_menu = QtGui.QMenu(
            QtCore.QCoreApplication.translate('MainWindow', "OpenT&xs"), self)
        for Action in tulpenmanie.ui.ot.actions:
            action = Action(self)
            ot_menu.addAction(action)
        self.menuBar().addMenu(ot_menu)

        options_menu = QtGui.QMenu(QtCore.QCoreApplication.translate(
            "MainWindow", "&options"), self)
        options_menu.addAction(edit_definitions_action)
        self.menuBar().addMenu(options_menu)

        self.setDockNestingEnabled(True)


        self.parse_markets()

        self.docks = set()


    def parse_markets(self):
        for market in tulpenmanie.markets.container:
            if market.pair in self.markets_menu:
                menu = self.markets_menu.getSubmenu(market.pair)
            else:
                menu = self.markets_menu.addSubmenu(market.pair,
                                                    market.prettyName())

            for exchange_proxy in market:
                action = ShowTradeDockAction(exchange_proxy, market.pair, self)
                menu.addAction(action)

    """
    def _parse_exchanges(self):

                    self.markets[local_market]['menu'].addAction(
                        exchange_dock.enable_exchange_action)

                    exchange_docks_dict[exchange_name] = exchange_dock

                enable = markets_item.child(
                    market_row, exchange_item.MARKET_ENABLE).text()
                if enable == "true":
                    enable = True
                else:
                    enable = False
                exchange_dock.enable_exchange(enable)
                exchange_dock.enable_exchange_action.setChecked(enable)

                account_widget = exchange_dock.account_widget
                if not account_widget and account_object:
                    account_widget = tulpenmanie.ui.exchange.AccountWidget(
                        account_object, remote_pair, exchange_dock)
                    account_widget.enable_account(enable)
                if account_widget and not account_object:
                    exchange_dock.account_widget = None
                    account_widget.deleteLater()
    """

    def _edit_definitions(self):
        dialog = tulpenmanie.ui.edit.EditDefinitionsDialog(self)
        dialog.exec_()
        #self.parse_models()

    # TODO make the edit dialog do this
    def closeEvent(self, event):
        tulpenmanie.model.commodities.commodities_model.submit()
        #tulpenmanie.model.markets.markets_model.submit()
        #tulpenmanie.model.exchanges.exchanges_model.submit()

        otapi.OT_API_Cleanup()

        event.accept()


class MarketsMenu(QtGui.QMenu):

    def __init__(self, parent=None):
        super(MarketsMenu, self).__init__(
            QtCore.QCoreApplication.translate("MainWindow", "&market"),
            parent)
        self.submenus = dict()

    def __contains__(self, marketId):
        return (marketId in self.submenus)

    def getSubmenu(self, marketId):
        return self.submenus[marketId]

    def addSubmenu(self, marketId, marketName):
        submenu = MarketSubMenu(marketName, self)
        self.addMenu(submenu)
        self.submenus[marketId] = submenu
        return submenu

        
class MarketSubMenu(QtGui.QMenu):

    def __init__(self, marketName, parent=None):
        super(MarketSubMenu, self).__init__(marketName, parent)
        # now I have to deal with exchanges with multiple markets for a pair


class ShowTradeDockAction(QtGui.QAction):

    def __init__(self, exchangeProxy, marketPair, parent):
        super(ShowTradeDockAction, self).__init__(exchangeProxy.name,
                                                    parent)
        self.setCheckable(True)
        self.exchange_proxy = exchangeProxy
        self.market_pair = marketPair
        self.dock = None

        # now I need to overwrite the activate method to show the dialog
        # if I want the market pair I can get that from the parent() menu

        # this action will also have to display something to differentiate
        # markets with different minimum orders

        self.triggered.connect(self.enableExchange)

    def enableExchange(self, state):
        if state is False and self.dock is None:
            return

        if self.dock is None:
            self.createDock()

        self.dock.enableExchange(state)

    def createDock(self):
        # these nested docks may not be needed, but rather a set
        main_window = self.parent()

        self.dock = tulpenmanie.ui.exchange.ExchangeDockWidget(
                self.exchange_proxy, self.market_pair, self)
        main_window.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.dock)
        # may not need this to keep the dock instance alive
        #main_window.docks.add(dock)

    # Make this the enable_exchange_action
