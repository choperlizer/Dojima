# Tulpenmanie, a commodities market client.
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

import tulpenmanie.commodity
import tulpenmanie.market
import tulpenmanie.providers
#This next import registers providers with the former module
from tulpenmanie.provider_modules import *
import tulpenmanie.ui.wizard
from tulpenmanie.ui.edit import EditMarketsDialog, EditProvidersDialog
from tulpenmanie.ui.market import MarketDockWidget
from tulpenmanie.ui.exchange import ExchangeWidget
from tulpenmanie.ui.account import ExchangeAccountWidget


class MainWindow(QtGui.QMainWindow):

    def __init__(self, parent=None):
        super (MainWindow, self).__init__(parent)

        edit_markets_action = QtGui.QAction("&markets", self,
                                            shortcut="Ctrl+E",
                                            triggered=self._edit_markets)

        edit_providers_action = QtGui.QAction("&providers", self,
                                              shortcut="Ctrl+P",
                                              triggered=self._edit_providers)

        self.markets_menu = QtGui.QMenu(tulpenmanie.translation.markets,
                                        self)
        self.menuBar().addMenu(self.markets_menu)
        self.exchanges_menu = QtGui.QMenu(tulpenmanie.translation.exchanges,
                                          self)
        self.menuBar().addMenu(self.exchanges_menu)
        options_menu = QtGui.QMenu(QtCore.QCoreApplication.translate(
            "options menu title", "options"), self)
        options_menu.addAction(edit_markets_action)
        options_menu.addAction(edit_providers_action)
        self.menuBar().addMenu(options_menu)

        # A place to put exchange accounts
        self.accounts = dict()

        tulpenmanie.commodity.create_model(self)
        tulpenmanie.market.create_model(self)
        tulpenmanie.providers.create_exchanges_model(self)

        self.parse_models()

    def parse_models(self):
        # parse markets
        markets_model = tulpenmanie.market.markets_model
        for market_row in range(markets_model.rowCount()):
            enable = markets_model.item(market_row, markets_model.ENABLE).text()
            if enable == "true":
                ## make dock
                dock = MarketDockWidget(market_row, self)
                dock.setAllowedAreas(QtCore.Qt.TopDockWidgetArea)
                self.addDockWidget(QtCore.Qt.TopDockWidgetArea, dock)
                enable_action = dock.enable_action
                self.markets_menu.addAction(enable_action)

                market_uuid = markets_model.item(market_row, markets_model.UUID).text()
                tulpenmanie.market.market_docks[market_uuid] = dock

        # parse exchanges
        exchanges_model = tulpenmanie.providers.exchanges_model
        for exchange_row in range(exchanges_model.rowCount()):
            exchange_item = exchanges_model.item(exchange_row)
            exchange_name = str(exchange_item.text())
            account_objects = dict()
            self.accounts[exchange_name] = account_objects

            ## parse exchange accounts
            accounts_item = exchange_item.child(0, exchange_item.ACCOUNTS)
            for account_row in range(accounts_item.rowCount()):
                enable = accounts_item.child(account_row,
                                             exchange_item.ACCOUNT_ENABLE).text()
                if enable == 'true':
                    ### make account object
                    account_identifier = accounts_item.child(
                        account_row, exchange_item.ACCOUNT_ID).text()
                    credentials = []
                    ### the first two columns are id and enable
                    for column in range(exchange_item.ACCOUNT_COLUMNS):
                        credentials.append(exchange_item.accounts_item.child(
                                           account_row, column).text())
                    AccountClass = tulpenmanie.providers.accounts[exchange_name]
                    account_object = AccountClass(credentials)
                    account_objects[account_identifier] = account_object

            ## parse remote markets
            markets_item = exchange_item.child(0, exchange_item.MARKETS)
            for market_row in range(markets_item.rowCount()):
                enable = markets_item.child(market_row,
                                            exchange_item.MARKET_ENABLE).text()
                local_market = markets_item.child(market_row,
                                                  exchange_item.MARKET_LOCAL).text()

                if (enable == "true") and (local_market in tulpenmanie.market.market_docks):
                    dock = tulpenmanie.market.market_docks[local_market]
                    remote_market = markets_item.child(
                        market_row, exchange_item.MARKET_REMOTE).text()
                    ### make exchange widget
                    exchange_widget = ExchangeWidget(exchange_item,
                                                     market_row,
                                                     remote_market,
                                                     dock)
                    self.exchanges_menu.addAction(exchange_widget.enable_action)

                    for account_id, account_object in account_objects.items():
                        ### make account widget
                        account_widget = ExchangeAccountWidget(account_object,
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
        tulpenmanie.commodity.commodities_model.save()
        tulpenmanie.market.markets_model.save()
        tulpenmanie.providers.exchanges_model.save()

        event.accept()
