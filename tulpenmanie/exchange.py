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

import abc
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
	_exchange_classes[exchange_class.provider_name] = exchange_class

accounts = dict()
def register_account(account_class):
    accounts[account_class.provider_name] = account_class


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
        super(ExchangeItem, self).__init__(self.provider_name)
        self.settings = QtCore.QSettings()
        self.settings.beginGroup(self.provider_name)
        self.setColumnCount(self.COLUMNS)

        logger.debug("loading %s settings", self.provider_name)
        if self.mappings:
            for setting, column in self.mappings:
                value = self.settings.value(setting)
                if value:
                    item = QtGui.QStandardItem(value)
                else:
                    item = QtGui.QStandardItem()
                self.setChild(0, column, item)

        if self.markets:
            logger.debug("loading %s markets", self.provider_name)
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
        logger.debug("saving %s settings", self.provider_name)
        if self.mappings:
            #!!!TODO wont save refresh rate
            for setting, column in self.mappings:
                value = self.child(0, column).text()
                self.settings.setValue(setting, value)

        logger.debug("saving %s markets", self.provider_name)
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
