from PyQt4 import QtCore, QtGui

from ui.widget import BigCommodityWidget, CommodityWidget, UuidComboBox
import providers


class EditExchangesTab(QtGui.QWidget):

    def __init__(self, parent=None):
        super(EditExchangesTab, self).__init__(parent)

        model = self.manager.exchanges_model

        list_view = QtGui.QListView()
        list_view.setModel(model)

        self.stacked_widget = QtGui.QStackedWidget()
        self.mappers = []
        for row in range(model.rowCount()):
            exchange_item = model.item(row)
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
                market_combo = UuidComboBox()
                market_combo.setModel(self.manager.markets_model)
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

            widget = QtGui.QWidget()
            widget.setLayout(market_layout)
            scroll = QtGui.QScrollArea()
            scroll.setWidget(widget)
            self.stacked_widget.addWidget(scroll)

        layout = QtGui.QHBoxLayout()
        layout.addWidget(list_view)
        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)

        # Connections
        list_view.clicked.connect(self._exchange_changed)

    def _exchange_changed(self, exchange_index):
        #row = self.manager.exchanges_model.item(exchange_index).row()
        row = exchange_index.row()
        self.stacked_widget.setCurrentIndex(row)


class ExchangeWidget(QtGui.QGroupBox):

    def __init__(self, exchange_item, market_row, remote_market, parent):
        super(ExchangeWidget, self).__init__(parent)

        # Data
        exchange_name = exchange_item.text()
        self.setTitle(exchange_name + ' - ' + remote_market)

        ExchangeClass = providers.exchanges[str(exchange_name)]
        self.exchange = ExchangeClass(remote_market)

        self.base_row = parent.base_row
        self.counter_row = parent.counter_row

        #Widgets
        side_layout = QtGui.QVBoxLayout()

        label_font = QtGui.QFont()
        label_font.setPointSize(7)
        for i, stat in enumerate(self.exchange.stats):
            label = QtGui.QLabel(stat)
            #label.setAlignment(QtCore.Qt.AlignRight)
            label.setFont(label_font)

            if self.exchange.is_counter[i]:
                widget = CommodityWidget(self.counter_row)
            else:
                widget = CommodityWidget(self.base_row)
            layout = QtGui.QHBoxLayout()
            layout.addWidget(label)
            layout.addWidget(widget)
            side_layout.addLayout(layout)

            self.exchange.signals[stat].connect(widget.setValue)

            #side_layout.addWidget(separator, 0,3,
            #                  len(self.exchange.stats),1)
        side_layout.addStretch()

        self.account_layout = QtGui.QVBoxLayout()
        layout = QtGui.QHBoxLayout()
        layout.addStretch()
        layout.addLayout(side_layout)
        layout.addLayout(self.account_layout)
        self.setLayout(layout)

        parent.add_exchange_widget(self)

    def add_account_widget(self, widget):
        self.account_layout.addWidget(widget)
