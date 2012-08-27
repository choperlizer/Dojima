import logging

from PyQt4 import QtCore, QtGui

#from tulpenmanie.model.base import FlatSettingsModel


logger = logging.getLogger(__name__)

class AccountsModel(QtGui.QStandardItemModel):

    def __init__(self, exchange, parent=None):
        super(AccountsModel, self).__init__(parent)
        self.name = exchange
        self.settings = QtCore.QSettings()
        self.settings.beginGroup(self.name)
        self.settings.beginGroup("accounts")
        self.setColumnCount(self.COLUMNS)
        self._populate()

    def _populate(self):
        logger.debug("loading %s accounts", self.name)
        rows = self.settings.childGroups()
        for row in self.settings.childGroups():
            self.settings.beginGroup(row)
            for setting, column in self.MAPPINGS:
                item = QtGui.QStandardItem(
                    self.settings.value(setting).toString())
                self.setItem(int(row), column, item)
            self.settings.endGroup()

    def save(self, row=None):
        logger.debug("saving %s", self.name)
        if row is None:
            rows = range(self.rowCount())
        else:
            rows = [row]

        for row in rows:
            self.settings.beginGroup(str(row))
            for setting, column in self.MAPPINGS:
                self.settings.setValue(
                    setting, self.item(row, column).text() )
            self.settings.endGroup()

    def delete_row(self, row):
        self.settings.remove(str(row))
        self.removeRow(row)
