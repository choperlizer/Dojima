from PyQt4 import QtCore, QtGui

from tulpenmanie.model.base import FlatSettingsModel

# maybe this should go somewhere else
#from tulpenmanie import services
#from tulpenmanie.providers import *


class ExchangesModel(FlatSettingsModel):

    COLUMNS = 6
    UUID, NAME, MARKET, PROVIDER, REMOTE, ENABLE = range(COLUMNS)
    SETTINGS_MAP = (('name', NAME), ('market', MARKET),
                    ('provider', PROVIDER), ('remote', REMOTE),
                    ('enable', ENABLE))

    def __init__(self, parent=None):
        super(ExchangesModel, self).__init__('exchanges', parent)

    def new_exchange(self):
        uuid = QtCore.QUuid.createUuid().toString()[1:-1]
        item = QtGui.QStandardItem(uuid)
        self.appendRow( (item,
                         QtGui.QStandardItem(),
                         QtGui.QStandardItem(),
                         QtGui.QStandardItem(),
                         QtGui.QStandardItem(),
                         QtGui.QStandardItem()) )
        return item.row()

    def new_account(self, exchange_index):
        parent = self.itemFromIndex(exchange_index)
        child_item = QtGui.QStandardItem("")
        self.appendRow(child_item)
        return child_item.index()
