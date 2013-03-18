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

import dojima.ui.ot.views
from dojima.ot import objEasy


class InitiateTransferAction(QtGui.QAction):

    def __init__(self, parent):
        super(InitiateTransferAction, self).__init__(
            QtCore.QCoreApplication.translate('OTTransferDialog',
                                              "Initiate Transfer",
                                              "The menu action to trigger the "
                                              "InitiateTransferDialog"),
                                              parent)
        self.triggered.connect(self.show_dialog)

    def show_dialog(self):
        dialog = InitiateTransferDialog(self.parent())
        dialog.show()


class ChequeCreateAction(QtGui.QAction):

    def __init__(self, parent):
        super(ChequeCreateAction, self).__init__(
            QtCore.QCoreApplication.translate('ChequeCreateDialog',
                                              "Write Cheque",
                                              "The menu action to trigger the "
                                              "ChequeCreateDialog"),
                                              parent)
        self.triggered.connect(self.show_dialog)

    def show_dialog(self):
        dialog = ChequeCreateDialog(self.parent())
        dialog.show()


class CashWithdrawAction(QtGui.QAction):

    def __init__(self, parent):
        super(CashWithdrawAction, self).__init__(
            QtCore.QCoreApplication.translate('ChequeCreateDialog',
                                              "Cash Withdraw",
                                              "The menu action to trigger the "
                                              "CashWithdrawDialog"),
                                              parent)
        self.triggered.connect(self.show_dialog)

    def show_dialog(self):
        dialog = CashWithdrawDialog(self.parent())
        dialog.show()


actions = (InitiateTransferAction,
           ChequeCreateAction,
           CashWithdrawAction,)


class _TransferDialog():

    def accountChanged(self, ot_id):
        ot_id = otapi.OTAPI_Basic.GetAccountWallet_AssetTypeID( str(ot_id))
        contract = dojima.ot.contract.CurrencyContract(ot_id)
        self.amount_spin.setFactor(contract.getFactor())


class InitiateTransferDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        super(InitiateTransferDialog, self).__init__(parent)

        self.server_combo  = dojima.ui.ot.views.ComboBox()
        self.account_combo = dojima.ui.ot.views.ComboBox()
        self.recipient_edit = QtGui.QLineEdit()
        self.amount_spin = dojima.ui.widget.AssetSpinBox()
        memo_label = QtGui.QLabel(
            QtCore.QCoreApplication.translate('InitiateTransferDialog',
                                              "Memo:",
                                              "The label for the "
                                              "memo entry box."))
        self.memo_edit = QtGui.QPlainTextEdit()
        memo_label.setBuddy(self.memo_edit)

        self.transfer_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate('InitiateTransferDialog',
                                              "&Transfer",
                                              "The label on the transfer button."))

        button_box = QtGui.QDialogButtonBox()
        button_box.addButton(button_box.Close)
        button_box.addButton(self.transfer_button, button_box.ActionRole)

        layout = QtGui.QFormLayout()
        layout.addRow(QtCore.QCoreApplication.translate('InitiateTransferDialog',
                                                        "Server:",
                                                        "Label for the server combo."),
                                                        self.server_combo)

        layout.addRow(QtCore.QCoreApplication.translate('InitiateTransferDialog',
                                                        "From:",
                                                        "Label for the account combo."),
                                                        self.account_combo)

        layout.addRow(QtCore.QCoreApplication.translate('InitiateTransferDialog',
                                                        "To:",
                                                        "Label for the transfer "
                                                        "recipient account edit."),
                                                        self.recipient_edit)

        layout.addRow(QtCore.QCoreApplication.translate('InitiateTransferDialog',
                                                        "Amount:",
                                                        "Label for transsfer amount "
                                                        "spin."),
                                                        self.amount_spin)

        layout.addRow(memo_label)
        layout.addRow(self.memo_edit)
        layout.addRow(button_box)
        self.setLayout(layout)

        self.server_combo.setModel(dojima.model.ot.servers.model)
        base_accounts_model = dojima.model.ot.accounts.OTAccountsModel()

        self.accounts_model = dojima.model.ot.accounts.OTAccountsProxyModel()
        self.accounts_model.setSourceModel(base_accounts_model)
        self.accounts_model.setFilterRole(QtCore.Qt.UserRole)
        self.accounts_model.setFilterKeyColumn(base_accounts_model.SERVER)
        self.accounts_model.setDynamicSortFilter(True)
        self.account_combo.setModel(self.accounts_model)

        self.server_combo.otIdChanged.connect(self.accounts_model.setFilterFixedString)
        self.account_combo.otIdChanged.connect(self.accountChanged)

        self.transfer_button.clicked.connect(self.transfer)
        button_box.rejected.connect(self.reject)

        self.server_combo.emitOTID(0)
        self.account_combo.emitOTID(0)

    def accountChanged(self, ot_id):
        ot_id = otapi.OTAPI_Basic.GetAccountWallet_AssetTypeID(ot_id)
        contract = dojima.ot.contract.CurrencyContract(ot_id)
        self.amount_spin.setFactor(contract.getFactor())

    def transfer(self):
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        server_id = self.server_combo.getOTID()
        from_id = self.account_combo.getOTID()
        to_id = self.recipient_edit.text()
        nym_id = otapi.OTAPI_Basic_GetAccountWallet_NymID(from_id)
        #TODO make get string method at the spin box
        amount = self.amount_spin.value()
        note = self.memo_edit.toPlainText()
        msg = objEasy.send_transfer(server_id, nym_id, from_id, to_id, amount, note)
        if objEasy.VerifyMsgTrnxSuccess(server_id, nym_id, from_id, msg) < 1:
            QtGui.QMessageBox.warning(
                self,
                QtCore.QCoreApplication.translate('InitiateTransferDialog',
                                                  "Transfer Failed",
                                                  "The title bar of the transfer failed "
                                                  "popup."),
                QtCore.QCoreApplication.translate('InitiateTransferDialog',
                                                  "Failed to send transfer.",
                                                  "The failed transfer "
                                                  "popup dialog text."))

            QtGui.QApplication.restoreOverrideCursor()
            return

        print(msg)

        # Test if this is a local account
        nym_id = otapi.OTAPI_Basic_GetAccountWallet_NymID(to_id)
        if not nym_id:
            QtGui.QApplication.restoreOverrideCursor()
            self.accept()
            return

        # nym_id is now the recipient nym
        objEasy.retrieve_account(server_id, nym_id, to_id)




        QtGui.QApplication.restoreOverrideCursor()
        self.accept()

        #TODO show receipt after transfer

class ChequeCreateDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        super(ChequeCreateDialog, self).__init__(parent)

        self.server_combo = dojima.ui.ot.views.ComboBox()
        self.account_combo = dojima.ui.ot.views.ComboBox()
        self.recipient_edit = QtGui.QLineEdit(
            placeholderText=QtCore.QCoreApplication.translate('ChequeCreateDialog',
                                                              "None"))
        self.valid_from_edit = QtGui.QDateTimeEdit()
        self.expiry_check = QtGui.QCheckBox()
        self.valid_to_edit = QtGui.QDateTimeEdit()
        self.valid_to_edit.setDisabled(True)
        self.amount_spin = dojima.ui.widget.AssetSpinBox()
        memo_label = QtGui.QLabel(
            QtCore.QCoreApplication.translate('ChequeCreateDialog',
                                              "Memo:",
                                              "The label for the "
                                              "memo entry box."))
        self.memo_edit = QtGui.QPlainTextEdit()
        memo_label.setBuddy(self.memo_edit)
        self.cheque_view = QtGui.QPlainTextEdit(readOnly=True)

        self.create_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate('ChequeCreateDialog',
                                              "&Write",
                                              "The label on the create/write "
                                              "button."))

        button_box = QtGui.QDialogButtonBox()
        button_box.addButton(button_box.Close)
        button_box.addButton(self.create_button, button_box.ActionRole)

        layout = QtGui.QFormLayout()
        layout.addRow(QtCore.QCoreApplication.translate('ChequeCreateDialog',
                                                        "Server:",
                                                        "the OT server"),
                                                        self.server_combo)

        layout.addRow(QtCore.QCoreApplication.translate('ChequeCreateDialog',
                                                        "Account:",
                                                        "the account from"),
                                                        self.account_combo)

        layout.addRow(QtCore.QCoreApplication.translate('ChequeCreateDialog',
                                                        "Recipient:",
                                                        "the optional cheque "
                                                        "recipient"),
                                                        self.recipient_edit)


        layout.addRow(QtCore.QCoreApplication.translate('ChequeCreateDialog',
                                                        "Valid From:",
                                                        "cheque valid from"),
                                                        self.valid_from_edit)

        layout.addRow(QtCore.QCoreApplication.translate('ChequeCreateDialog',
                                                        "Expires:",
                                                        "shall the check expire"),
                                                        self.expiry_check)

        layout.addRow(QtCore.QCoreApplication.translate('ChequeCreateDialog',
                                                        "Valid To:",
                                                        "cheque valid to"),
                                                        self.valid_to_edit)

        layout.addRow(QtCore.QCoreApplication.translate('ChequeCreateDialog',
                                                        "Amount:",
                                                        "cheque amount"),
                                                        self.amount_spin)

        layout.addRow(memo_label)
        layout.addRow(self.memo_edit)
        layout.addRow(self.cheque_view)
        layout.addRow(button_box)
        self.setLayout(layout)

        self.server_combo.setModel(dojima.model.ot.servers.model)
        base_accounts_model = dojima.model.ot.accounts.OTAccountsModel()

        self.accounts_model = dojima.model.ot.accounts.OTAccountsProxyModel()
        self.accounts_model.setSourceModel(base_accounts_model)
        self.accounts_model.setFilterRole(QtCore.Qt.UserRole)
        self.accounts_model.setFilterKeyColumn(base_accounts_model.SERVER)
        self.accounts_model.setDynamicSortFilter(True)
        self.account_combo.setModel(self.accounts_model)

        self.server_combo.otIdChanged.connect(self.accounts_model.setFilterFixedString)
        self.account_combo.otIdChanged.connect(self.accountChanged)
        self.expiry_check.stateChanged.connect(self.valid_to_edit.setEnabled)

        self.create_button.clicked.connect(self.createCheque)
        button_box.rejected.connect(self.reject)

        self.server_combo.emitOTID(0)
        self.account_combo.emitOTID(0)

        # connect the account combo to the asset spin, so factor gets set

    def accountChanged(self, ot_id):
        ot_id = otapi.OTAPI_Basic.GetAccountWallet_AssetTypeID(ot_id)
        contract = dojima.ot.contract.CurrencyContract(ot_id)
        self.amount_spin.setFactor(contract.getFactor())

    def createCheque(self):
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        server_id = self.server_combo.getOTID()
        #TODO make get string method at the spin box
        amount = self.amount_spin.value()
        valid_from, valid_to = "", ""
        account_id = self.account_combo.getOTID()
        nym_id = otapi.OTAPI_Basic_GetAccountWallet_NymID(account_id)
        memo = self.memo_edit.toPlainText()
        recipient = self.recipient_edit.text()

        cheque = otapi.OTAPI_Basic_WriteCheque(server_id, amount, valid_from, valid_to,
                                               account_id, nym_id, memo, recipient)
        self.cheque_view.setPlainText(cheque)
        QtGui.QApplication.restoreOverrideCursor()


class CashWithdrawDialog(QtGui.QDialog, _TransferDialog):

    def __init__(self, parent=None):
        super(CashWithdrawDialog, self).__init__(parent)

        self.server_combo  = dojima.ui.ot.views.ComboBox()
        self.account_combo = dojima.ui.ot.views.ComboBox()
        self.amount_spin = dojima.ui.widget.AssetSpinBox()

        withdraw_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate('CashWithdrawDialog',
                                              "Withdraw",
                                              "The label on the withdraw button."))

        button_box = QtGui.QDialogButtonBox()
        button_box.addButton(withdraw_button, button_box.ActionRole)
        button_box.addButton(button_box.Cancel)

        layout = QtGui.QFormLayout()
        layout.addRow(QtCore.QCoreApplication.translate('CashWithdrawDialog',
                                                        "Server:",
                                                        "The label of the server combo, "
                                                        "that is the server to withdraw "
                                                        "cash from."),
                                                        self.server_combo)

        layout.addRow(QtCore.QCoreApplication.translate('CashWithdrawDialog',
                                                       "Account:",
                                                       "The label of the account combo. "
                                                       "This account that the cash comes "
                                                       "from."),
                                                       self.account_combo)

        layout.addRow(QtCore.QCoreApplication.translate('CashWithdrawDialog',
                                                        "Amount:",
                                                        "The label for the withdraw "
                                                        "amount spin."),
                                                        self.amount_spin)
        layout.addRow(button_box)
        self.setLayout(layout)

        self.server_combo.setModel(dojima.model.ot.servers.model)

        self.accounts_model = dojima.model.ot.accounts.OTAccountsServerModel()
        self.account_combo.setModel(self.accounts_model)

        self.server_combo.otIdChanged.connect(self.accounts_model.setServer)
        self.account_combo.otIdChanged.connect(self.accountChanged)

        withdraw_button.clicked.connect(self.withdraw)
        button_box.rejected.connect(self.reject)

    def withdraw(self):
        amount = self.amount_spin.value()
        if amount < 1:
            return

        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        server_id  = self.server_combo.getOTID()
        account_id = self.account_combo.getOTID()
        nym_id = otapi.OTAPI_Basic_GetAccountWallet_NymID(account_id)
        amount = str(amount)

        msg = objEasy.withdraw_cash(server_id, nym_id, account_id, amount)
        QtGui.QApplication.restoreOverrideCursor()

        if objEasy.VerifyMessageSuccess(msg) < 1:
            QtGui.QMessageBox.warning(
                self,
                QtCore.QCoreApplication.translate('CashWithdrawDialog',
                                                  "Withdraw Failed",
                                                  "The title bar of the cash withdraw failed "
                                                  "popup."),
                QtCore.QCoreApplication.translate('InitiateTransferDialog',
                                                  "Failed to withdraw cash.",
                                                  "The failed cash withdraw "
                                                  "popup dialog text."))

            self.reject()

        else:
            self.accept()
