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

import dojima.model.ot.accounts
import dojima.ui.ot.nym
import dojima.ui.ot.views
import dojima.ui.widget

#TODO trim debugger
import pdb

class NewOfferDialog(QtGui.QDialog):

    def __init__(self, server_id, parent=None):
        super(NewOfferDialog, self).__init__(parent)

        self.server_id = server_id
        assert self.server_id
        self.nym_combo = dojima.ui.ot.views.ComboBox()
        self.base_account_combo = dojima.ui.ot.views.ComboBox()
        self.counter_account_combo = dojima.ui.ot.views.ComboBox()
        self.scale_spin = dojima.ui.widget.ScaleSpin()
        self.price_spin = dojima.ui.widget.AssetSpinBox()
        self.amount_spin = dojima.ui.widget.AssetSpinBox()

        ask_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate('NewOfferDialog',
                                              "Ask Offer"))
        bid_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate('NewOfferDialog',
                                              "Bid Offer"))

        button_box = QtGui.QDialogButtonBox()
        button_box.addButton(ask_button, button_box.ActionRole)
        button_box.addButton(bid_button, button_box.ActionRole)
        button_box.addButton(button_box.Cancel)

        layout = QtGui.QFormLayout()
        layout.addRow(
            QtCore.QCoreApplication.translate('NewOfferDialog',
                                              "Nym",
                                              "the nym to chose accounts from."),
            self.nym_combo)

        layout.addRow(
            QtCore.QCoreApplication.translate('NewOfferDialog',
                                              "Base",
                                              "The base account."),
            self.base_account_combo)

        layout.addRow(
            QtCore.QCoreApplication.translate('NewOfferDialog',
                                              "Counter",
                                              "The counter account."),
            self.counter_account_combo)

        layout.addRow(
            QtCore.QCoreApplication.translate('NewOfferDialog',
                                              "Scale",
                                              "The offer amount scale, "
                                              "the offer amount shall be "
                                              "a multiple of this number, "
                                              "usually a multiple of ten."),
            self.scale_spin)

        layout.addRow(
            QtCore.QCoreApplication.translate('NewOfferDialog',
                                              "Amount",
                                              "The offer amount."),
            self.amount_spin)

        layout.addRow(
            QtCore.QCoreApplication.translate('NewOfferDialog',
                                              "Price",
                                              "The offer price."),
            self.price_spin)

        layout.addRow(button_box)
        self.setLayout(layout)

        #model
        self.nyms_model = dojima.model.ot.nyms.model
        accounts_model = dojima.model.ot.accounts.OTServerAccountsModel(
            self.server_id)

        simple_accounts_model = dojima.model.ot.accounts.OTAccountsProxyModel()
        simple_accounts_model.setSourceModel(accounts_model)
        simple_accounts_model.setFilterRole(QtCore.Qt.UserRole)
        simple_accounts_model.setFilterKeyColumn(accounts_model.TYPE)
        simple_accounts_model.setFilterFixedString('s')
        simple_accounts_model.setDynamicSortFilter(True)

        self.nym_accounts_model = dojima.model.ot.accounts.OTAccountsProxyModel()
        self.nym_accounts_model.setSourceModel(simple_accounts_model)
        self.nym_accounts_model.setFilterRole(QtCore.Qt.UserRole)
        self.nym_accounts_model.setFilterKeyColumn(accounts_model.NYM)
        self.nym_accounts_model.setDynamicSortFilter(True)

        self.base_accounts_model = dojima.model.ot.accounts.OTAccountsProxyModel()
        self.base_accounts_model.setSourceModel(self.nym_accounts_model)
        self.base_accounts_model.setFilterRole(QtCore.Qt.UserRole)
        self.base_accounts_model.setFilterKeyColumn(accounts_model.ASSET)
        self.base_accounts_model.setDynamicSortFilter(True)

        self.counter_accounts_model = dojima.model.ot.accounts.OTAccountsProxyModel()
        self.counter_accounts_model.setSourceModel(self.nym_accounts_model)
        self.counter_accounts_model.setFilterRole(QtCore.Qt.UserRole)
        self.counter_accounts_model.setFilterKeyColumn(accounts_model.ASSET)
        self.counter_accounts_model.setDynamicSortFilter(True)

        self.nym_combo.setModel(self.nyms_model)
        self.base_account_combo.setModel(self.base_accounts_model)
        self.counter_account_combo.setModel(self.counter_accounts_model)

        # connections
        button_box.rejected.connect(self.reject)
        self.nym_combo.otIdChanged.connect(self.changeNym)
        self.base_account_combo.otIdChanged.connect(self.changeBase)
        self.counter_account_combo.otIdChanged.connect(self.changeCounter)
        self.scale_spin.valueChanged.connect(self.amount_spin.setScale)
        bid_button.clicked.connect(self.placeAskOffer)
        ask_button.clicked.connect(self.placeBidOffer)

        # select
        self.nym_combo.currentIndexChanged.emit(0)
        self.disableInputs(True)

    def changeBase(self, account_id):
        if account_id == self.counter_account_combo.getOTID():
            self.disableInputs(True)
        else:
            self.disableInputs(False)

        assert account_id
        asset_id = otapi.OTAPI_Basic_GetAccountWallet_AssetTypeID(account_id)
        assert asset_id
        contract = dojima.ot.contract.CurrencyContract(asset_id)
        factor = contract.getFactor()
        self.amount_spin.setFactor(factor)
        self.amount_spin.setPrefix(contract.getTLA() + " ")

    def changeCounter(self, account_id):
        if account_id == self.base_account_combo.getOTID():
            self.disableInputs(True)
        else:
            self.disableInputs(False)

        assert account_id
        asset_id = otapi.OTAPI_Basic_GetAccountWallet_AssetTypeID(account_id)
        assert asset_id
        contract = dojima.ot.contract.CurrencyContract(asset_id)
        factor = contract.getFactor()
        self.price_spin.setFactor(factor)
        # this space breaks right to left scripts
        self.price_spin.setPrefix(contract.getTLA() + " ")

    def changeNym(self, nym_id):
        self.nym_accounts_model.setFilterFixedString(nym_id)

    def disableInputs(self, disabled_bool):
        for widget in (self.scale_spin,
                       self.amount_spin,
                       self.price_spin):
            widget.setDisabled(disabled_bool)

    def placeAskOffer(self):
        self._placeOffer(1)

    def placeBidOffer(self):
        self._placeOffer(0)

    def _placeOffer(self, offer_type):
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)

        base_account_id = self.base_account_combo.getOTID()
        base_asset_id = otapi.OTAPI_Basic_GetAccountWallet_AssetTypeID(
            base_account_id)
        counter_account_id = self.counter_account_combo.getOTID()
        counter_asset_id = otapi.OTAPI_Basic_GetAccountWallet_AssetTypeID(
            counter_account_id)

        scale = self.scale_spin.value()
        # TODO perhaps make an increment option
        increment = 1
        total = self.amount_spin.value() / scale # * increment

        r = otapi.OTAPI_Basic_issueMarketOffer(self.server_id,
                                          self.nym_combo.getOTID(),
                                          base_asset_id,
                                          base_account_id,
                                          counter_asset_id,
                                          counter_account_id,
                                          scale,
                                          increment,
                                          total,
                                          self.price_spin.value(),
                                          offer_type)

        QtGui.QApplication.restoreOverrideCursor()

        if r < 1:
            logger.error("issue market offer failed")
            self.getRequestNumber_queue.put(None)
            self.offer_queue.put( (market_id, total, price, buy_sell,) )
            self.reject()
            return

        self.accept()
