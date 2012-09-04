from PyQt4 import QtCore, QtGui

from tulpenmanie.ui.widget import CommoditySpinBox, CommodityWidget
import tulpenmanie.providers


class EditExchangeAccountsTab(QtGui.QWidget):

    def __init__(self, parent=None):
        super(EditExchangeAccountsTab, self).__init__(parent)

        model = self.manager.exchanges_model

        exchange_combo = QtGui.QComboBox()
        exchange_combo.setModel(model)

        self.accounts_view = QtGui.QListView()
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
            for name, column in exchange_item.account_mappings[1:]:
                edit = QtGui.QLineEdit()
                if column in exchange_item.hidden_account_settings:
                    edit.setEchoMode(QtGui.QLineEdit.Password)
                layout.addRow(name, edit)
                mapper.addMapping(edit, column)
            enable_check = QtGui.QCheckBox()
            # TODO translate
            layout.addRow('enable', enable_check)
            mapper.addMapping(enable_check, exchange_item.ACCOUNT_ENABLE)
            widget.setLayout(layout)
            self.stacked_layout.addWidget(widget)

        new_button = QtGui.QPushButton("new")
        delete_button = QtGui.QPushButton("delete")

        grid_layout = QtGui.QGridLayout()
        grid_layout.setColumnStretch(1, 1)
        grid_layout.addWidget(exchange_combo, 0,0)
        grid_layout.addWidget(self.accounts_view, 1,0, 2,1)
        grid_layout.addLayout(self.stacked_layout, 0,1, 2,2,)
        grid_layout.addWidget(new_button, 2,1)
        grid_layout.addWidget(delete_button, 2,2)
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

        self.accounts_view.setRootIndex(accounts_item.index())
        self.stacked_layout.setCurrentIndex(row)
        self.mapper = self.mappers[row]
        self.mapper.toFirst()

    def _account_changed(self, index):
        self.mapper.setCurrentIndex(index.row())

    def _new(self):
        index = self.exchange_item.new_account()
        print index.row()
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


    def __init__(self, exchange_item, account_row, remote_market, parent=None):
        super(ExchangeAccountWidget, self).__init__(parent)

        # Data
        exchange_name = exchange_item.text()

        credentials = []
        for column in range(exchange_item.ACCOUNT_COLUMNS):
            credentials.append(exchange_item.accounts_item.child(account_row,
                                                                column).text())

        AccountClass = tulpenmanie.providers.accounts[str(exchange_name)]
        self.account = AccountClass(credentials, remote_market)

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

        # TODO these views should prefix/suffix price and amounts
        self.ask_orders_view = QtGui.QTableView()
        self.ask_orders_view.setModel(self.account.ask_orders_model)
        self.account.ask_orders_model.setHorizontalHeaderLabels(("id", "ask",
                                                                 "amount"))
        self.ask_orders_view.setSortingEnabled(True)
        self.bid_orders_view = QtGui.QTableView()
        self.account.bid_orders_model.setHorizontalHeaderLabels(("id", "bid",
                                                                 "amount"))
        self.bid_orders_view.setModel(self.account.bid_orders_model)
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

        #Cancel order action
        cancel_ask = QtGui.QAction("&cancel ask order", self,
                                   triggered=self._cancel_ask)
        self.ask_orders_view.addAction(cancel_ask)
        cancel_bid = QtGui.QAction("&cancel bid order", self,
                                   triggered=self._cancel_bid)
        self.bid_orders_view.addAction(cancel_bid)

        # Connect to account
        self.account.counter_balance_signal.connect(counter_balance_label.setValue)
        self.account.base_balance_signal.connect(base_balance_label.setValue)

        self.account.ask_enable_signal.connect(ask_button.setEnabled)
        self.account.bid_enable_signal.connect(bid_button.setEnabled)
        ask_button.clicked.connect(self._ask)
        bid_button.clicked.connect(self._bid)
        refresh_button.clicked.connect(self.account.refresh)
        #self.account.pending_requests_signal.connect(pending_requests_view.setNum)
        #self.account.pending_replies_signal.connect(pending_replies_view.setNum)


        # Request account info
        self.account.refresh()
        self.account.check_order_status()

        parent.add_account_widget(self)

    def _bid(self):
        amount = self.bid_amount_spin.value()
        price = self.bid_price_spin.value()
        self.account.place_bid_order(amount, price)

    def _ask(self):
        amount = self.ask_amount_spin.value()
        price = self.ask_price_spin.value()
        self.account.place_ask_order(amount, price)

    def _cancel_ask(self):
        row = self.ask_orders_view.currentIndex().row()
        order_id = self.account.ask_orders_model.item(row, 0).text()
        self.account.cancel_ask_order(order_id)

    def _cancel_bid(self):
        row = self.bid_orders_view.currentIndex().row()
        item = self.account.bid_orders_model.item(
            row, self.account.bid_orders_model.ORDER_ID)
        if item is not None:
            self.account.cancel_bid_order(item.text())
