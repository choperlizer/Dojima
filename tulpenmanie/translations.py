# Tuplenmanie, a commodities market client.
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

account_id = QtCore.QCoreApplication.translate(
    'a unique indentifying string for an account', 'unique account identifier')
enable = QtCore.QCoreApplication.translate(
    'the state of if something shall be made active or not', 'enable')
exchange = QtCore.QCoreApplication.translate(
    'something that provides exchange service', 'exchange')
