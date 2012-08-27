# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui

from tulpenmanie.ui.commodity import EditCommoditiesTab
from tulpenmanie.ui.market import EditMarketsTab
from tulpenmanie.ui.exchange import EditExchangesTab
from tulpenmanie.ui.account import EditExchangeAccountsTab



class EditMarketsDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        super(EditMarketsDialog, self).__init__(parent)

        self.tab_widget = QtGui.QTabWidget()
        self.tab_widget.addTab(EditCommoditiesTab(), "&commodities")
        self.tab_widget.addTab(EditMarketsTab(), "&markets")

        button_box = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Save | 
            QtGui.QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save)
        button_box.rejected.connect(self.reject)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.tab_widget)
        layout.addWidget(button_box)
        self.setLayout(layout)
        
        self.setWindowTitle("edit commodities, markets")

    def save(self):
        for index in range(self.tab_widget.count()):
            self.tab_widget.widget(index).save()
        self.accept()


class EditProvidersDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        super(EditProvidersDialog, self).__init__(parent)

        self.tab_widget = QtGui.QTabWidget()
        self.tab_widget.addTab(EditExchangesTab(), "&exchanges")
        self.tab_widget.addTab(EditExchangeAccountsTab(), "&accounts")

        button_box = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Close)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.tab_widget)
        layout.addWidget(button_box)
        self.setLayout(layout)
        
        self.setWindowTitle("edit providers, account")
