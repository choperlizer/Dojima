# -*- coding: utf-8 -*-
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

import os.path

import otapi
from PyQt4 import QtCore, QtGui

from tulpenmanie.model.ot.assets import OTAssetsModel
from tulpenmanie.model.commodities import commodities_model


class EditWidget(QtGui.QWidget):

    def __init__(self, parent=None):
        super(EditWidget, self).__init__(parent)

        # Widgets
        self.list_view = CommoditiesListView()
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

        self.ot_child_assets_view = QtGui.QListView()
        #self.ot_child_assets_view.setAcceptDrops(True)
        #self.ot_child_assets_view.setDropIndicatorShown(True)
        #self.ot_child_assets_view.setDragEnabled(True)

        parent_of_label = QtGui.QLabel(QtCore.QCoreApplication.translate(
            'EditWidget', "parent of:",
            "the defined commoditiy shall be equivilant to one or more of"
            "the following"))
        parent_of_label.setBuddy(self.ot_child_assets_view)
        add_child_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate('EditWidget', "add"))
        remove_child_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate('EditWidget', "remove"))

        self.ot_assets_view = QtGui.QListView()
        self.ot_assets_view.setDragEnabled(True)

        ot_assets_label = QtGui.QLabel(QtCore.QCoreApplication.translate(
            'EditWidget', "Open Transactions assets:"))
        ot_assets_label.setBuddy(self.ot_assets_view)

        layout = QtGui.QGridLayout()
        layout.addWidget(self.list_view, 0,0, 6,2)

        layout.addLayout(edit_layout, 0,2, 1,2)
        layout.addWidget(parent_of_label, 1,2, 1,2)
        layout.addWidget(self.ot_child_assets_view, 2,2, 1,2)
        layout.addWidget(add_child_button, 3,2)
        layout.addWidget(remove_child_button, 3,3)

        layout.addWidget(ot_assets_label, 4,2, 1,2)
        layout.addWidget(self.ot_assets_view, 5,2, 1,2)

        layout.addWidget(import_button, 6,3)
        layout.addWidget(new_button, 6,0)
        layout.addWidget(delete_button, 6,1)
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
        # there needs to be multiple mapping models that change with commodity
        self.ot_child_assets_view.setModel(commodities_model)
        self.ot_child_assets_view.setModelColumn(1)

        self.ot_assets_model = ReduceableOTAssetsModel(self)
        self.ot_assets_view.setModel(self.ot_assets_model)
        self.ot_assets_view.setModelColumn(1)

        # Connect
        self.list_view.commodityChanged.connect(self.changeCommodityIndex)
        add_child_button.clicked.connect(self.add_child_asset)
        remove_child_button.clicked.connect(self.remove_child_asset)
        import_button.clicked.connect(self.import_contract)
        new_button.clicked.connect(self.new)
        delete_button.clicked.connect(self.delete)

        # Select
        index = commodities_model.index(0, commodities_model.NAME)
        self.list_view.setCurrentIndex(index)
        self.mapper.toFirst()
        self.ot_child_assets_view.setRootIndex(index)

    def new(self):
        row = commodities_model.new_commodity()
        self.mapper.setCurrentIndex(row)
        index = commodities_model.index(
            row, commodities_model.NAME)
        self.list_view.setCurrentIndex(index)
        self.list_view.setFocus()
        self.list_view.edit(index)

    def delete(self):
        # TODO Check if any markets use the selected commodity
        row = self.mapper.currentIndex()
        commodities_model.removeRow(row)

    def changeCommodityIndex(self, index):
        self.mapper.setCurrentModelIndex(index)
        self.ot_child_assets_view.setRootIndex(index)

    def add_child_asset(self):
        commodity_item = self.list_view.currentIndex().internalPointer()
        for index in self.ot_assets_view.selectedIndexes():
            asset_id = otapi.OT_API_GetAssetType_ID(index.row())
            self.ot_assets_model.disableAsset(asset_id)
            commodity_item.appendAsset(asset_id)

    def remove_child_asset(self):
        for index in self.ot_child_assets_view.selectedIndexes():
            asset_id = self.ot_child_assets_model.popRow(index.row())
            self.ot_assets_model.enableAsset(asset_id)

    def import_contract(self):
        dialog = ContractImportDialog(self)
        dialog.exec_()
        # reload the ot model I guess


class ContractImportDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        super(ContractImportDialog, self).__init__(parent)

        self.import_occurred = False
        self.recent_dir = QtCore.QString(QtGui.QDesktopServices.HomeLocation)

        self.import_box = QtGui.QPlainTextEdit()
        self.import_box.setMinimumWidth(512)
        paste_button = QtGui.QPushButton(QtCore.QCoreApplication.translate(
            'ContractImportDialog', "paste"))
        file_button = QtGui.QPushButton(QtCore.QCoreApplication.translate(
            'ContractImportDialog', "file"))
        import_button = QtGui.QPushButton(QtCore.QCoreApplication.translate(
            'ContractImportDialog', "import"))
        button_box = QtGui.QDialogButtonBox()
        button_box.addButton(paste_button, QtGui.QDialogButtonBox.ActionRole)
        button_box.addButton(file_button, QtGui.QDialogButtonBox.ActionRole)
        button_box.addButton(import_button, QtGui.QDialogButtonBox.ActionRole)
        button_box.addButton(QtGui.QDialogButtonBox.Close)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.import_box)
        layout.addWidget(button_box)
        self.setLayout(layout)
        paste_button.clicked.connect(self.paste_text)
        file_button.clicked.connect(self.import_file)
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
        parse_result = otapi.OT_API_AddAssetContract(str(text))
        subdialog_title = QtCore.QCoreApplication.translate(
            'ContractImportDialog', "contract import result")
        if parse_result == 1:
            self.import_box.clear()
            QtGui.QMessageBox.information(self, subdialog_title,
                QtCore.QCoreApplication.translate(
                    'ContractImportDialog', "contract imported"))

            self.import_occured = True
            # TODO get the proper indexes and emit
            #self.parent.ot_asset_model.dataChanged.emit(
        else:
            QtGui.QMessageBox.warning(self, subdialog_title,
                                      otapi.OT_API_PeekMemlogFront())

    def close(self):
        if self.import_occured is True:
            self.accept()
        self.reject()


class CommoditiesListView(QtGui.QListView):

    commodityChanged = QtCore.pyqtSignal(QtCore.QModelIndex)

    def currentChanged(self, current, previous):
        self.commodityChanged.emit(current)


class ReduceableOTAssetsModel(OTAssetsModel):

    def __init__(self, parent=None):
        super(ReduceableOTAssetsModel, self).__init__(parent)
        self.disabled_asset_ids = list()

    def flags(self, index):
        asset_id = otapi.OT_API_GetAssetType_ID(index.row())
        if asset_id in self.disabled_asset_ids:
            flags = QtCore.Qt.NoItemFlags
        else:
           flags = super(ReduceableOTAssetsModel, self).flags(index)
           flags |= QtCore.Qt.ItemIsDragEnabled
        return flags

    def enableAsset(self, asset_id):
        i = self.disabled_asset_ids.index(asset_id)
        self.disabled_asset_ids.pop(i)
        topLeft = self.createIndex(0, 0)
        bottomRight = self.createIndex(otapi.OT_API_GetAssetTypeCount() - 1, 1)
        self.dataChanged.emit(topLeft, bottomRight)

    def disableAsset(self, asset_id):
        self.disabled_asset_ids.append(asset_id)
        topLeft = self.createIndex(0, 0)
        bottomRight = self.createIndex(otapi.OT_API_GetAssetTypeCount() - 1, 1)
        self.dataChanged.emit(topLeft, bottomRight)
