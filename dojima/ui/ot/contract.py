# -*- coding: utf-8 -*-
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
# GNU General Public Licnense for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os.path

import otapi
from PyQt4 import QtCore, QtGui


class _ContractImportDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        super(_ContractImportDialog, self).__init__(parent)

        self.import_occurred = False
        self.recent_dir = QtGui.QDesktopServices.HomeLocation

        self.import_box = QtGui.QPlainTextEdit()
        self.import_box.setMinimumWidth(512)
        file_button = QtGui.QPushButton(QtCore.QCoreApplication.translate(
            'ServerContractImportDialog', "File"))
        paste_button = QtGui.QPushButton(QtCore.QCoreApplication.translate(
            'ContractImportDialog', "Paste"))
        import_button = QtGui.QPushButton(QtCore.QCoreApplication.translate(
            'ContractImportDialog', "Import"))
        button_box = QtGui.QDialogButtonBox()
        button_box.addButton(file_button, QtGui.QDialogButtonBox.ActionRole)
        button_box.addButton(paste_button, QtGui.QDialogButtonBox.ActionRole)
        button_box.addButton(import_button, QtGui.QDialogButtonBox.ActionRole)
        button_box.addButton(QtGui.QDialogButtonBox.Close)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.import_box)
        layout.addWidget(button_box)
        self.setLayout(layout)
        file_button.clicked.connect(self.import_file)
        paste_button.clicked.connect(self.paste_text)
        import_button.clicked.connect(self.parse_text)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.accept)

    def paste_text(self):
        clipboard = QtGui.QApplication.clipboard()
        self.import_box.setPlainText(clipboard.text())

    def import_file(self):
        filenames = QtGui.QFileDialog.getOpenFileNames(self,
            QtCore.QCoreApplication.translate(
                'ContractImportDialog', "select contract file"),
            self.recent_dir,
            QtCore.QCoreApplication.translate(
                'ContractImportDialog', "Open Transactions contracts (*.otc)"))
        if not len(filenames):
            return
        self.recent_dir = os.path.dirname(str(filenames[-1]))

        for filename in filenames:
            contract_file = QtCore.QFile(filename)
            if not contract_file.open(QtCore.QIODevice.ReadOnly |
                                      QtCore.QIODevice.Text):
                continue
            stream = QtCore.QTextStream(contract_file)
            # TODO this could exaust memory if one loaded a malicious file
            contract = stream.readAll()
            self.parse_contract(contract)

    def parse_text(self):
        text = self.import_box.toPlainText()
        if not len(text):
            self.accept()
            return
        self.parse_contract(text)

    def parse_contract(self, text):
        # TODO extract the contract name and put that in the result dialog
        # since if multiple contract files are imported the result can only
        # be distinguished by the order they pop up
        parse_result = self.contract_import_method(str(text))
        subdialog_title = QtCore.QCoreApplication.translate(
            'ContractImportDialog', "contract import result")
        if parse_result == 1:
            self.import_box.clear()
            QtGui.QMessageBox.information(self, subdialog_title,
                QtCore.QCoreApplication.translate(
                    'ContractImportDialog',
                    "contract imported (if not already present)" ))

            self.import_occured = True
            # TODO get the proper indexes and emit
            #self.parent.ot_asset_model.dataChanged.emit(
        else:
            QtGui.QMessageBox.warning(self, subdialog_title,
                                      otapi.OTAPI_Basic_PeekMemlogFront())

    def close(self):
        if self.import_occured is True:
            self.accept()
        self.reject()


class AssetContractImportDialog(_ContractImportDialog):

    contract_import_method = otapi.OTAPI_Basic_AddAssetContract

    
class ServerContractImportDialog(_ContractImportDialog):

    contract_import_method = otapi.OTAPI_Basic_AddServerContract
