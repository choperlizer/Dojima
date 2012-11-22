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


class CommoditiesModel(dojima.model.base.FlatSettingsModel):

    name = 'commodities'
    COLUMNS = 5
    UUID, NAME, PREFIX, SUFFIX, PRECISION = range(COLUMNS)
    SETTINGS_MAP = (('name', NAME), ('prefix', PREFIX),
                    ('suffix', SUFFIX), ('precision', PRECISION))

    def new_commodity(self):
        uuid = QtCore.QUuid.createUuid().toString()[1:-1]
        items = [QtGui.QStandardItem(uuid)]
        for column in range(self.COLUMNS -1):
            items.append(QtGui.QStandardItem())
        self.appendRow(items)
        return items[0].row()

    #TODO can't instantiate until after we have an app
commodities_model = CommoditiesModel()
