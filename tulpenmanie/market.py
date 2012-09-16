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

#import tulpenmanie.model
import tulpenmanie.commodity
import tulpenmanie.translation
from tulpenmanie.widget import UuidComboBox

logger = logging.getLogger(__name__)

model = None

def create_model(parent):
    global model
    model = _MarketsModel(parent)

    # This class shouldn't be here, I have no idea
    # why it needs to be
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

class _MarketsModel(FlatSettingsModel):
    """QtGui.QStandardItemModel that contain market configuration."""
    """Intended to be instaniated in this module only."""

    name = 'markets'
    COLUMNS = 5
    UUID, NAME, BASE, COUNTER, ENABLE = range(COLUMNS)
    SETTINGS_MAP = (('name', NAME), ('base', BASE),
                    ('counter', COUNTER), ('enable', ENABLE))

    def new_market(self):
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
        self.list_view.setModel(model)
        self.list_view.setModelColumn(model.NAME)

        self.base_combo.setModel(tulpenmanie.commodity.model)
        self.base_combo.setModelColumn(tulpenmanie.commodity.model.NAME)
        self.counter_combo.setModel(tulpenmanie.commodity.model)
        self.counter_combo.setModelColumn(tulpenmanie.commodity.model.NAME)

        self.mapper = QtGui.QDataWidgetMapper(self)
        self.mapper.setModel(model)
        self.mapper.setSubmitPolicy(QtGui.QDataWidgetMapper.AutoSubmit)
        self.mapper.addMapping(self.base_combo, model.BASE, 'currentUuid')
        self.mapper.addMapping(self.counter_combo, model.COUNTER, 'currentUuid')
        self.mapper.addMapping(enable_check, model.ENABLE)

        # Connections
        self.list_view.clicked.connect(self._market_changed)
        new_button.clicked.connect(self._new)
        delete_button.clicked.connect(self._delete)

        # Load data
        self.list_view.setCurrentIndex(model.index(0, model.NAME))
        self.mapper.toFirst()

    def _market_changed(self, index):
        self.mapper.setCurrentIndex(index.row())

    def _new(self):
        row = model.new_market()
        index = model.index(row, model.NAME)
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
        self.list_view.setCurrentIndex(model.index(
            row, model.NAME))
        self.mapper.setCurrentIndex(row)


class DockWidget(QtGui.QDockWidget):

    enable_market_changed = QtCore.pyqtSignal(bool)

    def __init__(self, model_row, parent=None):
        self.row = model_row
        name = model.item(self.row, model.NAME).text()
        super(DockWidget, self).__init__(name, parent)
        self.exchanges = dict()

        base_uuid = model.item(self.row, model.BASE).text()
        base_item = tulpenmanie.commodity.model.findItems(
            base_uuid)[0]
        self.base_row = base_item.row()
        counter_uuid = model.item(self.row, model.COUNTER).text()
        counter_item = tulpenmanie.commodity.model.findItems(
            counter_uuid)[0]
        self.counter_row = counter_item.row()

        widget = QtGui.QWidget(self)
        self.setWidget(widget)
        self.layout = QtGui.QVBoxLayout()
        widget.setLayout(self.layout)

        # the action belongs to parent
        # so self can be disabled without disabling
        # the action
        self.enable_market_action = QtGui.QAction(
            tulpenmanie.translation.enable, parent)
        self.enable_market_action.setCheckable(True)
        self.enable_market_action.triggered.connect(self.enable_market)

    def add_exchange_widget(self, exchange_widget, exchange_name):
        self.layout.addWidget(exchange_widget)
        self.addAction(exchange_widget.enable_exchange_action)
        exchange_widget.enable_exchange_action.setEnabled(self.isEnabled())
        self.exchanges[exchange_name] = exchange_widget

    def enable_market(self, enable):
        self.setEnabled(enable)
        self.setVisible(enable)
        self.enable_market_changed.emit(enable)
        for action in self.actions():
            action.setEnabled(enable)

        enable_item = model.item(self.row, model.ENABLE)
        if enable:
            enable_item.setText("true")
        else:
            enable_item.setText("false")

    def closeEvent(self, event):
        self.enable_market_action.setChecked(False)
        self.enable_market(False)
        event.accept()
