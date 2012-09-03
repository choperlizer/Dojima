import logging
from PyQt4 import QtCore, QtGui


logger = logging.getLogger(__name__)


exchanges = dict()
accounts = dict()
exchange_model_items = list()


def register_exchange(exchange_class):
	exchanges[exchange_class.provider_name] = exchange_class

def register_account(account_class):
    accounts[account_class.provider_name] = account_class

def register_exchange_model_item(item_class):
    exchange_model_items.append(item_class)


class ExchangesModel(QtGui.QStandardItemModel):

    def save(self):
        for row in range(self.rowCount()):
            item = self.item(row)
            item.save()


class ProviderItem(QtGui.QStandardItem):

    mappings = None
    markets = None

    MARKET_COLUMNS = 3
    MARKET_REMOTE, MARKET_ENABLE, MARKET_LOCAL = range(MARKET_COLUMNS)
    market_mappings = (('enable', MARKET_ENABLE),
                       ('local_market', MARKET_LOCAL))

    def __init__(self):
        super(ProviderItem, self).__init__(self.provider_name)
        self.settings = QtCore.QSettings()
        self.settings.beginGroup(self.provider_name)
        self.setColumnCount(self.COLUMNS)

        logger.debug("loading %s settings", self.provider_name)
        if self.mappings:
            for setting, column in self.mappings:
                item = QtGui.QStandardItem(
                    self.settings.value(setting).toString())
                self.appendItem(0, column, item)

        if self.markets:
            logger.debug("loading %s markets", self.provider_name)
            self.markets_item = QtGui.QStandardItem()
            self.setChild(0, self.MARKETS, self.markets_item)
            self.settings.beginGroup('markets')
            for remote_market in self.markets:
                items = [ QtGui.QStandardItem(remote_market) ]
                self.settings.beginGroup(remote_market)
                for setting, column in self.market_mappings:
                    value = self.settings.value(setting).toString()
                    items.append(QtGui.QStandardItem(value))
                self.markets_item.appendRow(items)
                self.settings.endGroup()
            self.settings.endGroup()

        self.accounts_item = QtGui.QStandardItem()
        self.setChild(0, self.ACCOUNTS, self.accounts_item)
        self.settings.beginGroup('accounts')
        for account in self.settings.childGroups():
            self.settings.beginGroup(account)
            items = [ QtGui.QStandardItem(account) ]
            for setting, column in self.account_mappings:
                value = self.settings.value(setting).toString()
                items.append(QtGui.QStandardItem(value))
            self.accounts_item.appendRow(items)
            self.settings.endGroup()
        self.settings.endGroup()

    def save(self):
        logger.debug("saving %s settings", self.provider_name)
        if self.mappings:
            for setting, column in self.mappings:
                value = self.item(0, column).text()
                self.settings.setValue(setting, value)

        if self.markets:
            logger.debug("saving %s markets", self.provider_name)
            self.settings.beginGroup('markets')
            for row in range(self.markets_item.rowCount()):
                remote_market = self.markets_item.child(row, 0).text()
                self.settings.beginGroup(remote_market)
                for setting, column in self.market_mappings:
                    value = self.markets_item.child(row, column).text()
                    self.settings.setValue(setting, value)
                self.settings.endGroup()
            self.settings.endGroup()

        self.settings.beginGroup('accounts')
        for row in range(self.accounts_item.rowCount()):
            name = self.accounts_item.child(row, 0).text()
            self.settings.beginGroup(name)
            for setting, column in self.account_mappings:
                value = self.accounts_item.child(row, column).text()
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
