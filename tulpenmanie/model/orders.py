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

from PyQt4 import QtCore, QtGui

from tulpenmanie.model.commodities import commodities_model


class OrdersModel(QtGui.QStandardItemModel):

    # TODO set prefixes and suffixes
    # TODO data should be read-only

    COLUMNS = 3
    ORDER_ID, PRICE, AMOUNT = range(COLUMNS)

    def __init__(self, base_row, counter_row, parent=None):
        super(OrdersModel, self).__init__(parent)
        self.base_row = base_row
        self.counter_row = counter_row

    def append_orders(self, orders):
        c_precision = self.get_counter_precision()
        b_precision = self.get_base_precision()
        c_prefix = self.get_counter_prefix()
        b_prefix = self.get_base_prefix()
        c_suffix = self.get_counter_suffix()
        b_suffix = self.get_base_suffix()

        for order_id, price, amount, in orders:
            if c_precision:
                price = round(price, c_precision)
            if b_precision:
                amount = round(amount, b_precision)
            price = c_prefix + str(price) + c_suffix
            amount = b_prefix + str(amount) + b_suffix

            self.appendRow( (QtGui.QStandardItem(str(order_id)),
                             QtGui.QStandardItem(price),
                             QtGui.QStandardItem(amount)) )
        self.sort(self.PRICE, QtCore.Qt.DescendingOrder)

    def remove_order(self, order_id):
        orders = self.findItems(str(order_id))
        for order in orders:
            self.removeRow(order.row())

    def clear_orders(self):
        self.removeRows(0, self.rowCount())

    def get_base_prefix(self):
        return commodities_model.item(
            self.base_row, commodities_model.PREFIX).text()

    def get_counter_prefix(self):
        return commodities_model.item(
            self.counter_row, commodities_model.PREFIX).text()

    def get_base_suffix(self):
        return commodities_model.item(
            self.base_row, commodities_model.SUFFIX).text()

    def get_counter_suffix(self):
        return commodities_model.item(
            self.counter_row, commodities_model.SUFFIX).text()

    def get_base_precision(self):
        precision = commodities_model.item(
            self.base_row, commodities_model.PRECISION).text()
        if not precision:
            return None
        return int(precision)

    def get_counter_precision(self):
        precision = commodities_model.item(
            self.counter_row, commodities_model.PRECISION).text()
        if not precision:
            return None
        else:
            return int(precision)
