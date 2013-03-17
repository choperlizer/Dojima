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

import logging

import otapi
from PyQt4 import QtCore, QtGui


class MarketTableView(QtGui.QTableView):

    marketChanged = QtCore.pyqtSignal(str)
    baseChanged = QtCore.pyqtSignal(str)
    counterChanged = QtCore.pyqtSignal(str)

    def currentChanged(self, current, previous):
        row = current.row()
        model = self.model()
        self.marketChanged.emit(model.getMarketId(row))
        index = model.index(row, model.BASE)
        self.baseChanged.emit(model.data(index, QtCore.Qt.UserRole))
        index = model.index(row, model.COUNTER)
        self.counterChanged.emit(model.data(index, QtCore.Qt.UserRole))


class ComboBox(QtGui.QComboBox):

    otIdChanged = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(ComboBox, self).__init__(parent)
        self.currentIndexChanged[int].connect(self.emitOtId)

    def emitOtId(self, row):
        self.otIdChanged.emit(self.itemData(row, QtCore.Qt.UserRole))

    def getOTID(self):
        return self.itemData(self.currentIndex(), QtCore.Qt.UserRole)


class AccountComboBox(ComboBox):

    @QtCore.pyqtProperty(str)
    def remote_commodity_id(self):
        ot_id = self.itemData(self.currentIndex(), QtCore.Qt.UserRole)
        if ot_id is None:return ''
        ot_id = otapi.OTAPI_Basic_GetAccountWallet_AssetTypeID(ot_id)
        if ot_id is None:return ''
        return ot_id

    @QtCore.pyqtProperty(str)
    def remote_commodity_name(self):
        ot_id = self.itemData(self.currentIndex(), QtCore.Qt.UserRole)
        if ot_id is None:return ''
        ot_id = otapi.OTAPI_Basic_GetAccountWallet_AssetTypeID(ot_id)
        if ot_id is None:return ''
        return otapi.OTAPI_Basic_GetAssetType_Name(ot_id)
