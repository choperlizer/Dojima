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

class _OTAccountsModel:
    """ Defined so that labels and column indexes can be resused in proxy models."""

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

        self.row_count = otapi.OTAPI_Basic_GetAccountCount()
        for row in range(self.row_count):
            account_id = otapi.OTAPI_Basic_GetAccountWallet_ID(row)
            self.addRow(account_id, row)

    def addRow(self, account_id, row=None):
        """Set item text to human readable labes, set UserRole data to OT ID's"""
        assert account_id
        if not row:
            row = self.rowCount()

        label = otapi.OTAPI_Basic_GetAccountWallet_Name(account_id)
        item = QtGui.QStandardItem(label)          
        item.setData(account_id, QtCore.Qt.UserRole)
        self.setItem(row, self.ACCOUNT, item)

        ot_id = otapi.OTAPI_Basic_GetAccountWallet_AssetTypeID(account_id)
        label = otapi.OTAPI_Basic_GetAssetType_Name(ot_id)
        item = QtGui.QStandardItem(label)
        item.setData(ot_id, QtCore.Qt.UserRole)
        self.setItem(row, self.ASSET, item)

        ot_id = otapi.OTAPI_Basic_GetAccountWallet_NymID(account_id)
        label = otapi.OTAPI_Basic_GetNym_Name(ot_id)
        item = QtGui.QStandardItem(label)
        item.setData(ot_id, QtCore.Qt.UserRole)
        self.setItem(row, self.NYM, item)

        ot_id = otapi.OTAPI_Basic_GetAccountWallet_ServerID(account_id)
        label = otapi.OTAPI_Basic_GetServer_Name(ot_id)
        item = QtGui.QStandardItem(label)
        item.setData(ot_id, QtCore.Qt.UserRole)
        self.setItem(row, self.SERVER, item)

        account_type = otapi.OTAPI_Basic_GetAccountWallet_Type(account_id)
        if account_type == 'simple':
            label = self.simple_translation
            data = 's'
            
        elif account_type == 'issuer':
            label = self.issuer_translation
            data = 'i'
        else:
            label = account_type
            data = account_type[0]

        item = QtGui.QStandardItem(label)
        item.setData(data, QtCore.Qt.UserRole)
        self.setItem(row, self.TYPE, item)

        item = QtGui.QStandardItem(
            otapi.OTAPI_Basic_GetAccountWallet_Balance(account_id))
        self.setItem(row, self.BALANCE, item)
    
    def refresh(self):
        for row in range(otapi.OTAPI_Basic_GetAccountCount()):
            account_id = otapi.OTAPI_Basic_GetAccountWallet_ID(row)
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
        account_id = self.item(row, self.ID).text()
        signer_nym = self.item(row, self.NYM_ID).text()
        otapi.OTAPI_Basic_SetAccountWallet_Name(account_id,
                                           signer_nym,
                                           data)
        self.item(row, self.ACCOUNT).setText(data)
        self.dataChanged.emit(index, index)
        return True

model = OTAccountsModel()
        

class OTAccountsProxyModel(QtGui.QSortFilterProxyModel, _OTAccountsModel):

    def refresh(self):
        self.sourceModel().refresh()


class OTAccountsServerModel(OTAccountsProxyModel):

    def __init__(self, serverId=None, parent=None):
        super(OTAccountsServerModel, self).__init__(parent)
        source_model = model # model global defined above
        self.setSourceModel(source_model)
        self.setFilterKeyColumn(OTAccountsModel.SERVER)
        self.setFilterRole(QtCore.Qt.UserRole)
        self.setDynamicSortFilter(True)
        if serverId:
            self.setFilterFixedString(serverId)

    def setServer(self, serverId):
        self.setFilterFixedString(serverId)


class OTAccountsSimpleModel(OTAccountsProxyModel):

    def __init__(self, parent=None):
        super(OTAccountsSimpleModel, self).__init__(parent)
        source_model = model # model global defined above
        self.setSourceModel(source_model)
        self.setFilterKeyColumn(source_model.TYPE)
        self.setFilterRole(QtCore.Qt.UserRole)
        self.setFilterFixedString('s')
        self.setDynamicSortFilter(True)
