import logging
from PyQt4 import QtCore, QtGui

from tulpenmanie.model.commodity import CommoditiesModel
from tulpenmanie.model.market import MarketsModel

import tulpenmanie.network
import tulpenmanie.providers
from tulpenmanie.provider_modules import *

from tulpenmanie.ui.mainwindow import MainWindow

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
        self.exchanges_model = tulpenmanie.providers.ExchangesModel()

        for Item in tulpenmanie.providers.exchange_model_items:
            item = Item()
            self.exchanges_model.appendRow(item)

        # Network stuff
        self.network_manager = tulpenmanie.network.NetworkAccessManager()

        # Start the gui
        self.window = MainWindow()

    def run(self):
        self.window.show()
        res = self.exec_()
        self.exit()
        return res
