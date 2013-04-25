# Dōjima, a commodities market client.
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

from decimal import Decimal

from PyQt4 import QtCore


class BalanceProxy(QtCore.QObject):

    balance_total = QtCore.pyqtSignal([int], [Decimal])
    balance_liquid = QtCore.pyqtSignal([int], [Decimal])
    balance_total_changed = QtCore.pyqtSignal([int], [Decimal])
    balance_liquid_changed = QtCore.pyqtSignal([int], [Decimal])

    balance_total = QtCore.pyqtSignal([int], [Decimal])
    balance_liquid = QtCore.pyqtSignal([int], [Decimal])
    balance_total_changed = QtCore.pyqtSignal([int], [Decimal])
    balance_liquid_changed = QtCore.pyqtSignal([int], [Decimal])
