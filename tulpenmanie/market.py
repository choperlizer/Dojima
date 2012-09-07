# Tulpenmanie, a commodities market client.
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

import tulpenmanie.model.base

markets_model = None
market_docks = dict()

def create_model(parent):
    global markets_model
    markets_model = _MarketsModel(parent)


class _MarketsModel(tulpenmanie.model.base.FlatSettingsModel):
    """QtGui.QStandardItemModel that contain market configuration."""
    """Intended to be instaniated in this module only."""

    name = 'markets'
    COLUMNS = 5
    UUID, NAME, BASE, COUNTER, ENABLE = range(COLUMNS)
    SETTINGS_MAP = (('name', NAME), ('base', BASE),
                    ('counter', COUNTER), ('enable', ENABLE))

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
