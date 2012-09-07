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

from PyQt4 import QtCore, QtGui

import tulpenmanie.market
import tulpenmanie.providers
import tulpenmanie.ui.widget


class EditExchangesWidget(QtGui.QWidget):

    def __init__(self, parent=None):
        super(EditExchangesWidget, self).__init__(parent)

        model = tulpenmanie.providers.exchanges_model

        list_view = QtGui.QListView()
        list_view.setModel(model)

        self.stacked_widget = QtGui.QStackedWidget()
        self.mappers = []
        for row in range(model.rowCount()):
            exchange_item = model.item(row)
            exchange_layout = QtGui.QGridLayout()
            grid_row = 0
            mapper = QtGui.QDataWidgetMapper()
            mapper.setModel(model)
            mapper.setRootIndex(exchange_item.index())
            mapper.setSubmitPolicy(QtGui.QDataWidgetMapper.AutoSubmit)
            self.mappers.append(mapper)

            for setting, column in exchange_item.mappings:
                label = QtGui.QLabel(setting)
                if setting in exchange_item.numeric_settings:
                    edit = QtGui.QDoubleSpinBox()
                elif setting in exchange_item.boolean_settings:
                    edit = QtGui.QCheckBox()
                else:
                    edit = QtGui.QLineEdit()
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
                mapper.setModel(model)
                mapper.setRootIndex(markets_item.index())
                mapper.setSubmitPolicy(QtGui.QDataWidgetMapper.AutoSubmit)
                self.mappers.append(mapper)

                remote_market = markets_item.child(row, 0).text()
                check_state = bool(markets_item.child(row, 1).text())
                remote_label = QtGui.QLabel(remote_market)
                check_box = QtGui.QCheckBox()
                market_combo = tulpenmanie.ui.widget.UuidComboBox()
                market_combo.setModel(tulpenmanie.market.markets_model)
                market_combo.setModelColumn(1)
                market_combo.setEnabled(check_state)
                check_box.toggled.connect(market_combo.setEnabled)

                mapper.addMapping(check_box, 1)
                mapper.addMapping(market_combo, 2, 'currentUuid')
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
        #row = tulpenmanie.providers.exchanges_model.item(exchange_index).row()
        row = exchange_index.row()
        self.stacked_widget.setCurrentIndex(row)


class ExchangeWidget(QtGui.QGroupBox):

    def __init__(self, exchange_item, market_row, remote_market, parent):
        super(ExchangeWidget, self).__init__(parent)

        # Data
        exchange_name = exchange_item.text()
        self.setTitle(exchange_name + ' - ' + remote_market)

        ExchangeClass = tulpenmanie.providers.exchanges[str(exchange_name)]
        self.exchange = ExchangeClass(remote_market)

        self.base_row = parent.base_row
        self.counter_row = parent.counter_row

        refresh_rate = exchange_item.child(0, exchange_item.REFRESH_RATE).text()
        if not refresh_rate:
            refresh_rate = 10
        refresh_rate = int(refresh_rate) * 1000

        #Widgets
        side_layout = QtGui.QGridLayout()
        side_layout.setColumnStretch(1,1)
        label_font = QtGui.QFont()
        label_font.setPointSize(7)
        for i, stat in enumerate(self.exchange.stats):
            label = QtGui.QLabel(stat)
            label.setAlignment(QtCore.Qt.AlignRight)
            label.setFont(label_font)
            if self.exchange.is_counter[i]:
                widget = tulpenmanie.ui.widget.CommodityLcdWidget(self.counter_row)
            else:
                widget = tulpenmanie.ui.widget.CommodityLcdWidget(self.base_row)
            side_layout.addWidget(label, i,0)
            side_layout.addWidget(widget, i,1)

            self.exchange.signals[stat].connect(widget.setValue)

            #side_layout.addWidget(separator, 0,3,
            #                  len(self.exchange.stats),1)
            #side_layout.addStretch()

        self.account_layout = QtGui.QVBoxLayout()
        layout = QtGui.QHBoxLayout()
        layout.addLayout(side_layout)
        layout.addLayout(self.account_layout)
        self.setLayout(layout)

        self.exchange.refresh()
        self.refresh_timer = QtCore.QTimer(self)
        self.refresh_timer.timeout.connect(self.exchange.refresh)
        self.refresh_timer.start(refresh_rate)

        parent.add_exchange_widget(self)

    def add_account_widget(self, widget):
        self.account_layout.addWidget(widget)
