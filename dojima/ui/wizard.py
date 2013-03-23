# Dojima, a markets client.
# Copyright (C) 2013  Emery Hemingway
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

import dojima.exchanges

class AddMarketsWizard(QtGui.QWizard):

    def __init__(self, parent):
        super(AddMarketsWizard, self).__init__(parent)
        self.main_window = parent
        self.addPage(SelectExchangePage(self))

    """
    def done(self, result):
        self.parent().reloadMarkets(True)
    # can't just do it like that because every market for a given scale
    # would be shown.
    """


class SelectExchangePage(QtGui.QWizardPage):

    def __init__(self, parent):
        super(SelectExchangePage, self).__init__(parent)
        self.setTitle(
            QtCore.QCoreApplication.translate('AddMarketsWizard',
                                              "Exchanges",
                                              "Title of the select exchange "
                                              "page of the add markets wizard."))
        self.list_widget = QtGui.QListWidget(self)
        add_server_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate('AddMarketsWizard',
                                              'Add Server Contract',
                                              "Title to a button to import an "
                                              "open transactions server "
                                              "contract."))
        button_box = QtGui.QDialogButtonBox()
        button_box.addButton(add_server_button, button_box.ActionRole)
        layout = QtGui.QVBoxLayout()

        layout.addWidget(self.list_widget)
        layout.addWidget(button_box)
        #layout.setStretch(0, 1)
        self.setLayout(layout)

        self.list_widget.currentRowChanged.connect(self.completeChanged.emit)
        #exchangeChanged)
        add_server_button.clicked.connect(self.showImportDialog)

    def exchangeChanged(self, row):
        self.completeChanged.emit()

    def initializePage(self):
        wizard = self.wizard()
        for exchange_proxy in dojima.exchanges.container:
            list_item = ExchangeListItem(exchange_proxy.name, self.list_widget)
            list_item.setNextPageId(
                wizard.addPage(exchange_proxy.getWizardPage(wizard)))

        self.list_widget.sortItems()
        self.list_widget.setCurrentRow(0)

    def isComplete(self):
        return bool(self.list_widget.currentItem())

    def nextId(self):
        item = self.list_widget.currentItem()
        if item is None:
            return 1
        return self.list_widget.currentItem().getNextPageId()

    def showImportDialog(self):
        dialog = dojima.ui.ot.contract.ServerContractImportDialog(self)
        if dialog.exec_():
            dojima.exchange_modules.opentxs.parse_servers()

            exchange_proxy =  dojima.exchanges.container.last
            if exchange_proxy is None:
                return

            list_item = ExchangeListItem(exchange_proxy.name, self.list_widget)
            list_item.setNextPageId(
                self.wizard().addPage(exchange_proxy.nextPage(self.wizard())))
            self.list_widget.sortItems()

            
class ExchangeListItem(QtGui.QListWidgetItem):
        
    def setNextPageId(self, page_id):
        self.nextPageId = page_id

    def getNextPageId(self):
        return self.nextPageId
