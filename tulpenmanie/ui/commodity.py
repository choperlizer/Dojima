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

import logging
from PyQt4 import QtCore, QtGui

import tulpenmanie.commodity
import tulpenmanie.market


logger = logging.getLogger(__name__)

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
        self.list_view.setModel(tulpenmanie.commodity.model)
        self.list_view.setModelColumn(tulpenmanie.commodity.model.NAME)

        self.mapper = QtGui.QDataWidgetMapper(self)
        self.mapper.setModel(tulpenmanie.commodity.model)
        self.mapper.addMapping(prefix_edit, tulpenmanie.commodity.model.PREFIX)
        self.mapper.addMapping(suffix_edit, tulpenmanie.commodity.model.SUFFIX)
        self.mapper.addMapping(precision_spin,
                               tulpenmanie.commodity.model.PRECISION)

        # Connect
        self.list_view.clicked.connect(self.mapper.setCurrentModelIndex)
        new_button.clicked.connect(self._new)
        delete_button.clicked.connect(self._delete)

        # Select
        self.list_view.setCurrentIndex(
            tulpenmanie.commodity.model.index(
                0, tulpenmanie.commodity.model.NAME))
        self.mapper.toFirst()

    def _new(self):
        row = tulpenmanie.commodity.model.new_commodity()
        self.mapper.setCurrentIndex(row)
        index = tulpenmanie.commodity.model.index(
            row, tulpenmanie.commodity.model.NAME)
        self.list_view.setCurrentIndex(index)
        self.list_view.setFocus()
        self.list_view.edit(index)

    def _delete(self):
        # Check if any markets use the selected commodity
        row = self.mapper.currentIndex()
        uuid = tulpenmanie.commodity.model.item(
            row, tulpenmanie.commodity.model.UUID).text()
        results = tulpenmanie.market.model.findItems(
            uuid, QtCore.Qt.MatchExactly, 2)
        results += tulpenmanie.market.model.findItems(
            uuid, QtCore.Qt.MatchExactly, 3)
        if results:
            name = tulpenmanie.commodity.model.item(
                row, tulpenmanie.commodity.model.NAME).text()
            QtGui.QMessageBox.critical(self, name,
                                       "%s is still in use." % name,
                                       "Ok")
        else:
            tulpenmanie.commodity.model.delete_row(self.mapper.currentIndex())
            self.list_view.setCurrentIndex(
                tulpenmanie.commodity.model.index(
                    0, tulpenmanie.commodity.model.NAME))
            self.mapper.toFirst()
