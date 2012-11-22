# Dojima, a markets client.
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


class MarketsModel(dojima.model.base.FlatSettingsModel):
    """QtGui.QStandardItemModel that contain market configuration."""

    name = 'markets'
    COLUMNS = 4
    UUID, NAME, BASE, COUNTER = range(COLUMNS)
    SETTINGS_MAP = (('name', NAME), ('base', BASE), ('counter', COUNTER))

    def new_market(self):
        uuid = QtCore.QUuid.createUuid().toString()[1:-1]
        items = [QtGui.QStandardItem(uuid)]
        for column in range(self.COLUMNS -1):
            items.append(QtGui.QStandardItem())
        self.appendRow(items)
        return items[0].row()

    def delete_row(self, row):
        uuid = self.item(row, self.UUID).text()
        self.removeRow(row)

        for exchange_row in range(dojima.exchange.model.rowCount()):
            exchange_item = dojima.exchange.model.item(exchange_row)
            markets_item = exchange_item.markets_item
            for market_row in range(markets_item.rowCount()):
                local_market_item = markets_item.child(
                    market_row, exchange_item.MARKET_LOCAL)
                if str(local_market_item.text()) == uuid:
                    local_market_item.setText("")
                    enable_market_item = markets_item.child(
                        market_row, exchange_item.MARKET_ENABLE)
                    enable_market_item.setText("false")

                    
markets_model = MarketsModel()
