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

class ExchangesContainer(object):

    def __init__(self):
        self.exchanges = dict()

    def __iter__(self):
        return self.exchanges.values().__iter__()

    def __len__(self):
        return len(self.exchanges)

    def addExchange(self, exchange_proxy):
        self.exchanges[exchange_proxy.name] = exchange_proxy

        
container = ExchangesContainer()
