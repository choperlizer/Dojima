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

import logging
from PyQt4 import QtCore, QtGui

import tulpenmanie.bitcoin
import tulpenmanie.translate


class BitcoinDepositAction(QtGui.QAction):

    def __init__(self, parent):
        super(BitcoinDepositAction, self).__init__(
            QtCore.QCoreApplication.translate("BitcoinDepositAction",
                                              "exchange &deposit addresses"),
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


actions = (BitcoinDepositAction, BitcoinTransferAction,)


class TransferDialog(QtGui.QDialog):

    def __init__(self, parent):
        super(TransferDialog, self).__init__(parent)

        self.withdraw_combo = QtGui.QComboBox(self)
        self.deposit_combo = QtGui.QComboBox(self)
        self.amount_spin = QtGui.QDoubleSpinBox(self)
        self.amount_spin.setMaximum(21000000)
        self.amount_spin.setDecimals(8)
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
        for exchange_name, exchange_dict in parent.exchanges.items():
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
        self.log_view.insertPlainText(str(QtCore.QCoreApplication.translate(
            "BitcoinDialog", "requesting deposit address from %s... \n\t"))
            % (self.deposit_combo.currentText()))
        deposit_account.bitcoin_deposit_address_signal.connect(
            self._receive_deposit_address)
        deposit_account.get_bitcoin_deposit_address()
        for widget in self.widgets_to_toggle:
            widget.setEnabled(False)

    def _receive_deposit_address(self, address):
        valid_version = tulpenmanie.bitcoin.validate_address(address)
        if valid_version is None:
            self.log_view.appendPlainText(QtCore.QCoreApplication.translate(
                "BitcoinDialog", "deposit address failed verification"))
            self._reset()
            return

        self.log_view.appendPlainText(str(QtCore.QCoreApplication.translate(
            "BitcoinDialog", "deposit address %s is a valid version %s address"))
            % (address, valid_version))
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


class GetDepositAddressDialog(QtGui.QDialog):

    def __init__(self, parent):
        super(GetDepositAddressDialog, self).__init__(parent)

        self.exchange_combo = QtGui.QComboBox()
        self.accounts = list()
        self.request_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate("GetDepositAddressDialog",
                                              "request"))
        self.address_view = QtGui.QLineEdit()
        self.address_view.setReadOnly(True)
        self.address_view.setMinimumWidth(280)

        close_button_box = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Close)

        layout = QtGui.QGridLayout()
        layout.setColumnStretch(0, 1)
        layout.addWidget(self.exchange_combo, 0,0)
        layout.addWidget(self.request_button, 0,1)
        layout.addWidget(self.address_view, 1,0, 1,2)
        layout.addWidget(close_button_box, 2,0, 1,2)
        self.setLayout(layout)

        for exchange_name, exchange_dict in parent.exchanges.items():
            if 'account' not in exchange_dict:
                continue
            account_object = exchange_dict['account']
            if not account_object:
                continue
            if hasattr(account_object, 'get_bitcoin_deposit_address'):
                self.exchange_combo.addItem(exchange_name)
                self.accounts.append(account_object)

        self.request_button.clicked.connect(self._request)
        close_button_box.rejected.connect(self.reject)

    def _request(self):
        self.exchange_combo.setEnabled(False)
        self.request_button.setEnabled(False)
        self.address_view.clear()

        index = self.exchange_combo.currentIndex()
        account_obj = self.accounts[index]
        account_obj.bitcoin_deposit_address_signal.connect(self._process_address)
        account_obj.get_bitcoin_deposit_address()

    def _process_address(self, address):
        if tulpenmanie.bitcoin.validate_address(address) is None:
            self.address_view.setText(QtCore.QCoreApplication.translate(
                "GetDepositAddressDialog", "received invalid address"))
            return

        self.address_view.setText(address)
        self.exchange_combo.setEnabled(True)
        self.request_button.setEnabled(True)
