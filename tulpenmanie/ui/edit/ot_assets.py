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

class AssetsListView(QtGui.QListView):

    assetRowChanged = QtCore.pyqtSignal(int)

    def currentChanged(self, current, previous):
        self.assetRowChanged.emit(current.row())

