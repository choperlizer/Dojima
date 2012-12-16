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

from PyQt4 import QtCore

import dojima.model.commodities

class MarketsContainer(object):

    """ A container for containers that hold ExchangeProxys.

        Each ExchangeProxy may contain multiple markets.
    """

    def __init__(self):
        self.markets = dict()

    def __iter__(self):
        return self.markets.values().__iter__()

    def __len__(self):
        return len(self.markets)

    def addExchange(self, exchange_proxy, local_pair):
        base, counter = local_pair.split('_')
        b_row, c_row = dojima.model.commodities.local_model.getRows(base, counter)
        if (b_row is None) or (c_row is None):
            return

        if local_pair in self.markets:
            container = self.markets[local_pair]
        else:
            container = ExchangesContainer(local_pair)
            self.markets[local_pair] = container
        container.append(exchange_proxy)


class ExchangesContainer(object):

    def __init__(self, marketPair):
        self.exchanges = list()
        self.pair = marketPair
        self.base, self.counter = marketPair.split('_')

    def append(self, exchangeProxy):
        self.exchanges.append(exchangeProxy)

    def prettyName(self):
        base_name, counter_name = dojima.model.commodities.local_model.getNames(
            self.base, self.counter)

        return (base_name + ' / ' + counter_name)

    def __iter__(self):
        return self.exchanges.__iter__()

    def __len__(self):
        return len(self.exchanges)

    def __str__(self):
        return self.pair


container = MarketsContainer()
