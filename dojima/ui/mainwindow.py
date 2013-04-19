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

#import otapi
from PyQt4 import QtCore, QtGui

import dojima.markets
#This next import registers the exchanges into dojima.markets
from dojima.exchange_modules import *
import dojima.ui.exchange
import dojima.ui.edit.commodities
import dojima.ui.wizard
#import dojima.ui.ot.action
import dojima.ui.transfer.bitcoin
#import dojima.ui.transfer.ot


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
            QtCore.QCoreApplication.translate("MainWindow", "&Transfer"), self)

        bitcoin_menu = QtGui.QMenu(
            QtCore.QCoreApplication.translate("MainWindow", "&Bitcoin"), self)
        for Action in dojima.ui.transfer.bitcoin.actions:
            action = Action(self)
            bitcoin_menu.addAction(action)
        transfer_menu.addMenu(bitcoin_menu)
        """
        ot_menu = QtGui.QMenu(
            QtCore.QCoreApplication.translate("MainWindow", "Open &Transactions"), self)
        for Action in dojima.ui.transfer.ot.actions:
            action = Action(self)
            ot_menu.addAction(action)
        transfer_menu.addMenu(ot_menu)
        """

        self.menuBar().addMenu(transfer_menu)

        """
        ot_menu = QtGui.QMenu(
            QtCore.QCoreApplication.translate('MainWindow', "OpenT&xs"), self)
        for Action in dojima.ui.ot.action.actions:
            action = Action(self)
            ot_menu.addAction(action)
        self.menuBar().addMenu(ot_menu)
        """

        options_menu = QtGui.QMenu(
            QtCore.QCoreApplication.translate('MainWindow', "&Options", "Title of the options menu in the main menu bar."),
            self)
        
        edit_commodities_action = QtGui.QAction(
            QtCore.QCoreApplication.translate("MainWindow", "&Commodities"),
            self, triggered=self.showEditCommoditiesDialog,
            menuRole=QtGui.QAction.PreferencesRole)
        
        options_menu.addAction(edit_commodities_action)
        self.menuBar().addMenu(options_menu)

        self.setDockNestingEnabled(True)

        self.refreshMarkets()

    def refreshMarkets(self, showNew=False):
        dojima.exchanges.refresh()
        for market_proxy in dojima.markets.container:
            if market_proxy.pair in self.markets_menu:
                market_menu = self.markets_menu.getMarketMenu(
                    market_proxy.pair)
            else:
                market_menu = self.markets_menu.addMarketMenu(
                    market_proxy.pair, market_proxy.getPrettyName())

            for exchange_proxy in market_proxy:
                # This exchange proxy has multiple markets, we only want
                # the ones that mapped to the local pair
                if exchange_proxy.id in market_menu:
                    exchange_menu = market_menu.getExchangeMenu(exchange_proxy.id)
                else:
                    exchange_menu = market_menu.addExchangeMenu(exchange_proxy.id, exchange_proxy.name)
                    for remote_market_id in exchange_proxy.getRemoteMarketIDs(market_proxy.pair):
                        if remote_market_id not in exchange_menu:
                            action = exchange_menu.addMarketAction(market_proxy, exchange_proxy, remote_market_id)
                            if showNew:
                                action.trigger()

    def showAddMarketsWizard(self):
        wizard = dojima.ui.wizard.AddMarketsWizard(self)
        wizard.exec_()
        self.refreshMarkets(True)

    def showEditCommoditiesDialog(self):
        dialog = dojima.ui.edit.commodities.EditDialog(self)
        dialog.exec_()


class ExchangeMarketsMenu(QtGui.QMenu):

    def __init__(self, exchange_id, exchange_name, parent=None):
        super(ExchangeMarketsMenu, self).__init__(exchange_name, parent)
        self.actions = dict()

    def __contains__(self, market_id):
        return (market_id in self.actions)

    def addMarketAction(self, marketProxy, exchangeProxy, marketID):
        action = ShowTradeDockAction(marketProxy, exchangeProxy, marketID, self)
        self.addAction(action)
        return action

    def getAction(self, remote_market_id):
        return self.actions[remote_market_id]

    def getMainWindow(self):
        return self.parent().getMainWindow()


class MarketsMenu(QtGui.QMenu):

    def __init__(self, parent):
        super(MarketsMenu, self).__init__(
            QtCore.QCoreApplication.translate("MainWindow", "&Market"),
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

    def __init__(self, marketProxy, exchangeProxy, remoteMarketID, parent):
        super(ShowTradeDockAction, self).__init__(parent)
        self.setCheckable(True)
        self.market_proxy = marketProxy
        self.exchange_proxy = exchangeProxy
        self.remote_market_id = remoteMarketID
        self.dock = None

        self.setText(self.exchange_proxy.getPrettyMarketName(remoteMarketID))

        self.triggered.connect(self.enableExchange)

    def enableExchange(self, state):
        if state is False and self.dock is None:
            return

        if self.dock is None:
            self.createDock()

        self.dock.enableExchange(state)

    def createDock(self):
        self.dock = dojima.ui.exchange.ExchangeDockWidget(self.market_proxy, self.exchange_proxy, self.remote_market_id, self)
        self.parent().getMainWindow().addDockWidget(QtCore.Qt.TopDockWidgetArea, self.dock)
