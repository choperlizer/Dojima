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

from PyQt4 import QtCore

commodities = QtCore.QCoreApplication.translate(
    "plural of commodity", "commodities")
markets = QtCore.QCoreApplication.translate(
    "plural of market", "market")
exchanges = QtCore.QCoreApplication.translate(
    "plural of exchange", "exchanges")
accounts = QtCore.QCoreApplication.translate(
    "plural of account", "accounts")

base = QtCore.QCoreApplication.translate(
    "base commoditiy being traded", "base")
counter = QtCore.QCoreApplication.translate(
    "commoditiy used to trade against", "counter")

best_ask = QtCore.QCoreApplication.translate(
    "the lowest standing ask price", "ask")
best_bid = QtCore.QCoreApplication.translate(
    "the highest standing bid price", "bid")
last_price = QtCore.QCoreApplication.translate(
    "the price of the last executed order", "last")

new = QtCore.QCoreApplication.translate(
    "create something new", "new")
remove = QtCore.QCoreApplication.translate(
    "remove something", "remove")

refresh_rate = QtCore.QCoreApplication.translate(
    "the rate at which information is refreshed", "refresh rate")

account_id = QtCore.QCoreApplication.translate(
    'a unique indentifying string for an account', 'account identifier')

enable = QtCore.QCoreApplication.translate(
    'whether if something shall be made active or not', 'enable')

password = QtCore.QCoreApplication.translate(
    "secret string of characters used for authentication", "password")

exchange = QtCore.QCoreApplication.translate(
    'exchange service provider', 'exchange')
