from PyQt4 import QtCore, QtGui

from model import market as Market

from ui.edit import EditMarketsDialog, EditProvidersDialog
from ui.market import MarketDockWidget
from ui.exchange import ExchangeWidget
from ui.account import ExchangeAccountWidget


class MainWindow(QtGui.QMainWindow):

    def __init__(self, parent=None):
        super (MainWindow, self).__init__(parent)
        self.market_docks = dict()

        edit_markets_action = QtGui.QAction(
            "&markets", self, shortcut="Ctrl+E",
            triggered=self._edit_markets)

        edit_providers_action = QtGui.QAction(
            "&providers", self, shortcut="Ctrl+P",
            triggered=self._edit_providers)

        self.markets_menu = QtGui.QMenu("markets", self)
        self.menuBar().addMenu(self.markets_menu)
        options_menu = QtGui.QMenu("options", self)
        options_menu.addAction(edit_markets_action)
        options_menu.addAction(edit_providers_action)
        self.menuBar().addMenu(options_menu)

        # parse markets
        markets_model = self.manager.markets_model
        for market_row in range(markets_model.rowCount()):
            enable = markets_model.item(market_row, markets_model.ENABLE).text()
            if enable == 'true':
                market_uuid = markets_model.item(market_row,
                                                 markets_model.UUID).text()
                ## Create market
                base_uuid = markets_model.item(market_row,
                                               markets_model.BASE).text()
                base_item = self.manager.commodities_model.findItems(base_uuid)[0]
                base_row = base_item.row()
                counter_uuid = markets_model.item(market_row,
                                                  markets_model.COUNTER).text()
                counter_item = self.manager.commodities_model.findItems(counter_uuid)[0]
                counter_row = counter_item.row()

                ### make dock
                dock = MarketDockWidget(market_row, self)
                dock.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea)
                self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock)
                toggle_action = dock.toggleViewAction()
                self.markets_menu.addAction(toggle_action)

                # parse exchanges
                exchange_model = self.manager.exchanges_model
                for exchange_row in range(exchange_model.rowCount()):
                    this_market_uuid = exchange_model.item(
                        exchange_row, exchange_model.MARKET).text()
                    enable = exchange_model.item(
                        exchange_row, exchange_model.ENABLE).text()
                    if enable == 'true'and this_market_uuid == market_uuid:
                        ## make exchange widget
                        exchange_widget = ExchangeWidget(exchange_row,
                                                         base_row, counter_row)
                        dock.add_exchange_widget(exchange_widget)
                        ### BAD ###
                        exchange_name = exchange_widget.exchange.name
                        ###     ###
                        # parse exchange accounts
                        account_model = self.manager.accounts_models[exchange_name]
                        for account_row in range(account_model.rowCount()):
                            enable = account_model.item(account_row,
                                                account_model.ENABLE).text()
                            if enable == 'true':
                                account_widget = ExchangeAccountWidget(
                                    exchange_name, exchange_row, account_row,
                                    base_row, counter_row)
                                exchange_widget.add_account_widget(
                                    account_widget)
            else:
                # make one of those enable actions
                pass

    def _edit_markets(self):
        dialog = EditMarketsDialog(self)
        dialog.exec_()

    def _edit_providers(self):
        dialog = EditProvidersDialog(self)
        dialog.exec_()

    def closeEvent(self, event):
        self.manager.markets_model.save()
        event.accept()
