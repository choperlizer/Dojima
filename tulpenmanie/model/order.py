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

class OrdersModel(QtGui.QStandardItemModel):

    # TODO set prefixes and suffixes
    # TODO data should be read-only

    COLUMNS = 3
    ORDER_ID, PRICE, AMOUNT = range(COLUMNS)

    def __init__(self, parent=None):
        super(OrdersModel, self).__init__(parent)

    def append_order(self, order_id, price, amount):
        self.appendRow( (QtGui.QStandardItem(str(order_id)),
                         QtGui.QStandardItem(str(price)),
                         QtGui.QStandardItem(str(amount)) ) )

    def remove_order(self, order_id):
        orders = self.findItems(str(order_id))
        for order in orders:
            self.removeRow(order.row())

    def clear_orders(self):
        self.removeRows(0, self.rowCount())
