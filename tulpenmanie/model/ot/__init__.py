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

import otapi
from PyQt4 import QtCore


class OTBaseModel(QtCore.QAbstractTableModel):

    COLUMNS = 2
    ID, NAME = range(COLUMNS)

    def columnCount(self, parent=None):
        if parent and parent.isValid():
            return 0
        return self.COLUMNS

    def parent(self):
        return QtCore.QModelIndex()

    def flags(self, index):
        flags = super(OTBaseModel, self).flags(index)
        if index.column == self.NAME:
            flags |= QtCore.Qt.ItemIsEditable
        return flags

