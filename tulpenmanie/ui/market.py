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

from tulpenmanie.model.market import *
from tulpenmanie.ui.widget import UuidComboBox

class EditMarketsWidget(QtGui.QWidget):

    def __init__(self, parent=None):
        super(EditMarketsWidget, self).__init__(parent)

        # Widgets
        self.list_view = QtGui.QListView()
        self.base_combo = UuidComboBox()
        self.counter_combo = UuidComboBox()
        enable_check = QtGui.QCheckBox()
        new_button = QtGui.QPushButton("new")
        delete_button = QtGui.QPushButton("delete")

        layout = QtGui.QGridLayout()
        layout.addWidget(self.list_view, 0,0, 2,1)

        combo_layout = QtGui.QFormLayout()
        combo_layout.addRow("&base:", self.base_combo)
        combo_layout.addRow("coun&ter:", self.counter_combo)
        combo_layout.addRow("enable:", enable_check)

        layout.addLayout(combo_layout, 0,1, 1,2)
        layout.addWidget(new_button, 1,1)
        layout.addWidget(delete_button, 1,2)
        self.setLayout(layout)

        # Model
        self.model = self.manager.markets_model

        self.list_view.setModel(self.model)
        self.list_view.setModelColumn(self.model.NAME)

        self.base_combo.setModel(self.manager.commodities_model)
        self.base_combo.setModelColumn(self.manager.commodities_model.NAME)
        self.counter_combo.setModel(self.manager.commodities_model)
        self.counter_combo.setModelColumn(self.manager.commodities_model.NAME)

        self.mapper = QtGui.QDataWidgetMapper(self)
        self.mapper.setModel(self.model)
        self.mapper.setSubmitPolicy(QtGui.QDataWidgetMapper.AutoSubmit)
        self.mapper.addMapping(self.base_combo, self.model.BASE, 'currentUuid')
        self.mapper.addMapping(self.counter_combo, self.model.COUNTER, 'currentUuid')
        self.mapper.addMapping(enable_check, self.model.ENABLE)

        # Connections
        self.list_view.clicked.connect(self._market_changed)
        new_button.clicked.connect(self._new)
        delete_button.clicked.connect(self._delete)

        # Load data
        self.list_view.setCurrentIndex(self.model.index(0, self.model.NAME))
        self.mapper.toFirst()

    def _market_changed(self, index):
        self.mapper.setCurrentIndex(index.row())

    def _new(self):
        row = self.model.new_market()
        index = self.model.index(row, self.model.NAME)
        self.list_view.setCurrentIndex(index)
        self.mapper.setCurrentIndex(row)
        self.base_combo.setCurrentIndex(0)
        self.counter_combo.setCurrentIndex(0)
        self.mapper.submit()
        self.list_view.setFocus()
        self.list_view.edit(index)

    def _delete(self):
        row = self.list_view.currentIndex().row()
        self.model.delete_row(row)
        row -= 1
        if row < 0:
            row = 0
        self.list_view.setCurrentIndex(self.model.index(row, self.model.NAME))
        self.mapper.setCurrentIndex(row)


class MarketDockWidget(QtGui.QDockWidget):

    def __init__(self, markets_model_row, parent=None):
        model = self.manager.markets_model
        row = markets_model_row
        name = model.item(row, model.NAME).text()

        base_uuid = model.item(row, model.BASE).text()
        base_item = self.manager.commodities_model.findItems(base_uuid)[0]
        self.base_row = base_item.row()
        counter_uuid = model.item(row, model.COUNTER).text()
        counter_item = self.manager.commodities_model.findItems(counter_uuid)[0]
        self.counter_row = counter_item.row()

        super(MarketDockWidget, self).__init__(name, parent)

        widget = QtGui.QWidget(self)
        self.setWidget(widget)
        self.layout = QtGui.QVBoxLayout()
        widget.setLayout(self.layout)

    def add_exchange_widget(self, exchange_widget):
        self.layout.addWidget(exchange_widget)
