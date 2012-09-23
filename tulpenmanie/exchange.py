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

import tulpenmanie.market
import tulpenmanie.model.order


logger = logging.getLogger(__name__)

model = None

exchange_model_items = list()
def register_exchange_model_item(item_class):
    exchange_model_items.append(item_class)

def create_exchanges_model(parent):
    global model
    model = _ExchangesModel(parent)
    for Item in exchange_model_items:
        item = Item()
        model.appendRow(item)

_exchange_classes = dict()
def register_exchange(exchange_class):
	_exchange_classes[exchange_class.exchange_name] = exchange_class

accounts = dict()
def register_account(account_class):
    accounts[account_class.exchange_name] = account_class


_exchange_objects = dict()
def get_exchange_object(exchange_name, market_uuid):
    if exchange_name in _exchange_objects:
        dict_ = _exchange_objects[exchange_name]
    else:
        dict_ = dict()
        _exchange_objects[exchange_name] = dict_

    if market_uuid in dict_:
        exchange_object = dict_[market_uuid]
    else:
        remote_pair = None
        search = tulpenmanie.exchange.model.findItems(exchange_name)
        exchange_item = search[0]
        markets_item = exchange_item.markets_item
        for market_row in range(markets_item.rowCount()):
            local_market_item = markets_item.child(
                market_row, exchange_item.MARKET_LOCAL)
            if str(local_market_item.text()) == market_uuid:
                remote_pair_item = markets_item.child(
                    market_row, exchange_item.MARKET_REMOTE)
                remote_pair = remote_pair_item.text()
        if remote_pair:
            ExchangeClass = _exchange_classes[str(exchange_name)]
            exchange_object = ExchangeClass(remote_pair)
        else:
            exchange_object = None
    return exchange_object


def parse_model():
    for exchange_row in range(model.rowCount()):
        exchange_item = model.item(exchange_row)
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



class _ExchangesModel(QtGui.QStandardItemModel):

    def save(self):
        for row in range(self.rowCount()):
            item = self.item(row)
            item.save()


class ExchangeItem(QtGui.QStandardItem):

    MARKET_COLUMNS = 3
    MARKET_REMOTE, MARKET_ENABLE, MARKET_LOCAL = range(MARKET_COLUMNS)
    market_mappings = (('enable', MARKET_ENABLE),
                       ('local_market', MARKET_LOCAL))

    def __init__(self):
        super(ExchangeItem, self).__init__(self.exchange_name)
        self.settings = QtCore.QSettings()
        self.settings.beginGroup(self.exchange_name)
        self.setColumnCount(self.COLUMNS)

        logger.debug("loading %s settings", self.exchange_name)
        if self.mappings:
            for setting, column in self.mappings:
                value = self.settings.value(setting)
                if value:
                    item = QtGui.QStandardItem(value)
                else:
                    item = QtGui.QStandardItem()
                self.setChild(0, column, item)

        if self.markets:
            logger.debug("loading %s markets", self.exchange_name)
            self.markets_item = QtGui.QStandardItem()
            self.setChild(0, self.MARKETS, self.markets_item)
            self.settings.beginGroup('markets')
            for remote_pair in self.markets:
                items = [ QtGui.QStandardItem(remote_pair) ]
                self.settings.beginGroup(remote_pair)
                for setting, column in self.market_mappings:
                    value = self.settings.value(setting)
                    if value:
                        items.append(QtGui.QStandardItem(value))
                    else:
                        items.append(QtGui.QStandardItem())
                self.markets_item.appendRow(items)
                self.settings.endGroup()
            self.settings.endGroup()

    def save(self):
        logger.debug("saving %s settings", self.exchange_name)
        if self.mappings:
            #!!!TODO wont save refresh rate
            for setting, column in self.mappings:
                value = self.child(0, column).text()
                self.settings.setValue(setting, value)

        logger.debug("saving %s markets", self.exchange_name)
        # wipe out account information format from previous version
        self.settings.remove("accounts")
        self.settings.beginGroup('markets')
        for row in range(self.markets_item.rowCount()):
            remote_pair = self.markets_item.child(row, 0).text()
            self.settings.beginGroup(remote_pair)
            for setting, column in self.market_mappings:
                value = self.markets_item.child(row, column).text()
                self.settings.setValue(setting, value)
            self.settings.endGroup()
        self.settings.endGroup()

    def new_account(self):
        columns = self.ACCOUNT_COLUMNS
        items = []
        while columns:
            items.append(QtGui.QStandardItem())
            columns -= 1
        self.accounts_item.appendRow(items)
        return items[0].index()

#TODO decorate the functions below with @required_function

class Exchange:

    def pop_request(self):
        request = heapq.heappop(self._requests)
        request.send()
        self._replies.add(request)

class ExchangeAccount:

    def pop_request(self):
        request = heapq.heappop(self._requests)
        request.send()
        self._replies.add(request)

    def get_ask_orders_model(self, remote_pair):
        if remote_pair in self.ask_orders.keys():
            return self.ask_orders[remote_pair]
        else:
            model = tulpenmanie.model.order.OrdersModel()
            self.ask_orders[remote_pair] = model
            return model

    def get_bid_orders_model(self, remote_pair):
        if remote_pair in self.bid_orders.keys():
            return self.bid_orders[remote_pair]
        else:
            model = tulpenmanie.model.order.OrdersModel()
            self.bid_orders[remote_pair] = model
            return model
