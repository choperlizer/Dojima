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

import tulpenmanie.market
import tulpenmanie.commodity
import tulpenmanie.translation
from tulpenmanie.widget import UuidComboBox


logger = logging.getLogger(__name__)

class EditWidget(QtGui.QWidget):

    def __init__(self, parent=None):
        super(EditWidget, self).__init__(parent)

        # Widgets
        self.list_view = QtGui.QListView()
        self.base_combo = UuidComboBox()
        self.counter_combo = UuidComboBox()
        enable_check = QtGui.QCheckBox()
        new_button = QtGui.QPushButton(tulpenmanie.translation.new)
        delete_button = QtGui.QPushButton(tulpenmanie.translation.remove)

        layout = QtGui.QGridLayout()
        layout.addWidget(self.list_view, 0,0, 2,1)

        combo_layout = QtGui.QFormLayout()
        combo_layout.addRow(tulpenmanie.translation.base, self.base_combo)
        combo_layout.addRow(tulpenmanie.translation.counter, self.counter_combo)
        combo_layout.addRow(tulpenmanie.translation.enable, enable_check)

        layout.addLayout(combo_layout, 0,1, 1,2)
        layout.addWidget(new_button, 1,1)
        layout.addWidget(delete_button, 1,2)
        self.setLayout(layout)

        # Model
        self.list_view.setModel(tulpenmanie.market.model)
        self.list_view.setModelColumn(tulpenmanie.market.model.NAME)

        self.base_combo.setModel(tulpenmanie.commodity.model)
        self.base_combo.setModelColumn(tulpenmanie.commodity.model.NAME)
        self.counter_combo.setModel(tulpenmanie.commodity.model)
        self.counter_combo.setModelColumn(tulpenmanie.commodity.model.NAME)

        self.mapper = QtGui.QDataWidgetMapper(self)
        self.mapper.setModel(tulpenmanie.market.model)
        self.mapper.setSubmitPolicy(QtGui.QDataWidgetMapper.AutoSubmit)
        self.mapper.addMapping(self.base_combo, tulpenmanie.market.model.BASE, 'currentUuid')
        self.mapper.addMapping(self.counter_combo, tulpenmanie.market.model.COUNTER, 'currentUuid')
        self.mapper.addMapping(enable_check, tulpenmanie.market.model.ENABLE)

        # Connections
        self.list_view.clicked.connect(self._market_changed)
        new_button.clicked.connect(self._new)
        delete_button.clicked.connect(self._delete)

        # Load data
        self.list_view.setCurrentIndex(tulpenmanie.market.model.index(0, tulpenmanie.market.model.NAME))
        self.mapper.toFirst()

    def _market_changed(self, index):
        self.mapper.setCurrentIndex(index.row())

    def _new(self):
        row = tulpenmanie.market.model.new_market()
        index = tulpenmanie.market.model.index(row,
                                               tulpenmanie.market.model.NAME)
        self.list_view.setCurrentIndex(index)
        self.mapper.setCurrentIndex(row)
        self.base_combo.setCurrentIndex(0)
        self.counter_combo.setCurrentIndex(0)
        self.mapper.submit()
        self.list_view.setFocus()
        self.list_view.edit(index)

    def _delete(self):
        row = self.list_view.currentIndex().row()
        model.delete_row(row)
        row -= 1
        if row < 0:
            row = 0
        self.list_view.setCurrentIndex(tulpenmanie.market.model.index(
            row, tulpenmanie.market.model.NAME))
        self.mapper.setCurrentIndex(row)


class DockWidget(QtGui.QDockWidget):

    enable_market_changed = QtCore.pyqtSignal(bool)

    def __init__(self, model_row, parent=None):
        self.row = model_row
        name = tulpenmanie.market.model.item(self.row, tulpenmanie.market.model.NAME).text()
        super(DockWidget, self).__init__(name, parent)
        self.exchanges = dict()

        base_uuid = tulpenmanie.market.model.item(self.row, tulpenmanie.market.model.BASE).text()
        search = tulpenmanie.commodity.model.findItems(base_uuid)
        if not search:
            logger.critical("settings error, invalid base commodity mapping "
                            "in market '%s'", name)
        # TODO raise error
        base_item = search[0]
        self.base_row = base_item.row()
        counter_uuid = tulpenmanie.market.model.item(self.row, tulpenmanie.market.model.COUNTER).text()
        search = tulpenmanie.commodity.model.findItems(counter_uuid)
        if not search:
            logger.critical("settings error, invalid counter commodity mapping "
                            "in market '%s'", name)
        # TODO raise error
        counter_item = search[0]
        self.counter_row = counter_item.row()

        widget = QtGui.QWidget(self)
        self.setWidget(widget)
        self.layout = QtGui.QVBoxLayout()
        widget.setLayout(self.layout)

        # Create menu and action
        # the menu and action belongs to parent
        # so self can be disabled without disabling
        # menu and action
        self.menu = QtGui.QMenu(name, parent)
        self.enable_market_action = QtGui.QAction(
            tulpenmanie.translation.enable, parent)
        self.enable_market_action.setCheckable(True)
        #changed from toggle
        self.enable_market_action.triggered.connect(self.enable_market)

        self.menu.addAction(self.enable_market_action)
        # TODO perhaps this menu could tear off
        # also, looking into collapsing separators
        self.menu.addSeparator()

    def add_exchange_widget(self, exchange_widget, exchange_name):
        self.layout.addWidget(exchange_widget)
        self.menu.addAction(exchange_widget.enable_exchange_action)
        self.addAction(exchange_widget.enable_exchange_action)
        exchange_widget.enable_exchange_action.setEnabled(self.isEnabled())
        self.exchanges[exchange_name] = exchange_widget

    def enable_market(self, enable):
        self.setEnabled(enable)
        self.setVisible(enable)
        self.enable_market_changed.emit(enable)
        for action in self.actions():
            action.setEnabled(enable)

        enable_item = tulpenmanie.market.model.item(
            self.row, tulpenmanie.market.model.ENABLE)
        if enable:
            enable_item.setText("true")
        else:
            enable_item.setText("false")

    def closeEvent(self, event):
        # TODO is close event ever called?
        self.enable_market_action.setChecked(False)
        self.enable_market(False)
        event.accept()