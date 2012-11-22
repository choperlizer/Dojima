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

import otapi
from PyQt4 import QtCore, QtGui

import dojima.model.ot

class _OTAccountsModel():

    ACCOUNT = 0
    ASSET = 1
    NYM = 2
    SERVER = 3
    TYPE = 4
    BALANCE = 5

    simple_translation = QtCore.QCoreApplication.translate(
        'OTAccountsModel', "simple",
        "the simple, standard type of account")
    issuer_translation = QtCore.QCoreApplication.translate(
        'OTAccountsModel', "issuer",
        "the type of account that can issue assets onto a server, this account "
        "only ever goes into the negative, because the credit in a simple "
        "must originate from an issuer account.")

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal:
            if section == self.ACCOUNT:
                return QtCore.QCoreApplication.translate('OTAccountsModel',
                                                         "Account")
            if section == self.ASSET:
                return QtCore.QCoreApplication.translate('OTAccountsModel',
                                                         "Asset")
            if section == self.NYM:
                return QtCore.QCoreApplication.translate('OTAccountsModel',
                                                         "Nym")
            if section == self.SERVER:
                return QtCore.QCoreApplication.translate('OTAccountsModel',
                                                         "Server")
            if section == self.TYPE:
                return QtCore.QCoreApplication.translate('OTAccountsModel',
                                                         "Type")
            if section == self.BALANCE:
                return QtCore.QCoreApplication.translate('OTAccountsModel',
                                                         "Balance")
        return section


class OTAccountsModel(QtGui.QStandardItemModel, _OTAccountsModel):

    def __init__(self, parent=None):
        super(OTAccountsModel, self).__init__(parent)

        self.row_count = otapi.OT_API_GetAccountCount()
        # redundantly defined below
        for row in range(self.row_count):
            account_id = otapi.OT_API_GetAccountWallet_ID(row)
            self.addRow(account_id, row)

    def addRow(self, account_id, row=None):
        if not row:
            row = self.rowCount()

        item = QtGui.QStandardItem(
            otapi.OT_API_GetAccountWallet_Name(account_id))
        item.setData(account_id, QtCore.Qt.UserRole)
        self.setItem(row, self.ACCOUNT, item)

        ot_id = otapi.OT_API_GetAccountWallet_AssetTypeID(account_id)
        item = QtGui.QStandardItem(otapi.OT_API_GetAssetType_Name(ot_id))
        item.setData(ot_id, QtCore.Qt.UserRole)
        self.setItem(row, self.ASSET, item)

        ot_id = otapi.OT_API_GetAccountWallet_NymID(account_id)
        item = QtGui.QStandardItem(otapi.OT_API_GetNym_Name(ot_id))
        item.setData(ot_id, QtCore.Qt.UserRole)
        self.setItem(row, self.NYM, item)

        ot_id = otapi.OT_API_GetAccountWallet_ServerID(account_id)
        item = QtGui.QStandardItem(otapi.OT_API_GetServer_Name(ot_id))
        item.setData(ot_id, QtCore.Qt.UserRole)
        self.setItem(row, self.SERVER, item)

        account_type = otapi.OT_API_GetAccountWallet_Type(account_id)
        if account_type == 'simple':
            item = QtGui.QStandardItem(self.simple_translation)
            item.setData('s', QtCore.Qt.UserRole)
        elif account_type == 'issuer':
            item = QtGui.QStandardItem(self.issuer_translation)
            item.setData('i', QtCore.Qt.UserRole)
        else:
            # this shouldn't happen, but why not plan ahead?
            item = QtGui.QStandardItem(account_type)
            item.setData(account_type[0], QtCore.Qt.UserRole)
        self.setItem(row, self.TYPE, item)

        item = QtGui.QStandardItem(
            otapi.OT_API_GetAccountWallet_Balance(account_id))
        self.setItem(row, self.BALANCE, item)

    def refresh(self):
        for row in range(otapi.OT_API_GetAccountCount()):
            account_id = otapi.OT_API_GetAccountWallet_ID(row)
            search = self.findItems(account_id)
            if not search: self.addRow(account_id)

    def setData(self, index, data, role=QtCore.Qt.EditRole):
        # more that account label could be edited but it'd have to sync across
        # multiplie items
        if not index.isValid() or role != QtCore.Qt.EditRole:
            return False
        if index.column() != self.ACCOUNT:
            return False

        row = index.row()
        account_id = str(self.item(row, self.ID).text())
        signer_nym = str(self.item(row, self.NYM_ID).text())
        otapi.OT_API_SetAccountWallet_Name(account_id,
                                           signer_nym,
                                           str(data))
        self.item(row, self.ACCOUNT).setText(data)
        self.dataChanged.emit(index, index)
        return True


class OTAccountsProxyModel(QtGui.QSortFilterProxyModel, _OTAccountsModel):

    def refresh(self):
        self.model().refresh()


class OTServerAccountsModel(OTAccountsProxyModel):

    def __init__(self, server_id, parent=None):
        super(OTServerAccountsModel, self).__init__(parent)
        source_model = OTAccountsModel()
        self.setSourceModel(source_model)
        self.setFilterKeyColumn(OTAccountsModel.SERVER)
        self.setFilterRole(QtCore.Qt.UserRole)
        self.setFilterFixedString(server_id)
        self.setDynamicSortFilter(True)
