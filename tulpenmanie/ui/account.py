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

from tulpenmanie.ui.widget import CommoditySpinBox, CommodityWidget
import tulpenmanie.providers
import tulpenmanie.translations

class EditAccountsWidget(QtGui.QWidget):

    def __init__(self, parent=None):
        super(EditAccountsWidget, self).__init__(parent)

        model = self.manager.exchanges_model

        exchange_label = QtGui.QLabel(tulpenmanie.translations.exchange)
        exchange_combo = QtGui.QComboBox()
        exchange_label.setBuddy(exchange_combo)
        exchange_combo.setModel(model)

        self.account_id_label = QtGui.QLabel(tulpenmanie.translations.account_id)
        self.accounts_view = QtGui.QListView()
        self.account_id_label.setBuddy(self.accounts_view)
        self.accounts_view.setModel(model)

        self.stacked_layout = QtGui.QStackedLayout()
        self.mappers = []
        for exchange_row in range(model.rowCount()):
            exchange_item = model.item(exchange_row)
            accounts_item = exchange_item.child(0, exchange_item.ACCOUNTS)
            widget = QtGui.QWidget()
            mapper = QtGui.QDataWidgetMapper()
            mapper.setModel(model)
            mapper.setRootIndex(accounts_item.index())
            mapper.setSubmitPolicy(QtGui.QDataWidgetMapper.AutoSubmit)
            self.mappers.append(mapper)

            layout = QtGui.QFormLayout()
            # first two columns are id and enable
            for name, column in exchange_item.account_mappings[2:]:
                edit = QtGui.QLineEdit()
                if column in exchange_item.hidden_account_settings:
                    edit.setEchoMode(QtGui.QLineEdit.Password)
                layout.addRow(name, edit)
                mapper.addMapping(edit, column)
            enable_check = QtGui.QCheckBox()
            layout.addRow(tulpenmanie.translations.enable, enable_check)
            mapper.addMapping(enable_check, exchange_item.ACCOUNT_ENABLE)
            widget.setLayout(layout)
            self.stacked_layout.addWidget(widget)

        new_button = QtGui.QPushButton("new")
        delete_button = QtGui.QPushButton("delete")

        grid_layout = QtGui.QGridLayout()
        grid_layout.addWidget(exchange_label, 0,0)
        grid_layout.addWidget(exchange_combo, 1,0)
        grid_layout.addWidget(self.account_id_label, 2,0)
        grid_layout.addWidget(self.accounts_view, 3,0, 2,1)
        grid_layout.addLayout(self.stacked_layout, 1,1, 3,2,)
        grid_layout.addWidget(new_button, 4,1)
        grid_layout.addWidget(delete_button, 4,2)
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setRowStretch(3, 1)
        self.setLayout(grid_layout)

        # Connections
        exchange_combo.currentIndexChanged.connect(self._exchange_changed)
        self.accounts_view.clicked.connect(self._account_changed)

        new_button.clicked.connect(self._new)
        delete_button.clicked.connect(self._delete)

        # Load data
        self._exchange_changed(0)

    def _exchange_changed(self, row):
        self.exchange_item = self.manager.exchanges_model.item(row)
        accounts_item = self.exchange_item.child(0, self.exchange_item.ACCOUNTS)

        self.account_id_label.setText(self.exchange_item.account_mappings[0][0])
        self.accounts_view.setRootIndex(accounts_item.index())
        self.stacked_layout.setCurrentIndex(row)
        self.mapper = self.mappers[row]
        self.mapper.toFirst()

    def _account_changed(self, index):
        self.mapper.setCurrentIndex(index.row())

    def _new(self):
        index = self.exchange_item.new_account()
        self.accounts_view.setCurrentIndex(index)
        self.mapper.setCurrentModelIndex(index)
        self.accounts_view.setFocus()
        self.accounts_view.edit(index)

    def _delete(self):
        row = self.accounts_view.currentIndex().row()
        self.exchange_item.accounts_item.removeRow(row)
        row -= 1
        if row < 0:
            row = 0
        next_account = self.exchange_item.accounts_item.child(row)
        self.accounts_view.setCurrentIndex(next_account.index())
        self.mapper.setCurrentIndex(row)


class ExchangeAccountWidget(QtGui.QWidget):

    #TODO balance signals should connect to multiple account widgets,
    # where accounts and commodities are the same

    def __init__(self, account_object, remote_market, parent):
        super(ExchangeAccountWidget, self).__init__(parent)

        self.remote_pair = str(remote_market)
        #TODO this will break if pair does not have 3 character codes
        base = self.remote_pair[:3]
        counter = self.remote_pair[-3:]

        # Data
        self.account = account_object

        # Create UI
        self.ask_amount_spin = CommoditySpinBox(parent.base_row)

        self.ask_price_spin = CommoditySpinBox(parent.counter_row)
        ask_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate('exchange account widget', 'ask'))
        ask_button.setEnabled(False)

        self.bid_amount_spin = CommoditySpinBox(parent.base_row)
        self.bid_price_spin = CommoditySpinBox(parent.counter_row)
        bid_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate('exchange account widget', 'bid'))
        bid_button.setEnabled(False)

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

        self.bid_orders_view = QtGui.QTableView()
        self.bid_orders_view.setModel(self.bid_model)

        for view in self.ask_orders_view, self.bid_orders_view:
            view.setSelectionMode(QtGui.QListView.SingleSelection)
            view.setSelectionBehavior(QtGui.QListView.SelectRows)
            view.setColumnHidden(0, True)
            view.setShowGrid(False)
            view.verticalHeader().hide()
            view.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

        refresh_button = QtGui.QPushButton("refresh")

        balance_label = QtGui.QLabel(
            QtCore.QCoreApplication.translate('exchange account widget',
                                              ':balance:') )
        base_balance_label = CommodityWidget(parent.base_row)
        counter_balance_label = CommodityWidget(parent.counter_row)
        for label in balance_label, base_balance_label, counter_balance_label:
            label.setAlignment(QtCore.Qt.AlignHCenter)

        #pending_requests_label = QtGui.QLabel("pending requests: ")
        #pending_requests_view = QtGui.QLabel()
        #pending_replies_label = QtGui.QLabel("pending replies: ")
        #pending_replies_view = QtGui.QLabel()

        # Layout
        layout = QtGui.QVBoxLayout()

        upper_layout = QtGui.QGridLayout()


        upper_layout.addWidget(base_balance_label, 0,1, 1,2)
        upper_layout.addWidget(balance_label, 0,2, 1,2)
        upper_layout.addWidget(counter_balance_label, 0,3, 1,2)

        upper_layout.addWidget(refresh_button, 0,5)

        upper_layout.addWidget(self.ask_amount_spin, 1,0)
        upper_layout.addWidget(self.ask_price_spin, 1,1)
        upper_layout.addWidget(ask_button, 1,2)

        upper_layout.addWidget(self.bid_amount_spin, 1,3)
        upper_layout.addWidget(self.bid_price_spin, 1,4)
        upper_layout.addWidget(bid_button, 1,5)

        upper_layout.addWidget(self.ask_orders_view, 2,0, 1,3)
        upper_layout.addWidget(self.bid_orders_view, 2,3, 1,3)
        layout.addLayout(upper_layout)

        network_layout = QtGui.QHBoxLayout()
        network_layout.addStretch()
        #network_layout.addWidget(pending_requests_label)
        #network_layout.addWidget(pending_requests_view)
        #network_layout.addWidget(pending_replies_label)
        #network_layout.addWidget(pending_replies_view)
        layout.addLayout(network_layout)

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
        signal = getattr(self.account, base + '_balance_signal')
        signal.connect(base_balance_label.setValue)

        signal = getattr(self.account, self.remote_pair + '_ready_signal')
        signal.connect(ask_button.setEnabled)
        signal.connect(bid_button.setEnabled)
        ask_button.clicked.connect(self._ask)
        bid_button.clicked.connect(self._bid)
        refresh_button.clicked.connect(self.account.refresh)
        #self.account.pending_requests_signal.connect(pending_requests_view.setNum)
        #self.account.pending_replies_signal.connect(pending_replies_view.setNum)

        # Request account info
        self.account.check_order_status(self.remote_pair)
        self.account.refresh()
        self.account.refresh_orders()

        parent.add_account_widget(self)

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
