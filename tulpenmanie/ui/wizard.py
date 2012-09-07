# Tulpenmanie, a commodities market client.
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

import tulpenmanie.translation
import tulpenmanie.ui.commodity
import tulpenmanie.ui.market
import tulpenmanie.ui.exchange
import tulpenmanie.ui.account


class Wizard(QtGui.QWizard):

    def __init__(self, parent=None):
        super(Wizard, self).__init__(parent)

        self.addPage(self.create_intro_page())
        for title, widget in ((tulpenmanie.translation.commodities,
                               tulpenmanie.ui.commodity.EditCommoditiesWidget()),
                              (tulpenmanie.translation.markets,
                               tulpenmanie.ui.market.EditMarketsWidget()),
                              (tulpenmanie.translation.exchanges,
                               tulpenmanie.ui.exchange.EditExchangesWidget()),
                              (tulpenmanie.translation.accounts,
                               tulpenmanie.ui.account.EditAccountsWidget()) ):
            page = QtGui.QWizardPage()
            page.setTitle(title)
            layout = QtGui.QVBoxLayout()
            layout.addWidget(widget)
            page.setLayout(layout)
            self.addPage(page)

    def create_intro_page(self):
        page = QtGui.QWizardPage()
        page.setTitle(QtCore.QCoreApplication.translate(
            "settings wizard",
            "inital markets and exchanges definition"))
        label = QtGui.QLabel(
            QtCore.QCoreApplication.translate(
                "First page of the wizard",
                """Tulpenmanie was conceived to be a customizable and """
                """extensible commodity exchange client. As such, it """
                """comes without any predefined commodities. First you """
                """must create at least two commodities, at least one """
                """market, map a local market to a remote one, and if """
                """you desire to trade, enter exchange account """
                """information."""))
        label.setWordWrap(True)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(label)
        page.setLayout(layout)
        return page
