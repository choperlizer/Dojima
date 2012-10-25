# Tulpenmanie, a markets client.
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


from tulpenmanie.model.commodities import commodities_model

class MarketsContainer(object):

    def __init__(self):
        self.markets = dict()

    def __iter__(self):
        return self.markets.values().__iter__()

    def __len__(self):
        return len(self.markets)

    def addExchange(self, exchange_proxy, local_pair):
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
        search = commodities_model.findItems(self.base)
        base_name = commodities_model.item(
            search[0].row(), commodities_model.NAME).text()

        search = commodities_model.findItems(self.counter)
        counter_name = commodities_model.item(
            search[0].row(), commodities_model.NAME).text()

        return (base_name + ' / ' + counter_name)

    def __iter__(self):
        return self.exchanges.__iter__()

    def __len__(self):
        return len(self.exchanges)

    def __str__(self):
        return self.pair


container = MarketsContainer()
