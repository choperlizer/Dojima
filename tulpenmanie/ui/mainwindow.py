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

import logging
from PyQt4 import QtCore, QtGui

import tulpenmanie.commodity
import tulpenmanie.market
import tulpenmanie.exchange
#This next import registers providers with the former module
from tulpenmanie.exchange_modules import *
import tulpenmanie.translate
import tulpenmanie.ui.exchange
import tulpenmanie.ui.edit
import tulpenmanie.ui.transfer.bitcoin

logger = logging.getLogger(__name__)

class MainWindow(QtGui.QMainWindow):

    def __init__(self, parent=None):
        super (MainWindow, self).__init__(parent)

        tulpenmanie.commodity.create_model(self)
        tulpenmanie.market.create_model(self)
        tulpenmanie.exchange.create_exchanges_model(self)

        edit_definitions_action = QtGui.QAction(
            QtCore.QCoreApplication.translate("main window options menu",
                                              "markets and exchanges"),
            self, triggered=self._edit_definitions)

        self.markets_menu = QtGui.QMenu(QtCore.QCoreApplication.translate(
                                        "MainWindow", "&market"), self)
        self.menuBar().addMenu(self.markets_menu)

        transfer_menu = QtGui.QMenu(QtCore.QCoreApplication.translate(
            "transfer menu title", "&transfer"), self)
        bitcoin_menu = QtGui.QMenu(tulpenmanie.translate.bitcoin, self)
        for Action in tulpenmanie.ui.transfer.bitcoin.actions:
            action = Action(self)
            bitcoin_menu.addAction(action)
        transfer_menu.addMenu(bitcoin_menu)
        self.menuBar().addMenu(transfer_menu)

        options_menu = QtGui.QMenu(QtCore.QCoreApplication.translate(
            "options menu title", "&options"), self)
        options_menu.addAction(edit_definitions_action)
        self.menuBar().addMenu(options_menu)

        self.setDockNestingEnabled(True)

        self.markets = dict()
        self.exchanges = dict()
        self.parse_models()

    def parse_models(self):
        self.parse_markets()
        self.parse_exchanges()

    def parse_markets(self):
        for uuid in self.markets.keys():
            if not tulpenmanie.market.model.findItems(
                    uuid, QtCore.Qt.MatchExactly, tulpenmanie.market.model.UUID):
                for value in self.markets[uuid].values():
                    value.deleteLater()
                self.markets.pop(uuid)

        for market_row in range(tulpenmanie.market.model.rowCount()):
            market_uuid = str(tulpenmanie.market.model.item(
                market_row, tulpenmanie.market.model.UUID).text())

            if market_uuid not in self.markets:
                market_dict = dict()
                market_name = tulpenmanie.market.model.item(
                    market_row, tulpenmanie.market.model.NAME).text()
                menu = QtGui.QMenu(market_name, self)
                self.markets_menu.addMenu(menu)

                market_dict['menu'] = menu
                market_dict['dock'] = dict()
                self.markets[market_uuid] = market_dict

    def parse_exchanges(self):
        for exchange_row in range(tulpenmanie.exchange.model.rowCount()):
            exchange_item = tulpenmanie.exchange.model.item(exchange_row)
            exchange_name = str(exchange_item.text())
            if exchange_name not in self.exchanges:
                self.exchanges[exchange_name] = dict()

            # parse accounts
            credentials = []
            account_valid = True
            for setting in exchange_item.required_account_settings:
                credential = exchange_item.child(0, setting).text()
                if credential:
                    credentials.append(credential)
                else:
                    account_valid = False
                    break

            if account_valid:
                if 'account' in self.exchanges[exchange_name]:
                    account_object = self.exchanges[exchange_name]['account']
                    if account_object:
                        account_object.set_credentials(credentials)
                else:
                    AccountClass = tulpenmanie.exchange.accounts[exchange_name]
                    account_object = AccountClass(credentials)
                    self.exchanges[exchange_name]['account'] = account_object
            else:
                account_object = None
                if 'account' in self.exchanges[exchange_name]:
                    self.exchanges[exchange_name].pop('account')

            ## parse remote markets
            markets_item = exchange_item.child(0, exchange_item.MARKETS)
            for market_row in range(markets_item.rowCount()):
                local_market = str(markets_item.child(
                    market_row, exchange_item.MARKET_LOCAL).text())

                if not local_market:
                    continue

                remote_pair = markets_item.child(
                    market_row, exchange_item.MARKET_REMOTE).text()

                if local_market not in self.markets:
                    logger.critical("%s has a remote market %s mapped to "
                                    "unknown local market %s",
                                    exchange_name, remote_pair, local_market)
                    continue

                exchange_docks_dict = self.markets[local_market]['dock']
                if exchange_name in exchange_docks_dict:
                    exchange_dock = exchange_docks_dict[exchange_name]
                else:
                    exchange_dock = tulpenmanie.ui.exchange.ExchangeDockWidget(
                        exchange_item, market_row, self)
                    self.addDockWidget(QtCore.Qt.LeftDockWidgetArea,
                                       exchange_dock)
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
                refresh_rate = exchange_item.child(
                    0, exchange_item.REFRESH_RATE).text()
                if refresh_rate and enable:
                    exchange_dock.set_refresh_rate(float(refresh_rate))

                account_widget = exchange_dock.account_widget
                if not account_widget and account_object:
                    account_widget = tulpenmanie.ui.exchange.AccountWidget(
                        account_object, remote_pair, exchange_dock)
                    account_widget.enable_account(enable)
                if account_widget and not account_object:
                    exchange_dock.account_widget = None
                    account_widget.deleteLater()

    def _edit_definitions(self):
        dialog = tulpenmanie.ui.edit.EditDefinitionsDialog(self)
        dialog.exec_()
        self.parse_models()

    def closeEvent(self, event):
        #TODO maybe a market model could store
        #commodities items in a second place
        tulpenmanie.commodity.model.save()
        tulpenmanie.market.model.save()
        tulpenmanie.exchange.model.save()

        event.accept()
