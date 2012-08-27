import logging

from PyQt4 import QtCore, QtGui, QtSql


logger = logging.getLogger(__name__)


class FlatSettingsModel(QtGui.QStandardItemModel):

    #def __init__(self, name, mappings, parent=None):
    def __init__(self, name, parent=None):
        super(FlatSettingsModel, self).__init__(parent)
        self.name = name
        self.settings = QtCore.QSettings()
        self.settings.beginGroup(self.name)
        self.setColumnCount(self.COLUMNS)
        self._populate()

    def _populate(self):
        logger.debug("loading %s", self.name)
        for row, uuid in enumerate(self.settings.childGroups()):
            self.settings.beginGroup(uuid)
            item = QtGui.QStandardItem(uuid)
            self.setItem(row, self.UUID, item)
            for setting, column in self.SETTINGS_MAP:
                item = QtGui.QStandardItem(
                    self.settings.value(setting).toString())
                self.setItem(int(row), column, item)
            self.settings.endGroup()

    def save(self):
        logger.debug("saving %s", self.name)
        rows = range(self.rowCount())

        for row in rows:
            uuid = self.item(row, self.UUID).text()
            self.settings.beginGroup(uuid)
            for setting, column in self.SETTINGS_MAP:
                self.settings.setValue(
                    setting, self.item(row, column).text() )
            self.settings.endGroup()

    def delete_row(self, row):
        uuid = self.item(self.UUID, row).text()
        self.settings.remove(uuid)
        self.removeRow(row)
