from PyQt4 import QtCore, QtGui

from tulpenmanie.model.exchange import *
from tulpenmanie.ui.widget import BigCommodityWidget, CommodityWidget, UuidComboBox

class EditExchangesTab(QtGui.QWidget):

    def __init__(self, parent=None):
        super(EditExchangesTab, self).__init__(parent)

        model = self.manager.exchanges_model

        # Widgets
        self.list_view = QtGui.QListView()
        market_combo = UuidComboBox()
        provider_combo = QtGui.QComboBox()
        self.remote_combo = QtGui.QComboBox()
        enable_check = QtGui.QCheckBox()

        new_button = QtGui.QPushButton("new")
        delete_button = QtGui.QPushButton("delete")

        edit_layout = QtGui.QFormLayout()
        edit_layout.addRow("&local market:", market_combo)
        edit_layout.addRow("&provider:", provider_combo)
        edit_layout.addRow("&remote market:", self.remote_combo)
        edit_layout.addRow("enabled", enable_check)

        grid_layout = QtGui.QGridLayout()
        grid_layout.addWidget(self.list_view, 0,0, 2,1)
        grid_layout.addLayout(edit_layout, 0,1, 1,2)
        grid_layout.addWidget(new_button, 1,1)
        grid_layout.addWidget(delete_button, 1,2)
        self.setLayout(grid_layout)

        # Model
        self.model = self.manager.exchanges_model
        # maybe could be better
        self.provider_model = QtGui.QStandardItemModel()
        for Exchange in self.manager.exchange_classes.values():
            provider_item = QtGui.QStandardItem(Exchange.name)
            self.provider_model.appendRow(provider_item)
            for remote in Exchange.markets:
                remote_item = QtGui.QStandardItem(remote)
                provider_item.appendRow(remote_item)

        self.list_view.setModel(self.model)
        self.list_view.setModelColumn(self.model.NAME)
        market_combo.setModel(self.manager.markets_model)
        market_combo.setModelColumn(self.manager.markets_model.NAME)


        for Exchange in self.manager.exchange_classes.values():
            provider_combo.addItem(Exchange.name)

        self.mapper = QtGui.QDataWidgetMapper(self)
        self.mapper.setModel(self.model)
        self.mapper.setSubmitPolicy(QtGui.QDataWidgetMapper.AutoSubmit)
        self.mapper.addMapping(market_combo, model.MARKET, 'currentUuid')
        self.mapper.addMapping(provider_combo, model.PROVIDER)#, 'currentText')
        self.mapper.addMapping(self.remote_combo, model.REMOTE)#, 'currentText')
        self.mapper.addMapping(enable_check, model.ENABLE)

        # Connections
        self.list_view.activated.connect(self.mapper.setCurrentModelIndex)
        provider_combo.currentIndexChanged.connect(self._provider_changed)
        new_button.clicked.connect(self._new)
        delete_button.clicked.connect(self._delete)

        # Load data
        self.list_view.setCurrentIndex(self.model.index(0, model.NAME))
        self.mapper.toFirst()
        self.remote_combo.setRootModelIndex(self.provider_model.index(0,0))

    def _provider_changed(self, row):
        pass



    def _new(self):
        row = self.model.new_exchange()
        index = self.model.index(row, self.model.NAME)
        self.list_view.setCurrentIndex(index)
        self.mapper.setCurrentIndex(row)
        self.list_view.setFocus()
        self.list_view.edit(index)

    def _delete(self):
        row = self.list_view.currentIndex().row()
        self.model.delete_row(row)
        row -= 1
        self.list_view.setCurrentIndex(self.model.index(row, self.model.NAME))
        self.mapper.setCurrentIndex(row)

    def save(self):
        self.model.save()


class ExchangeWidget(QtGui.QGroupBox):

    def __init__(self, exchange_row, base_row, counter_row, parent=None):
        model = self.manager.exchanges_model
        title = model.item(exchange_row, model.NAME).text()
        super(ExchangeWidget, self).__init__(title, parent)

        # Data
        model = self.manager.exchanges_model
        provider = str(model.item(exchange_row, model.PROVIDER).text())
        remote = model.item(exchange_row, model.REMOTE).text()
        ExchangeClass = self.manager.exchange_classes[provider]
        self.exchange = ExchangeClass(remote)

        #Widgets
        side_layout = QtGui.QVBoxLayout()

        label_font = QtGui.QFont()
        label_font.setPointSize(7)
        for i, stat in enumerate(self.exchange.stats):
            label = QtGui.QLabel(stat)
            #label.setAlignment(QtCore.Qt.AlignRight)
            label.setFont(label_font)

            if self.exchange.is_counter[i]:
                widget = CommodityWidget(counter_row)
            else:
                widget = CommodityWidget(base_row)
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
        self.exchange.refresh()

    def add_account_widget(self, widget):
        self.account_layout.addWidget(widget)
