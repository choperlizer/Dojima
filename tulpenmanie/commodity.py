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

from PyQt4 import QtCore, QtGui

import tulpenmanie.model.base

commodities_model = None

def create_model(parent):
    global commodities_model
    commodities_model = _CommoditiesModel(parent)


class _CommoditiesModel(tulpenmanie.model.base.FlatSettingsModel):

    name = 'commodities'
    COLUMNS = 5
    UUID, NAME, PREFIX, SUFFIX, PRECISION = range(COLUMNS)
    SETTINGS_MAP = (('name', NAME), ('prefix', PREFIX),
                    ('suffix', SUFFIX), ('precision', PRECISION))

    def new_commodity(self):
        uuid = QtCore.QUuid.createUuid().toString()[1:-1]
        item = QtGui.QStandardItem(uuid)

        self.appendRow( (item,
                         QtGui.QStandardItem(),
                         QtGui.QStandardItem(),
                         QtGui.QStandardItem(),
                         QtGui.QStandardItem()) )
        return item.row()


commodities_model = _CommoditiesModel()
