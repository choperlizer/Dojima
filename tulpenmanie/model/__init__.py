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

from PyQt4 import QtCore


class TreeModel(QtCore.QAbstractItemModel):

    def columnCount(self, parent):
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self.rootItem.columnCount()

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None

        item = index.internalPointer()
        return item.data(index.column(), role)

    """
    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        item = index.internalPointer()
        return item.flags(index)
    """

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.rootItem.data(section)
        return None

    def index(self, row, column, parent=QtCore.QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        child_item = parentItem.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)

        return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        child_item = index.internalPointer()
        parentItem = child_item.parent()
        if parentItem == self.rootItem:
            return QtCore.QModelIndex()
        return self.createIndex(parentItem.row(), 0, parentItem)

    def removeRows(self, row, count, parent=QtCore.QModelIndex()):
        if parent is None or not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()
        self.beginRemoveRows(parent, row, row + count)
        remove_result = parentItem.removeRows(row, count)
        self.endRemoveRows()
        return remove_result

    def rowCount(self, parent=None):
        if not parent or not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()
        return parentItem.childCount()

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if not index.isValid():
            return False

        item = index.internalPointer()
        returned = item.setData(index, value, role)
        if returned: self.dataChanged.emit(index, index)
        return returned


class RootItem(object):
    def __init__(self, parent):
        self.parentItem = parent
        self.childIndexes = list()
        self.childItems = list()

    def appendChild(self, item_id, item):
        self.childIndexes.append(item_id)
        self.childItems.append(item)

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def data(self, column, role=None):
        return None

    def parent(self):
        return self.parentItem

    def removeRows(self, row, count):
        while count:
            self.childItems.pop(row)
            count -= 1
            row += 1

        return True

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)

        return 0


class TreeItem(RootItem):
    def __init__(self, identifier, parent):
        self.id = identifier
        self.parentItem = parent
        self.childIndexes = list()
        self.childItems = list()

    def childFromID(self, child_id, ChildClass=None):
        if child_id not in self.childIndexes:
            if ChildClass is None:
                return None
            child_item = ChildClass(child_id, self)
            self.appendChild(child_id, child_item)
            return child_item
        i = self.childIndexes.index(child_id)
        return self.childItems[i]
