# Tuplenmanie, a commodities market client.
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

from PyQt4 import QtCore, QtGui

import tulpenmanie.ui.wizard
from tulpenmanie.ui.edit import EditMarketsDialog, EditProvidersDialog
from tulpenmanie.ui.market import MarketDockWidget
from tulpenmanie.ui.exchange import ExchangeWidget
from tulpenmanie.ui.account import ExchangeAccountWidget


class MainWindow(QtGui.QMainWindow):

    def __init__(self, parent=None):
        super (MainWindow, self).__init__(parent)
        self.market_docks = dict()

        edit_markets_action = QtGui.QAction(
            "&markets", self, shortcut="Ctrl+E",
            triggered=self._edit_markets)

        edit_providers_action = QtGui.QAction(
            "&providers", self, shortcut="Ctrl+P",
            triggered=self._edit_providers)

        self.markets_menu = QtGui.QMenu("markets", self)
        self.menuBar().addMenu(self.markets_menu)
        options_menu = QtGui.QMenu("options", self)
        options_menu.addAction(edit_markets_action)
        options_menu.addAction(edit_providers_action)
        self.menuBar().addMenu(options_menu)

        self.parse_models()

    def parse_models(self):
        # parse markets
        markets_model = self.manager.markets_model
        self.market_docks = dict()
        for market_row in range(markets_model.rowCount()):
            enable = markets_model.item(market_row, markets_model.ENABLE).text()
            if enable == "true":
                ## make dock
                dock = MarketDockWidget(market_row, self)
                dock.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea)
                self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock)
                toggle_action = dock.toggleViewAction()
                self.markets_menu.addAction(toggle_action)

                market_uuid = markets_model.item(market_row, markets_model.UUID).text()
                self.market_docks[market_uuid] = dock

        # parse exchanges
        for exchange_row in range(self.manager.exchanges_model.rowCount()):
            exchange_item = self.manager.exchanges_model.item(exchange_row)
            markets_item = exchange_item.child(0, exchange_item.MARKETS)
            accounts_item = exchange_item.child(0, exchange_item.ACCOUNTS)

            for market_row in range(markets_item.rowCount()):
                enable = markets_item.child(market_row,
                                            exchange_item.MARKET_ENABLE).text()
                local_market = markets_item.child(market_row,
                                                  exchange_item.MARKET_LOCAL).text()

                if (enable == "true") and (local_market in self.market_docks):
                    dock = self.market_docks[local_market]
                    remote_market = markets_item.child(market_row,
                                                       exchange_item.MARKET_REMOTE).text()
                    ## make exchange widget
                    exchange_widget = ExchangeWidget(exchange_item,
                                                     market_row,
                                                     remote_market,
                                                     dock)
                    # parse exchange accounts
                    for account_row in range(accounts_item.rowCount()):
                        enable = accounts_item.child(account_row,
                                                     exchange_item.ACCOUNT_ENABLE).text()
                        if enable == 'true':
                            ## make account widget
                            account_widget = ExchangeAccountWidget(exchange_item,
                                                                   account_row,
                                                                   remote_market,
                                                                   exchange_widget)


    def _edit_markets(self):
        dialog = EditMarketsDialog(self)
        dialog.exec_()

    def _edit_providers(self):
        dialog = EditProvidersDialog(self)
        dialog.exec_()

    def closeEvent(self, event):
        #TODO maybe a market model could store
        #commodities items in a second place
        self.manager.commodities_model.save()
        self.manager.markets_model.save()
        self.manager.exchanges_model.save()

        event.accept()
