from PyQt4 import QtCore, QtGui
import getopt
import logging
import os
import sys


from model.commodity import CommoditiesModel
from model.market import MarketsModel
from model.exchange import ExchangesModel
from network import NetworkAccessManager

import services
from providers import *

from ui.mainwindow import MainWindow

class Manager(QtGui.QApplication):

    __instance = None

    def __init__(self, args):
        QtGui.QApplication.__init__(self, args)
        self.__class__.__instance = self
        logger = logging.getLogger(__name__)
        QtCore.QObject.manager = self

        self.setOrganizationName("Emery Hemingway")
        self.setApplicationName("Tulpenmanie")
        self.setApplicationVersion('alpha')

        self.commodities_model = CommoditiesModel()
        self.markets_model = MarketsModel()
        self.exchanges_model = ExchangesModel()

        self.exchange_classes = dict()
        for Exchange in services.exchanges:
            self.exchange_classes[Exchange.name] = Exchange

        self.accounts_models = dict()
        for Model in services.account_models:
            model = Model()
            self.accounts_models[model.name] = model

        self.exchange_account_classes = dict()
        for Account in services.exchange_accounts:
            self.exchange_account_classes[Account.name] = Account

        # Network stuff
        self.network_manager = NetworkAccessManager()

        self.window = MainWindow()

    def run(self):
        self.window.show()
        res = self.exec_()
        self.exit()
        return res


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    manager = Manager(sys.argv)
    sys.exit(manager.run())
