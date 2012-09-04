# Tuplenmanie, a commodities market client.
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

from tulpenmanie.model.base import FlatSettingsModel


class MarketsModel(FlatSettingsModel):

    name = 'markets'
    COLUMNS = 5
    UUID, NAME, BASE, COUNTER, ENABLE = range(COLUMNS)
    SETTINGS_MAP = (('name', NAME), ('base', BASE),
                    ('counter', COUNTER), ('enable', ENABLE))

    #def __init__(self, parent=None):
        #super(MarketsModel, self).__init__('markets', parent)
        #if self.rowCount() == 0:
        #    null_uuid_item = QtGui.QStandardItem(
        #        "00000000-0000-0000-0000-000000000000")
        #    null_name_item = QtGui.QStandardItem(
        #        QtCore.QCoreApplication.translate("market settings model",
        #                                          "None") )
        #    self.appendRow((null_uuid_item, null_name_item))

    def new_market(self):
        columns = self.COLUMNS - 1
        items = []
        uuid = QtCore.QUuid.createUuid().toString()[1:-1]
        items.append(QtGui.QStandardItem(uuid))
        while columns:
            items.append(QtGui.QStandardItem())
            columns -= 1
        self.appendRow(items)
        return items[0].row()
