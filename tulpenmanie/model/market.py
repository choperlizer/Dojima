from PyQt4 import QtCore, QtGui

from tulpenmanie.model.base import FlatSettingsModel


class MarketsModel(FlatSettingsModel):

    COLUMNS = 5
    UUID, NAME, BASE, COUNTER, ENABLE = range(COLUMNS)
    SETTINGS_MAP = (('name', NAME), ('base', BASE),
                    ('counter', COUNTER), ('enable', ENABLE))

    def __init__(self, parent=None):
        super(MarketsModel, self).__init__('markets', parent)

    def new_market(self):
        uuid = QtCore.QUuid.createUuid().toString()[1:-1]
        item = QtGui.QStandardItem(uuid)
        self.appendRow( (item,
                         QtGui.QStandardItem(),
                         QtGui.QStandardItem(),
                         QtGui.QStandardItem(),
                         QtGui.QStandardItem()) )
        return item.row()
