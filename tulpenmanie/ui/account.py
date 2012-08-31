from PyQt4 import QtCore, QtGui

from ui.widget import CommoditySpinBox, CommodityWidget

class EditExchangeAccountsTab(QtGui.QWidget):

    def __init__(self, parent=None):
        super(EditExchangeAccountsTab, self).__init__(parent)

        # Widgets
        exchange_combo = QtGui.QComboBox()
        self.list_view = QtGui.QListView()
        self.edit_area = QtGui.QStackedLayout()
        new_button = QtGui.QPushButton("new")
        delete_button = QtGui.QPushButton("delete")

        # Models
        ## BAD this
        for exchange in self.manager.exchange_classes.values():
            exchange_combo.addItem(exchange.name)

        self.models = self.manager.accounts_models.values()
        self.mappers = []
        for model in self.models:
            widget = QtGui.QWidget()
            layout = QtGui.QFormLayout()
            mapper = QtGui.QDataWidgetMapper()
            mapper.setModel(model)
            mapper.setSubmitPolicy(QtGui.QDataWidgetMapper.AutoSubmit)
            for name, column in model.MAPPINGS[2:]:
                edit = QtGui.QLineEdit()
                if column in model.hide:
                    edit.setEchoMode(QtGui.QLineEdit.Password)
                # TODO should set field validators
                layout.addRow(name, edit)
                mapper.addMapping(edit, column)
            enable_check = QtGui.QCheckBox()
            # TODO translate
            layout.addRow('enable', enable_check)
            mapper.addMapping(enable_check, model.ENABLE)
            widget.setLayout(layout)
            self.edit_area.addWidget(widget)
            self.mappers.append(mapper)

        grid_layout = QtGui.QGridLayout()
        grid_layout.addWidget(exchange_combo, 0,0)
        grid_layout.addWidget(self.list_view, 1,0, 2,1)
        grid_layout.addLayout(self.edit_area, 0,1, 2,2,)
        grid_layout.addWidget(new_button, 2,1)
        grid_layout.addWidget(delete_button, 2,2)
        self.setLayout(grid_layout)

        # Connections
        exchange_combo.currentIndexChanged.connect(self._exchange_changed)
        self.list_view.activated.connect(self._account_changed)

        new_button.clicked.connect(self._new)
        delete_button.clicked.connect(self._delete)

        # Load data
        self._exchange_changed(0)

    def _exchange_changed(self, row):
        self.model = self.models[row]
        self.mapper = self.mappers[row]

        self.list_view.setModel(self.model)
        self.list_view.setModelColumn(self.model.NAME)
        self.edit_area.setCurrentIndex(row)
        self.mapper.toFirst()

    def _account_changed(self, index):
        self.mapper.setCurrentIndex(index.row())

    def _new(self):
        row = self.model.new_account()
        index = self.model.index(row, self.model.NAME)
        self.list_view.setCurrentIndex(index)
        self.mapper.setCurrentIndex(row)
        self.list_view.setFocus()
        self.list_view.edit(index)

    def _delete(self):
        row = self.list_view.currentIndex().row()
        self.model.delete_row(row)
        row -= 1
        self.list_view.setCurrentIndex(row)
        self.mapper.setCurrentIndex(row)

    def save(self):
        self.model.save()


class ExchangeAccountWidget(QtGui.QWidget):

    def __init__(self, exchange_name, exchange_row, account_row,
                 base_row, counter_row, parent=None):
        super(ExchangeAccountWidget, self).__init__(parent)

        #BAD too many arguments

        # Model
        model = self.manager.accounts_models[exchange_name]
        credentials = []
        for column in range(model.COLUMNS):
            credentials.append(model.item(account_row, column).text())
        model = self.manager.exchanges_model
        remote = model.item(exchange_row, model.REMOTE).text()

        AccountClass = self.manager.exchange_account_classes[exchange_name]
        self.account = AccountClass(credentials, remote)

        # Create UI
        self.ask_amount_spin = CommoditySpinBox(base_row)
        self.ask_price_spin = CommoditySpinBox(counter_row)
        ask_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate('exchange account widget', 'ask'))
        ask_button.setEnabled(False)

        self.bid_amount_spin = CommoditySpinBox(base_row)
        self.bid_price_spin = CommoditySpinBox(counter_row)
        bid_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate('exchange account widget', 'bid'))
        bid_button.setEnabled(False)

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
        base_balance_label = CommodityWidget(base_row)
        counter_balance_label = CommodityWidget(counter_row)
        for label in balance_label, base_balance_label, counter_balance_label:
            label.setAlignment(QtCore.Qt.AlignHCenter)

        pending_requests_label = QtGui.QLabel("pending requests: ")
        pending_requests_view = QtGui.QLabel()
        pending_replies_label = QtGui.QLabel("pending replies: ")
        pending_replies_view = QtGui.QLabel()

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
        network_layout.addWidget(pending_requests_label)
        network_layout.addWidget(pending_requests_view)
        network_layout.addWidget(pending_replies_label)
        network_layout.addWidget(pending_replies_view)
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
        self.account.pending_requests_signal.connect(pending_requests_view.setNum)
        self.account.pending_replies_signal.connect(pending_replies_view.setNum)


        # Request account info
        self.account.refresh()
        self.account.check_order_status()

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
