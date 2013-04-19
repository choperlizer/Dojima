# -*- coding: utf-8 -*-
# Dojima, a graphical speculation platform.
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
import dojima.model.base


class LocalCommoditiesModel(QtGui.QStandardItemModel):

    name = 'local_commodities'
    ID = 0
    COLUMNS = 4
    NAME, PREFIX, SUFFIX, PRECISION = list(range(COLUMNS))
    SETTINGS_MAP = (('prefix', PREFIX),
                    ('suffix', SUFFIX),
                    ('precision', PRECISION))

    def __init__(self, parent=None):
        super(LocalCommoditiesModel, self).__init__(parent)
        self.setColumnCount(self.COLUMNS)
        self.revert()

    def delete_row(self, row):
        uuid = self.item(self.ID, row).text()
        self.settings.remove(uuid)
        self.removeRow(row)

    def getName(self, uuid):
        name = None
        for row in range(self.rowCount()):
            item = self.item(row, self.ID)

            if item.data(QtCore.Qt.UserRole) == uuid:
                return item.text()

    def getNames(self, uuid1, uuid2):
        name1, name2 = None, None
        for row in range(self.rowCount()):
            item = self.item(row, self.ID)

            if item.data(QtCore.Qt.UserRole) == uuid1:
                name1 = item.text()
                if name2 is not None: break

            if item.data(QtCore.Qt.UserRole) == uuid2:
                name2 = item.text()
                if name1 is not None: break

        return name1, name2

    def getPrecision(self, uuid):
        for row in range(self.rowCount()):
            item = self.item(row, self.ID)

            if item.data(QtCore.Qt.UserRole) == uuid:
                return int(self.item(row, self.PRECISION).text())
        
    def getPrefixSuffix(self, uuid):
        for row in range(self.rowCount()):
            item = self.item(row, self.ID)

            if item.data(QtCore.Qt.UserRole) == uuid:
                prefix = self.item(row, self.PREFIX).text()
                suffix = self.item(row, self.SUFFIX).text()
                return prefix, suffix

    def getRow(self, uuid):
        name = None
        for row in range(self.rowCount()):
            item = self.item(row, self.ID)

            if item.data(QtCore.Qt.UserRole) == uuid:
                return row

    def getRows(self, uuid1, uuid2):
        row1, row2 = None, None
        for row in range(self.rowCount()):
            item = self.item(row, self.ID)

            if item.data(QtCore.Qt.UserRole) == uuid1:
                row1 = row
                if row2 is not None: break

            if item.data(QtCore.Qt.UserRole) == uuid2:
                row2 = row
                if row1 is not None: break

        return row1, row2

    def newCommodity(self):
        item = QtGui.QStandardItem()
        item.setData(QtCore.QUuid.createUuid().toString()[1:-1],
                     QtCore.Qt.UserRole)
        items = [item]
        for column in range(self.COLUMNS -1):
            items.append(QtGui.QStandardItem())
        self.appendRow(items)
        return item.row()

    def revert(self):
        settings = QtCore.QSettings()
        settings.beginGroup('local_commodities')

        for row, uuid in enumerate(settings.childGroups()):
            settings.beginGroup(uuid)
            item = QtGui.QStandardItem(settings.value('name'))
            item.setData(uuid, QtCore.Qt.UserRole)

            self.setItem(row, self.ID, item)
            for setting, column in self.SETTINGS_MAP:
                item = QtGui.QStandardItem(settings.value(setting))
                self.setItem(row, column, item)
            settings.endGroup()
            # THIS IS ONLY HERE BECAUSE NOT ALL COMMODITIES IN SETTINGS WILL HAVE PRECISION SET
            item = self.item(row, self.PRECISION)
            if not len(item.text()):
                item.setText('4')
            
        return True

    def submit(self):
        settings = QtCore.QSettings()
        settings.beginGroup('local_commodities')
        rows = list(range(self.rowCount()))
        settings.remove('')
        for row in rows:
            uuid = self.item(row, self.ID).data(QtCore.Qt.UserRole)
            settings.beginGroup(uuid)
            settings.setValue('name', self.item(row, self.NAME).text())
            for setting, column in self.SETTINGS_MAP:
                value =  self.item(row, column).text()
                settings.setValue(setting, value)
            settings.endGroup()
        return True


class RemoteCommoditiesModel(QtGui.QStandardItemModel):

    name = 'remote_commodities'
    COLUMNS = 2
    ID, LOCAL_ID = list(range(COLUMNS))
    SETTINGS_MAP = (('local', LOCAL_ID),)

    def __init__(self, parent=None):
        super(RemoteCommoditiesModel, self).__init__(parent)
        self.setColumnCount(self.COLUMNS)
        self.revert()

    def getLocalToRemoteMap(self, local_id):
        search = self.findItems(local_id, QtCore.Qt.MatchExactly, self.LOCAL_ID)
        if not search:
            return None
        return self.item(search[0].row(), self.ID).text()

    def getRemoteToLocalMap(self, remote_id):
        search = self.findItems(remote_id, QtCore.Qt.MatchExactly, self.ID)
        if not search:
            return None
        return self.item(search[0].row(), self.LOCAL_ID).text()

    def hasMap(self, remote_id):
        search = self.findItems(remote_id)
        return bool(search)

    def map(self, remote_id, local_id):
        search = self.findItems(remote_id)
        if search:
            self.item(search[0].row(), self.LOCAL_ID).setData(local_id)
            return

        self.appendRow( (QtGui.QStandardItem(remote_id),
                         QtGui.QStandardItem(local_id),) )

    def revert(self):
        settings = QtCore.QSettings()
        settings.beginGroup('remote_commodities')
        for remote_id in settings.childKeys():
            remote_item = QtGui.QStandardItem(remote_id)
            local_item = QtGui.QStandardItem(settings.value(remote_id))
            self.appendRow((remote_item, local_item,))

    def submit(self):
        settings = QtCore.QSettings()
        settings.beginGroup('remote_commodities')
        settings.remove('')
        for row in range(self.rowCount()):
            settings.setValue(self.item(row, self.ID).text(),
                              self.item(row, self.LOCAL_ID).text())
        return True

#TODO can't instantiate until after we have an app
local_model = LocalCommoditiesModel()
remote_model = RemoteCommoditiesModel()
