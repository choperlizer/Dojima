# Dojima, a markets client.
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

import otapi
from PyQt4 import QtCore, QtGui

class MarketAccountsDialog(QtGui.QDialog):

    def __init__(self, server_id, market_id, parent):
        super(MarketAccountsDialog, self).__init__(parent)

        base_label = QtGui.QLabel(
            QtCore.QCoreApplication.translate('MarketAccountsDialog',
                                              "base"))
        counter_label = QtGui.QLabel(
            QtCore.QCoreApplication.translate('MarketAccountsDialog',
                                              "counter"))

        base_combo = QtGui.QComboBox()
        counter_combo = QtGui.QComboBox()

        new_base_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate('MarketAccountDialog',
                                              "new account"))
        new_counter_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate('MarketAccountDialog',
                                              "new account"))

        layout = QtGui.QGridLayout()
        layout.addWidget(base_label, 0,0)
        layout.addWidget(counter_label, 0,1)
        layout.addWidget(base_combo, 1,0)
        layout.addWidget(counter_combo, 1,1)
        layout.addWidget(new_base_button, 2,0)
        layout.addWidget(new_counter_button, 2,1)

        # get the account balances and put them in the combo labels
