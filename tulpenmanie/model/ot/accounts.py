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

import otapi
from PyQt4 import QtCore

import tulpenmanie.model.ot

class OTAccountsLowModel(tulpenmanie.model.ot.OTBaseModel):

    COLUMNS = 7
    ID, ASSET_ID, NYM_ID, SERVER_ID, NAME, TYPE, BALANCE = range(COLUMNS)

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal:
            if section == self.ID:
                return QtCore.QCoreApplication.translate('OTAccountsModel',
                                                         "id")
            if section == self.ASSET_ID:
                return QtCore.QCoreApplication.translate('OTAccountsModel',
                                                         "asset")
            if section == self.NYM_ID:
                return QtCore.QCoreApplication.translate('OTAccountsModel',
                                                         "nym")
            if section == self.SERVER_ID:
                return QtCore.QCoreApplication.translate('OTAccountsModel',
                                                         "server")
            if section == self.NAME:
                return QtCore.QCoreApplication.translate('OTAccountsModel',
                                                         "label")
            if section == self.TYPE:
                return QtCore.QCoreApplication.translate('OTAccountsModel',
                                                         "type")
            if section == self.BALANCE:
                return QtCore.QCoreApplication.translate('OTAccountsModel',
                                                         "balance")
        return section

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return 0
        if role == QtCore.Qt.TextAlignmentRole:
            return int(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        elif role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            column = index.column()
            ot_id = otapi.OT_API_GetAccountWallet_ID(index.row())

            if column == self.ID:
                return ot_id

            if column == self.ASSET_ID:
                return otapi.OT_API_GetAccountWallet_AssetTypeID(ot_id)

            if column == self.NYM_ID:
                return otapi.OT_API_GetAccountWallet_NymID(ot_id)

            if column == self.SERVER_ID:
                return otapi.OT_API_GetAccountWallet_ServerID(ot_id)

            if column == self.NAME:
                return otapi.OT_API_GetAccountWallet_Name(ot_id)

            if column == self.TYPE:
                return otapi.OT_API_GetAccountWallet_Type(ot_id)

            if column == self.BALANCE:
                return otapi.OT_API_GetAccountWallet_Balance(ot_id)

    def setData(self, index, data, role=QtCore.Qt.EditRole):
        if not index.isValid() or role != QtCore.Qt.EditRole:
            return False
        if index.column() != self.NAME:
            return False
        account_id = otapi.OT_API_GetAccountWallet_ID(index.row())
        otapi.OT_API_SetAccount_Name(account_id, str(data))
        self.dataChanged.emit(index, index)
        return True

    def rowCount(self, parent=None):
        if parent and parent.isValid():
            return 0
        return otapi.OT_API_GetAccountCount()

""" def flags(self, index):
        flags = super(_MyTableModel, self).flags(index)
        flags |= QtCore.Qt.ItemIsEditable
        return flags
"""


class OTAccountsModel(QtCore.QAbstractTableModel):

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return 0
        if role == QtCore.Qt.TextAlignmentRole:
            return int(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        elif role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            column = index.column()
            ot_id = otapi.OT_API_GetAccountWallet_ID(index.row())

            if column == self.ID:
                return ot_id

            if column == self.ASSET_ID:
                ot_id = otapi.OT_API_GetAccountWallet_AssetTypeID(ot_id)
                return  otapi.OT_API_GetAssetType_Name(ot_id)

            if column == self.NYM_ID:
                ot_id = otapi.OT_API_GetAccountWallet_NymID(ot_id)
                return  otapi.OT_API_GetNym_Name(ot_id)

            if column == self.SERVER_ID:
                ot_id = otapi.OT_API_GetAccountWallet_ServerID(ot_id)
                return  otapi.OT_API_GetServer_Name(ot_id)

            if column == self.NAME:
                return otapi.OT_API_GetAccountWallet_Name(ot_id)

            if column == self.TYPE:
                return otapi.OT_API_GetAccountWallet_Type(ot_id)

            if column == self.BALANCE:
                return otapi.OT_API_GetAccountWallet_Balance(ot_id)
