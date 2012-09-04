# -*- coding: utf-8 -*-
# Tuplenmanie, a commodities market client.
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

from PyQt4 import QtCore, QtGui

from tulpenmanie.model.commodity import *

class EditCommoditiesWidget(QtGui.QWidget):

    def __init__(self, parent=None):
        super(EditCommoditiesWidget, self).__init__(parent)

        # Widgets
        self.list_view = QtGui.QListView()
        prefix_edit = QtGui.QLineEdit()
        prefix_edit.setToolTip(u"optional, eg. $, €")
        suffix_edit = QtGui.QLineEdit()
        suffix_edit.setToolTip("optional, eg. kg, lb")
        precision_spin = QtGui.QSpinBox()
        precision_spin.setValue(3)
        precision_spin.setMinimum(-99)
        precision_spin.setToolTip(
            """Decimal precision used to display quantities and prices.\n"""
            """A negative precision is not recommended.""")
        new_button = QtGui.QPushButton("new")
        delete_button = QtGui.QPushButton("delete")

        edit_layout = QtGui.QFormLayout()
        edit_layout.addRow("prefix:", prefix_edit)
        edit_layout.addRow("suffix:", suffix_edit)
        edit_layout.addRow("display precision:", precision_spin)

        layout = QtGui.QGridLayout()
        layout.addWidget(self.list_view, 0,0, 2,1)
        layout.addLayout(edit_layout, 0,1, 1,2)
        layout.addWidget(new_button, 1,1)
        layout.addWidget(delete_button, 1,2)
        self.setLayout(layout)

        # Model
        self.model = self.manager.commodities_model

        self.list_view.setModel(self.model)
        self.list_view.setModelColumn(self.model.NAME)

        self.mapper = QtGui.QDataWidgetMapper(self)
        self.mapper.setModel(self.model)
        self.mapper.addMapping(prefix_edit, self.model.PREFIX)
        self.mapper.addMapping(suffix_edit, self.model.SUFFIX)
        self.mapper.addMapping(precision_spin, self.model.PRECISION)

        # Connect
        self.list_view.clicked.connect(self.mapper.setCurrentModelIndex)
        new_button.clicked.connect(self._new)
        delete_button.clicked.connect(self._delete)

        # Select
        self.list_view.setCurrentIndex(self.model.index(0, self.model.NAME))
        self.mapper.toFirst()

    def _new(self):
        row = self.model.new_commodity()
        self.mapper.setCurrentIndex(row)
        index = self.model.index(row, self.model.NAME)
        self.list_view.setCurrentIndex(index)
        self.list_view.setFocus()
        self.list_view.edit(index)

    def _delete(self):
        # Check if any markets use the selected commodity
        row = self.mapper.currentIndex()
        uuid = self.model.item(row, self.model.UUID).text()
        results = self.manager.markets_model.findItems(
            uuid, QtCore.Qt.MatchExactly, 2)
        results += self.manager.markets_model.findItems(
            uuid, QtCore.Qt.MatchExactly, 3)
        if results:
            name = self.model.item(row, self.model.NAME).text()
            QtGui.QMessageBox.critical(self, name,
                                       "%s is still in use." % name,
                                       "Ok")

        else:
            self.model.delete_row(self.mapper.currentIndex())
            self.list_view.setCurrentIndex(self.model.index(0, self.model.NAME))
            self.mapper.toFirst()
        
