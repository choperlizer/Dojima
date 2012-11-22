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

from PyQt4 import QtCore, QtGui

import dojima.ui.widget
from dojima.model.markets import markets_model
from dojima.model.exchanges import exchanges_model


class EditWidget(QtGui.QWidget):

    def __init__(self, parent=None):
        super(EditWidget, self).__init__(parent)

        list_view = QtGui.QListView()
        list_view.setModel(exchanges_model)

        self.stacked_widget = QtGui.QStackedWidget()
        self.mappers = []
        for row in range(exchanges_model.rowCount()):
            exchange_item = exchanges_model.item(row)
            exchange_layout = QtGui.QGridLayout()
            grid_row = 0
            mapper = QtGui.QDataWidgetMapper()
            mapper.setModel(exchanges_model)
            mapper.setRootIndex(exchange_item.index())
            mapper.setSubmitPolicy(QtGui.QDataWidgetMapper.AutoSubmit)
            self.mappers.append(mapper)

            for setting, column in exchange_item.mappings:
                # TODO get required length if any and set that to
                # the edit length, or make a validator
                label = QtGui.QLabel(setting)
                if column in exchange_item.numeric_settings:
                    edit = QtGui.QDoubleSpinBox()
                elif column in exchange_item.boolean_settings:
                    edit = QtGui.QCheckBox()
                else:
                    edit = QtGui.QLineEdit()
                    if column in exchange_item.hidden_settings:
                        edit.setEchoMode(QtGui.QLineEdit.Password)
                exchange_layout.addWidget(label, grid_row,0)
                exchange_layout.addWidget(edit, grid_row,1)
                grid_row += 1
                mapper.addMapping(edit, column)
            mapper.toFirst()
            mapper.setCurrentIndex(row)

            markets_item = exchange_item.child(0, exchange_item.MARKETS)
            market_layout = QtGui.QGridLayout()
            for row in range(markets_item.rowCount()):

                mapper = QtGui.QDataWidgetMapper()
                mapper.setModel(exchanges_model)
                mapper.setRootIndex(markets_item.index())
                mapper.setSubmitPolicy(QtGui.QDataWidgetMapper.AutoSubmit)
                self.mappers.append(mapper)

                check_state = bool(markets_item.child(
                    row, exchange_item.MARKET_ENABLE).text())
                remote_label = QtGui.QLabel(
                    markets_item.child(
                        row, exchange_item.MARKET_REMOTE).text())
                check_box = QtGui.QCheckBox()
                market_combo = dojima.ui.widget.UuidComboBox()
                market_combo.setModel(markets_model)
                market_combo.setModelColumn(1)
                market_combo.setEnabled(check_state)
                check_box.toggled.connect(market_combo.setEnabled)

                mapper.addMapping(check_box, exchange_item.MARKET_ENABLE)
                mapper.addMapping(market_combo,
                                  exchange_item.MARKET_LOCAL, 'currentUuid')
                mapper.toFirst()
                mapper.setCurrentIndex(row)
                market_layout.addWidget(remote_label, row,0)
                market_layout.addWidget(check_box, row,1)
                market_layout.addWidget(market_combo, row,2)

            markets_widget = QtGui.QWidget()
            markets_widget.setLayout(market_layout)
            scroll = QtGui.QScrollArea()
            scroll.setWidget(markets_widget)

            exchange_layout.addWidget(scroll, grid_row,0, 1,2)
            exchange_widget = QtGui.QWidget()
            exchange_widget.setLayout(exchange_layout)

            self.stacked_widget.addWidget(exchange_widget)

        layout = QtGui.QHBoxLayout()
        layout.addWidget(list_view)
        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)

        # Connections
        list_view.clicked.connect(self._exchange_changed)

    def _exchange_changed(self, exchange_index):
        row = exchange_index.row()
        self.stacked_widget.setCurrentIndex(row)
