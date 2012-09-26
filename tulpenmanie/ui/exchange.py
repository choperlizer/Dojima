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

import tulpenmanie.exchange


logger =  logging.getLogger(__name__)


class EditWidget(QtGui.QWidget):

    def __init__(self, parent=None):
        super(EditWidget, self).__init__(parent)

        list_view = QtGui.QListView()
        list_view.setModel(tulpenmanie.exchange.model)

        self.stacked_widget = QtGui.QStackedWidget()
        self.mappers = []
        for row in range(tulpenmanie.exchange.model.rowCount()):
            exchange_item = tulpenmanie.exchange.model.item(row)
            exchange_layout = QtGui.QGridLayout()
            grid_row = 0
            mapper = QtGui.QDataWidgetMapper()
            mapper.setModel(tulpenmanie.exchange.model)
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
                mapper.setModel(tulpenmanie.exchange.model)
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


class ErrorHandling(object):

    def exchange_error_handler(self, message):
        message_box = QtGui.QMessageBox(self)
        message_box.setIcon(QtGui.QMessageBox.Warning)
        message_box.setText(message)
        message_box.exec_()


class ExchangeDockWidget(QtGui.QDockWidget, ErrorHandling):

    def __init__(self, exchange_item, exchange_market_row, parent=None):
        exchange_name = exchange_item.text()
        market_uuid = exchange_item.markets_item.child(
            exchange_market_row, exchange_item.MARKET_LOCAL).text()
        remote_pair = exchange_item.markets_item.child(
            exchange_market_row, exchange_item.MARKET_REMOTE).text()
        title = exchange_name + ' ' + remote_pair
        super(ExchangeDockWidget, self).__init__(title, parent)

        self.account_widget = None
        self.exchange_item = exchange_item
        self.market_row = exchange_market_row


        self.exchange = tulpenmanie.exchange.get_exchange_object(
            str(exchange_name), market_uuid)

        try:
            market_uuid = exchange_item.markets_item.child(
                exchange_market_row, exchange_item.MARKET_LOCAL).text()
            market_item = tulpenmanie.market.model.findItems(market_uuid)[0]
            local_market_row = market_item.row()

            base_uuid = tulpenmanie.market.model.item(
                local_market_row, tulpenmanie.market.model.BASE).text()
            base_item = tulpenmanie.commodity.model.findItems(base_uuid)[0]

            counter_uuid = tulpenmanie.market.model.item(
                local_market_row, tulpenmanie.market.model.COUNTER).text()
            counter_item = tulpenmanie.commodity.model.findItems(counter_uuid)[0]
        except IndexError:
            logger.critical("settings error, invalid model mapping in market "
                            "%s or exchange %s", market_uuid, exchange_name)
            logger.critical(msg)
            return None

        self.base_row = base_item.row()
        self.counter_row = counter_item.row()

        #Widgets
        self.widget = QtGui.QWidget(self)
        side_layout = QtGui.QGridLayout()
        side_layout.setColumnStretch(1,1)
        label_font = QtGui.QFont()
        label_font.setPointSize(7)

        row = 0
        for translation, stat in (
            (QtCore.QCoreApplication.translate(
                'ExchangeDockWidget', "ask", "best ask price"), 'ask'),
            (QtCore.QCoreApplication.translate(
                'ExchangeDockWidget', "last", "price of last trade"), 'last'),
            (QtCore.QCoreApplication.translate(
                'ExchangeDockWidget', "bid", "best bid price"), 'bid')):

            label = QtGui.QLabel(translation)
            label.setAlignment(QtCore.Qt.AlignRight)
            label.setFont(label_font)
            widget = tulpenmanie.widget.CommodityLcdWidget(self.counter_row)
            signal = getattr(self.exchange, stat + '_signal')
            signal.connect(widget.setValue)
            side_layout.addWidget(label, row,0)
            side_layout.addWidget(widget, row,1)
            row += 1

        self.account_layout = QtGui.QVBoxLayout()
        layout = QtGui.QHBoxLayout()
        layout.addLayout(side_layout)
        layout.addLayout(self.account_layout)
        self.widget.setLayout(layout)
        self.setWidget(self.widget)

        self.refresh_timer = QtCore.QTimer(self)
        self.refresh_timer.timeout.connect(self.exchange.refresh_ticker)

        self.exchange.exchange_error_signal.connect(self.exchange_error_handler)

        self.enable_exchange_action = QtGui.QAction(title, parent)
        self.enable_exchange_action.setCheckable(True)
        self.enable_exchange_action.triggered.connect(self.enable_exchange)

    def closeEvent(self, event):
        # TODO is close event ever called?
        self.enable_exchange(False)
        self.enable_exchange_action.setChecked(False)
        event.accept()

    def enable_exchange(self, enable):
        self.setEnabled(enable)
        self.setVisible(enable)
        self._enable_timer(enable)
        #self.enable_exchange_action.setChecked(enable)


        market_item = self.exchange_item.child(0, self.exchange_item.MARKETS)
        enable_item = market_item.child(self.market_row,
                                        self.exchange_item.MARKET_ENABLE)
        #TODO try str(enable)
        if enable:
            enable_item.setText("true")
        else:
            enable_item.setText("false")


    def _enable_timer(self, enable):
        # TODO test if this works
        self.setVisible(enable)
        self.setEnabled(enable)
        if enable and self.isEnabled():
            self.exchange.refresh_ticker()
            refresh_rate = self.exchange_item.child(
                0, self.exchange_item.REFRESH_RATE).text()
            if not refresh_rate:
                refresh_rate = 10000
            else:
                refresh_rate = int(refresh_rate) * 1000
            self.refresh_timer.start(refresh_rate)
        else:
            self.refresh_timer.stop()

    def add_account_widget(self, widget):
        self.account_widget = widget
        self.account_layout.addWidget(widget)

    def set_refresh_rate(self, rate):
        self.refresh_timer.start(rate * 1000)


class AccountWidget(QtGui.QWidget, ErrorHandling):

    #TODO balance signals should connect to multiple account widgets,
    # where accounts and commodities are the same

    def __init__(self, account_object, remote_pair, parent):
        super(AccountWidget, self).__init__(parent)

        self.remote_pair = str(remote_pair)
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
            QtCore.QCoreApplication.translate('AccountWidget', "ask",
                                              "as in ask order"))
        ask_order_menu = QtGui.QMenu()
        ask_limit_action = QtGui.QAction(
            QtCore.QCoreApplication.translate('AccountWidget', "limit order"),
            ask_button)
        ask_limit_action.setEnabled(False)
        ask_market_action = QtGui.QAction(
            QtCore.QCoreApplication.translate('AccountWidget', "market order"),
            ask_button)
        ask_market_action.setEnabled(False)
        ask_order_menu.addAction(ask_limit_action)
        ask_order_menu.addAction(ask_market_action)
        ask_order_menu.setDefaultAction(ask_limit_action)
        ask_button.setMenu(ask_order_menu)

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
            QtCore.QCoreApplication.translate('AccountWidget', "bid",
                                              "as in bid order"))
        bid_order_menu = QtGui.QMenu()
        bid_limit_action = QtGui.QAction(
            QtCore.QCoreApplication.translate('AccountWidget', "limit order"),
            bid_button)
        bid_limit_action.setEnabled(False)
        bid_market_action = QtGui.QAction(
            QtCore.QCoreApplication.translate('AccountWidget', "market order"),
            bid_button)
        bid_market_action.setEnabled(False)
        bid_order_menu.addAction(bid_limit_action)
        bid_order_menu.addAction(bid_market_action)
        bid_order_menu.setDefaultAction(bid_limit_action)
        bid_button.setMenu(bid_order_menu)
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
        refresh_balance_button.setToolTip(QtCore.QCoreApplication.translate(
            "AccountWidget", "refresh account balances"))
        balance_layout = QtGui.QHBoxLayout()
        base_balance_label = tulpenmanie.widget.BalanceLabel(parent.base_row)
        counter_balance_label = tulpenmanie.widget.BalanceLabel(parent.counter_row)
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

        self.account.exchange_error_signal.connect(self.exchange_error_handler)

        # Check if ready to order
        signal = getattr(self.account, self.remote_pair + '_ready_signal')
        if hasattr(self.account, 'place_ask_limit_order'):
            signal.connect(ask_limit_action.setEnabled)
            signal.connect(bid_limit_action.setEnabled)
            ask_limit_action.triggered.connect(self._ask_limit)
            bid_limit_action.triggered.connect(self._bid_limit)
        if hasattr(self.account, 'place_ask_market_order'):
            signal.connect(ask_market_action.setEnabled)
            signal.connect(bid_market_action.setEnabled)
            ask_market_action.triggered.connect(self._ask_market)
            bid_market_action.triggered.connect(self._bid_market)

        refresh_balance_button.clicked.connect(self.account.refresh_funds)
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
            # TODO sometimes redundant to refresh() and refresh_orders()
            self.account.check_order_status(self.remote_pair)
            self.account.refresh_funds()
            self.account.refresh_orders()

    def _ask_limit(self):
        amount = self.ask_amount_spin.value()
        price = self.ask_price_spin.value()
        self.account.place_ask_limit_order(self.remote_pair, amount, price)

    def _bid_limit(self):
        amount = self.bid_amount_spin.value()
        price = self.bid_price_spin.value()
        self.account.place_bid_limit_order(self.remote_pair, amount, price)

    def _ask_market(self):
        amount = self.ask_amount_spin.value()
        self.account.place_ask_market_order(self.remote_pair, amount)

    def _bid_market(self):
        amount = self.bid_amount_spin.value()
        self.account.place_bid_market_order(self.remote_pair, amount)

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
