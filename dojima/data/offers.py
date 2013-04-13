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

from PyQt4 import QtCore, QtGui

"""
Offer models need to be consistant, so here are column index references.
"""

ID = 0
PRICE = 1
OUTSTANDING = 2
TYPE = 3
BASE = 4
COUNTER = 5
# use account ids, simple exchanges can just use TLA as account ids

ASK = 'a'
BID = 'b'


class Model(QtGui.QStandardItemModel):

    def __init__(self, parent=None):
        super(Model, self).__init__(parent)
        self.setColumnCount(6)

class _OffersModel(QtGui.QSortFilterProxyModel):

    def __init__(self, model, parent=None):
        super(_OffersModel, self).__init__(parent,
                                           dynamicSortFilter=True,
                                           filterKeyColumn=TYPE)
        self.setSourceModel(model)


    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                if section == ID:
                    return QtCore.QCoreApplication.translate('OffersModel',
                                                             "ID")
                if section == PRICE:
                    return self._price_label

                if section == OUTSTANDING:
                    return QtCore.QCoreApplication.translate('OffersModel',
                                                             "Amount")

class FilterAsksModel(_OffersModel):

    _price_label = QtCore.QCoreApplication.translate('OffersModel', "Ask",
                                                     "The label over the ask "
                                                     "price column")

    def __init__(self, model, parent=None):
        super(FilterAsksModel, self).__init__(model, parent)
        self.setFilterFixedString(ASK)


class FilterBidsModel(_OffersModel):
    _price_label = QtCore.QCoreApplication.translate('OffersModel', "Bid",
                                                     "The label over the bid "
                                                     "price column")

    def __init__(self, model, parent=None):
        super(FilterBidsModel, self).__init__(model, parent)
        self.setFilterFixedString(BID)
