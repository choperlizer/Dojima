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


class LocalCommoditiesModel(dojima.model.base.FlatSettingsModel):

    name = 'local_commodities'
    COLUMNS = 5
    ID, NAME, PREFIX, SUFFIX, PRECISION = range(COLUMNS)
    SETTINGS_MAP = (('name', NAME), ('prefix', PREFIX),
                    ('suffix', SUFFIX), ('precision', PRECISION))

    def new_commodity(self):
        uuid = QtCore.QUuid.createUuid().toString()[1:-1]
        items = [QtGui.QStandardItem(uuid)]
        for column in range(self.COLUMNS -1):
            items.append(QtGui.QStandardItem())
        self.appendRow(items)
        return items[0].row()


class RemoteCommoditiesModel(dojima.model.base.FlatSettingsModel):

    name = 'remote_commodities'
    COLUMNS = 2
    ID, LOCAL_ID = range(COLUMNS)
    SETTINGS_MAP = (('local', LOCAL_ID),)

    def map(self, remote_id, local_id):
        search = self.findItems(remote_id)
        if search:
            self.item(search[0].row(), self.LOCAL_ID).setData(local_id)
            return

        self.appendRow( (QtGui.QStandardItem(remote_id),
                         QtGui.QStandardItem(local_id),) )

    def getLocalToRemoteMap(self, local_id):
        search = self.findItems(local_id, QtCore.Qt.MatchExactly, self.LOCAL_ID)
        return self.item(search[0].row(), ID).text()

    def hasMap(self, remote_id):
        search = self.findItems(remote_id)
        return bool(search)

    #TODO can't instantiate until after we have an app
local_model = LocalCommoditiesModel()
remote_model = RemoteCommoditiesModel()
