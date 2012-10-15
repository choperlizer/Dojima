# -*- coding: utf-8 -*-
# Tulpenmanie, a graphical speculation platform.
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

from tulpenmanie.model.ot_assets import OTAssetsModel
from tulpenmanie.model.commodities import commodities_model
from tulpenmanie.model.markets import markets_model


class EditWidget(QtGui.QWidget):

    def __init__(self, parent=None):
        super(EditWidget, self).__init__(parent)

        # Widgets
        self.list_view = QtGui.QListView()
        prefix_edit = QtGui.QLineEdit()
        prefix_edit.setToolTip(u"optional, eg. $, €")
        suffix_edit = QtGui.QLineEdit()
        suffix_edit.setToolTip("optional, eg. kg, lb")
        precision_spin = QtGui.QSpinBox()
        precision_spin.setValue(3)
        precision_spin.setMinimum(-99)
        precision_spin.setToolTip(QtCore.QCoreApplication.translate(
            'EditWidget',
            """Decimal precision used to display quantities and prices.\n"""
            """A negative precision is not recommended."""))

        import_button = QtGui.QPushButton(QtCore.QCoreApplication.translate(
            'EditWidget', "&import contract"))
        new_button = QtGui.QPushButton(QtCore.QCoreApplication.translate(
            'EditWidget', "&new"))
        delete_button = QtGui.QPushButton(QtCore.QCoreApplication.translate(
            'EditWidget', "&delete"))

        edit_layout = QtGui.QFormLayout()
        edit_layout.addRow(QtCore.QCoreApplication.translate('EditWidget',
                                                             "prefix:"),
                                                             prefix_edit)
        edit_layout.addRow(QtCore.QCoreApplication.translate('EditWidget',
                                                             "suffix:"),
                                                             suffix_edit)
        edit_layout.addRow(
            QtCore.QCoreApplication.translate('EditWidget',
                                              "display precision:"),
                                              precision_spin)

        ot_assets_label = QtGui.QLabel(QtCore.QCoreApplication.translate(
            'EditWidget', "Open Transactions assets:"))
        self.ot_assets_view = QtGui.QListView()
        ot_assets_label.setBuddy(self.ot_assets_view)

        layout = QtGui.QGridLayout()
        layout.addWidget(self.list_view, 0,0, 5,1)

        layout.addLayout(edit_layout, 0,1, 1,2)
        layout.addWidget(ot_assets_label, 2,1, 1,2)
        layout.addWidget(self.ot_assets_view, 3,1, 1,2)

        layout.addWidget(import_button, 4,1, 1,2)
        layout.addWidget(new_button, 5,1)
        layout.addWidget(delete_button, 5,2)
        self.setLayout(layout)

        # Model
        self.list_view.setModel(commodities_model)
        self.list_view.setModelColumn(commodities_model.NAME)

        self.mapper = QtGui.QDataWidgetMapper(self)
        self.mapper.setModel(commodities_model)
        self.mapper.addMapping(prefix_edit, commodities_model.PREFIX)
        self.mapper.addMapping(suffix_edit, commodities_model.SUFFIX)
        self.mapper.addMapping(precision_spin,
                               commodities_model.PRECISION)
        ot_assets_model = OTAssetsModel(self)
        self.ot_assets_view.setModel(ot_assets_model)
        self.ot_assets_view.setModelColumn(1)

        # Connect
        self.list_view.clicked.connect(self.mapper.setCurrentModelIndex)
        import_button.clicked.connect(self.import_contract)
        new_button.clicked.connect(self._new)
        delete_button.clicked.connect(self._delete)

        # Select
        self.list_view.setCurrentIndex(
            commodities_model.index(
                0, commodities_model.NAME))
        self.mapper.toFirst()

    def _new(self):
        row = commodities_model.new_commodity()
        self.mapper.setCurrentIndex(row)
        index = commodities_model.index(
            row, commodities_model.NAME)
        self.list_view.setCurrentIndex(index)
        self.list_view.setFocus()
        self.list_view.edit(index)

    def _delete(self):
        # Check if any markets use the selected commodity
        row = self.mapper.currentIndex()
        uuid = commodities_model.item(
            row, commodities_model.UUID).text()
        results = markets_model.findItems(
            uuid, QtCore.Qt.MatchExactly, 2)
        results += markets_model.findItems(
            uuid, QtCore.Qt.MatchExactly, 3)
        if results:
            name = commodities_model.item(
                row, commodities_model.NAME).text()
            QtGui.QMessageBox.critical(self, name,
                                       "%s is still in use." % name,
                                       "Ok")
        else:
            commodities_model.delete_row(self.mapper.currentIndex())
            self.list_view.setCurrentIndex(
                commodities_model.index(
                    0, commodities_model.NAME))
            self.mapper.toFirst()

    def import_contract(self):
        dialog = ContractImportDialog(self)
        dialog.exec_()
        # reload the ot model I guess


class ContractImportDialog(QtGui.QDialog):

    # TODO this puppy crashes hard

    def __init__(self, parent=None):
        super(ContractImportDialog, self).__init__(parent)

        self.import_box = QtGui.QPlainTextEdit()
        self.import_box.setMinimumWidth(512)
        button_box = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.import_box)
        layout.addWidget(button_box)
        self.setLayout(layout)
        button_box.accepted.connect(self.parse_text)

    def parse_text(self):
        text = str(self.import_box.toPlainText())
        if not text:
            self.accept()
        # TODO this will crash everything if the contract isn't good
        if otapi.OT_API_AddAssetContract(text):
            self.import_box.clear()
            QtGui.QMessageBox.information(self,
                QtCore.QCoreApplication.translate('ContractImportDialog',
                                                  "Contract Import"),
                otapi.OT_API_PeekMemlogFront())
            self.accept()
        else:
            # Not sure if we get here unless we check the text then
            # bypass AddAssetContract
            QtGui.QMessageBox.warning(self,
                QtCore.QCoreApplication.translate('ContractImportDialog',
                                                  "Contract Import"),
                otapi.OT_API_PeekMemlogFront())
            self.reject()
