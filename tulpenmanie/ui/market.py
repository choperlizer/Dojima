from PyQt4 import QtCore, QtGui

from model.market import *
from ui.widget import UuidComboBox

class EditMarketsTab(QtGui.QWidget):

    def __init__(self, parent=None):
        super(EditMarketsTab, self).__init__(parent)

        # Widgets
        self.list_view = QtGui.QListView()
        base_combo = UuidComboBox()
        counter_combo = UuidComboBox()
        enable_check = QtGui.QCheckBox()
        new_button = QtGui.QPushButton("new")
        delete_button = QtGui.QPushButton("delete")

        layout = QtGui.QGridLayout()
        layout.addWidget(self.list_view, 0,0, 2,1)

        combo_layout = QtGui.QFormLayout()
        combo_layout.addRow("&base:", base_combo)
        combo_layout.addRow("coun&ter:", counter_combo)
        combo_layout.addRow("enable:", enable_check)

        layout.addLayout(combo_layout, 0,1, 1,2)
        layout.addWidget(new_button, 1,1)
        layout.addWidget(delete_button, 1,2)
        self.setLayout(layout)

        # Model
        self.model = self.manager.markets_model

        self.list_view.setModel(self.model)
        self.list_view.setModelColumn(self.model.NAME)

        base_combo.setModel(self.manager.commodities_model)
        base_combo.setModelColumn(self.manager.commodities_model.NAME)
        counter_combo.setModel(self.manager.commodities_model)
        counter_combo.setModelColumn(self.manager.commodities_model.NAME)

        self.mapper = QtGui.QDataWidgetMapper(self)
        self.mapper.setModel(self.model)
        self.mapper.setSubmitPolicy(QtGui.QDataWidgetMapper.AutoSubmit)
        self.mapper.addMapping(base_combo, self.model.BASE, 'currentUuid')
        self.mapper.addMapping(counter_combo, self.model.COUNTER, 'currentUuid')
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
        self.list_view.setFocus()
        self.list_view.edit(index)

    def _delete(self):
        #TODO do something about exchange accounts
        row = self.list_view.currentIndex().row()
        self.model.delete_row(row)
        row -= 1
        self.list_view.setCurrentIndex(self.model.index(row, self.model.NAME))
        self.mapper.setCurrentIndex(row)

    def save(self):
        self.model.save()


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
        self.layout = QtGui.QHBoxLayout()
        widget.setLayout(self.layout)

    def add_exchange_widget(self, exchange_widget):
        self.layout.addWidget(exchange_widget)
