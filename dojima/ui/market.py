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

import logging
import otapi

from PyQt4 import QtCore, QtGui

import dojima.exchanges
import dojima.model.commodities
import dojima.ui.edit.commodity
import dojima.ui.ot.contract

import dojima.exchange_modules.opentxs

logger = logging.getLogger(__name__)

"""
class EditWidget(QtGui.QWidget):

    def __init__(self, parent=None):
        super(EditWidget, self).__init__(parent)

        # Widgets
        self.list_view = QtGui.QListView()
        self.base_combo = UuidComboBox()
        self.counter_combo = UuidComboBox()
        new_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate('EditWidget', "new"))
        delete_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate('EditWidget', "remove"))

        layout = QtGui.QGridLayout()
        layout.addWidget(self.list_view, 0,0, 2,1)

        combo_layout = QtGui.QFormLayout()
        combo_layout.addRow(
            QtCore.QCoreApplication.translate('EditWidget', "base"),
            self.base_combo)
        combo_layout.addRow(
            QtCore.QCoreApplication.translate('EditWidget', "counter"),
            self.counter_combo)

        layout.addLayout(combo_layout, 0,1, 1,2)
        layout.addWidget(new_button, 1,1)
        layout.addWidget(delete_button, 1,2)
        self.setLayout(layout)

        # Model
        self.list_view.setModel(dojima.market.model)
        self.list_view.setModelColumn(dojima.market.model.NAME)

        self.base_combo.setModel(dojima.commodity.model)
        self.base_combo.setModelColumn(dojima.commodity.model.NAME)
        self.counter_combo.setModel(dojima.commodity.model)
        self.counter_combo.setModelColumn(dojima.commodity.model.NAME)

        self.mapper = QtGui.QDataWidgetMapper(self)
        self.mapper.setModel(dojima.market.model)
        self.mapper.setSubmitPolicy(QtGui.QDataWidgetMapper.AutoSubmit)
        self.mapper.addMapping(self.base_combo, dojima.market.model.BASE, 'currentUuid')
        self.mapper.addMapping(self.counter_combo, dojima.market.model.COUNTER, 'currentUuid')

        # Connections
        self.list_view.clicked.connect(self._market_changed)
        new_button.clicked.connect(self._new)
        delete_button.clicked.connect(self._delete)

        # Load data
        self.list_view.setCurrentIndex(dojima.market.model.index(0, dojima.market.model.NAME))
        self.mapper.toFirst()

    def _market_changed(self, index):
        self.mapper.setCurrentIndex(index.row())

    def _new(self):
        row = dojima.market.model.new_market()
        index = dojima.market.model.index(row,
                                               dojima.market.model.NAME)
        self.list_view.setCurrentIndex(index)
        self.mapper.setCurrentIndex(row)
        self.base_combo.setCurrentIndex(0)
        self.counter_combo.setCurrentIndex(0)
        self.mapper.submit()
        self.list_view.setFocus()
        self.list_view.edit(index)

    def _delete(self):
        row = self.list_view.currentIndex().row()
        dojima.market.model.delete_row(row)
        row -= 1
        if row < 0:
            row = 0
        self.list_view.setCurrentIndex(dojima.market.model.index(
            row, dojima.market.model.NAME))
        self.mapper.setCurrentIndex(row)
"""
