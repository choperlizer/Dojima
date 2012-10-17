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

from PyQt4 import QtCore, QtGui

import tulpenmanie.data.funds
import tulpenmanie.data.orders
from tulpenmanie.model.exchanges import exchanges_model

def register_exchange_model_item(ExchangeItem):
    item = ExchangeItem()
    exchanges_model.appendRow(item)

_exchange_classes = dict()
def register_exchange(exchange_class):
	_exchange_classes[exchange_class.exchange_name] = exchange_class


accounts = dict()
def register_account(account_class):
    accounts[account_class.exchange_name] = account_class


_exchange_objects = dict()
def get_exchange_object(exchange_name):
    exchange_name = str(exchange_name)
    if exchange_name in _exchange_objects:
        exchange_object = _exchange_objects[exchange_name]
    else:
        ExchangeClass = _exchange_classes[exchange_name]
        exchange_object = ExchangeClass()
        _exchange_objects[exchange_name] = exchange_object
    return exchange_object



#TODO decorate the functions below with @required_function

class Exchange:

    def pop_request(self):
        request = heapq.heappop(self._requests)
        request.send()
        self._replies.add(request)


class ExchangeAccount:

    def pop_request(self):
        request = heapq.heappop(self._requests)
        request.send()
        self._replies.add(request)

    def get_funds_proxy(self, symbol):
        if symbol not in self.funds_proxies:
            proxy = tulpenmanie.data.funds.FundsProxy(self)
            self.funds_proxies[symbol] = proxy
            return proxy
        return self.funds_proxies[symbol]

    def get_orders_proxy(self, remote_market):
        if remote_market not in self.orders_proxies:
            orders_proxy = tulpenmanie.data.orders.OrdersProxy(self)
            self.orders_proxies[remote_market] = orders_proxy
            return orders_proxy
        return self.orders_proxies[remote_market]

    def refresh(self):
        self.refresh_orders()
        self.refresh_funds()
