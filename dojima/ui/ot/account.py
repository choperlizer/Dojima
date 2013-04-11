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

import dojima.model.ot.nyms
import dojima.model.ot.accounts

objEasy = None

logger = logging.getLogger(__name__)

"""
# TODO get the factor and decorators for the account balances, or else
# this is going to get confusing

class MarketAccountsDialog(QtGui.QDialog):

    def __init__(self, server_id, base_id, counter_id, parent=None):
        super(MarketAccountsDialog, self).__init__(parent)
        self.server_id = server_id
        self.base_id = base_id
        self.counter_id = counter_id

        form_layout = QtGui.QFormLayout()
        self.nym_combo = QtGui.QComboBox()
        form_layout.addRow(
            QtCore.QCoreApplication.translate('MarketAccountDialog',
                                              "default nym"),
            self.nym_combo)

        self.base_combo = QtGui.QComboBox()
        form_layout.addRow(otapi.OTAPI_Basic_GetAssetType_Name(base_id),
                           self.base_combo)

        new_base_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate('MarketAccountDialog',
                                              "new account",
                                              "new base account"))
        form_layout.addRow("", new_base_button)

        self.counter_combo = QtGui.QComboBox()
        form_layout.addRow(otapi.OTAPI_Basic_GetAssetType_Name(counter_id),
                           self.counter_combo)

        new_counter_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate('MarketAccountDialog',
                                              "new account",
                                              "new counter account"))
        form_layout.addRow("", new_counter_button)

        button_box = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok |
                                            QtGui.QDialogButtonBox.Cancel)

        layout = QtGui.QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addWidget(button_box)
        self.setLayout(layout)

        self.nym_combo.currentIndexChanged[int].connect(self.changeNym)
        new_base_button.clicked.connect(self.newBaseAccount)
        new_counter_button.clicked.connect(self.newCounterAccount)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        # populate combos

        nyms_model = dojima.model.ot.nyms.OTNymsModel()
        self.nym_combo.setModel(nyms_model)

        self.accounts_model = dojima.model.ot.accounts.OTAccountsModel()

        self.server_accounts_model = QtGui.QSortFilterProxyModel()
        self.server_accounts_model.setSourceModel(self.accounts_model)
        self.server_accounts_model.setFilterRole(QtCore.Qt.UserRole)
        self.server_accounts_model.setFilterKeyColumn(
            self.accounts_model.SERVER)
        self.server_accounts_model.setFilterFixedString(server_id)
        self.server_accounts_model.setDynamicSortFilter(True)

        assert(True)
        assert(True)
        assert(True)
        assert(True)
        assert(True)
        assert(True)
        assert(True)
        assert(True)
        assert(True)
        assert(True)
        assert(True)
        assert(True)
        assert(True)
        assert(True)

        # Strange interpreter bug

        self.nym_accounts_model = QtGui.QSortFilterProxyModel()
        self.nym_accounts_model.setSourceModel(self.server_accounts_model)
        self.nym_accounts_model.setFilterRole(QtCore.Qt.UserRole)
        self.nym_accounts_model.setFilterKeyColumn(self.accounts_model.NYM)
        self.nym_accounts_model.setDynamicSortFilter(True)

        self.base_accounts_model = QtGui.QSortFilterProxyModel()
        self.base_accounts_model.setSourceModel(self.nym_accounts_model)
        self.base_accounts_model.setFilterRole(QtCore.Qt.UserRole)
        self.base_accounts_model.setFilterKeyColumn(
            self.accounts_model.ASSET)
        self.base_accounts_model.setFilterFixedString(base_id)
        self.base_accounts_model.setDynamicSortFilter(True)

        self.counter_accounts_model = QtGui.QSortFilterProxyModel()
        self.counter_accounts_model.setSourceModel(self.nym_accounts_model)
        self.counter_accounts_model.setFilterRole(QtCore.Qt.UserRole)
        self.counter_accounts_model.setFilterKeyColumn(
            self.accounts_model.ASSET)
        self.counter_accounts_model.setFilterFixedString(counter_id)
        self.counter_accounts_model.setDynamicSortFilter(True)

        self.base_combo.setModel(self.base_accounts_model)
        self.counter_combo.setModel(self.counter_accounts_model)
        self.base_combo.setModelColumn(self.accounts_model.ACCOUNT)
        self.counter_combo.setModelColumn(self.accounts_model.ACCOUNT)

        self.changeNym(0)

    def changeNym(self, row):
        nym_id = self.nym_combo.itemData(row, QtCore.Qt.UserRole)
        # this model apparently isn't in scope
        self.nym_accounts_model.setFilterFixedString(nym_id)

    def getNymId(self):
        row = self.nym_combo.currentIndex()
        return self.nym_combo.itemData(row, QtCore.Qt.UserRole)

    def getBaseAccountId(self):
        row = self.base_combo.currentIndex()
        return self.base_combo.itemData(row, QtCore.Qt.UserRole)

    def getCounterAccountId(self):
        row = self.base_combo.currentIndex()
        return self.counter_combo.itemData(row, QtCore.Qt.UserRole)

    def getAccountLabel(self, account_id):
        # TODO move the balance display to a dedicated widget
        # showing the balance is nice but if the balances are factored
        # down they'll look funny
        name = otapi.OTAPI_Basic_GetAccountWallet_Name(account_id)
        balance = otapi.OTAPI_Basic_GetAccountWallet_Balance(account_id)
        return QtCore.QCoreApplication.translate('MarketAccountsDialog',
            "%1 - %2", "name, balance").arg(name).arg(balance)

    def newBaseAccount(self):
        dialog = NewAccountDialog(self.server_id, self.base_id, self)
        if dialog.exec_():
            self.base_accounts_model.sort(self.accounts_model.NAME)

    def newCounterAccount(self):
        dialog = NewAccountDialog(self.server_id, self.counter_id, self)
        if dialog.exec_():
            self.counter_accounts_model.sort(self.accounts_model.NAME)
"""

class NewAccountDialog(QtGui.QDialog):

    tradesRequestSignal = QtCore.pyqtSignal(str)

    def __init__(self, server_id, parent):
        super(NewAccountDialog, self).__init__(parent)
        self.server_id = server_id

        nyms_model = dojima.model.ot.nyms.OTNymsModel()
        assets_model = dojima.model.ot.assets.OTAssetsModel()

        server_label = QtGui.QLabel(otapi.OTAPI_Basic_GetServer_Name(server_id))
        self.nym_combo = QtGui.QComboBox()
        self.nym_combo.setModel(nyms_model)
        self.asset_combo = QtGui.QComboBox()
        self.asset_combo.setModel(assets_model)
        #asset_label = QtGui.QLabel(otapi.OTAPI_Basic_GetAssetType_Name(asset_id))
        self.name_edit = QtGui.QLineEdit(self)

        register_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate('NewAccountDialog', "Register"),
            self)
        button_box = QtGui.QDialogButtonBox()
        button_box.addButton(register_button, button_box.ActionRole)
        button_box.addButton(QtGui.QDialogButtonBox.Cancel)

        register_button.clicked.connect(self.register)
        button_box.rejected.connect(self.reject)

        layout = QtGui.QVBoxLayout()
        form_layout = QtGui.QFormLayout()
        form_layout.addRow(
            QtCore.QCoreApplication.translate('NewAccountDialog', "server:"),
            server_label)
        form_layout.addRow(
            QtCore.QCoreApplication.translate('NewAccountDialog', "nym:"),
            self.nym_combo)
        form_layout.addRow(
            QtCore.QCoreApplication.translate('NewAccountDialog', "asset:"),
            self.asset_combo)
        form_layout.addRow(
            QtCore.QCoreApplication.translate('NewAccountDialog', "label:"),
            self.name_edit)
        layout.addLayout(form_layout)
        layout.addWidget(button_box)
        self.setLayout(layout)

    def register(self):
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        error_title = QtCore.QCoreApplication.translate('NewAccountDialog',
                                                        "Error")
        nym_id = self.nym_combo.itemData(self.nym_combo.currentIndex(),
                                         QtCore.Qt.UserRole)
        asset_id = self.asset_combo.itemData(self.asset_combo.currentIndex(),
                                             QtCore.Qt.UserRole)

        # get the account ids so we can tell which is the new one
        account_ids = list()
        for i in range(otapi.OTAPI_Basic_GetAccountCount()):
            account_ids.append(otapi.OTAPI_Basic_GetAccountWallet_ID(i))

        # register the nym if needed
        if not otapi.OTAPI_Basic_IsNym_RegisteredAtServer(nym_id,
                                                     self.server_id):
            logger.info("registering %s at %s", nym_id, self.server_id)
            msg = objEasy.register_nym(self.server_id, nym_id)
            if objEasy.VerifyMessageSuccess(msg) < 1:
                QtGui.QApplication.restoreOverrideCursor()
                QtGui.QMessageBox.warning(self, error_title,
                QtCore.QCoreApplication.translate('NewAccountDialog'
                    "Error registering the nym with the server."))
                return

        logger.info("opening account at %s", self.server_id)
        msg = objEasy.create_asset_acct(self.server_id, nym_id, asset_id)
        if objEasy.VerifyMessageSuccess(msg) < 1:
            QtGui.QApplication.restoreOverrideCursor()
            QtGui.QMessageBox.warning(self, error_title,
                QtCore.QCoreApplication.translate('NewAccountDialog',
                                                  "Error registering account."))
            self.setEnabled(True)
            return

        # look through and find the new account_id
        for i in range(otapi.OTAPI_Basic_GetAccountCount()):
            account_id = otapi.OTAPI_Basic_GetAccountWallet_ID(i)
            if account_id not in account_ids:
                break

        otapi.OTAPI_Basic_SetAccountWallet_Name(account_id, nym_id,
                                                self.name_edit.text())


        QtGui.QApplication.restoreOverrideCursor()
        self.accept()
