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
from PyQt4 import QtCore, QtGui


logger = logging.getLogger(__name__)
SETTINGS_GROUP = 'exchange_markets'


class ExchangesModel(QtCore.QAbstractItemModel):

    # so this should hold market id's that correspond to a market object class

    def __init__(self, parent=None):
        super(ExchangesModel, self).__init__(parent)
        self.indexes = list()
        self.objects = list()

    def revert(self):
        settings = QtCore.QSettings()
        settings.beginGroup(SETTINGS_GROUP)
        markets = settings.childGroups()
        for market in markets:
            if market not in self.indexes:
                self.indexes.append(market)
                # don't just append a dict, find something better to do
                obj = dict()
                self.objects.append(dict())
            else:
                obj = self.objects[self.indexes.index(market)]

            settings.beginGroup(market)
            for key in settings.childKeys():
                value = settings.value(key).toString()
                obj[key] = value
            settings.endGroup()
        return True

    def submit(self):
        settings = QtCore.QSettings()
        settings.beginGroup(SETTINGS_GROUP)
        for i, market in enumerate(self.indexes):
            obj = self.objects[i]
            settings.beginGroup(market)
            for key, value in obj.items():
                # TODO check if value is save to write as text
                settings.setValue(key, item)
            settings.endGroup()


class ExchangeItem(QtGui.QStandardItem):

    MARKET_COLUMNS = 3
    MARKET_REMOTE, MARKET_ENABLE, MARKET_LOCAL = range(MARKET_COLUMNS)
    market_mappings = (('enable', MARKET_ENABLE),
                       ('local_market', MARKET_LOCAL))

    def __init__(self):
        super(ExchangeItem, self).__init__(self.exchange_name)
        settings = QtCore.QSettings()
        settings.beginGroup(self.exchange_name)
        self.setColumnCount(self.COLUMNS)

        if self.mappings:
            for setting, column in self.mappings:
                value = settings.value(setting)
                if value:
                    item = QtGui.QStandardItem(value)
                else:
                    item = QtGui.QStandardItem()
                self.setChild(0, column, item)

        self.markets_item = QtGui.QStandardItem()
        self.setChild(0, self.MARKETS, self.markets_item)
        settings.beginGroup('markets')

        remotes_in_model = list()

        for remote_string in settings.childGroups():
            settings.beginGroup(remote_string)
            remote_market = str(QtCore.QUrl.fromPercentEncoding(
                remote_string.toUtf8()))
            items = [ QtGui.QStandardItem(remote_market) ]
            for setting, column in self.market_mappings:
                value = settings.value(setting)
                if not value: value = ''
                items.append(QtGui.QStandardItem(value))
            self.markets_item.appendRow(items)
            remotes_in_model.append(remote_string)
            settings.endGroup()

        for remote_market in self.markets:
            if remote_market not in remotes_in_model:
                items = [ QtGui.QStandardItem(remote_market) ]
                columns_left = self.COLUMNS
                while columns_left:
                    columns_left -= 1
                    items.append(QtGui.QStandardItem())
                self.markets_item.appendRow(items)

        self.markets_item.sortChildren(self.MARKET_REMOTE)

    def submit(self):
        settings = QtCore.QSettings()
        settings.beginGroup(self.exchange_name)
        if self.mappings:
            #!!!TODO wont save refresh rate
            for setting, column in self.mappings:
                value = self.child(0, column).text()
                settings.setValue(setting, value)

        # wipe out account information format from preivous version
        settings.remove("accounts")
        settings.beginGroup('markets')
        for row in range(self.markets_item.rowCount()):
            remote_string = self.markets_item.child(row, 0).text()
            remote_string = str(QtCore.QUrl.toPercentEncoding(remote_string))
            settings.beginGroup(remote_string)
            for setting, column in self.market_mappings:
                value = self.markets_item.child(row, column).text()
                settings.setValue(setting, value)
            settings.endGroup()
        settings.endGroup()

    def new_account(self):
        columns = self.ACCOUNT_COLUMNS
        items = []
        while columns:
            items.append(QtGui.QStandardItem())
            columns -= 1
        self.accounts_item.appendRow(items)
        return items[0].index()


class DynamicExchangeItem(ExchangeItem):

    def __init__(self):
        super(ExchangeItem, self).__init__(self.exchange_name)
        settings = QtCore.QSettings()
        settings.beginGroup(self.exchange_name)
        self.setColumnCount(self.COLUMNS)

        if self.mappings:
            for setting, column in self.mappings:
                value = settings.value(setting)
                if value:
                    item = QtGui.QStandardItem(value)
                else:
                    item = QtGui.QStandardItem()
                self.setChild(0, column, item)

        self.markets_item = QtGui.QStandardItem()
        self.setChild(0, self.MARKETS, self.markets_item)
        settings.beginGroup('markets')

        for remote_string in settings.childGroups():
            settings.beginGroup(remote_string)
            remote_string = QtCore.QUrl.fromPercentEncoding(
                remote_string.toUtf8())
            items = [ QtGui.QStandardItem(remote_string) ]
            for setting, column in self.market_mappings:
                value = settings.value(setting)
                if not value: value = ''
                items.append(QtGui.QStandardItem(value))
            #self.markets_item.appendRow(items)
            settings.endGroup()
        self.markets_item.sortChildren(self.MARKET_REMOTE)
        self.new_markets_request()

    def reload(self):
        for market in self.markets:
            if not self.in_markets(market):
                items = [ QtGui.QStandardItem(market) ]
                columns = self.MARKET_COLUMNS
                while columns:
                    columns -= 1
                    items.append(QtGui.QStandardItem())
                self.markets_item.appendRow(items)

    def in_markets(self, market):
        for row in range(self.markets_item.rowCount()):
            if market == self.markets_item.child(row).text():
                return True
        return False


exchanges_model = ExchangesModel()
