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
import tulpenmanie.providers
import tulpenmanie.widget

logger = logging.getLogger(__name__)

model = None
menus = dict()
widgets = dict()

def create_exchanges_model(parent):
    global model
    model = _ExchangesModel(parent)
    for Item in tulpenmanie.providers.exchange_model_items:
        item = Item()
        model.appendRow(item)


class _ExchangesModel(QtGui.QStandardItemModel):

    def save(self):
        for row in range(self.rowCount()):
            item = self.item(row)
            item.save()


class ExchangeItem(QtGui.QStandardItem):

    mappings = None
    markets = None

    MARKET_COLUMNS = 3
    MARKET_REMOTE, MARKET_ENABLE, MARKET_LOCAL = range(MARKET_COLUMNS)
    market_mappings = (('enable', MARKET_ENABLE),
                       ('local_market', MARKET_LOCAL))

    def __init__(self):
        super(ExchangeItem, self).__init__(self.provider_name)
        self.settings = QtCore.QSettings()
        self.settings.beginGroup(self.provider_name)
        self.setColumnCount(self.COLUMNS)

        logger.debug("loading %s settings", self.provider_name)
        if self.mappings:
            for setting, column in self.mappings:
                item = QtGui.QStandardItem(
                    self.settings.value(setting).toString())
                self.setChild(0, column, item)

        if self.markets:
            logger.debug("loading %s markets", self.provider_name)
            self.markets_item = QtGui.QStandardItem()
            self.setChild(0, self.MARKETS, self.markets_item)
            self.settings.beginGroup('markets')
            for remote_market in self.markets:
                items = [ QtGui.QStandardItem(remote_market) ]
                self.settings.beginGroup(remote_market)
                for setting, column in self.market_mappings:
                    value = self.settings.value(setting).toString()
                    items.append(QtGui.QStandardItem(value))
                self.markets_item.appendRow(items)
                self.settings.endGroup()
            self.settings.endGroup()

    def save(self):
        logger.debug("saving %s settings", self.provider_name)
        if self.mappings:
            #!!!TODO wont save refresh rate
            for setting, column in self.mappings:
                value = self.child(0, column).text()
                self.settings.setValue(setting, value)

        if self.markets:
            logger.debug("saving %s markets", self.provider_name)
            # wipe out account information format from previous version
            self.settings.remove("accounts")
            self.settings.beginGroup('markets')
            self.settings.remove("")
            for row in range(self.markets_item.rowCount()):
                remote_market = self.markets_item.child(row, 0).text()
                self.settings.beginGroup(remote_market)
                for setting, column in self.market_mappings:
                    value = self.markets_item.child(row, column).text()
                    self.settings.setValue(setting, value)
                self.settings.endGroup()
            self.settings.endGroup()



    def new_account(self):
        columns = self.ACCOUNT_COLUMNS
        items = []
        while columns:
            items.append(QtGui.QStandardItem())
            columns -= 1
        self.accounts_item.appendRow(items)
        return items[0].index()


class ExchangeAccount(object):

    def check_order_status(self):
        self.ask_enable_signal.emit(True)
        self.bid_enable_signal.emit(True)

    def get_ask_orders_model(self, remote_pair):
        if remote_pair in self.ask_orders.keys():
            return self.ask_orders[remote_pair]
        else:
            model = tulpenmanie.model.order.OrdersModel()
            self.ask_orders[remote_pair] = model
            return model

    def get_bid_orders_model(self, remote_pair):
        if remote_pair in self.bid_orders.keys():
            return self.bid_orders[remote_pair]
        else:
            model = tulpenmanie.model.order.OrdersModel()
            self.bid_orders[remote_pair] = model
            return model


class EditWidget(QtGui.QWidget):

    def __init__(self, parent=None):
        super(EditWidget, self).__init__(parent)

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
                # TODO get required length if any and set that to
                # the edit length, or make a validator
                label = QtGui.QLabel(setting)
                if setting in exchange_item.numeric_settings:
                    edit = QtGui.QDoubleSpinBox()
                elif setting in exchange_item.boolean_settings:
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
                mapper.setModel(model)
                mapper.setRootIndex(markets_item.index())
                mapper.setSubmitPolicy(QtGui.QDataWidgetMapper.AutoSubmit)
                self.mappers.append(mapper)


                check_state = bool(markets_item.child(
                    row, exchange_item.MARKET_ENABLE).text())
                remote_label = QtGui.QLabel(
                    markets_item.child(
                        row, exchange_item.MARKET_REMOTE).text())
                check_box = QtGui.QCheckBox()
                market_combo = tulpenmanie.widget.UuidComboBox()
                market_combo.setModel(tulpenmanie.market.model)
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


class ExchangeWidget(QtGui.QGroupBox):

    def __init__(self, exchange_item, market_row, remote_market, parent):
        super(ExchangeWidget, self).__init__(parent)
        self.account_widget = None

        self.row = market_row
        # Data
        exchange_name = str(exchange_item.text())
        title = exchange_name + ' - ' + remote_market
        self.setTitle(title)

        ExchangeClass = tulpenmanie.providers.exchanges[exchange_name]
        self.exchange_item = exchange_item
        self.exchange = ExchangeClass(remote_market)

        self.base_row = parent.base_row
        self.counter_row = parent.counter_row

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
                widget = tulpenmanie.widget.CommodityLcdWidget(self.counter_row)
            else:
                widget = tulpenmanie.widget.CommodityLcdWidget(self.base_row)
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

        self.enable_exchange_action = QtGui.QAction(title, parent)
        self.enable_exchange_action.setCheckable(True)
        self.enable_exchange_action.triggered.connect(self.enable_exchange)

        self.refresh_timer = QtCore.QTimer(self)
        self.refresh_timer.timeout.connect(self.exchange.refresh)

        parent.add_exchange_widget(self, exchange_name)
        parent.enable_market_action.triggered.connect(self._enable_timer)
        parent.enable_market_changed.connect(self._enable_timer)


    def add_account_widget(self, widget):
        self.account_widget = widget
        self.account_layout.addWidget(widget)

    def enable_exchange(self, enable):
        self.setVisible(enable)
        self.setEnabled(enable)

        market_item = self.exchange_item.child(0, self.exchange_item.MARKETS)
        enable_item = market_item.child(self.row,
                                        self.exchange_item.MARKET_ENABLE)
        if enable:
            enable_item.setText("true")
        else:
            enable_item.setText("false")

        if enable and self.parent().isEnabled():
            self._enable_timer(True)
        else:
            self._enable_timer(False)

    def _enable_timer(self, enable):
        # TODO test if this works
        self.setVisible(enable)
        self.setEnabled(enable)
        if enable and self.isEnabled():
            self.exchange.refresh()
            refresh_rate = self.exchange_item.child(
                0, self.exchange_item.REFRESH_RATE).text()
            if not refresh_rate:
                refresh_rate = 10000
            else:
                refresh_rate = int(refresh_rate) * 1000
            self.refresh_timer.start(refresh_rate)
        else:
            self.refresh_timer.stop()


class AccountWidget(QtGui.QWidget):

    #TODO balance signals should connect to multiple account widgets,
    # where accounts and commodities are the same

    def __init__(self, account_object, remote_market, parent):
        super(AccountWidget, self).__init__(parent)

        self.remote_pair = str(remote_market)
        #TODO this will break if pair does not have 3 character codes
        base = self.remote_pair[:3]
        counter = self.remote_pair[-3:]

        # Data
        self.account = account_object

        # Create UI
        # TODO
        # make a parent widget to hold ask stuff and handle the enter-key
        ask_widget = QtGui.QWidget(self)
        ask_layout = QtGui.QGridLayout()
        self.ask_amount_spin = tulpenmanie.widget.CommoditySpinBox(
            parent.base_row)
        self.ask_price_spin = tulpenmanie.widget.CommoditySpinBox(
            parent.counter_row)
        ask_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate('exchange account widget', 'ask'))
        ask_button.setEnabled(False)
        ask_layout.addWidget(self.ask_amount_spin, 0,0)
        ask_layout.addWidget(self.ask_price_spin, 0,1)
        ask_layout.addWidget(ask_button, 1,0, 1,2)
        ask_widget.setLayout(ask_layout)

        bid_widget = QtGui.QWidget(self)
        bid_layout = QtGui.QGridLayout()
        self.bid_amount_spin = tulpenmanie.widget.CommoditySpinBox(
            parent.base_row)
        self.bid_price_spin = tulpenmanie.widget.CommoditySpinBox(
            parent.counter_row)
        bid_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate('exchange account widget', 'bid'))
        bid_button.setEnabled(False)
        bid_layout.addWidget(self.bid_amount_spin, 0,0)
        bid_layout.addWidget(self.bid_price_spin, 0,1)
        bid_layout.addWidget(bid_button, 1,0, 1,2)
        bid_widget.setLayout(bid_layout)

        for spin in (self.ask_amount_spin, self.ask_price_spin,
                     self.bid_amount_spin, self.bid_price_spin):
            spin.setMaximum(999999)

        self.ask_model = self.account.get_ask_orders_model(self.remote_pair)
        self.bid_model = self.account.get_bid_orders_model(self.remote_pair)
        self.ask_model.setHorizontalHeaderLabels(("id", "ask", "amount"))
        self.bid_model.setHorizontalHeaderLabels(("id", "bid", "amount"))

        # TODO these views should prefix/suffix price and amounts
        self.ask_orders_view = QtGui.QTableView()
        self.ask_orders_view.setModel(self.ask_model)
        ask_layout.addWidget(self.ask_orders_view, 2,0, 1,2)

        self.bid_orders_view = QtGui.QTableView()
        self.bid_orders_view.setModel(self.bid_model)
        bid_layout.addWidget(self.bid_orders_view, 2,0, 1,2)

        for view in self.ask_orders_view, self.bid_orders_view:
            view.setSelectionMode(QtGui.QListView.SingleSelection)
            view.setSelectionBehavior(QtGui.QListView.SelectRows)
            view.setColumnHidden(0, True)
            view.setShowGrid(False)
            view.verticalHeader().hide()
            view.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

        refresh_balance_button = QtGui.QPushButton("balance")

        balance_layout = QtGui.QHBoxLayout()
        balance_label = QtGui.QLabel(
            QtCore.QCoreApplication.translate('exchange account widget',
                                              ':balance:') )
        base_balance_label = tulpenmanie.widget.CommodityWidget(parent.base_row)
        counter_balance_label = tulpenmanie.widget.CommodityWidget(parent.counter_row)
        for label in base_balance_label, counter_balance_label:
            label.setAlignment(QtCore.Qt.AlignHCenter)
            balance_font = QtGui.QFont()
            balance_font.setPointSize(13)
            label.setFont(balance_font)
        balance_layout.addWidget(base_balance_label)
        balance_layout.addWidget(refresh_balance_button)
        balance_layout.addWidget(counter_balance_label)


        #pending_requests_label = QtGui.QLabel("pending requests: ")
        #pending_requests_view = QtGui.QLabel()
        #pending_replies_label = QtGui.QLabel("pending replies: ")
        #pending_replies_view = QtGui.QLabel()

        # Layout
        layout = QtGui.QGridLayout()
        layout.addLayout(balance_layout, 0,0, 1,2)
        layout.addWidget(ask_widget, 1,0)
        layout.addWidget(bid_widget, 1,1)

        #network_layout = QtGui.QHBoxLayout()
        #network_layout.addStretch()
        #network_layout.addWidget(pending_requests_label)
        #network_layout.addWidget(pending_requests_view)
        #network_layout.addWidget(pending_replies_label)
        #network_layout.addWidget(pending_replies_view)
        #layout.addLayout(network_layout)

        self.setLayout(layout)

        #Refresh orders action
        refresh_orders_action = QtGui.QAction(
            "&refresh orders", self, triggered=self.account.refresh_orders)
        #Cancel order action
        cancel_ask_action = QtGui.QAction("&cancel ask order", self,
                                   triggered=self._cancel_ask)
        self.ask_orders_view.addAction(cancel_ask_action)
        self.ask_orders_view.addAction(refresh_orders_action)
        cancel_bid_action = QtGui.QAction("&cancel bid order", self,
                                   triggered=self._cancel_bid)
        self.bid_orders_view.addAction(cancel_bid_action)
        self.bid_orders_view.addAction(refresh_orders_action)

        # Connect to account
        signal = getattr(self.account, counter + '_balance_signal')
        signal.connect(counter_balance_label.setValue)
        signal = getattr(self.account, counter + '_balance_changed_signal', None)
        if signal:
            signal.connect(counter_balance_label.change_value)

        signal = getattr(self.account, base + '_balance_signal')
        signal.connect(base_balance_label.setValue)
        signal = getattr(self.account, base + '_balance_changed_signal', None)
        if signal:
            signal.connect(base_balance_label.change_value)

        signal = getattr(self.account, self.remote_pair + '_ready_signal')
        signal.connect(ask_button.setEnabled)
        signal.connect(bid_button.setEnabled)
        ask_button.clicked.connect(self._ask)
        bid_button.clicked.connect(self._bid)
        refresh_balance_button.clicked.connect(self.account.refresh)
        #self.account.pending_requests_signal.connect(pending_requests_view.setNum)
        #self.account.pending_replies_signal.connect(pending_replies_view.setNum)

        #self.enable_action = QtGui.QAction(self)
        #self.enable_action.setCheckable(True)
        #parent.enable_action.toggled.connect(self.enable_action.toggle)
        #self.enable_action.toggled.connect(self.enable)

        parent.add_account_widget(self)
        parent.enable_exchange_action.toggled.connect(self.enable_account)

    def enable_account(self, enable):
        if enable:
            self.account.check_order_status(self.remote_pair)
            self.account.refresh()
            self.account.refresh_orders()

    def _bid(self):
        amount = self.bid_amount_spin.value()
        price = self.bid_price_spin.value()
        self.account.place_bid_order(self.remote_pair, amount, price)

    def _ask(self):
        amount = self.ask_amount_spin.value()
        price = self.ask_price_spin.value()
        self.account.place_ask_order(self.remote_pair, amount, price)

    def _cancel_ask(self):
        row = self.ask_orders_view.currentIndex().row()
        item = self.ask_model.item(row, self.bid_model.ORDER_ID)
        if item:
            order_id = item.text()
            self.account.cancel_ask_order(self.remote_pair, item.text())

    def _cancel_bid(self):
        row = self.bid_orders_view.currentIndex().row()
        item = self.bid_model.item(row, self.bid_model.ORDER_ID)
        if item:
            order_id = item.text()
            self.account.cancel_bid_order(self.remote_pair, item.text())
