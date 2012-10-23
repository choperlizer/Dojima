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
# GNU General Public Licnense for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os.path

import otapi
from PyQt4 import QtCore, QtGui

import tulpenmanie.model.ot.assets
from tulpenmanie.model.commodities import commodities_model
from tulpenmanie.ui.edit.commodity import NewCommodityDialog


class EditWidget(QtGui.QWidget):


    factor_prefix_string = QtCore.QCoreApplication.translate('EditWidget',
                                                             "%1 is ",
                                                             "x is z of y")
    factor_suffix_string = QtCore.QCoreApplication.translate('EditWidget',
                                                             " of one %1%2%3",
                                                             "x is z of y")
    def __init__(self, parent=None):
        super(EditWidget, self).__init__(parent)

        # Widgets
        self.assets_view = AssetsListView()
        enable_checkbox = QtGui.QCheckBox(
            QtCore.QCoreApplication.translate('EditWidget',
                                              "map to local commodity"))
        self.mapping_label = QtGui.QLabel(
            QtCore.QCoreApplication.translate('EditWidget', "map to commodity:"))
        commodity_combo = QtGui.QComboBox()
        self.factor_prefix_label = QtGui.QLabel()
        self.factor_spin = QtGui.QDoubleSpinBox()
        self.factor_spin.setDecimals(8)
        self.factor_suffix_label = QtGui.QLabel()

        self.optional_widgets = (self.mapping_label,
                                 commodity_combo,
                                 self.factor_spin)

        save_button = QtGui.QPushButton("save")

        import_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate('EditWidget', "&import contract"))

        layout = QtGui.QGridLayout()
        layout.addWidget(self.assets_view, 0,0, 8,1)
        layout.addWidget(enable_checkbox, 0,1)
        layout.addWidget(self.mapping_label, 1,1)
        layout.addWidget(commodity_combo, 2,1)
        #layout.setRowStretch(2, 1)
        layout.addWidget(self.factor_prefix_label, 3,1)
        layout.addWidget(self.factor_spin, 4,1)
        layout.addWidget(self.factor_suffix_label, 5,1)
        layout.setRowStretch(6, 2)
        layout.addWidget(import_button, 7,1)
        layout.addWidget(save_button, 8,1)
        self.setLayout(layout)

        # Model
        self.assets_model = tulpenmanie.model.ot.assets.OTAssetsSettingsModel()
        self.assets_model.refresh()
        self.assets_view.setModel(self.assets_model)
        self.assets_view.setModelColumn(self.assets_model.NAME)

        self.mapper = QtGui.QDataWidgetMapper(self)
        self.mapper.setSubmitPolicy(QtGui.QDataWidgetMapper.AutoSubmit)
        self.mapper.setModel(self.assets_model)
        self.mapper.addMapping(enable_checkbox, self.assets_model.ENABLE)
        self.mapper.addMapping(self.factor_spin, self.assets_model.FACTOR)

        # Connect
        self.assets_view.assetRowChanged.connect(self.mapper.setCurrentIndex)
        enable_checkbox.stateChanged.connect(commodity_combo.setEnabled)
        import_button.clicked.connect(self.import_contract)

        save_button.clicked.connect(self.assets_model.submit)

        # Select
        self.assets_view.setCurrentIndex(self.assets_model.index(0, 1))
        self.mapper.toFirst()

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
        file_button = QtGui.QPushButton(QtCore.QCoreApplication.translate(
            'ContractImportDialog', "file"))
        paste_button = QtGui.QPushButton(QtCore.QCoreApplication.translate(
            'ContractImportDialog', "paste"))
        import_button = QtGui.QPushButton(QtCore.QCoreApplication.translate(
            'ContractImportDialog', "import"))
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
        parse_result = otapi.OT_API_AddAssetContract(str(text))
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
                                      otapi.OT_API_PeekMemlogFront())

    def close(self):
        if self.import_occured is True:
            self.accept()
        self.reject()


class AssetsListView(QtGui.QListView):

    assetRowChanged = QtCore.pyqtSignal(int)

    def currentChanged(self, current, previous):
        self.assetRowChanged.emit(current.row())


class AssetMappingDialog(QtGui.QDialog):

    preview_string = QtCore.QCoreApplication.translate('AssetMappingDialog',
                                                       "A %1 is %2 %3")

    # TODO extract the factor and decimal out of the contract
    
    def __init__(self, assetId, parent=None):
        super(AssetMappingDialog, self).__init__(parent)

        self.asset_id = assetId
        # another redundant otapi call
        self.asset_name = otapi.OT_API_GetAssetType_Name(self.asset_id)

        # UI
        self.commodity_combo = QtGui.QComboBox()
        self.commodity_combo.setModel(commodities_model)
        self.commodity_combo.setModelColumn(commodities_model.NAME)
        self.commodity_combo.setToolTip(
            QtCore.QCoreApplication.translate('AssetMappingDialog',
                """Map this Open Transactions Asset to a locally defined  """
                """fungible instrument."""))

        self.factor_spin = QtGui.QSpinBox()
        self.factor_spin.setMaximum(1000000000)
        self.factor_spin.setToolTip(
            # TODO probably strip this tip
            QtCore.QCoreApplication.translate('AssetMappingDialog',
                """Open Transactions only uses integer math, therefore """
                """assets backed by instruments that may be divided into """
                """increments less than one (1.0) will most commonly be """
                """ expressed """
                """using that instrument's smallest unit, such as a cent. """
                """To display these assets in the most practical manner """
                """a factor may be used to convert these units into larger, """
                """more common units. """))

        new_local_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate('AssetMappingDialog',
                                              "new local"))
        self.preview_label = QtGui.QLabel()

        self.contract_view = QtGui.QPlainTextEdit(
            otapi.OT_API_GetAssetType_Contract(self.asset_id))
        self.contract_view.setReadOnly(True)
        self.contract_view.setLineWrapMode(QtGui.QPlainTextEdit.NoWrap)

        button_box = QtGui.QDialogButtonBox()
        button_box.addButton(new_local_button, QtGui.QDialogButtonBox.ActionRole)
        button_box.addButton(QtGui.QDialogButtonBox.Ok)
        button_box.addButton(QtGui.QDialogButtonBox.Cancel)

        # layout
        form_layout = QtGui.QFormLayout()
        form_layout.addRow(
            QtCore.QCoreApplication.translate('AssetMappingDialog',
                                              "map to"),
            self.commodity_combo)
        form_layout.addRow(
            QtCore.QCoreApplication.translate('AssetMappingDialog',
                                              "at a factor of"),
            self.factor_spin)

        layout = QtGui.QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addWidget(self.preview_label)
        layout.addWidget(self.contract_view)
        layout.addWidget(button_box)
        self.setLayout(layout)

        # connections
        self.commodity_combo.currentIndexChanged[str].connect(
            self.commodityChanged)
        self.factor_spin.valueChanged[str].connect(
            self.factorChanged)
        new_local_button.clicked.connect(self.new_local)
        button_box.accepted.connect(self.submit)
        button_box.rejected.connect(self.reject)

        # select
        self.model = tulpenmanie.model.ot.assets.OTAssetsSettingsModel()
        search = self.model.findItems(self.asset_id)
        if not search:
            self.row = None
            self.factor_spin.setValue(1)
            return

        self.row = search[0].row()
        commodity_id = self.model.item(self.row, self.model.LOCAL_ID).text()

        search = commodities_model.findItems(commodity_id)
        if not search: return

        commodity_row = search[0].row()
        self.commodity_combo.setCurrentIndex(commodity_row)
        factor = self.model.item(self.row, self.model.FACTOR).text()
        if factor:
            self.factor_spin.setValue(int(factor))
        else:
            self.factor_spin.setValue(1)

        self.preview_label.setText(
            QtCore.QCoreApplication.translate('AssetMappingDialog',
                                              "previous mapping found"))

    def commodityChanged(self, commodity):
        factor = self.factor_spin.value()
        self.setPreview(commodity, factor)

    def factorChanged(self, factor):
        commodity = self.commodity_combo.currentText()
        self.setPreview(commodity, factor)

    def setPreview(self, commodity, factor):
        self.preview_label.setText(
            self.preview_string.arg(commodity
                                    ).arg(factor
                                          ).arg(self.asset_name))
    def new_local(self):
        dialog = NewCommodityDialog(self)
        if dialog.exec_():
            self.commodity_combo.setCurrentIndex(dialog.row)

    def submit(self):
        commodity_id = commodities_model.item(
            self.commodity_combo.currentIndex(), commodities_model.UUID).text()
        print commodity_id

        if self.row is None:
            self.row = self.model.rowCount()

        item = QtGui.QStandardItem(self.asset_id)
        self.model.setItem(self.row, self.model.ASSET_ID, item)

        item = QtGui.QStandardItem(commodity_id)
        self.model.setItem(self.row, self.model.LOCAL_ID, item)

        item = QtGui.QStandardItem(self.factor_spin.cleanText())
        self.model.setItem(self.row, self.model.FACTOR, item)

        self.model.submit()
        self.accept()
