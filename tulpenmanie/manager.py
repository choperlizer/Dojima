import getopt
import logging
import os
import sys
from PyQt4 import QtCore, QtGui

from model.commodity import CommoditiesModel
from model.market import MarketsModel
from network import NetworkAccessManager

import providers
from provider_modules import *

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
        self.setApplicationVersion('0.1.0')

        # Make settings models
        self.commodities_model = CommoditiesModel()
        self.markets_model = MarketsModel()
        self.exchanges_model = providers.ExchangesModel()

        for Item in providers.exchange_model_items:
            item = Item()
            self.exchanges_model.appendRow(item)

        # Network stuff
        self.network_manager = NetworkAccessManager()

        # Start the gui
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
