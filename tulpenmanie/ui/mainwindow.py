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
import tulpenmanie.ui.market
import tulpenmanie.ui.ot.action
import tulpenmanie.ui.transfer.bitcoin

import pdb

logger = logging.getLogger(__name__)

class MainWindow(QtGui.QMainWindow):

    def __init__(self, parent=None):
        super (MainWindow, self).__init__(parent)

        self.markets_menu = MarketsMenu(self)
        action = self.markets_menu.addAction(
            QtCore.QCoreApplication.translate('MainWindow', "Add new markets",
                                              "The title of a menu action to "
                                              "show a wizard to make more "
                                              "markets available."))
        action.triggered.connect(self.showAddMarketsWizard)

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
        for Action in tulpenmanie.ui.ot.action.actions:
            action = Action(self)
            ot_menu.addAction(action)
        self.menuBar().addMenu(ot_menu)

        options_menu = QtGui.QMenu(
            QtCore.QCoreApplication.translate('MainWindow', "&options",
                                              "Title of the options menu in "
                                              "the main menu bar."),
            self)
        edit_definitions_action = QtGui.QAction(
            QtCore.QCoreApplication.translate("MainWindow",
                                              "&markets and exchanges"),
            self, triggered=self.showEditDefinitionsDialog)
        options_menu.addAction(edit_definitions_action)
        self.menuBar().addMenu(options_menu)

        self.setDockNestingEnabled(True)

        self.refreshMarkets()

    def refreshMarkets(self):
        for market_container in tulpenmanie.markets.container:
            if market_container.pair in self.markets_menu:
                market_menu = self.markets_menu.getMarketMenu(
                    market_container.pair)
            else:
                market_menu = self.markets_menu.addMarketMenu(
                    market_container.pair, market_container.prettyName())

            for exchange_proxy in market_container:
                # This exchange proxy has multiple markets, we only want
                # the ones that mapped to the local pair
                if exchange_proxy.id in market_menu:
                    exchange_menu = market_menu.getExchangeMenu(
                        exchange_proxy.id)
                else:
                    exchange_menu = market_menu.addExchangeMenu(
                        exchange_proxy.id, exchange_proxy.name)
                    for market_id in exchange_proxy.getRemoteMarketIDs(
                            str(market_container.pair)):
                        if market_id not in exchange_menu:
                            action = exchange_menu.addMarketAction(
                                exchange_proxy, market_id)

    def showAddMarketsWizard(self):
        wizard = tulpenmanie.ui.market.AddMarketsWizard(self)
        wizard.show()

    def showEditDefinitionsDialog(self):
        dialog = tulpenmanie.ui.edit.EditDefinitionsDialog(self)
        dialog.exec_()

    def parse_markets(self):
        for market in tulpenmanie.markets.container:
            if market.pair in self.markets_menu:
                menu = self.markets_menu.getSubMenu(market.pair)
            else:
                menu = self.markets_menu.addSubMenu(market.pair,
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

        #self.parse_models()

    # TODO make the edit dialog do this
    def closeEvent(self, event):
        tulpenmanie.model.commodities.commodities_model.submit()
        #tulpenmanie.model.markets.markets_model.submit()
        #tulpenmanie.model.exchanges.exchanges_model.submit()

        otapi.OT_API_Cleanup()

        event.accept()


# Don't nest the menu building, this way the exchange proxy is always available

class ExchangeMarketsMenu(QtGui.QMenu):

    def __init__(self, exchange_id, exchange_name, parent=None):
        super(ExchangeMarketsMenu, self).__init__(exchange_name, parent)
        self.actions = dict()

    def __contains__(self, market_id):
        return (market_id in self.actions)

    def addMarketAction(self, exchangeProxy, marketID):
        action = ShowTradeDockAction(exchangeProxy, marketID, self)
        self.addAction(action)
        return action

    def getAction(self, remote_market_id):
        return self.actions[remote_market_id]

    def getMainWindow(self):
        return self.parent().getMainWindow()


class MarketsMenu(QtGui.QMenu):

    def __init__(self, parent):
        super(MarketsMenu, self).__init__(
            QtCore.QCoreApplication.translate("MainWindow", "&market"),
            parent)
        self.submenus = dict()

    def __contains__(self, marketId):
        return (marketId in self.submenus)

    def addMarketMenu(self, marketId, marketName):
        submenu = MarketMenu(marketId, marketName, self)
        self.addMenu(submenu)
        self.submenus[marketId] = submenu
        return submenu

    def getMarketMenu(self, marketId):
        return self.submenus[marketId]

    def getMainWindow(self):
        return self.parent()


class MarketMenu(QtGui.QMenu):

    def __init__(self, marketID, marketName, parent=None):
        super(MarketMenu, self).__init__(marketName, parent)
        self.exchanges = dict()

    def __contains__(self, exchange_id):
        return (exchange_id in self.exchanges)

    def getExchangeMenu(self, exchangeID):
        return self.exchanges[exchangeID]

    def addExchangeMenu(self, exchangeID, exchangeName):
        menu = ExchangeMarketsMenu(exchangeID, exchangeName, self)
        self.addMenu(menu)
        self.exchanges[exchangeID] = menu
        return menu

    def getMainWindow(self):
        return self.parent().getMainWindow()


class ShowTradeDockAction(QtGui.QAction):

    def __init__(self, exchangeProxy, marketID, parent):
        super(ShowTradeDockAction, self).__init__(parent)
        self.setCheckable(True)
        self.exchange_proxy = exchangeProxy
        self.marketID = marketID
        self.dock = None

        self.setText(self.exchange_proxy.getPrettyMarketName(marketID))

        self.triggered.connect(self.enableExchange)

    def enableExchange(self, state):
        if state is False and self.dock is None:
            return

        if self.dock is None:
            self.createDock()

        self.dock.enableExchange(state)

    def createDock(self):
        marketPair = self.exchange_proxy.remoteToLocal(self.marketID)
        self.dock = tulpenmanie.ui.exchange.ExchangeDockWidget(
                self.exchange_proxy, marketPair, self.marketID, self)
        self.parent().getMainWindow().addDockWidget(
            QtCore.Qt.LeftDockWidgetArea, self.dock)
        # may not need this to keep the dock instance alive
        #main_window.docks.add(dock)

    # Make this the enable_exchange_action
