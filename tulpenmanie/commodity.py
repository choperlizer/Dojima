# -*- coding: utf-8 -*-
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

import tulpenmanie.model
import tulpenmanie.market


logger = logging.getLogger(__name__)

model = None

def create_model(parent):
    global model
    model = _CommoditiesModel(parent)


    
class FlatSettingsModel(QtGui.QStandardItemModel):

    def __init__(self, parent=None):
        super(FlatSettingsModel, self).__init__(parent)
        self.settings = QtCore.QSettings()
        self.settings.beginGroup(self.name)
        self.setColumnCount(self.COLUMNS)
        self._populate()

    def _populate(self):
        logger.debug("loading %s", self.name)
        for row, uuid in enumerate(self.settings.childGroups()):
            self.settings.beginGroup(uuid)
            item = QtGui.QStandardItem(uuid)
            self.setItem(row, self.UUID, item)
            for setting, column in self.SETTINGS_MAP:
                item = QtGui.QStandardItem(
                    self.settings.value(setting).toString())
                self.setItem(int(row), column, item)
            self.settings.endGroup()

    def save(self):
        logger.debug("saving %s", self.name)
        rows = range(self.rowCount())

        for row in rows:
            uuid = self.item(row, self.UUID).text()
            self.settings.beginGroup(uuid)
            for setting, column in self.SETTINGS_MAP:
                value =  self.item(row, column).text()
                self.settings.setValue(setting, value)
            self.settings.endGroup()

    def delete_row(self, row):
        uuid = self.item(self.UUID, row).text()
        self.settings.remove(uuid)
        self.removeRow(row)



class _CommoditiesModel(FlatSettingsModel):

    name = 'commodities'
    COLUMNS = 5
    UUID, NAME, PREFIX, SUFFIX, PRECISION = range(COLUMNS)
    SETTINGS_MAP = (('name', NAME), ('prefix', PREFIX),
                    ('suffix', SUFFIX), ('precision', PRECISION))

    def new_commodity(self):
        uuid = QtCore.QUuid.createUuid().toString()[1:-1]
        items = [QtGui.QStandardItem(uuid)]
        for column in range(self.COLUMNS -1):
            items.append(QtGui.QStandardItem())
        self.appendRow(items)
        return items[0].row()


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
        self.list_view.setModel(model)
        self.list_view.setModelColumn(model.NAME)

        self.mapper = QtGui.QDataWidgetMapper(self)
        self.mapper.setModel(model)
        self.mapper.addMapping(prefix_edit, model.PREFIX)
        self.mapper.addMapping(suffix_edit, model.SUFFIX)
        self.mapper.addMapping(precision_spin, model.PRECISION)

        # Connect
        self.list_view.clicked.connect(self.mapper.setCurrentModelIndex)
        new_button.clicked.connect(self._new)
        delete_button.clicked.connect(self._delete)

        # Select
        self.list_view.setCurrentIndex(model.index(0, model.NAME))
        self.mapper.toFirst()

    def _new(self):
        row = model.new_commodity()
        self.mapper.setCurrentIndex(row)
        index = model.index(row, model.NAME)
        self.list_view.setCurrentIndex(index)
        self.list_view.setFocus()
        self.list_view.edit(index)

    def _delete(self):
        # Check if any markets use the selected commodity
        row = self.mapper.currentIndex()
        uuid = model.item(row, model.UUID).text()
        results = tulpenmanie.market.model.findItems(
            uuid, QtCore.Qt.MatchExactly, 2)
        results += tulpenmanie.market.model.findItems(
            uuid, QtCore.Qt.MatchExactly, 3)
        if results:
            name = model.item(row, model.NAME).text()
            QtGui.QMessageBox.critical(self, name,
                                       "%s is still in use." % name,
                                       "Ok")
        else:
            model.delete_row(self.mapper.currentIndex())
            self.list_view.setCurrentIndex(model.index(0, model.NAME))
            self.mapper.toFirst()
