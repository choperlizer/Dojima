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
from PyQt4 import QtCore, QtGui

import dojima.bitcoin


class BitcoinDepositAction(QtGui.QAction):

    def __init__(self, parent):
        super(BitcoinDepositAction, self).__init__(
            QtCore.QCoreApplication.translate("BitcoinDepositAction",
                                              "&deposit"),
                                              parent)
        self.triggered.connect(self._show_dialog)

    def _show_dialog(self):
        dialog = GetDepositAddressDialog(self.parent())
        dialog.show()


class BitcoinTransferAction(QtGui.QAction):

    def __init__(self, parent):
        super(BitcoinTransferAction, self).__init__(
            QtCore.QCoreApplication.translate("BitcoinTransferAction",
                                              "inter-exchange &transfer"),
                                              parent)
        self.triggered.connect(self._show_dialog)

    def _show_dialog(self):
        dialog = TransferDialog(self.parent())
        dialog.show()


class BitcoinWithdrawAction(QtGui.QAction):

    def __init__(self, parent):
        super(BitcoinWithdrawAction, self).__init__(
            QtCore.QCoreApplication.translate("BitcoinWithdrawAction",
                                              "&withdraw"),
                                              parent)
        self.triggered.connect(self._show_dialog)

    def _show_dialog(self):
        dialog = WithdrawDialog(self.parent())
        dialog.show()

actions = (BitcoinDepositAction, BitcoinTransferAction, BitcoinWithdrawAction)



class GetDepositAddressDialog(QtGui.QDialog):

    def __init__(self, parent):
        super(GetDepositAddressDialog, self).__init__(parent)

        self.exchange_combo = QtGui.QComboBox()
        self.accounts = list()
        self.request_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate("GetDepositAddressDialog",
                                              "get address"))
        self.address_view = QtGui.QLineEdit()
        self.address_view.setReadOnly(True)
        self.address_view.setMinimumWidth(280)

        button_box = QtGui.QDialogButtonBox()

        layout = QtGui.QGridLayout()
        layout.setColumnStretch(0, 1)
        layout.addWidget(self.exchange_combo, 0,0)
        layout.addWidget(self.request_button, 0,1)
        layout.addWidget(self.address_view, 1,0, 1,2)
        layout.addWidget(button_box, 2,0, 1,2)
        self.setLayout(layout)

        for exchange_name, exchange_dict in list(parent.exchanges.items()):
            if 'account' not in exchange_dict:
                continue
            account_object = exchange_dict['account']
            if not account_object:
                continue
            if hasattr(account_object, 'get_bitcoin_deposit_address'):
                self.exchange_combo.addItem(exchange_name)
                self.accounts.append(account_object)

        self.request_button.clicked.connect(self._request)
        button_box.rejected.connect(self.reject)

    def _request(self):
        self.exchange_combo.setEnabled(False)
        self.request_button.setEnabled(False)
        self.address_view.clear()

        index = self.exchange_combo.currentIndex()
        account_obj = self.accounts[index]
        account_obj.bitcoin_deposit_address_signal.connect(self._process_address)
        account_obj.get_bitcoin_deposit_address()

    def _process_address(self, address):
        if not dojima.bitcoin.is_valid_address(address):
            self.address_view.setText(QtCore.QCoreApplication.translate(
                "GetDepositAddressDialog", "received invalid address",
                "try and make 34 characters or less in length."))
            return

        self.address_view.setText(address)
        self.exchange_combo.setEnabled(True)
        self.request_button.setEnabled(True)


class TransferDialog(QtGui.QDialog):

    def __init__(self, parent):
        super(TransferDialog, self).__init__(parent)

        self.withdraw_combo = QtGui.QComboBox(self)
        self.deposit_combo = QtGui.QComboBox(self)
        self.amount_spin = dojima.widget.BitcoinSpin(self)
        self.log_view = QtGui.QPlainTextEdit(self)
        self.log_view.setReadOnly(True)

        self.transfer_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate("bitcoin transfer dialog",
                                              "transfer"))
        self.cancel_button = QtGui.QDialogButtonBox.Cancel
        button_box = QtGui.QDialogButtonBox()
        button_box.addButton(self.transfer_button,
                             QtGui.QDialogButtonBox.ActionRole)
        button_box.addButton(self.cancel_button)

        upper_layout = QtGui.QFormLayout()
        upper_layout.addRow(QtCore.QCoreApplication.translate(
            "bitcoin transfer dialog", "withdraw:"), self.withdraw_combo)
        upper_layout.addRow(QtCore.QCoreApplication.translate(
            "bitcoin transfer dialog", "deposit:"), self.deposit_combo)
        upper_layout.addRow(QtCore.QCoreApplication.translate(
            "bitcoin transfer dialog", "amount:"), self.amount_spin)
        layout = QtGui.QVBoxLayout()
        layout.addLayout(upper_layout)
        layout.addWidget(self.log_view)
        layout.addWidget(button_box)
        self.setLayout(layout)

        self.withdraw_combo.currentIndexChanged.connect(self._check_exchanges)
        self.deposit_combo.currentIndexChanged.connect(self._check_exchanges)

        self.transfer_button.clicked.connect(self._transfer)
        button_box.rejected.connect(self.reject)

        self.widgets_to_toggle = (self.withdraw_combo,
                                  self.deposit_combo,
                                  self.amount_spin,
                                  self.transfer_button)

        self.withdraw_accounts = list()
        self.deposit_accounts = list()
        for exchange_name, exchange_dict in list(parent.exchanges.items()):
            if 'account' not in exchange_dict:
                continue
            account_object = exchange_dict['account']
            if not account_object:
                continue
            if hasattr(account_object, 'withdraw_bitcoin'):
                self.withdraw_combo.addItem(exchange_name)
                self.withdraw_accounts.append(account_object)

            if hasattr(account_object, 'get_bitcoin_deposit_address'):
                self.deposit_combo.addItem(exchange_name)
                self.deposit_accounts.append(account_object)

    def _check_exchanges(self, ignored):
        withdraw_exchange = self.withdraw_combo.currentText()
        deposit_exchange = self.deposit_combo.currentText()
        enable_state = (withdraw_exchange != deposit_exchange)
        self.transfer_button.setEnabled(enable_state)

    def _transfer(self):
        deposit_index = self.deposit_combo.currentIndex()
        deposit_account = self.deposit_accounts[deposit_index]
        self.log_view.insertPlainText(QtCore.QCoreApplication.translate(
            "BitcoinDialog", "requesting deposit address from %1... \n\t").arg(
                self.deposit_combo.currentText()))
        deposit_account.bitcoin_deposit_address_signal.connect(
            self._receive_deposit_address)
        deposit_account.get_bitcoin_deposit_address()
        for widget in self.widgets_to_toggle:
            widget.setEnabled(False)

    def _receive_deposit_address(self, address):
        if not dojima.bitcoin.is_valid_address(address):
            self.log_view.appendPlainText(QtCore.QCoreApplication.translate(
                "BitcoinDialog", "deposit address failed verification"))
            self._reset()
            return

        self.log_view.appendPlainText(QtCore.QCoreApplication.translate(
            "BitcoinDialog", "deposit address validated"))
        amount = self.amount_spin.value()

        withdraw_index = self.withdraw_combo.currentIndex()
        withdraw_account = self.withdraw_accounts[withdraw_index]
        withdraw_account.withdraw_bitcoin_reply_signal.connect(
            self._receive_reply)
        withdraw_account.withdraw_bitcoin(address, amount)

    def _receive_reply(self, reply):
        self.log_view.appendPlainText(reply)
        self._reset()

    def _reset(self):
        for widget in self.widgets_to_toggle:
            widget.setEnabled(True)


class WithdrawDialog(QtGui.QDialog):

    def __init__(self, parent):
        super(WithdrawDialog, self).__init__(parent)

        self.exchange_combo = QtGui.QComboBox()
        self.accounts = list()
        self.address_edit = QtGui.QLineEdit()
        self.address_edit.setMinimumWidth(280)
        self.address_edit.setPlaceholderText
        self.amount_spin = dojima.widget.BitcoinSpin()
        self.log_view = QtGui.QPlainTextEdit()
        self.log_view.setReadOnly(True)

        self.withdraw_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate("WithdrawDialog",
                                              "withdraw"))
        button_box = QtGui.QDialogButtonBox()
        button_box.addButton(self.withdraw_button,
                             QtGui.QDialogButtonBox.ActionRole)
        button_box.addButton(QtGui.QDialogButtonBox.Close)

        self.input_widgets = (self.exchange_combo, self.address_edit,
                              self.amount_spin, self.withdraw_button)

        entry_layout = QtGui.QFormLayout()
        entry_layout.addRow(QtCore.QCoreApplication.translate(
            "WithdrawDialog", "destination address"),
            self.address_edit)
        entry_layout.addRow(QtCore.QCoreApplication.translate(
            "WithdrawDialog", "amount"),
            self.amount_spin)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.exchange_combo)
        layout.addLayout(entry_layout)
        layout.addWidget(self.log_view)
        layout.addWidget(button_box)
        self.setLayout(layout)

        for exchange_name, exchange_dict in list(parent.exchanges.items()):
            if 'account' not in exchange_dict:
                continue
            account_object = exchange_dict['account']
            if not account_object:
                continue
            if hasattr(account_object, 'withdraw_bitcoin'):
                self.exchange_combo.addItem(exchange_name)
                self.accounts.append(account_object)

        self.withdraw_button.clicked.connect(self.withdraw)
        button_box.rejected.connect(self.reject)

    def withdraw(self):
        for widget in self.input_widgets:
            widget.setEnabled(False)

        index = self.exchange_combo.currentIndex()
        account_obj = self.accounts[index]
        account_obj.withdraw_bitcoin_reply_signal.connect(self.receive_reply)
        address = self.address_edit.text()
        if dojima.bitcoin.is_valid_address(address):
            amount = self.amount_spin.value()
            account_obj.withdraw_bitcoin(address, amount)
            self.log_view.appendPlainText(QtCore.QCoreApplication.translate(
                "WithdrawDialog", "address validated"))
            self.log_view.appendPlainText(QtCore.QCoreApplication.translate(
                "WithdrawDialog", "requesting withdraw from %1...").arg(
                    self.exchange_combo.currentText()))
        else:
            self.log_view.appendPlainText(QtCore.QCoreApplication.translate(
                "WithdrawDialog", "address failed verification"))
            self.reset()

    def receive_reply(self, reply):
        self.log_view.appendPlainText(reply)
        self.reset()

    def reset(self):
        for widget in self.input_widgets:
            widget.setEnabled(True)
