# -*- coding: utf-8 -*-
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

import logging
from PyQt4 import QtCore, QtGui

import tulpenmanie.model.base
import tulpenmanie.market
import tulpenmanie.translate

logger = logging.getLogger(__name__)

model = None

def create_model(parent):
    global model
    model = _CommoditiesModel(parent)

class _CommoditiesModel(tulpenmanie.model.base.FlatSettingsModel):

    name = 'commodities'
    COLUMNS = 5
    UUID, NAME, PREFIX, SUFFIX, PRECISION = range(COLUMNS)
    SETTINGS_MAP = (('name', NAME), ('prefix', PREFIX),
                    ('suffix', SUFFIX), ('precision', PRECISION))
    BITCOIN_UUID = 'ef699000-02d3-45f8-8dc1-c1345bf1f521'

    def __init__(self, parent=None):
        super(_CommoditiesModel, self).__init__(parent)
        search_static = self.findItems(self.BITCOIN_UUID,
                                QtCore.Qt.MatchExactly,
                                self.UUID)
        if not search_static:
            search_existing = self.findItems(tulpenmanie.translate.bitcoin,
                                             QtCore.Qt.MatchFixedString,
                                             self.NAME)
            for item in search_existing:
                text = item.text()
                item.setText(text + QtCore.QCoreApplication.translate(
                    "commodities", " (user defined)"))

            items = [QtGui.QStandardItem(self.BITCOIN_UUID),
                     QtGui.QStandardItem(tulpenmanie.translate.bitcoin),
                     QtGui.QStandardItem(),
                     QtGui.QStandardItem(),
                     QtGui.QStandardItem('8')]
            self.appendRow(items)

            # Create a bitcoin commodity
            # TODO search for existing bitcoin and rename it

    def new_commodity(self):
        uuid = QtCore.QUuid.createUuid().toString()[1:-1]
        items = [QtGui.QStandardItem(uuid)]
        for column in range(self.COLUMNS -1):
            items.append(QtGui.QStandardItem())
        self.appendRow(items)
        return items[0].row()
